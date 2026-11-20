"""Coordinador de los 20 intercambios gRPC con reloj de Lamport.

Uso, desde la raíz del repositorio:
    python src/grpc/coordinador_lamport.py
    python src/grpc/coordinador_lamport.py --manual --sesion 20261119-201500-bryan

En el modo normal lanza los tres nodos como procesos hijos, ordena los
20 envíos, une los CSV de cada nodo en eventos.csv y ejecuta el verificador.
En el modo --manual se conecta a nodos que ya están en marcha.
"""

import argparse
import csv
import getpass
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import grpc

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import mensajes_pb2
import mensajes_pb2_grpc
from src.common.config import HOST, NODOS, RUTAS_LAMPORT

TIMEOUT_S = 10
ENCABEZADO = ["nodo", "tipo_evento", "reloj", "hora_real", "contraparte", "msg_id"]
PATRON_SESION = re.compile(r"^\d{8}-\d{6}-[A-Za-z0-9._-]+$")


def nueva_sesion():
    usuario = re.sub(r"[^A-Za-z0-9._-]", "-", getpass.getuser())
    return datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + usuario


def esperar_nodo(nombre):
    with grpc.insecure_channel(f"{HOST}:{NODOS[nombre]}") as canal:
        grpc.channel_ready_future(canal).result(timeout=TIMEOUT_S)


def lanzar_nodos(sesion):
    procesos = []
    for nombre in NODOS:
        proceso = subprocess.Popen(
            [
                sys.executable,
                str(RAIZ / "src" / "grpc" / "nodo.py"),
                nombre,
                "--sesion",
                sesion,
            ],
            cwd=RAIZ,
        )
        procesos.append(proceso)
    return procesos


def detener_nodos(procesos):
    for proceso in procesos:
        if proceso.poll() is None:
            proceso.terminate()
    for proceso in procesos:
        try:
            proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proceso.kill()


def unir_eventos(sesion):
    carpeta = RAIZ / "data" / sesion / "grpc" / "eventos" / "lamport-01"
    filas = []
    for nombre in NODOS:
        ruta = carpeta / f"{nombre}.csv"
        with ruta.open(encoding="utf-8", newline="") as archivo:
            filas.extend(csv.DictReader(archivo))

    esperados = 2 * len(RUTAS_LAMPORT)
    if len(filas) != esperados:
        raise RuntimeError(
            f"Se esperaban {esperados} eventos y se leyeron {len(filas)}"
        )

    filas.sort(key=lambda fila: fila["hora_real"])
    eventos = carpeta / "eventos.csv"
    with eventos.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=ENCABEZADO, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)
    return eventos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sesion", help="Identificador AAAAMMDD-HHMMSS-usuario")
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Usar nodos ya iniciados en otras terminales",
    )
    args = parser.parse_args()

    sesion = args.sesion or nueva_sesion()
    if not PATRON_SESION.fullmatch(sesion):
        parser.error("La sesión debe tener el formato AAAAMMDD-HHMMSS-usuario")

    procesos = []
    canales = []
    try:
        if args.manual:
            print(f"Sesión: {sesion} (nodos ya iniciados)", flush=True)
        else:
            print(f"Sesión: {sesion}", flush=True)
            print("Iniciando los tres nodos...", flush=True)
            procesos = lanzar_nodos(sesion)

        for nombre in NODOS:
            try:
                esperar_nodo(nombre)
            except grpc.FutureTimeoutError:
                raise RuntimeError(
                    f"{nombre} no respondió en {TIMEOUT_S} s"
                ) from None
            print(f"{nombre} listo en {HOST}:{NODOS[nombre]}", flush=True)

        stubs = {}
        for nombre in NODOS:
            canal = grpc.insecure_channel(f"{HOST}:{NODOS[nombre]}")
            canales.append(canal)
            stub = mensajes_pb2_grpc.ControlStub(canal)
            acuse = stub.Reiniciar(mensajes_pb2.Vacio(), timeout=TIMEOUT_S)
            if not acuse.ok:
                raise RuntimeError(f"{nombre}: no se pudo reiniciar ({acuse.error})")
            stubs[nombre] = stub

        for numero, (origen, destino) in enumerate(RUTAS_LAMPORT, start=1):
            acuse = stubs[origen].OrdenarEnvio(
                mensajes_pb2.Orden(destino=destino), timeout=TIMEOUT_S
            )
            if not acuse.ok:
                raise RuntimeError(
                    f"Paso {numero} ({origen}->{destino}): {acuse.error}"
                )
            print(
                f"Paso {numero:02d}/{len(RUTAS_LAMPORT)}: {origen} -> {destino} OK",
                flush=True,
            )

        eventos = unir_eventos(sesion)
        print(f"\nEventos escritos en {eventos.relative_to(RAIZ)}", flush=True)

        resultado = subprocess.run(
            [
                sys.executable,
                str(RAIZ / "analysis" / "verificar_lamport.py"),
                str(eventos),
                str(len(RUTAS_LAMPORT)),
            ],
            cwd=RAIZ,
        )
        if resultado.returncode != 0:
            raise RuntimeError("La verificación de Lamport falló")
    finally:
        for canal in canales:
            canal.close()
        detener_nodos(procesos)


if __name__ == "__main__":
    main()
