"""Genera las tablas LaTeX de la verificación de Lamport a partir de los CSV de eventos.

Uso (desde la raíz del repositorio):
    python3 analysis/tabla_lamport.py --tcp <eventos.csv> --grpc <eventos.csv> --empate <eventos.csv>

Escribe docs/tablas/lamport_resumen.tex y docs/tablas/empate.tex.
"""

import argparse
import csv
from pathlib import Path

NODOS = ["nodo-A", "nodo-B", "nodo-C"]


def leer(ruta):
    with open(ruta, encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def resumir(filas):
    """Cuenta eventos, pares envío-recepción y violaciones de la regla de Lamport."""
    envios = {f["msg_id"]: int(f["reloj"]) for f in filas if f["tipo_evento"] == "envio"}
    recepciones = {f["msg_id"]: int(f["reloj"]) for f in filas if f["tipo_evento"] == "recepcion"}
    pares = [m for m in envios if m in recepciones]
    # Violación: la recepción no tiene un reloj estrictamente mayor que el envío.
    violaciones = sum(1 for m in pares if recepciones[m] <= envios[m])
    finales = {n: max(int(f["reloj"]) for f in filas if f["nodo"] == n) for n in NODOS}
    return len(filas), len(pares), violaciones, finales


def escribir_resumen(tcp, grpc, ruta):
    lineas = [
        r"\small\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Mecanismo & Eventos & Pares & Violaciones & Reloj final A & Reloj final B & Reloj final C \\",
        r"\midrule",
    ]
    for nombre, filas in (("Sockets TCP", tcp), ("gRPC", grpc)):
        eventos, pares, violaciones, finales = resumir(filas)
        celdas = [nombre, eventos, pares, violaciones] + [finales[n] for n in NODOS]
        lineas.append(" & ".join(str(c) for c in celdas) + r" \\")
    lineas += [r"\bottomrule", r"\end{tabular}"]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def escribir_empate(filas, ruta):
    lineas = [
        r"\small\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{llrll}",
        r"\toprule",
        r"Nodo & Evento & Reloj & Contraparte & Mensaje \\",
        r"\midrule",
    ]
    for f in filas:
        celdas = [f["nodo"], f["tipo_evento"], f["reloj"], f["contraparte"], f["msg_id"]]
        lineas.append(" & ".join(celdas) + r" \\")
    lineas += [r"\bottomrule", r"\end{tabular}"]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tcp", type=Path, required=True)
    parser.add_argument("--grpc", type=Path, required=True)
    parser.add_argument("--empate", type=Path, required=True)
    parser.add_argument("--salida", type=Path, default=Path("docs"))
    args = parser.parse_args()

    carpeta = args.salida / "tablas"
    carpeta.mkdir(parents=True, exist_ok=True)
    escribir_resumen(leer(args.tcp), leer(args.grpc), carpeta / "lamport_resumen.tex")
    escribir_empate(leer(args.empate), carpeta / "empate.tex")
    print(f"Tablas escritas en {carpeta}")


if __name__ == "__main__":
    main()
