"""Registra las condiciones de la máquina donde se ejecuta la práctica."""

import argparse
import json
import platform
import re
import subprocess
import sys
from pathlib import Path


def hardware(sistema: str) -> tuple[str, int]:
    if sistema == "Linux":
        cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8")
        modelo = re.search(r"^model name\s*:\s*(.+)$", cpuinfo, re.MULTILINE)
        procesador = modelo[1] if modelo else platform.processor() or platform.machine()
        meminfo = Path("/proc/meminfo").read_text(encoding="utf-8")
        memoria = re.search(r"^MemTotal:\s*(\d+)\s+kB$", meminfo, re.MULTILINE)
        if memoria is None:
            raise ValueError("No se encontró MemTotal en /proc/meminfo.")
        return procesador, int(memoria[1]) * 1024

    if sistema == "Windows":
        consulta = (
            "Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name; "
            "Get-CimInstance Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory"
        )
        salida = subprocess.check_output(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", consulta],
            text=True,
        )
        procesador, memoria = salida.strip().splitlines()
        return procesador.strip(), int(memoria)

    if sistema == "Darwin":
        procesador = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
        ).strip()
        memoria = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)
        return procesador, int(memoria)

    raise ValueError(f"Sistema operativo sin detección de hardware: {sistema}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("usuario", help="Usuario que figura en el identificador de la sesión")
    parser.add_argument("modo", choices=("procesos", "contenedores"))
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.usuario):
        parser.error("El usuario solo puede contener letras ASCII, números, guiones y guiones bajos.")

    destino = Path(__file__).resolve().parents[1] / "data" / f"maquina_{args.usuario}.json"
    try:
        procesador, ram_bytes = hardware(platform.system())
        ficha = {
            "sistema_operativo": platform.platform(),
            "procesador": procesador,
            "ram_bytes": ram_bytes,
            "python": platform.python_version(),
            "modo_ejecucion": args.modo,
        }
        with destino.open("x", encoding="utf-8") as archivo:
            json.dump(ficha, archivo, ensure_ascii=False, indent=2)
            archivo.write("\n")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"No se pudo registrar la máquina: {error}", file=sys.stderr)
        return 1

    print(f"Ficha guardada en data/{destino.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
