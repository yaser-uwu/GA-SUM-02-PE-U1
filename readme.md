# GA-SUM-02 / PE-U1 — Comunicación entre procesos distribuidos: sockets TCP y gRPC

Aplicaciones Distribuidas (ISR-701) · UTEQ · 7mo nivel A · Grupo GLMR

Integrantes:
- Kevin Leonel García Bazurto
- Bryan Humberto Lombeida Escaleras
- Carlos Alexander Manotoa Álava
- Eduardo David Reinoso Vélez

Repositorio: https://github.com/yaser-uwu/GA-SUM-02-PE-U1

Video de respaldo: TODO (enlace)

## Estructura
```
/src/sockets/   código con sockets TCP
/src/grpc/      código gRPC (y el generado por grpcio-tools)
/src/common/    reloj de Lamport, configuración y escritura de CSV compartidos
/proto/         messaging.proto
/data/          CSV crudos y SHA256SUMS
/analysis/      script de análisis y gráficos
/docs/          .tex, .bib y PDF compilado
BITACORA.md     bitácora del equipo
```
Formatos de datos y nombres de archivo: ver `docs/CONTRATO.md`.

## Requisitos
- Python 3.11 o superior
- `pip install -r requirements.txt` (terminal cmd.exe, dentro de la raíz del repo)

## Ejecución de los nodos
TODO (se completa cuando exista el código): sockets, gRPC, orden de arranque de nodo-A/B/C.

## Ejecución del análisis
TODO: comando del script de `analysis/` y archivos que genera.

## Verificación de la integridad de los datos
TODO: `sha256sum -c data/SHA256SUMS` (o equivalente en Windows).

## Compilación del documento
- Compilador: pdflatex + biber
- Archivo principal: `docs/guia1_practica.tex`
- Orden de comandos (desde `docs/`):
  1. `pdflatex guia1_practica.tex`
  2. `biber guia1_practica`
  3. `pdflatex guia1_practica.tex`
  4. `pdflatex guia1_practica.tex`
- Dependencias LaTeX: TODO (listar paquetes finales, p. ej. amsmath, booktabs, listings, graphicx, tikz, biblatex, hyperref)
