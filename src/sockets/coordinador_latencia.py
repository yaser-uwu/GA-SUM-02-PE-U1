import argparse
import csv
import json
import queue
import re
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import HOST, NODOS, N_CORRIDAS, N_ENVIOS_LATENCIA, TAMANOS_MENSAJE
from client import RUTAS
from server import leer_json

RAIZ = Path(__file__).resolve().parents[2]
LATENCIA = ['mecanismo', 'tamano', 'tamano_bytes', 'modo', 'corrida', 'envio_n', 'rtt_s']
DURACION = ['mecanismo', 'tamano', 'tamano_bytes', 'modo', 'corrida', 'duracion_s', 'envios_ok', 'estado']


def iniciar_nodos(host, puerto_base):
    procesos = []
    try:
        for nombre in NODOS:
            proceso = subprocess.Popen(
                [sys.executable, '-u', str(Path(__file__).with_name('server.py')),
                 '--nodo', nombre, '--host', host, '--puerto-base', str(puerto_base),
                 '--sin-eventos'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8',
            )
            procesos.append(proceso)
            salida = queue.Queue()
            threading.Thread(target=lambda p=proceso, q=salida: q.put(p.stdout.readline()),
                             daemon=True).start()
            listo = json.loads(salida.get(timeout=10))
            if listo.get('tipo') != 'listo':
                raise RuntimeError(f'{nombre} no pudo iniciar: {listo}')
            print(f"{nombre} listo en {host}:{listo['puerto']} | sin registro de eventos", flush=True)
        return procesos
    except BaseException:
        detener_nodos(procesos)
        raise


def detener_nodos(procesos):
    for proceso in procesos:
        if proceso.poll() is None:
            try:
                proceso.stdin.write('{"accion":"cerrar"}\n')
                proceso.stdin.flush()
            except (OSError, ValueError):
                pass
    for proceso in procesos:
        try:
            proceso.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.wait()
        proceso.stdin.close()
        proceso.stdout.close()


def medir_solicitud(host, puerto, origen, timestamp, mensaje):
    with socket.create_connection((host, puerto), timeout=5) as conexion:
        with conexion.makefile('rb') as entrada:
            inicio = time.perf_counter()
            contenido = json.dumps({'sender': origen, 'timestamp': timestamp,
                                    'message': mensaje}).encode('utf-8') + b'\n'
            conexion.sendall(contenido)
            respuesta = leer_json(entrada)
            rtt = time.perf_counter() - inicio
        if not isinstance(respuesta, dict) or respuesta.get('ok') is not True:
            raise ValueError(f'Acuse rechazado: {respuesta}')
    return rtt


def medir_corrida(args, tamano, modo, corrida, carpeta):
    carpeta.mkdir(parents=True, exist_ok=False)
    comunes = ['sockets', tamano, TAMANOS_MENSAJE[tamano], modo, corrida]
    mensaje = 'x' * TAMANOS_MENSAJE[tamano]
    puertos = {nombre: args.puerto_base + i for i, nombre in enumerate(NODOS)}
    muestras = []
    errores = []
    lock = threading.Lock()

    def cliente(rutas, numeros, salida=None):
        relojes = {nombre: 0 for nombre in NODOS}
        if salida is not None:
            salida.wait(timeout=10)
        for (origen, destino), numero in zip(rutas, numeros):
            relojes[origen] += 1
            try:
                rtt = medir_solicitud(args.host, puertos[destino], origen,
                                      relojes[origen], mensaje)
                with lock:
                    muestras.append((numero, rtt))
            except (OSError, ValueError) as error:
                with lock:
                    errores.append(f'{origen}->{destino}, envío {numero}: {error}')
                break

    inicio = None
    try:
        if modo == 'secuencial':
            rutas = RUTAS * (N_ENVIOS_LATENCIA // len(RUTAS))
            inicio = time.perf_counter()
            cliente(rutas, range(1, N_ENVIOS_LATENCIA + 1))
        else:
            salida = threading.Barrier(4)
            trabajos = [('nodo-A', 'nodo-B', 1, 34),
                        ('nodo-B', 'nodo-C', 35, 67),
                        ('nodo-C', 'nodo-A', 68, 100)]
            with ThreadPoolExecutor(max_workers=3) as ejecutor:
                futuros = [ejecutor.submit(cliente, [(a, b)] * (fin-inicio_n+1),
                                           range(inicio_n, fin+1), salida)
                           for a, b, inicio_n, fin in trabajos]
                inicio = time.perf_counter()
                salida.wait(timeout=10)
                for futuro in futuros:
                    futuro.result()
    except (KeyboardInterrupt, threading.BrokenBarrierError, RuntimeError) as error:
        errores.append(str(error) or 'Ejecución interrumpida')
    finally:
        duracion = time.perf_counter() - inicio if inicio is not None else 0
        muestras.sort()
        completa = (not errores and [n for n, _ in muestras] == list(range(1, 101)))
        estado = 'completa' if completa else 'fallida'
        with (carpeta / 'latencia.csv').open('x', newline='', encoding='utf-8') as archivo:
            escritor = csv.writer(archivo, lineterminator='\n')
            escritor.writerow(LATENCIA)
            escritor.writerows(comunes + [n, f'{rtt:.9f}'] for n, rtt in muestras)
        with (carpeta / 'duracion.csv').open('x', newline='', encoding='utf-8') as archivo:
            escritor = csv.writer(archivo, lineterminator='\n')
            escritor.writerow(DURACION)
            escritor.writerow(comunes + [f'{duracion:.9f}', len(muestras), estado])
    print(f'{modo} | {tamano} | corrida {corrida:02d} | '
          f'{len(muestras)}/100 | {estado} | {duracion:.6f} s', flush=True)
    for error in errores:
        print(f'ERROR: {error}', file=sys.stderr)
    return completa


def main():
    parser = argparse.ArgumentParser(description='Mide TCP y conserva los CSV del contrato del equipo')
    parser.add_argument('--sesion', default=datetime.now().strftime('%Y%m%d-%H%M%S-kevin'))
    parser.add_argument('--host', default=HOST)
    parser.add_argument('--puerto-base', type=int, default=min(NODOS.values()))
    parser.add_argument('--tamano', choices=['corto', 'largo', 'ambos'], default='ambos')
    parser.add_argument('--modo', choices=['secuencial', 'concurrente', 'ambos'], default='ambos')
    parser.add_argument('--corrida', type=int, help='Sin este argumento ejecuta calentamiento y corridas 1 a 5')
    parser.add_argument('--intento', type=int, default=1)
    args = parser.parse_args()
    if not re.fullmatch(r'\d{8}-\d{6}-[A-Za-z0-9_-]+', args.sesion):
        parser.error('Sesión inválida; usa AAAAMMDD-HHMMSS-usuario')
    if not 1 <= args.puerto_base <= 65533 or args.intento < 1:
        parser.error('Puerto base o número de intento inválido')
    if args.corrida is not None and not 0 <= args.corrida <= N_CORRIDAS:
        parser.error('Corrida fuera del intervalo 0 a 5')
    if args.corrida is not None and args.modo != 'secuencial' and args.corrida != 1:
        parser.error('Concurrencia usa la corrida 1; indica --modo secuencial para otras corridas')
    if N_ENVIOS_LATENCIA != 100 or len(RUTAS) != 20:
        parser.error('La configuración no coincide con el contrato de 100 solicitudes y 20 rutas')
    tamanos = list(TAMANOS_MENSAJE) if args.tamano == 'ambos' else [args.tamano]
    modos = ['secuencial', 'concurrente'] if args.modo == 'ambos' else [args.modo]
    plan = []
    for modo in modos:
        corridas = [1] if modo == 'concurrente' else list(range(N_CORRIDAS + 1))
        if args.corrida is not None:
            corridas = [args.corrida]
        for tamano in tamanos:
            for corrida in corridas:
                carpeta = RAIZ/'data'/args.sesion/'sockets'/'latencia'/modo/tamano/f'corrida-{corrida:02d}'/f'intento-{args.intento:02d}'
                if carpeta.exists():
                    parser.error(f'El intento ya existe y se conserva: {carpeta}')
                plan.append((tamano, modo, corrida, carpeta))
    procesos = []
    try:
        print(f'Sesión: {args.sesion}', flush=True)
        procesos = iniciar_nodos(args.host, args.puerto_base)
        for tamano, modo, corrida, carpeta in plan:
            if not medir_corrida(args, tamano, modo, corrida, carpeta):
                return 1
        print(f'Finalizado: {len(plan)} corridas completas. CSV originales en data/{args.sesion}', flush=True)
        return 0
    except (OSError, ValueError, RuntimeError, queue.Empty, KeyboardInterrupt) as error:
        print(f'No se completó la medición: {error}', file=sys.stderr)
        return 1
    finally:
        detener_nodos(procesos)


if __name__ == '__main__':
    raise SystemExit(main())
