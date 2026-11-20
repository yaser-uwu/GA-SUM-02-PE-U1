# TCP con tres nodos y reloj de Lamport

Responsable: Kevin Leonel García Bazurto.

## Funcionamiento

El programa ejecuta tres procesos independientes en 127.0.0.1:

| Nodo | Puerto |
|---|---|
| nodo-A | 5000 |
| nodo-B | 5001 |
| nodo-C | 5002 |

Cada nodo envía y recibe solicitudes TCP y mantiene su propio reloj de Lamport. Antes de enviar incrementa el reloj en uno. Al recibir aplica `max(reloj_local, timestamp_recibido) + 1`.

El emisor espera el acuse antes de continuar con la siguiente ruta. Según el contrato del equipo, el acuse confirma la recepción y queda fuera del reloj lógico y del registro de eventos.

## Archivos

| Archivo | Función |
|---|---|
| `src/sockets/server.py` | Proceso de cada nodo: envío, recepción, validación JSON y actualización del reloj. |
| `src/sockets/client.py` | Coordinación de los tres procesos, ejecución de las 20 rutas y escritura del CSV. |
| `src/common/config.py` | Configuración compartida del equipo. |
| `analysis/verificar_lamport.py` | Verificación de los pares de envío y recepción. |

Las instrucciones locales del coordinador controlan la secuencia; no forman parte de los mensajes de la prueba ni modifican los relojes.

## Ejecución

Requisito: Python 3.11 o superior. Comando desde la raíz del repositorio:

```powershell
python src/sockets/client.py
```

El coordinador inicia los tres nodos, ejecuta los 20 intercambios, guarda los eventos, invoca el verificador y cierra los procesos al terminar.

## Secuencia de intercambios

| Pasos | Rutas en orden |
|---|---|
| 1 a 6 | A → B, B → C, C → A, A → C, C → B, B → A |
| 7 a 12 | A → B, B → C, C → A, A → C, C → B, B → A |
| 13 a 18 | A → B, B → C, C → A, A → C, C → B, B → A |
| 19 a 20 | A → B, B → C |

Cada ejecución inicia los tres relojes en cero. Las 20 solicitudes generan 40 eventos: 20 envíos y 20 recepciones.

## Registro de eventos

La ejecución realizada generó el archivo:

```text
data/20261119-222709-kevin/sockets/eventos/lamport-01/eventos.csv
```

Cada ejecución utiliza una carpeta de sesión identificada por fecha, hora y responsable. El programa impide sobrescribir una ejecución existente.

| Columna | Contenido |
|---|---|
| `nodo` | Nodo que registra el evento. |
| `tipo_evento` | `envio` o `recepcion`. |
| `reloj` | Valor del reloj después de aplicar la regla de Lamport. |
| `hora_real` | Fecha y hora local en formato ISO 8601 con milisegundos. |
| `contraparte` | Nodo destinatario o emisor, según el evento. |
| `msg_id` | Identificador formado por el emisor y su reloj al enviar, como `nodo-A:1`. |

El envío y la recepción de una solicitud comparten el mismo `msg_id`. Los nodos generan los relojes y las horas; el coordinador reúne sus eventos en el CSV. El emparejamiento se realiza por identificador, independientemente del orden de llegada de las filas.

## Verificación realizada

Comando para verificar el archivo de la ejecución:

```powershell
python analysis/verificar_lamport.py data/20261119-222709-kevin/sockets/eventos/lamport-01/eventos.csv 20
```

Resultado obtenido:

```text
Filas leídas: 40
Mensajes identificados: 20
Pares válidos: 20
Errores: 0
Resultado: VERIFICACIÓN CORRECTA
```

## Formato de mensajes y manejo de errores

Las solicitudes contienen `sender`, `timestamp` y `message` en JSON. Cada solicitud y cada acuse terminan con un salto de línea. El receptor acumula los bytes hasta ese delimitador, incluso cuando TCP entrega el mensaje en fragmentos.

El receptor valida el objeto JSON, el emisor, el entero positivo del reloj y el texto del mensaje. Cada línea tiene un límite de 65536 bytes. La conexión y la lectura tienen un tiempo de espera limitado.

Un fallo detiene la secuencia, conserva los eventos generados y devuelve un código de salida distinto de cero. No se realizan reintentos automáticos.

## Uso de IA

Se utilizó ChatGPT Sol 6.1 mediante Codex como apoyo para ayudarme a preparar el código y esta guía clara, tambien como ayuda para revisar el contrato, Yo hice parte de la práctica y ejecuté el programa en mi equipo y comprobé el resultado del verificador.