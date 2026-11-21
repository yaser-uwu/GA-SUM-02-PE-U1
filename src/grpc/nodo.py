"""Nodo gRPC con su propio reloj de Lamport.

Uso, desde la raíz del repositorio:
    python src/grpc/nodo.py nodo-A --sesion 20261119-201500-bryan
"""

import argparse
import csv
import sys
import threading
import time
from concurrent import futures
from datetime import datetime
from pathlib import Path

import grpc

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import mensajes_pb2
import mensajes_pb2_grpc
from src.common.config import HOST, NODOS, N_ENVIOS_LATENCIA, TAMANOS_MENSAJE

ENCABEZADO = ["nodo", "tipo_evento", "reloj", "hora_real", "contraparte", "msg_id"]
TIMEOUT_S = 10


class RegistroEventos:
    """Escribe los eventos de este nodo en su propio CSV."""

    def __init__(self, ruta):
        self.ruta = ruta
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._archivo = None
        self._escritor = None
        self.reiniciar()

    def reiniciar(self):
        with self._lock:
            if self._archivo is not None:
                self._archivo.close()
            self._archivo = self.ruta.open("w", encoding="utf-8", newline="")
            self._escritor = csv.writer(self._archivo, lineterminator="\n")
            self._escritor.writerow(ENCABEZADO)
            self._archivo.flush()

    def escribir(self, nodo, tipo_evento, reloj, contraparte, msg_id):
        hora_real = datetime.now().isoformat(timespec="milliseconds")
        with self._lock:
            self._escritor.writerow(
                [nodo, tipo_evento, reloj, hora_real, contraparte, msg_id]
            )
            self._archivo.flush()

    def cerrar(self):
        with self._lock:
            if self._archivo is not None:
                self._archivo.close()
                self._archivo = None


class Nodo:
    """Estado de un nodo: nombre, puerto, reloj y registro de eventos."""

    def __init__(self, nombre, sesion, registrar_eventos=True):
        self.nombre = nombre
        self.sesion = sesion
        self.puerto = NODOS[nombre]
        self.reloj = 0
        self.registrar_eventos = registrar_eventos
        self._lock = threading.Lock()
        self.registro = None
        if registrar_eventos:
            ruta = (
                RAIZ
                / "data"
                / sesion
                / "grpc"
                / "eventos"
                / "lamport-01"
                / f"{nombre}.csv"
            )
            self.registro = RegistroEventos(ruta)

    def reiniciar(self):
        with self._lock:
            self.reloj = 0
        if self.registro is not None:
            self.registro.reiniciar()

    def siguiente_reloj(self):
        """Regla de envío: incrementa el reloj antes de enviar."""
        with self._lock:
            self.reloj += 1
            return self.reloj

    def actualizar_reloj(self, timestamp_recibido):
        """Regla de recepción: max(local, recibido) + 1."""
        with self._lock:
            self.reloj = max(self.reloj, timestamp_recibido) + 1
            return self.reloj

    def enviar(self, destino):
        reloj = self.siguiente_reloj()
        msg_id = f"{self.nombre}:{reloj}"
        if self.registro is not None:
            self.registro.escribir(self.nombre, "envio", reloj, destino, msg_id)
        print(
            f"[{self.nombre}] envio -> {destino} | reloj={reloj} | {msg_id}",
            flush=True,
        )

        mensaje = mensajes_pb2.Mensaje(
            sender=self.nombre,
            timestamp=reloj,
            message=f"Hola desde {self.nombre}",
        )
        with grpc.insecure_channel(f"{HOST}:{NODOS[destino]}") as canal:
            stub = mensajes_pb2_grpc.MensajeriaStub(canal)
            acuse = stub.EnviarMensaje(mensaje, timeout=TIMEOUT_S)
        if not acuse.ok:
            raise RuntimeError(f"{destino}: {acuse.error}")
        return reloj


class ServicioMensajeria(mensajes_pb2_grpc.MensajeriaServicer):
    def __init__(self, nodo):
        self.nodo = nodo

    def EnviarMensaje(self, solicitud, contexto):
        if solicitud.sender not in NODOS or solicitud.timestamp <= 0:
            contexto.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            contexto.set_details("Mensaje invalido")
            return mensajes_pb2.Acuse(ok=False, error="Mensaje invalido")

        reloj = self.nodo.actualizar_reloj(solicitud.timestamp)
        if self.nodo.registro is not None:
            msg_id = f"{solicitud.sender}:{solicitud.timestamp}"
            self.nodo.registro.escribir(
                self.nodo.nombre, "recepcion", reloj, solicitud.sender, msg_id
            )
            print(
                f"[{self.nodo.nombre}] recepcion <- {solicitud.sender} | "
                f"reloj={reloj} | {msg_id}",
                flush=True,
            )
        return mensajes_pb2.Acuse(ok=True, error="")


class ServicioControl(mensajes_pb2_grpc.ControlServicer):
    def __init__(self, nodo):
        self.nodo = nodo
        self.canales = {}
        self.stubs = {}

    def cerrar(self):
        for canal in self.canales.values():
            canal.close()

    def PrepararLatencia(self, solicitud, contexto):
        if (
            self.nodo.registrar_eventos
            or solicitud.sesion != self.nodo.sesion
            or solicitud.nodo != self.nodo.nombre
        ):
            return mensajes_pb2.Acuse(error="Nodo, sesión o modo --sin-eventos incorrecto")

        for destino, puerto in NODOS.items():
            if destino == self.nodo.nombre:
                continue
            if destino not in self.canales:
                self.canales[destino] = grpc.insecure_channel(f"{HOST}:{puerto}")
            canal = self.canales[destino]
            try:
                grpc.channel_ready_future(canal).result(timeout=TIMEOUT_S)
            except grpc.FutureTimeoutError:
                return mensajes_pb2.Acuse(error=f"{destino} no está listo")
            self.stubs[destino] = mensajes_pb2_grpc.MensajeriaStub(canal)

        self.nodo.reiniciar()
        return mensajes_pb2.Acuse(ok=True)

    def MedirEnvios(self, orden, contexto):
        if (
            orden.destino not in self.stubs
            or orden.tamano_bytes not in TAMANOS_MENSAJE.values()
            or not orden.primer_envio
            or not orden.cantidad
            or orden.primer_envio + orden.cantidad - 1 > N_ENVIOS_LATENCIA
        ):
            contexto.abort(grpc.StatusCode.INVALID_ARGUMENT, "Orden de latencia inválida")

        invocar = self.stubs[orden.destino].EnviarMensaje
        payload = "x" * orden.tamano_bytes
        if orden.inicio_comun_ns:
            espera = (orden.inicio_comun_ns - time.perf_counter_ns()) / 1e9
            if not 0 < espera <= TIMEOUT_S:
                contexto.abort(grpc.StatusCode.FAILED_PRECONDITION, "Inicio común fuera de plazo")
            time.sleep(espera)

        for numero in range(orden.primer_envio, orden.primer_envio + orden.cantidad):
            if not contexto.is_active():
                return
            mensaje = mensajes_pb2.Mensaje(
                sender=self.nodo.nombre,
                timestamp=self.nodo.siguiente_reloj(),
                message=payload,
            )
            error = ""
            inicio = time.perf_counter_ns()
            try:
                acuse = invocar(mensaje, timeout=TIMEOUT_S)
                fin = time.perf_counter_ns()
                if not acuse.ok:
                    error = acuse.error or "Acuse negativo"
            except grpc.RpcError as exc:
                fin = time.perf_counter_ns()
                error = f"{exc.code().name}: {exc.details()}"
            yield mensajes_pb2.MuestraLatencia(
                envio_n=numero, inicio_ns=inicio, fin_ns=fin, error=error
            )
            if error:
                return

    def Reiniciar(self, solicitud, contexto):
        self.nodo.reiniciar()
        print(f"[{self.nodo.nombre}] reiniciado (reloj=0)", flush=True)
        return mensajes_pb2.Acuse(ok=True, error="")

    def OrdenarEnvio(self, solicitud, contexto):
        if solicitud.destino not in NODOS or solicitud.destino == self.nodo.nombre:
            return mensajes_pb2.Acuse(ok=False, error="Destino invalido")
        try:
            self.nodo.enviar(solicitud.destino)
        except grpc.RpcError as error:
            detalle = f"{error.code().name}: {error.details()}"
            print(f"[{self.nodo.nombre}] error: {detalle}", flush=True)
            return mensajes_pb2.Acuse(ok=False, error=detalle)
        except RuntimeError as error:
            print(f"[{self.nodo.nombre}] error: {error}", flush=True)
            return mensajes_pb2.Acuse(ok=False, error=str(error))
        return mensajes_pb2.Acuse(ok=True, error="")


def main():
    parser = argparse.ArgumentParser(description="Nodo gRPC con reloj de Lamport.")
    parser.add_argument("nombre", choices=sorted(NODOS))
    parser.add_argument(
        "--sesion",
        required=True,
        help="Identificador de sesión AAAAMMDD-HHMMSS-usuario",
    )
    parser.add_argument(
        "--sin-eventos",
        action="store_true",
        help="No registrar eventos de Lamport (solo para medir latencia)",
    )
    args = parser.parse_args()

    nodo = Nodo(
        args.nombre,
        args.sesion,
        registrar_eventos=not args.sin_eventos,
    )
    servidor = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), options=(("grpc.so_reuseport", 0),)
    )
    mensajes_pb2_grpc.add_MensajeriaServicer_to_server(
        ServicioMensajeria(nodo), servidor
    )
    control = ServicioControl(nodo)
    mensajes_pb2_grpc.add_ControlServicer_to_server(control, servidor)

    puerto = servidor.add_insecure_port(f"{HOST}:{nodo.puerto}")
    if puerto == 0:
        if nodo.registro is not None:
            nodo.registro.cerrar()
        raise RuntimeError(f"No se pudo abrir {HOST}:{nodo.puerto}")

    servidor.start()
    modo = "sin eventos" if args.sin_eventos else "eventos Lamport"
    print(
        f"[{nodo.nombre}] escuchando en {HOST}:{nodo.puerto} "
        f"(sesion {args.sesion}, {modo})",
        flush=True,
    )
    try:
        servidor.wait_for_termination()
    except KeyboardInterrupt:
        servidor.stop(grace=0)
        print(f"\n[{nodo.nombre}] detenido.", flush=True)
    finally:
        control.cerrar()
        if nodo.registro is not None:
            nodo.registro.cerrar()


if __name__ == "__main__":
    main()
