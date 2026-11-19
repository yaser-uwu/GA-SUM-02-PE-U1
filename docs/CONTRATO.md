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

## Secuencia de Lamport

Cada mecanismo ejecuta la misma secuencia, con los tres relojes inicialmente en cero.
En cada paso, el emisor espera el acuse antes de avanzar a la siguiente ruta.

| Pasos | Rutas en orden |
|---|---|
| 1 a 6 | A → B, B → C, C → A, A → C, C → B, B → A |
| 7 a 12 | A → B, B → C, C → A, A → C, C → B, B → A |
| 13 a 18 | A → B, B → C, C → A, A → C, C → B, B → A |
| 19 a 20 | A → B, B → C |

Los 40 eventos de Lamport corresponden a las 20 solicitudes, con un envío y una
recepción por solicitud. Los acuses confirman la entrega y sirven para medir la
ida y vuelta. En esta prueba quedan fuera del registro y del reloj lógico.
El informe explicará ese alcance.

## Carpetas de datos

Usar el mismo identificador de sesión para los dos mecanismos que se comparan.
El identificador sigue el formato `AAAAMMDD-HHMMSS-usuario`, con fecha y hora local.

```text
data/<sesion>/<mecanismo>/eventos/lamport-01/eventos.csv
data/<sesion>/<mecanismo>/eventos/empate-01/eventos.csv
data/<sesion>/<mecanismo>/latencia/<modo>/<tamano>/corrida-00/intento-01/latencia.csv
data/<sesion>/<mecanismo>/latencia/<modo>/<tamano>/corrida-00/intento-01/duracion.csv
```

- `<mecanismo>` es `sockets` o `grpc`, `<modo>` es `secuencial` o
  `concurrente` y `<tamano>` es `corto` o `largo`.
- Cada ejecución de Lamport tiene su propio CSV. Si se repite, se usa
  `lamport-02`, `lamport-03`, etc. Si hace falta una ejecución aparte para
  evidenciar el empate de relojes, se usa `empate-01`.
- La carpeta `corrida-00` corresponde al calentamiento secuencial. Si se repite
  una corrida fallida, se conserva el intento previo y se incrementa el
  número de intento en la carpeta de esa misma corrida.
- Los CSV se escriben en UTF-8, con encabezado, coma como separador de campos y
  punto como separador decimal.

## CSV de eventos (`eventos.csv`)

```csv
nodo,tipo_evento,reloj,hora_real,contraparte,msg_id
```

- `tipo_evento`: `envio` o `recepcion`.
- `reloj`: valor del reloj del nodo después de aplicar la regla en ese evento.
- `hora_real`: ISO 8601 local sin sufijo de zona horaria y con milisegundos
  (`datetime.now().isoformat(timespec="milliseconds")`).
- `contraparte`: el otro nodo del mensaje (destino si es envío, origen si es recepción).
- `msg_id`: `<emisor>:<timestamp>` (por ejemplo, `nodo-A:7`). Las dos filas
  de una solicitud llevan el mismo ID. La unicidad se comprueba dentro de
  cada ejecución, porque los relojes pueden reiniciarse.

El verificador se ejecuta desde la raíz del repositorio. Para la secuencia
principal, se indica el CSV de una ejecución y se esperan 20 pares. Por ejemplo:

```bash
python3 analysis/verificar_lamport.py data/20261119-140000-carlos/sockets/eventos/lamport-01/eventos.csv 20
```

## CSV de latencia (`latencia.csv`)

```csv
mecanismo,tamano,tamano_bytes,modo,corrida,envio_n,rtt_s
```

- `mecanismo`, `tamano` y `modo` coinciden con la ruta del intento.
- `tamano_bytes` es el tamaño del campo `message` en ASCII: 100 para
  `corto` y 10240 para `largo`.
- `corrida` es el número de la corrida como entero. Por ejemplo, `corrida-01`
  se registra como `1`.
- Cada solicitud con acuse exitoso genera una fila. En una corrida completa,
  `envio_n` contiene todos los números del 1 al 100, una sola vez cada uno.
- `rtt_s` es el tiempo en segundos desde justo antes del envío o la
  invocación hasta recibir el acuse, medido con `time.perf_counter()`.

## CSV de duración (`duracion.csv`)

```csv
mecanismo,tamano,tamano_bytes,modo,corrida,duracion_s,envios_ok,estado
```

- Se escribe una fila por intento, en la misma carpeta que su `latencia.csv`.
  Las primeras cinco columnas coinciden con las del archivo de latencias.
- `duracion_s` se mide con `time.perf_counter()` con los nodos ya listos.
  En secuencial se mide desde el inicio de los envíos hasta el último acuse.
  En concurrencia, el coordinador mide desde que da la señal de inicio hasta
  que terminan los tres clientes. Si el intento falla, registra el tiempo
  transcurrido hasta que se da por terminado.
- `envios_ok` cuenta los acuses exitosos. `estado` es `completa` si se
  completaron las 100 solicitudes o `fallida` si el intento quedó incompleto.
- Para el análisis, Eduardo toma un solo intento completo por corrida. Si hay
  varios, usa el de menor número de intento. Excluye el calentamiento y los
  intentos fallidos, y mantiene identificada la concurrencia. El rendimiento
  de una corrida se calcula como `envios_ok / duracion_s`.

## Condiciones de la máquina (`data/maquina_<usuario>.json`)
Sistema operativo, procesador, memoria, versión de Python y si los nodos corren como procesos o contenedores.
Se genera por script al momento de la corrida (no se escribe a mano).

## Datos crudos
- Los CSV en `data/` se conservan tal como se generaron, incluidos el
  calentamiento, la concurrencia y los intentos fallidos.
- `data/SHA256SUMS` incluye los CSV crudos con rutas relativas a la raíz del
  repositorio. Se verifica desde esa raíz con `sha256sum -c data/SHA256SUMS`.
- El usuario en el identificador de sesión permite relacionar los datos con
  la ficha de la máquina.

## Ubicación de archivos
- `proto/messaging.proto` (la guía en PDF lo ubica en src/grpc/, pero la guía de texto exige /proto/; se usa /proto/).
- Código generado por grpcio-tools (`messaging_pb2*.py`) va en `src/grpc/`.
- Sockets: `src/sockets/server.py`, `src/sockets/client.py`. gRPC: `src/grpc/server_grpc.py`, `src/grpc/client_grpc.py`.
- Verificación de eventos: `analysis/verificar_lamport.py`.
- Análisis: `analysis/analisis.py`. Figuras: `docs/figures/` (boxplot a 300 DPI).
- Documento: `docs/guia1_practica.tex`, `docs/referencias.bib`, `docs/guia1_practica.pdf`.

## Plan de ejecución experimental

### Matriz de pruebas

Para comparar TCP y gRPC se utilizarán las mismas
condiciones experimentales.

| Parámetro | Configuración |
|---|---|
| Mecanismos | Sockets TCP y gRPC |
| Nodos | A, B y C |
| Tamaños | 100 y 10240 bytes |
| Calentamiento | 1 corrida por combinación |
| Corridas válidas | 5 por combinación |
| Envíos por corrida | 100 |
| Intercambios Lamport | 20 por mecanismo |
| Concurrencia | 1 corrida por mecanismo y tamaño con 3 clientes simultáneos |

En modo secuencial, cada combinación de mecanismo y tamaño usa la corrida
`0` para calentamiento y las corridas `1` a `5` para medición. Cada corrida
repite cinco veces la secuencia de 20 rutas. Son 24 corridas y 2400 solicitudes,
incluido el calentamiento.

En modo concurrente, cada combinación de mecanismo y tamaño usa la corrida
`1`. Un coordinador da la señal común de inicio y reúne las muestras de los
tres clientes para escribir un solo `latencia.csv` por intento.

| Cliente | Destino | Solicitudes | `envio_n` |
|---|---|---|---|
| A | B | 34 | 1–34 |
| B | C | 33 | 35–67 |
| C | A | 33 | 68–100 |

Son cuatro corridas concurrentes de 100 solicitudes en total cada una.

### Orden de ejecución

1. Preparar el entorno y comprobar las dependencias.
2. Registrar las características de la máquina.
3. Ejecutar los 20 intercambios con TCP y gRPC.
4. Realizar las corridas de calentamiento.
5. Ejecutar las cinco corridas válidas por combinación.
6. Repetir las pruebas con tres clientes simultáneos.
7. Verificar los CSV generados por ambos mecanismos.
8. Generar las huellas SHA-256 de los datos originales.

### Condiciones de comparación

- Ejecutar ambos mecanismos en la misma máquina.
- Utilizar los mismos tamaños y cantidades de mensajes.
- No incluir el calentamiento en las estadísticas.
- Registrar las mediciones sin modificar los CSV originales.
- Identificar el mecanismo, la corrida y el escenario.
- Usar la duración real para calcular el rendimiento.

### Pendientes de coordinación

- Acordar los comandos de ejecución con los implementadores.
- Comprobar que TCP y gRPC generan los CSV del contrato.
