"""Genera o verifica el manifiesto SHA-256 de los CSV crudos."""

import argparse
import hashlib
import re
import sys
from pathlib import Path


def huellas_csv(raiz: Path) -> dict[str, str]:
    huellas = {}
    for ruta in sorted((raiz / "data").rglob("*.csv")):
        if ruta.is_file():
            with ruta.open("rb") as archivo:
                huellas[ruta.relative_to(raiz).as_posix()] = hashlib.file_digest(
                    archivo, "sha256"
                ).hexdigest()
    return huellas


def generar(manifiesto: Path, huellas: dict[str, str]) -> int:
    if not huellas:
        print("No hay CSV crudos en data/ para generar SHA256SUMS.", file=sys.stderr)
        return 1

    with manifiesto.open("x", encoding="utf-8", newline="\n") as archivo:
        for ruta, huella in huellas.items():
            archivo.write(f"{huella}  {ruta}\n")
    print(f"data/SHA256SUMS generado con {len(huellas)} CSV.")
    return 0


def verificar(manifiesto: Path, huellas: dict[str, str]) -> int:
    lineas = manifiesto.read_text(encoding="utf-8").splitlines()
    if not lineas:
        print("data/SHA256SUMS está vacío.", file=sys.stderr)
        return 1

    registrados = set()
    errores = 0
    for numero, linea in enumerate(lineas, start=1):
        huella, separador, ruta = linea.partition("  ")
        if not separador or not ruta or not re.fullmatch(r"[0-9a-f]{64}", huella):
            print(f"data/SHA256SUMS:{numero}: entrada inválida", file=sys.stderr)
        elif ruta in registrados:
            print(f"data/SHA256SUMS:{numero}: ruta repetida: {ruta}", file=sys.stderr)
        else:
            registrados.add(ruta)
            if ruta not in huellas:
                print(f"{ruta}: no está entre los CSV de data/", file=sys.stderr)
            elif huellas[ruta] != huella:
                print(f"{ruta}: huella distinta", file=sys.stderr)
            else:
                print(f"{ruta}: OK")
                continue
        errores += 1

    for ruta in sorted(huellas.keys() - registrados):
        print(f"{ruta}: falta en data/SHA256SUMS", file=sys.stderr)
        errores += 1

    return 1 if errores else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true", help="Comprueba el manifiesto guardado")
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    manifiesto = raiz / "data" / "SHA256SUMS"
    try:
        huellas = huellas_csv(raiz)
        if args.verificar:
            return verificar(manifiesto, huellas)
        return generar(manifiesto, huellas)
    except (OSError, UnicodeError) as error:
        print(f"Error con data/SHA256SUMS: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
