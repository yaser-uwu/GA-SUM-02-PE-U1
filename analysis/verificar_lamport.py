"""Verifica los eventos de Lamport de una ejecución de TCP o gRPC."""

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ENCABEZADO = ["nodo", "tipo_evento", "reloj", "hora_real", "contraparte", "msg_id"]
NODOS = {"nodo-A", "nodo-B", "nodo-C"}


@dataclass(frozen=True)
class Evento:
    nodo: str
    contraparte: str
    reloj: int


def leer_campos(linea: str) -> list[str]:
    # El contrato define un evento por línea. Una comilla abierta en una fila
    # inválida no debe impedir que se revisen las siguientes.
    campos = next(csv.reader([linea], strict=True, skipinitialspace=True))
    return [campo.strip() for campo in campos]


def entero(texto: str) -> int:
    if not re.fullmatch(r"[+-]?[0-9]+", texto):
        raise ValueError(texto)
    return int(texto)


def leer_evento(linea: str) -> tuple[str, str, Evento]:
    campos = leer_campos(linea)
    if len(campos) != len(ENCABEZADO):
        raise ValueError("columnas incorrectas")
    if "" in campos:
        raise ValueError("campo vacío")

    nodo, tipo, reloj_texto, hora_real, contraparte, msg_id = campos
    if tipo not in {"envio", "recepcion"}:
        raise ValueError(f"tipo desconocido [{tipo}]")
    if nodo not in NODOS or contraparte not in NODOS or nodo == contraparte:
        raise ValueError(f"ruta de nodos inválida [{nodo} → {contraparte}]")

    try:
        hora = datetime.fromisoformat(hora_real)
    except ValueError:
        raise ValueError(f"hora_real inválida [{hora_real}]") from None
    if hora.tzinfo is not None or hora.isoformat(timespec="milliseconds") != hora_real:
        raise ValueError(f"hora_real inválida [{hora_real}]")

    try:
        reloj = entero(reloj_texto)
    except ValueError:
        raise ValueError(f"reloj no numérico [{reloj_texto}]") from None
    if reloj <= 0:
        raise ValueError(f"reloj no positivo [{reloj}]")

    partes_id = msg_id.split(":")
    if len(partes_id) != 2 or not partes_id[0]:
        raise ValueError(f"msg_id inválido [{msg_id}]")
    emisor, timestamp = partes_id
    try:
        reloj_envio = entero(timestamp)
    except ValueError:
        raise ValueError(f"timestamp inválido [{msg_id}]") from None
    if reloj_envio <= 0 or msg_id != f"{emisor}:{reloj_envio}":
        raise ValueError(f"msg_id inválido [{msg_id}]")

    if tipo == "envio" and (nodo != emisor or reloj != reloj_envio):
        raise ValueError(f"envío inconsistente [{msg_id}]")
    if tipo == "recepcion" and contraparte != emisor:
        raise ValueError(f"recepción inconsistente [{msg_id}]")

    return msg_id, tipo, Evento(nodo, contraparte, reloj)


def verificar(ruta: Path, pares_esperados: int | None = None) -> bool:
    mensajes: dict[str, dict[str, Evento]] = {}
    duplicados: set[str] = set()
    errores = 0
    filas = 0
    pares_validos = 0

    with ruta.open(encoding="utf-8", newline="") as archivo:
        try:
            encabezado = leer_campos(next(archivo, ""))
        except csv.Error:
            encabezado = []
        if encabezado != ENCABEZADO:
            print(f"Archivo: {ruta} | Error: encabezado incorrecto")
            imprimir_resumen(ruta, 0, 0, 0, 1)
            return False

        for numero_linea, linea in enumerate(archivo, start=2):
            filas += 1
            try:
                msg_id, tipo, evento = leer_evento(linea)
            except (ValueError, csv.Error) as error:
                print(f"Archivo: {ruta} | Línea {numero_linea}: {error}")
                errores += 1
                continue

            par = mensajes.setdefault(msg_id, {})
            if tipo in par:
                evento_duplicado = "envío duplicado" if tipo == "envio" else "recepción duplicada"
                print(
                    f"Archivo: {ruta} | Línea {numero_linea}: "
                    f"{evento_duplicado} [{msg_id}]"
                )
                duplicados.add(msg_id)
                errores += 1
            else:
                par[tipo] = evento

    for msg_id, par in mensajes.items():
        envio = par.get("envio")
        recepcion = par.get("recepcion")
        if envio is None or recepcion is None:
            print(f"Archivo: {ruta} | ID: {msg_id} | Error: par incompleto")
            errores += 1
            continue
        if msg_id in duplicados:
            continue
        if envio.contraparte != recepcion.nodo or recepcion.contraparte != envio.nodo:
            print(f"Archivo: {ruta} | ID: {msg_id} | Error: nodos inconsistentes")
            errores += 1
            continue
        if recepcion.reloj <= envio.reloj:
            print(
                f"Archivo: {ruta} | ID: {msg_id} | "
                f"Error Lamport: envío={envio.reloj}, recepción={recepcion.reloj}"
            )
            errores += 1
            continue

        pares_validos += 1
        print(f"ID: {msg_id} | Envío: {envio.reloj} | Recepción: {recepcion.reloj} | OK")

    if filas == 0:
        print(f"Archivo: {ruta} | Error: no hay filas de eventos")
        errores += 1
    elif pares_esperados is not None and (
        filas != pares_esperados * 2 or len(mensajes) != pares_esperados
    ):
        print(
            f"Archivo: {ruta} | Error: se esperaban {pares_esperados} pares "
            f"({pares_esperados * 2} filas)"
        )
        errores += 1

    imprimir_resumen(ruta, filas, len(mensajes), pares_validos, errores)
    return errores == 0


def imprimir_resumen(
    ruta: Path, filas: int, mensajes: int, pares_validos: int, errores: int
) -> None:
    print("\n===== RESUMEN =====")
    print(f"Archivo: {ruta}")
    print(f"Filas leídas: {filas}")
    print(f"Mensajes identificados: {mensajes}")
    print(f"Pares válidos: {pares_validos}")
    print(f"Errores: {errores}")
    resultado = "VERIFICACIÓN CORRECTA" if errores == 0 else "SE DETECTARON ERRORES"
    print(f"Resultado: {resultado}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", nargs="?", type=Path, default=Path("eventos_prueba.csv"))
    parser.add_argument("pares_esperados", nargs="?", type=entero)
    args = parser.parse_args()
    if args.pares_esperados is not None and args.pares_esperados < 1:
        parser.error("pares_esperados debe ser un entero mayor que cero")

    try:
        return 0 if verificar(args.archivo, args.pares_esperados) else 1
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Archivo: {args.archivo} | Error de lectura: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
