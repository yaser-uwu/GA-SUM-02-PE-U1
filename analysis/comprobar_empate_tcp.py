"""Ejecuta dos envíos TCP independientes a C y registra el empate de Lamport."""

import argparse
import asyncio
import csv
import json
import re
import sys
from pathlib import Path

from verificar_lamport import ENCABEZADO, verificar


RAIZ = Path(__file__).resolve().parents[1]
SERVIDOR = RAIZ / "src" / "sockets" / "server.py"
CERRAR = '{"accion":"cerrar"}\n'


async def ejecutar() -> list[dict]:
    procesos = {}
    registros = {}
    try:
        for nodo in ("nodo-C", "nodo-A", "nodo-B"):
            proceso = await asyncio.create_subprocess_exec(
                sys.executable, str(SERVIDOR), "--nodo", nodo,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            procesos[nodo] = proceso
            listo = json.loads(await asyncio.wait_for(proceso.stdout.readline(), timeout=8))
            if listo.get("tipo") != "listo" or listo.get("reloj") != 0:
                raise ValueError(f"{nodo} no arrancó con reloj cero: {listo}")
            print(f"{nodo} listo en {listo['host']}:{listo['puerto']} | reloj=0", flush=True)

        # Ningún emisor espera la respuesta del otro para iniciar su envío.
        orden = json.dumps({
            "accion": "enviar", "destino": "nodo-C", "message": "Prueba de empate",
        }) + "\n" + CERRAR
        emisores = ("nodo-A", "nodo-B")
        salidas = await asyncio.wait_for(
            asyncio.gather(*(procesos[nodo].communicate(orden.encode()) for nodo in emisores)),
            timeout=15,
        )
        for nodo, (salida, _) in zip(emisores, salidas):
            registros[nodo] = [json.loads(linea) for linea in salida.splitlines()]
        salida, _ = await asyncio.wait_for(procesos["nodo-C"].communicate(CERRAR.encode()), timeout=8)
        registros["nodo-C"] = [json.loads(linea) for linea in salida.splitlines()]
    finally:
        for proceso in procesos.values():
            if proceso.returncode is None:
                try:
                    proceso.kill()
                except ProcessLookupError:
                    pass
                await proceso.wait()

    eventos = []
    for nodo, salida in registros.items():
        if procesos[nodo].returncode != 0 or any(r["tipo"] == "error" for r in salida):
            raise ValueError(f"{nodo}: ejecución fallida: {salida}")
        if nodo != "nodo-C" and not any(r["tipo"] == "acuse" and r["ok"] for r in salida):
            raise ValueError(f"{nodo}: falta el acuse de C")
        eventos.extend(r["datos"] for r in salida if r["tipo"] == "evento")
    return eventos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sesion", required=True, help="Identificador AAAAMMDD-HHMMSS-usuario")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[A-Za-z0-9_-]+", args.sesion):
        parser.error("Usa el formato AAAAMMDD-HHMMSS-usuario.")
    ruta = RAIZ / "data" / args.sesion / "sockets" / "eventos" / "empate-01" / "eventos.csv"

    try:
        ruta.parent.mkdir(parents=True, exist_ok=False)
        eventos = asyncio.run(ejecutar())
        with ruta.open("x", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=ENCABEZADO)
            escritor.writeheader()
            escritor.writerows(eventos)
        if not verificar(ruta, 2):
            return 1
        envios = {
            (evento["msg_id"], evento["contraparte"], evento["reloj"])
            for evento in eventos if evento["tipo_evento"] == "envio"
        }
        if envios != {("nodo-A:1", "nodo-C", 1), ("nodo-B:1", "nodo-C", 1)}:
            raise ValueError("Los dos primeros envíos a C no empataron con reloj 1.")
    except (OSError, ValueError, TimeoutError) as error:
        print(f"No se pudo comprobar el empate: {error}", file=sys.stderr)
        return 1

    print(f"Empate comprobado entre nodo-A:1 y nodo-B:1. CSV: {ruta.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
