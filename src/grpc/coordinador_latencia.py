"""Coordina las mediciones de latencia gRPC en una sola máquina, desde la raíz."""

import argparse
import csv
import statistics
import subprocess
import sys
import time
from contextlib import ExitStack

import grpc

import mensajes_pb2
import mensajes_pb2_grpc
from coordinador_lamport import PATRON_SESION, detener_nodos, nueva_sesion
from nodo import RAIZ, TIMEOUT_S
from src.common.config import (
    HOST,
    NODOS,
    N_CORRIDAS,
    N_ENVIOS_LATENCIA,
    RUTAS_LAMPORT,
    TAMANOS_MENSAJE,
)

CAMPOS = ("mecanismo", "tamano", "tamano_bytes", "modo", "corrida")
LOTES_CONCURRENTES = (
    ("nodo-A", "nodo-B", 1, 34),
    ("nodo-B", "nodo-C", 35, 33),
    ("nodo-C", "nodo-A", 68, 33),
)


def reservar_intento(raiz, sesion, modo, tamano, corrida, intento):
    padre = raiz / sesion / "grpc" / "latencia" / modo / tamano / f"corrida-{corrida:02d}"
    padre.mkdir(parents=True, exist_ok=True)
    automatico = intento is None
    if automatico:
        numeros = (
            int(sufijo)
            for ruta in padre.glob("intento-*")
            if (sufijo := ruta.name.removeprefix("intento-")).isascii() and sufijo.isdigit()
        )
        intento = max(numeros, default=0) + 1
    while True:
        carpeta = padre / f"intento-{intento:02d}"
        try:
            carpeta.mkdir()
            return carpeta
        except FileExistsError:
            if not automatico:
                raise RuntimeError(f"{carpeta} ya existe; no se sobrescribe") from None
            intento += 1


def medir(stubs, modo, tamano_bytes):
    filas = []
    errores = []
    comienzos = []
    finales = []
    inicio_control = time.perf_counter_ns()
    inicio_comun = 0

    def ordenar(origen, destino, primero, cantidad):
        orden = mensajes_pb2.OrdenLatencia(
            destino=destino,
            tamano_bytes=tamano_bytes,
            primer_envio=primero,
            cantidad=cantidad,
            inicio_comun_ns=inicio_comun,
        )
        return stubs[origen].MedirEnvios(orden, timeout=(cantidad + 1) * TIMEOUT_S)

    def recoger(flujo, origen, destino, primero, cantidad):
        recibidos = 0
        try:
            for muestra in flujo:
                if muestra.inicio_ns:
                    comienzos.append(muestra.inicio_ns)
                if muestra.fin_ns:
                    finales.append(muestra.fin_ns)
                if muestra.error:
                    errores.append(f"{origen} -> {destino}, envío {muestra.envio_n}: {muestra.error}")
                    return
                if (
                    recibidos >= cantidad
                    or muestra.envio_n != primero + recibidos
                    or muestra.inicio_ns <= 0
                    or muestra.inicio_ns < inicio_comun
                    or muestra.fin_ns <= muestra.inicio_ns
                ):
                    errores.append(f"{origen} -> {destino}: muestra inválida")
                    return
                filas.append((muestra.envio_n, (muestra.fin_ns - muestra.inicio_ns) / 1e9))
                recibidos += 1
            if recibidos != cantidad:
                errores.append(f"{origen} -> {destino}: {recibidos}/{cantidad} muestras")
        except grpc.RpcError as exc:
            errores.append(f"{origen} -> {destino}: {exc.code().name}: {exc.details()}")
        finally:
            flujo.cancel()
        if modo == "concurrente":
            print(f"  {origen} -> {destino}: {recibidos}/{cantidad}", flush=True)

    flujos = []
    try:
        if modo == "secuencial":
            rutas = RUTAS_LAMPORT * 5
            for numero, (origen, destino) in enumerate(rutas, start=1):
                recoger(ordenar(origen, destino, numero, 1), origen, destino, numero, 1)
                if errores:
                    break
        else:
            # Las tres llamadas quedan en curso antes de recoger sus muestras.
            # perf_counter_ns usa el mismo reloj monotónico en todos los procesos locales.
            inicio_comun = time.perf_counter_ns() + 500_000_000
            for lote in LOTES_CONCURRENTES:
                flujos.append((ordenar(*lote), lote))
            for flujo, lote in flujos:
                recoger(flujo, *lote)
    except grpc.RpcError as exc:
        errores.append(f"{exc.code().name}: {exc.details()}")
    except KeyboardInterrupt:
        errores.append("Interrumpida por el usuario")
    finally:
        for flujo, _ in flujos:
            flujo.cancel()

    filas.sort()
    if not errores and [numero for numero, _ in filas] != list(range(1, N_ENVIOS_LATENCIA + 1)):
        errores.append(f"Se esperaban los envíos 1..{N_ENVIOS_LATENCIA}")
    inicio = inicio_comun or min(comienzos, default=inicio_control)
    fin = time.perf_counter_ns() if errores else max(finales)
    return filas, max(0, fin - inicio) / 1e9, errores


def escribir_csvs(carpeta, modo, tamano, corrida, filas, duracion_s, errores):
    base = ("grpc", tamano, TAMANOS_MENSAJE[tamano], modo, corrida)
    with (carpeta / "latencia.csv").open("x", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow((*CAMPOS, "envio_n", "rtt_s"))
        escritor.writerows((*base, numero, f"{rtt:.9f}") for numero, rtt in filas)
    estado = "fallida" if errores else "completa"
    with (carpeta / "duracion.csv").open("x", encoding="utf-8", newline="") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow((*CAMPOS, "duracion_s", "envios_ok", "estado"))
        escritor.writerow((*base, f"{duracion_s:.9f}", len(filas), estado))
    return estado


def ejecutar_corrida(stubs, raiz, sesion, modo, tamano, corrida, intento):
    carpeta = reservar_intento(raiz, sesion, modo, tamano, corrida, intento)
    tamano_bytes = TAMANOS_MENSAJE[tamano]
    print(f"\n{modo} | {tamano} ({tamano_bytes} bytes) | corrida {corrida:02d}", flush=True)
    print(f"Salida: {carpeta}", flush=True)
    try:
        for nombre, stub in stubs.items():
            solicitud = mensajes_pb2.PreparacionLatencia(sesion=sesion, nodo=nombre)
            acuse = stub.PrepararLatencia(solicitud, timeout=3 * TIMEOUT_S)
            if not acuse.ok:
                raise RuntimeError(f"{nombre}: {acuse.error}")
        filas, duracion, errores = medir(stubs, modo, tamano_bytes)
    except (RuntimeError, grpc.RpcError, KeyboardInterrupt) as exc:
        # No empezó ningún envío si falló la preparación.
        filas, duracion, errores = [], 0, [str(exc) or "Interrumpida por el usuario"]

    estado = escribir_csvs(carpeta, modo, tamano, corrida, filas, duracion, errores)
    print(f"Resultado: {len(filas)}/{N_ENVIOS_LATENCIA} envíos OK | "
          f"duración={duracion:.6f} s | estado={estado}", flush=True)
    if filas:
        mediana_ms = statistics.median(rtt for _, rtt in filas) * 1000
        print(f"RTT mediano: {mediana_ms:.3f} ms", flush=True)
    for error in errores:
        print(f"ERROR: {error}", file=sys.stderr)
    return not errores


def main(raiz_datos=RAIZ / "data"):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sesion", help="Identificador AAAAMMDD-HHMMSS-usuario")
    parser.add_argument("--modo", choices=("secuencial", "concurrente"))
    parser.add_argument("--tamano", choices=TAMANOS_MENSAJE)
    parser.add_argument("--corrida", type=int, choices=range(N_CORRIDAS + 1))
    parser.add_argument("--intento", type=int, help="Intento explícito (debe ser nuevo)")
    parser.add_argument("--manual", action="store_true", help="Usar nodos locales con --sin-eventos")
    parser.add_argument("--matriz", action="store_true", help="Ejecutar las 14 corridas")
    args = parser.parse_args()

    sesion = args.sesion or nueva_sesion()
    if not PATRON_SESION.fullmatch(sesion):
        parser.error("La sesión debe tener el formato AAAAMMDD-HHMMSS-usuario")
    if args.intento is not None and args.intento < 1:
        parser.error("--intento debe ser mayor que cero")
    if args.matriz:
        if any(valor is not None for valor in (args.modo, args.tamano, args.corrida, args.intento)):
            parser.error("--matriz no se combina con --modo, --tamano, --corrida o --intento")
        plan = [
            (modo, tamano, corrida)
            for tamano in TAMANOS_MENSAJE
            for modo, corridas in (("secuencial", range(N_CORRIDAS + 1)), ("concurrente", (1,)))
            for corrida in corridas
        ]
    else:
        modo = args.modo or "secuencial"
        corrida = args.corrida if args.corrida is not None else int(modo == "concurrente")
        if modo == "concurrente" and corrida != 1:
            parser.error("El modo concurrente solo admite --corrida 1")
        plan = [(modo, args.tamano or "corto", corrida)]

    print(f"Sesión: {sesion} | gRPC | {len(plan)} corrida(s)", flush=True)
    with ExitStack() as recursos:
        procesos = []
        recursos.callback(detener_nodos, procesos)
        try:
            if not args.manual:
                for nodo in NODOS:
                    procesos.append(subprocess.Popen(
                        [sys.executable, str(RAIZ / "src/grpc/nodo.py"), nodo,
                         "--sesion", sesion, "--sin-eventos"],
                        cwd=RAIZ,
                    ))

            stubs = {}
            for nombre, puerto in NODOS.items():
                canal = recursos.enter_context(grpc.insecure_channel(f"{HOST}:{puerto}"))
                try:
                    grpc.channel_ready_future(canal).result(timeout=TIMEOUT_S)
                except grpc.FutureTimeoutError:
                    raise RuntimeError(f"{nombre} no está listo en {HOST}:{puerto}") from None
                stubs[nombre] = mensajes_pb2_grpc.ControlStub(canal)

            for modo, tamano, corrida in plan:
                if not ejecutar_corrida(stubs, raiz_datos, sesion, modo, tamano, corrida, args.intento):
                    return 1
        except (OSError, RuntimeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            return 130
    print(f"Corridas completas: {len(plan)}/{len(plan)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
