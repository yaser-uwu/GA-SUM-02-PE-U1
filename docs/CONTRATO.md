# Contrato de datos del equipo (sockets y gRPC deben producir lo mismo)

Este archivo fija los formatos para que cada parte encaje con las demás.
Cualquier cambio se acuerda con todo el equipo y se registra en BITACORA.md.

## Nodos
| Nodo   | Puerto | Host      |
|--------|--------|-----------|
| nodo-A | 5000   | 127.0.0.1 |
| nodo-B | 5001   | 127.0.0.1 |
| nodo-C | 5002   | 127.0.0.1 |

Cada nodo es un proceso con un servidor (recibe) y un cliente (envía) y
mantiene su propio reloj de Lamport. Los valores están en `src/common/config.py`.

## Mensaje
- JSON (sockets): `{"sender": "nodo-A", "timestamp": 7, "message": "texto"}`
- gRPC: el `.proto` usa los mismos tres campos: `sender`, `timestamp`, `message`.
- `timestamp` es el valor del reloj de Lamport del emisor al enviar.
- Reglas de Lamport: antes de enviar, `reloj += 1`; al recibir, `reloj = max(reloj, recibido) + 1`.

## CSV de eventos (`data/eventos_sockets.csv`, `data/eventos_grpc.csv`)
Columnas: `nodo,tipo_evento,reloj,hora_real,contraparte,msg_id`
- `tipo_evento`: `envio` o `recepcion`.
- `reloj`: valor del reloj del nodo DESPUÉS de aplicar la regla en ese evento.
- `hora_real`: ISO 8601 con milisegundos (`datetime.now().isoformat(timespec="milliseconds")`).
- `contraparte`: el otro nodo del mensaje (destino si es envío, origen si es recepción).
- `msg_id`: `"<emisor>:<timestamp>"` (p. ej. `nodo-A:7`). Es único por mensaje porque cada
  envío incrementa el reloj del emisor. Permite emparejar envío y recepción en la verificación.
- Las dos últimas columnas se agregan a las cuatro que pide la guía; son necesarias para verificar Lamport.

## CSV de latencia (`data/latencia_sockets.csv`, `data/latencia_grpc.csv`)
Columnas: `mecanismo,tamano,tamano_bytes,modo,corrida,envio_n,rtt_s`
- `mecanismo`: `sockets` o `grpc`.
- `tamano`: `corto` o `largo`; `tamano_bytes`: longitud real del campo `message`.
- `modo`: `secuencial` o `concurrente` (los tres clientes enviando a la vez).
- `corrida`: 0 = calentamiento (se guarda pero el análisis la descarta), 1..5 = corridas medidas.
- `envio_n`: 1..100.
- `rtt_s`: latencia de ida y vuelta en segundos, medida con `time.perf_counter()`.

## Condiciones de la máquina (`data/maquina_<usuario>.json`)
Sistema operativo, procesador, memoria, versión de Python y si los nodos corren como procesos o contenedores.
Se genera por script al momento de la corrida (no se escribe a mano).

## Datos crudos
- Los CSV en `data/` NO se editan nunca después de generarse.
- `data/SHA256SUMS` se genera al terminar las corridas y se verifica con `sha256sum -c SHA256SUMS`.
- Cada corrida oficial se guarda con el nombre de quien la ejecutó para poder rastrear la máquina.

## Ubicación de archivos
- `proto/messaging.proto` (la guía en PDF lo ubica en src/grpc/, pero la guía de texto exige /proto/; se usa /proto/).
- Código generado por grpcio-tools (`messaging_pb2*.py`) va en `src/grpc/`.
- Sockets: `src/sockets/server.py`, `src/sockets/client.py`. gRPC: `src/grpc/server_grpc.py`, `src/grpc/client_grpc.py`.
- Análisis: `analysis/analisis.py`. Figuras: `docs/figures/` (boxplot a 300 DPI).
- Documento: `docs/guia1_practica.tex`, `docs/referencias.bib`, `docs/guia1_practica.pdf`.
