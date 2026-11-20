"""Coordinador del piloto de latencia gRPC.

Uso, desde la raíz del repositorio:
    python src/grpc/coordinador_latencia.py --sesion 20261120-120000-bryan
    python src/grpc/coordinador_latencia.py --manual --sesion 20261120-120000-bryan
    python src/grpc/coordinador_latencia.py --tamano largo --corrida 01

En el modo normal lanza los tres nodos con --sin-eventos, mide 100 envíos
secuenciales y escribe latencia.csv y duracion.csv. En el modo --manual se
conecta a nodos que ya están en marcha con --sin-eventos.
"""

import argparse
import csv
import getpass
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import grpc

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import mensajes_pb2
import mensajes_pb2_grpc
from src.common.config import (
    HOST,
    NODOS,
    N_CORRIDAS,
    N_ENVIOS_LATENCIA,
    RUTAS_LAMPORT,
    TAMANOS_MENSAJE,
)

TIMEOUT_S = 10
MECANISMO = "grpc"
MODO = "secuencial"
COLS_LATENCIA = [
    "mecanismo",
    "tamano",
    "tamano_bytes",
    "modo",
    "corrida",
    "envio_n",
    "rtt_s",
]
COLS_DURACION = [
    "mecanismo",
    "tamano",
    "tamano_bytes",
    "modo",
    "corrida",
    "duracion_s",
    "envios_ok",
    "estado",
]
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
                "--sin-eventos",
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


def ruta_intento(sesion, tamano, corrida, intento):
    return (
        RAIZ
        / "data"
        / sesion
        / MECANISMO
        / "latencia"
        / MODO
        / tamano
        / f"corrida-{corrida:02d}"
        / f"intento-{intento:02d}"
    )


def rutas_latencia():
    if N_ENVIOS_LATENCIA % len(RUTAS_LAMPORT) != 0:
        raise RuntimeError(
            f"{N_ENVIOS_LATENCIA} envíos no se pueden repartir en "
            f"{len(RUTAS_LAMPORT)} rutas"
        )
    return RUTAS_LAMPORT * (N_ENVIOS_LATENCIA // len(RUTAS_LAMPORT))


def medir_secuencial(stubs, tamano_bytes):
    rutas = rutas_latencia()
    payload = "x" * tamano_bytes
    filas = []
    envios_ok = 0
    error = ""

    inicio = time.perf_counter()
    try:
        for numero, (origen, destino) in enumerate(rutas, start=1):
            mensaje = mensajes_pb2.Mensaje(
                sender=origen,
                timestamp=numero,
                message=payload,
            )
            antes = time.perf_counter()
            try:
                acuse = stubs[destino].EnviarMensaje(mensaje, timeout=TIMEOUT_S)
            except grpc.RpcError as exc:
                error = (
                    f"paso {numero} ({origen}->{destino}): "
                    f"{exc.code().name}: {exc.details()}"
                )
                print(f"ERROR: {error}", flush=True)
                break

            rtt_s = time.perf_counter() - antes
            if not acuse.ok:
                error = f"paso {numero} ({origen}->{destino}): {acuse.error}"
                print(f"ERROR: {error}", flush=True)
                break

            filas.append({"envio_n": numero, "rtt_s": rtt_s})
            envios_ok += 1
            if numero % 20 == 0 or numero == len(rutas):
                print(f"{numero:03d}/{len(rutas)} envíos OK", flush=True)
    except KeyboardInterrupt:
        error = "interrumpido por el usuario"
        print("\nEjecución interrumpida.", flush=True)

    duracion_s = time.perf_counter() - inicio
    estado = "completa" if envios_ok == len(rutas) and not error else "fallida"
    return filas, duracion_s, envios_ok, estado, error


def escribir_csvs(carpeta, tamano, tamano_bytes, corrida, filas, duracion_s, envios_ok, estado):
    carpeta.mkdir(parents=True, exist_ok=True)

    latencia = carpeta / "latencia.csv"
    with latencia.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(COLS_LATENCIA)
        for fila in filas:
            escritor.writerow(
                [
                    MECANISMO,
                    tamano,
                    tamano_bytes,
                    MODO,
                    corrida,
                    fila["envio_n"],
                    f"{fila['rtt_s']:.9f}",
                ]
            )

    duracion = carpeta / "duracion.csv"
    with duracion.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(COLS_DURACION)
        escritor.writerow(
            [
                MECANISMO,
                tamano,
                tamano_bytes,
                MODO,
                corrida,
                f"{duracion_s:.9f}",
                envios_ok,
                estado,
            ]
        )

    return latencia, duracion


def verificar_piloto(filas, duracion_s, envios_ok, estado):
    errores = []
    if len(filas) != N_ENVIOS_LATENCIA:
        errores.append(
            f"latencia.csv tiene {len(filas)} filas y se esperaban "
            f"{N_ENVIOS_LATENCIA}"
        )
    if sorted(fila["envio_n"] for fila in filas) != list(
        range(1, N_ENVIOS_LATENCIA + 1)
    ):
        errores.append("los envíos no están numerados del 1 al 100")
    if any(fila["rtt_s"] <= 0 for fila in filas):
        errores.append("hay un RTT no positivo")
    if envios_ok != N_ENVIOS_LATENCIA:
        errores.append(f"envios_ok={envios_ok}, se esperaban {N_ENVIOS_LATENCIA}")
    if estado != "completa":
        errores.append(f"estado={estado}, se esperaba completa")
    if duracion_s <= 0:
        errores.append("duracion_s no es positiva")
    return errores


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sesion", help="Identificador AAAAMMDD-HHMMSS-usuario")
    parser.add_argument(
        "--tamano",
        choices=sorted(TAMANOS_MENSAJE),
        default="corto",
        help="corto=100 bytes, largo=10240 bytes",
    )
    parser.add_argument(
        "--corrida",
        type=int,
        choices=range(0, N_CORRIDAS + 1),
        default=0,
        help="0=calentamiento; 1 a 5=corridas válidas",
    )
    parser.add_argument("--intento", type=int, default=1, help="Número de intento")
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Usar nodos ya iniciados con --sin-eventos",
    )
    args = parser.parse_args()

    if args.intento < 1:
        parser.error("--intento debe ser mayor que cero")

    sesion = args.sesion or nueva_sesion()
    if not PATRON_SESION.fullmatch(sesion):
        parser.error("La sesión debe tener el formato AAAAMMDD-HHMMSS-usuario")

    tamano_bytes = TAMANOS_MENSAJE[args.tamano]
    carpeta = ruta_intento(sesion, args.tamano, args.corrida, args.intento)

    print(f"Sesión: {sesion}", flush=True)
    print(
        f"Mecanismo: {MECANISMO} | Modo: {MODO} | "
        f"Tamaño: {args.tamano} ({tamano_bytes} bytes)",
        flush=True,
    )
    print(
        f"Corrida: {args.corrida:02d} | Intento: {args.intento:02d}",
        flush=True,
    )
    print(f"Salida: {carpeta.relative_to(RAIZ)}", flush=True)

    procesos = []
    canales = []
    codigo = 0
    try:
        if args.manual:
            print("Usando nodos ya iniciados con --sin-eventos", flush=True)
        else:
            print("Iniciando los tres nodos en modo sin eventos...", flush=True)
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
            stubs[nombre] = mensajes_pb2_grpc.MensajeriaStub(canal)

        filas, duracion_s, envios_ok, estado, error = medir_secuencial(
            stubs, tamano_bytes
        )
        latencia, duracion = escribir_csvs(
            carpeta,
            args.tamano,
            tamano_bytes,
            args.corrida,
            filas,
            duracion_s,
            envios_ok,
            estado,
        )

        print(f"\nLatencia escrita en {latencia.relative_to(RAIZ)}", flush=True)
        print(f"Duración escrita en {duracion.relative_to(RAIZ)}", flush=True)
        print(
            f"Resultado: {envios_ok}/{N_ENVIOS_LATENCIA} envíos OK | "
            f"duración={duracion_s:.6f} s | estado={estado}",
            flush=True,
        )

        if filas:
            rtts_ms = [fila["rtt_s"] * 1000 for fila in filas]
            print(
                f"RTT: min={min(rtts_ms):.3f} ms | "
                f"mediana={statistics.median(rtts_ms):.3f} ms | "
                f"max={max(rtts_ms):.3f} ms",
                flush=True,
            )

        errores = verificar_piloto(filas, duracion_s, envios_ok, estado)
        if error:
            errores.append(error)
        if errores:
            for detalle in errores:
                print(f"ERROR: {detalle}", flush=True)
            print("Verificación del piloto: CON ERRORES", flush=True)
            codigo = 1
        else:
            print("Verificación del piloto: CORRECTA", flush=True)
    finally:
        for canal in canales:
            canal.close()
        detener_nodos(procesos)

    return codigo


if __name__ == "__main__":
    sys.exit(main())
