import argparse
import csv
import json
import queue
import re
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import HOST, NODOS, N_INTERCAMBIOS

RAIZ = Path(__file__).resolve().parents[2]
COLUMNAS = ["nodo", "tipo_evento", "reloj", "hora_real", "contraparte", "msg_id"]
CICLO = [("nodo-A", "nodo-B"), ("nodo-B", "nodo-C"), ("nodo-C", "nodo-A"),
         ("nodo-A", "nodo-C"), ("nodo-C", "nodo-B"), ("nodo-B", "nodo-A")]
RUTAS = CICLO * 3 + CICLO[:2]


def ejecutar(args):
    carpeta = RAIZ / "data" / args.sesion / "sockets" / "eventos" / args.ejecucion
    carpeta.mkdir(parents=True, exist_ok=False)
    ruta = carpeta / "eventos.csv"
    procesos = {}
    hilos = []
    colas = {nodo: queue.Queue() for nodo in NODOS}
    errores = queue.Queue()
    lock = threading.Lock()
    conteo = {"eventos": 0}
    with ruta.open("x", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        archivo.flush()

        def recoger(nodo, proceso):
            try:
                for linea in proceso.stdout:
                    registro = json.loads(linea)
                    if registro.get("tipo") == "evento":
                        with lock:
                            escritor.writerow(registro["datos"])
                            archivo.flush()
                            conteo["eventos"] += 1
                    elif registro.get("tipo") == "error":
                        errores.put(f"{nodo}: {registro.get('detalle')}")
                        colas[nodo].put(registro)
                    else:
                        colas[nodo].put(registro)
            except (ValueError, OSError, KeyError) as error:
                errores.put(f"{nodo}: {error}")
            finally:
                colas[nodo].put({"tipo": "fin"})

        def esperar(nodo, tipo):
            registro = colas[nodo].get(timeout=12)
            if registro.get("tipo") != tipo:
                raise RuntimeError(f"{nodo}: se esperaba {tipo}, se recibió {registro}")
            return registro

        try:
            for nodo in NODOS:
                comando = [sys.executable, "-u", str(Path(__file__).with_name("server.py")),
                           "--nodo", nodo, "--host", args.host,
                           "--puerto-base", str(args.puerto_base)]
                proceso = subprocess.Popen(comando, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                           errors="strict")
                procesos[nodo] = proceso
                hilo = threading.Thread(target=recoger, args=(nodo, proceso))
                hilo.start()
                hilos.append(hilo)
            for nodo in NODOS:
                listo = esperar(nodo, "listo")
                print(f"{nodo} listo en {listo['host']}:{listo['puerto']}; reloj=0", flush=True)
            for paso, (origen, destino) in enumerate(RUTAS, 1):
                orden = {"accion": "enviar", "destino": destino,
                         "message": f"Intercambio {paso:02d} de Lamport"}
                procesos[origen].stdin.write(json.dumps(orden) + "\n")
                procesos[origen].stdin.flush()
                acuse = esperar(origen, "acuse")
                print(f"{paso:02d}/20 {origen} -> {destino} | {acuse['msg_id']} | acuse OK", flush=True)
        finally:
            for proceso in procesos.values():
                try:
                    proceso.stdin.write('{"accion":"cerrar"}\n')
                    proceso.stdin.flush()
                except (OSError, ValueError):
                    pass
                proceso.stdin.close()
            for proceso in procesos.values():
                try:
                    proceso.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proceso.kill()
                    proceso.wait()
            for hilo in hilos:
                hilo.join()
            for proceso in procesos.values():
                proceso.stdout.close()
        if not errores.empty():
            raise RuntimeError(errores.get())
        if any(p.returncode != 0 for p in procesos.values()) or conteo["eventos"] != 40:
            raise RuntimeError(f"Ejecución incompleta: {conteo['eventos']} eventos; revisar procesos")
    print(f"CSV: {ruta.relative_to(RAIZ).as_posix()}", flush=True)
    verificador = RAIZ / "analysis" / "verificar_lamport.py"
    resultado = subprocess.run([sys.executable, str(verificador), str(ruta), "20"], check=False)
    if resultado.returncode:
        raise RuntimeError("El CSV no superó el verificador del equipo")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Ejecuta las 20 rutas TCP con tres procesos y guarda eventos")
    parser.add_argument("--sesion", default=datetime.now().strftime("%Y%m%d-%H%M%S-kevin"))
    parser.add_argument("--ejecucion", default="lamport-01")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--puerto-base", type=int, default=min(NODOS.values()))
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[a-zA-Z0-9_-]+", args.sesion):
        parser.error("Usa una sesión AAAAMMDD-HHMMSS-usuario")
    if not re.fullmatch(r"lamport-[0-9]{2,}", args.ejecucion):
        parser.error("Usa una ejecución como lamport-01 o lamport-02")
    if not 1 <= args.puerto_base <= 65533:
        parser.error("Puerto base fuera de rango")
    if N_INTERCAMBIOS != len(RUTAS):
        parser.error("La configuración no coincide con las 20 rutas del contrato")
    try:
        return ejecutar(args)
    except (OSError, ValueError, RuntimeError, queue.Empty, KeyboardInterrupt) as error:
        print(f"No se completó la ejecución: {error}", file=sys.stderr)
        print("Se conservan los datos generados; usa otra ejecución para repetir.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
