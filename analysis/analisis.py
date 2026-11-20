"""Lector del experimento PE-U1 (sockets TCP y gRPC).

Lee y agrupa los CSV de una sesión, comprueba que cumplan docs/CONTRATO.md,
calcula la latencia y el rendimiento por mecanismo, modo y tamaño, y genera las
figuras (docs/figures) y las tablas LaTeX (docs/tablas) del informe.

Uso, desde la raíz del repositorio:
    python analysis/analisis.py data/<sesion>
    python analysis/analisis.py data/<sesion> --salida otra_carpeta
"""
import argparse
import sys
from itertools import product
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")  # solo guarda archivos, no abre ventanas
import matplotlib.pyplot as plt  # noqa: E402

COLS_LATENCIA = ["mecanismo", "tamano", "tamano_bytes", "modo", "corrida", "envio_n", "rtt_s"]
COLS_DURACION = ["mecanismo", "tamano", "tamano_bytes", "modo", "corrida",
                 "duracion_s", "envios_ok", "estado"]
TAMANO_BYTES = {"corto": 100, "largo": 10240}
CORRIDAS_VALIDAS = {"secuencial": 5, "concurrente": 1}
MECANISMOS = ["sockets", "grpc"]
ENVIOS = 100
CLAVE = ["mecanismo", "modo", "tamano", "corrida"]
NOMBRE = {"sockets": "Sockets TCP", "grpc": "gRPC"}
COLOR = {"sockets": "#0072B2", "grpc": "#E69F00"}
DPI = 300


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


def calcular_metricas(lat_usada, usados):
    """Latencia (ms) y rendimiento (mensajes/s) por mecanismo, modo y tamaño.

    Excluye el calentamiento. La latencia junta todas las muestras de las corridas
    válidas; el rendimiento se calcula por corrida como envios_ok / duracion_s.
    La desviación estándar es la muestral (n - 1) y el p95 interpola linealmente.
    """
    grupo = ["mecanismo", "modo", "tamano"]

    datos = lat_usada[~lat_usada["calentamiento"]].copy()
    datos["rtt_ms"] = datos["rtt_s"] * 1000
    latencia = datos.groupby(grupo)["rtt_ms"].agg(
        muestras="count", media_ms="mean", mediana_ms="median", desv_ms="std",
        p95_ms=lambda s: s.quantile(0.95)).reset_index()

    validas = usados[~usados["calentamiento"]].copy()
    validas["msg_por_s"] = validas["envios_ok"] / validas["duracion_s"]
    rendimiento = validas.groupby(grupo)["msg_por_s"].agg(
        corridas="count", msg_s_media="mean", msg_s_desv="std").reset_index()

    return latencia.merge(rendimiento, on=grupo)


def figura_cajas(lat_usada, ruta):
    """Diagrama de cajas de la latencia (ms) en las corridas secuenciales válidas."""
    datos = lat_usada[(~lat_usada["calentamiento"]) & (lat_usada["modo"] == "secuencial")]
    fig, ejes = plt.subplots(1, 2, figsize=(8, 4))
    for eje, tamano in zip(ejes, TAMANO_BYTES):
        grupos = []
        for mecanismo in MECANISMOS:
            filas = datos[(datos["mecanismo"] == mecanismo) & (datos["tamano"] == tamano)]
            grupos.append(filas["rtt_s"] * 1000)
        cajas = eje.boxplot(grupos, patch_artist=True)
        for caja, mecanismo in zip(cajas["boxes"], MECANISMOS):
            caja.set_facecolor(COLOR[mecanismo])
        for mediana in cajas["medians"]:
            mediana.set_color("black")
        eje.set_xticks([1, 2])
        eje.set_xticklabels([NOMBRE[m] for m in MECANISMOS])
        eje.set_title(f"Mensaje {tamano} ({TAMANO_BYTES[tamano]} B)")
        eje.set_ylabel("Latencia RTT (ms)")
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI)
    plt.close(fig)


def figura_barras(metricas, media, desv, etiqueta, ruta):
    """Barras de una métrica (media ± desviación estándar) en modo secuencial."""
    secuencial = metricas[metricas["modo"] == "secuencial"]
    ancho = 0.35
    fig, eje = plt.subplots(figsize=(6, 4))
    for mecanismo, desplazamiento in zip(MECANISMOS, [-ancho / 2, ancho / 2]):
        g = secuencial[secuencial["mecanismo"] == mecanismo].set_index("tamano")
        g = g.reindex(list(TAMANO_BYTES))  # un valor por tamaño, en el orden corto, largo
        eje.bar([0 + desplazamiento, 1 + desplazamiento], g[media], ancho,
                yerr=g[desv], capsize=4, color=COLOR[mecanismo], label=NOMBRE[mecanismo])
    eje.set_xticks([0, 1])
    eje.set_xticklabels([f"{t} ({b} B)" for t, b in TAMANO_BYTES.items()])
    eje.set_xlabel("Tamaño del mensaje")
    eje.set_ylabel(etiqueta)
    eje.legend()
    fig.tight_layout()
    fig.savefig(ruta, dpi=DPI)
    plt.close(fig)


def numero(valor, decimales):
    """Número con coma decimal para LaTeX en español; '---' si no hay valor."""
    if pd.isna(valor):
        return "---"
    return f"{valor:.{decimales}f}".replace(".", "{,}")


def escribir_tabla(metricas, columnas, encabezados, ruta):
    """Escribe un tabular con booktabs.

    columnas: {nombre de columna: decimales}. Antes de ellas van mecanismo, modo y tamaño.
    """
    lineas = [r"\small\setlength{\tabcolsep}{4pt}",
              r"\begin{tabular}{lll" + "r" * len(columnas) + "}",
              r"\toprule",
              " & ".join(["Mecanismo", "Modo", "Tamaño"] + encabezados) + r" \\",
              r"\midrule"]
    for _, fila in metricas.iterrows():
        celdas = [NOMBRE[fila["mecanismo"]], fila["modo"], fila["tamano"]]
        for columna, decimales in columnas.items():
            celdas.append(numero(fila[columna], decimales))
        lineas.append(" & ".join(celdas) + r" \\")
    lineas += [r"\bottomrule", r"\end{tabular}"]
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def guardar_resultados(lat_usada, metricas, salida):
    """Guarda las figuras en <salida>/figures y las tablas en <salida>/tablas."""
    figuras = salida / "figures"
    tablas = salida / "tablas"
    figuras.mkdir(parents=True, exist_ok=True)
    tablas.mkdir(parents=True, exist_ok=True)

    figura_cajas(lat_usada, figuras / "latencia_cajas.png")
    figura_barras(metricas, "media_ms", "desv_ms",
                  "Latencia media ± desviación estándar (ms)", figuras / "latencia_barras.png")
    figura_barras(metricas, "msg_s_media", "msg_s_desv",
                  "Rendimiento medio ± desviación estándar (mensajes/s)",
                  figuras / "rendimiento_barras.png")

    escribir_tabla(metricas,
                   {"muestras": 0, "media_ms": 3, "mediana_ms": 3, "desv_ms": 3, "p95_ms": 3},
                   ["$n$", "Media", "Mediana", "Desv.", "P95"], tablas / "latencia.tex")
    escribir_tabla(metricas, {"corridas": 0, "msg_s_media": 3, "msg_s_desv": 3},
                   ["Corridas", "Media", "Desv."], tablas / "rendimiento.tex")
    print(f"Figuras guardadas en {figuras}")
    print(f"Tablas guardadas en {tablas}")


def main():
    parser = argparse.ArgumentParser(description="Analiza una sesión del experimento PE-U1.")
    parser.add_argument("sesion", help="carpeta data/<sesion>")
    parser.add_argument("--salida", default="docs", type=Path,
                        help="carpeta donde se guardan figures/ y tablas/ (por defecto docs)")
    args = parser.parse_args()

    lat, dur = cargar_sesion(args.sesion)
    lat_usada, usados = intentos_usados(lat, dur)

    print(f"Sesión: {args.sesion}")
    print(f"Intentos leídos: {len(dur)} | fallidos: {(dur['estado'] == 'fallida').sum()} "
          f"| corridas completas usadas: {len(usados)}")
    resumen = usados.sort_values(CLAVE)[CLAVE + ["intento", "filas", "duracion_s"]]
    print(resumen.to_string(index=False))

    print()
    metricas = calcular_metricas(lat_usada, usados)
    print(metricas.round(3).to_string(index=False))

    print()
    guardar_resultados(lat_usada, metricas, args.salida)

    avisos = revisar_protocolo(usados)
    for aviso in avisos:
        print(f"AVISO: {aviso}")
    return 1 if avisos else 0


if __name__ == "__main__":
    sys.exit(main())
