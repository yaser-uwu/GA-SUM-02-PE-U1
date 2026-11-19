"""Lector del experimento PE-U1 (sockets TCP y gRPC).

Lee y agrupa los CSV de una sesión y comprueba que cumplan docs/CONTRATO.md.

Uso, desde la raíz del repositorio:
    python analysis/analisis.py data/<sesion>
"""
import argparse
import sys
from itertools import product
from pathlib import Path

import pandas as pd

COLS_LATENCIA = ["mecanismo", "tamano", "tamano_bytes", "modo", "corrida", "envio_n", "rtt_s"]
COLS_DURACION = ["mecanismo", "tamano", "tamano_bytes", "modo", "corrida",
                 "duracion_s", "envios_ok", "estado"]
TAMANO_BYTES = {"corto": 100, "largo": 10240}
CORRIDAS_VALIDAS = {"secuencial": 5, "concurrente": 1}
MECANISMOS = ["sockets", "grpc"]
ENVIOS = 100
CLAVE = ["mecanismo", "modo", "tamano", "corrida"]


def leer_csv(ruta, columnas):
    """Lee un CSV y falla con un mensaje claro si falta una columna del contrato."""
    df = pd.read_csv(ruta, encoding="utf-8")
    faltan = [c for c in columnas if c not in df.columns]
    if faltan:
        raise ValueError(f"{ruta}: faltan las columnas {faltan}")
    return df[columnas]


def leer_intento(carpeta):
    """Lee latencia.csv y duracion.csv de un intento y los contrasta con su ruta."""
    # .../<mecanismo>/latencia/<modo>/<tamano>/corrida-NN/intento-NN
    p = carpeta.parts
    mecanismo, modo, tamano = p[-6], p[-4], p[-3]
    corrida, intento = int(p[-2].split("-")[1]), int(p[-1].split("-")[1])
    if tamano not in TAMANO_BYTES or modo not in CORRIDAS_VALIDAS:
        raise ValueError(f"{carpeta}: modo o tamaño desconocidos ({modo}, {tamano})")

    lat = leer_csv(carpeta / "latencia.csv", COLS_LATENCIA)
    dur = leer_csv(carpeta / "duracion.csv", COLS_DURACION)
    if len(dur) != 1:
        raise ValueError(f"{carpeta}: duracion.csv debe tener una fila y tiene {len(dur)}")

    esperado = {"mecanismo": mecanismo, "modo": modo, "tamano": tamano,
                "corrida": corrida, "tamano_bytes": TAMANO_BYTES[tamano]}
    for nombre, df in (("latencia.csv", lat), ("duracion.csv", dur)):
        for col, valor in esperado.items():
            if not (df[col] == valor).all():
                raise ValueError(f"{carpeta / nombre}: la columna {col} no coincide "
                                 f"con la ruta (se esperaba {valor})")

    estado = dur.at[0, "estado"]
    if estado not in ("completa", "fallida"):
        raise ValueError(f"{carpeta}: estado desconocido '{estado}'")
    if estado == "completa" and (sorted(lat["envio_n"]) != list(range(1, ENVIOS + 1))
                                 or dur.at[0, "envios_ok"] != ENVIOS):
        raise ValueError(f"{carpeta}: marcada como completa pero no tiene los envíos 1..{ENVIOS}")

    return lat.assign(intento=intento), dur.assign(intento=intento, filas=len(lat))


def cargar_sesion(sesion):
    """Devuelve todos los intentos de la sesión: (latencias, duraciones)."""
    carpetas = sorted(f.parent for f in
                      Path(sesion).glob("*/latencia/*/*/corrida-*/intento-*/latencia.csv"))
    if not carpetas:
        raise FileNotFoundError(f"No hay intentos de latencia en {sesion}")
    lats, durs = zip(*(leer_intento(c) for c in carpetas))
    return pd.concat(lats, ignore_index=True), pd.concat(durs, ignore_index=True)


def intentos_usados(lat, dur):
    """Un solo intento completo por corrida: el de menor número (docs/CONTRATO.md)."""
    completos = dur[dur["estado"] == "completa"].sort_values("intento")
    usados = completos.drop_duplicates(CLAVE, keep="first")
    lat_usada = lat.merge(usados[CLAVE + ["intento"]], on=CLAVE + ["intento"])
    lat_usada["calentamiento"] = lat_usada["corrida"] == 0
    usados = usados.assign(calentamiento=usados["corrida"] == 0)
    return lat_usada, usados


def revisar_protocolo(usados):
    """Avisa de las combinaciones que no cumplen las repeticiones del protocolo."""
    avisos = []
    for mecanismo, modo, tamano in product(MECANISMOS, CORRIDAS_VALIDAS, TAMANO_BYTES):
        g = usados[(usados["mecanismo"] == mecanismo) & (usados["modo"] == modo)
                   & (usados["tamano"] == tamano)]
        validas = int((g["corrida"] >= 1).sum())
        esperadas = CORRIDAS_VALIDAS[modo]
        if validas < esperadas:
            avisos.append(f"{mecanismo}/{modo}/{tamano}: {validas} de {esperadas} corridas válidas")
        if modo == "secuencial" and not (g["corrida"] == 0).any():
            avisos.append(f"{mecanismo}/{modo}/{tamano}: falta la corrida de calentamiento")
    return avisos


def main():
    parser = argparse.ArgumentParser(description="Lee y valida los CSV de una sesión.")
    parser.add_argument("sesion", help="carpeta data/<sesion>")
    args = parser.parse_args()

    lat, dur = cargar_sesion(args.sesion)
    lat_usada, usados = intentos_usados(lat, dur)

    print(f"Sesión: {args.sesion}")
    print(f"Intentos leídos: {len(dur)} | fallidos: {(dur['estado'] == 'fallida').sum()} "
          f"| corridas completas usadas: {len(usados)}")
    resumen = usados.sort_values(CLAVE)[CLAVE + ["intento", "filas", "duracion_s"]]
    print(resumen.to_string(index=False))

    avisos = revisar_protocolo(usados)
    for aviso in avisos:
        print(f"AVISO: {aviso}")
    return 1 if avisos else 0


if __name__ == "__main__":
    sys.exit(main())
