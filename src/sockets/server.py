import argparse
import json
import socket
import sys
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import HOST, NODOS

LIMITE = 65536
SALIDA = threading.Lock()


def informar(tipo, **datos):
    with SALIDA:
        print(json.dumps({"tipo": tipo, **datos}), flush=True)


def leer_json(entrada):
    linea = entrada.readline(LIMITE + 1)
    if not linea or len(linea) > LIMITE or not linea.endswith(b"\n"):
        raise ValueError("Mensaje incompleto o demasiado largo")
    return json.loads(linea.decode("utf-8"))


class Nodo:
    def __init__(self, nombre, host, puertos, registrar_eventos=True):
        self.nombre = nombre
        self.host = host
        self.puertos = puertos
        self.reloj = 0
        self.registrar_eventos = registrar_eventos
        self.lock = threading.Lock()

    def evento(self, tipo, contraparte, msg_id):
        if not self.registrar_eventos:
            return
        informar("evento", datos={
            "nodo": self.nombre,
            "tipo_evento": tipo,
            "reloj": self.reloj,
            "hora_real": datetime.now().isoformat(timespec="milliseconds"),
            "contraparte": contraparte,
            "msg_id": msg_id,
        })

    def recibir(self, conexion):
        try:
            with conexion.makefile("rb") as entrada:
                mensaje = leer_json(entrada)
            if not isinstance(mensaje, dict) or set(mensaje) != {"sender", "timestamp", "message"}:
                raise ValueError("Se requieren sender, timestamp y message")
            origen = mensaje["sender"]
            reloj = mensaje["timestamp"]
            if not isinstance(origen, str) or origen not in self.puertos or origen == self.nombre:
                raise ValueError("Emisor inválido")
            if type(reloj) is not int or reloj < 1 or not isinstance(mensaje["message"], str):
                raise ValueError("timestamp debe ser entero positivo y message debe ser texto")
            with self.lock:
                self.reloj = max(self.reloj, reloj) + 1
                self.evento("recepcion", origen, f"{origen}:{reloj}")
            respuesta = {"ok": True}
        except (ValueError, UnicodeError) as error:
            respuesta = {"ok": False, "error": str(error)}
        conexion.sendall(json.dumps(respuesta).encode("utf-8") + b"\n")

    def enviar(self, destino, texto):
        if not isinstance(destino, str) or destino not in self.puertos or destino == self.nombre or not isinstance(texto, str):
            raise ValueError("Destino o texto inválido")
        with socket.create_connection((self.host, self.puertos[destino]), timeout=5) as conexion:
            with self.lock:
                timestamp = self.reloj + 1
                mensaje = {"sender": self.nombre, "timestamp": timestamp, "message": texto}
                contenido = json.dumps(mensaje, ensure_ascii=False).encode("utf-8") + b"\n"
                if len(contenido) > LIMITE:
                    raise ValueError("Mensaje demasiado largo")
                self.reloj = timestamp
                self.evento("envio", destino, f"{self.nombre}:{timestamp}")
                conexion.sendall(contenido)
            with conexion.makefile("rb") as entrada:
                respuesta = leer_json(entrada)
            if not isinstance(respuesta, dict) or respuesta.get("ok") is not True:
                raise ValueError(f"Acuse rechazado: {respuesta}")
        informar("acuse", msg_id=f"{self.nombre}:{timestamp}", destino=destino, ok=True)


def servir(servidor, nodo, detener):
    while not detener.is_set():
        try:
            conexion, _ = servidor.accept()
        except socket.timeout:
            continue
        except OSError:
            return
        with conexion:
            conexion.settimeout(5)
            try:
                nodo.recibir(conexion)
            except (OSError, ValueError) as error:
                informar("error", detalle=str(error))


def main():
    parser = argparse.ArgumentParser(description="Nodo TCP con un reloj compartido por envío y recepción")
    parser.add_argument("--nodo", choices=NODOS, required=True)
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--puerto-base", type=int, default=min(NODOS.values()))
    parser.add_argument("--sin-eventos", action="store_true",
                        help="Desactiva el registro de eventos durante las mediciones")
    args = parser.parse_args()
    if not 1 <= args.puerto_base <= 65533:
        parser.error("Puerto base fuera de rango")
    puertos = {nombre: args.puerto_base + i for i, nombre in enumerate(NODOS)}
    nodo = Nodo(args.nodo, args.host, puertos, registrar_eventos=not args.sin_eventos)
    detener = threading.Event()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((args.host, puertos[args.nodo]))
        servidor.listen()
        servidor.settimeout(0.2)
        receptor = threading.Thread(target=servir, args=(servidor, nodo, detener))
        receptor.start()
        informar("listo", nodo=args.nodo, host=args.host, puerto=puertos[args.nodo], reloj=0)
        try:
            for linea in sys.stdin:
                try:
                    orden = json.loads(linea)
                    if orden.get("accion") == "cerrar":
                        break
                    if orden.get("accion") != "enviar":
                        raise ValueError("Acción desconocida")
                    nodo.enviar(orden["destino"], orden["message"])
                except (OSError, ValueError, KeyError, TypeError) as error:
                    informar("error", detalle=str(error))
        finally:
            detener.set()
            receptor.join(timeout=6)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OSError as error:
        informar("error", detalle=str(error))
        raise SystemExit(1)
