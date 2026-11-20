# Medición de latencia con sockets TCP

Responsable: Kevin Leonel García Bazurto.

El coordinador inicia los tres nodos TCP, ejecuta las solicitudes y guarda la latencia de cada respuesta y la duración de cada corrida. Los mensajes llevan `sender`, `timestamp` y `message`, separados por un salto de línea. El receptor devuelve un acuse JSON.

## Corridas realizadas

Sesión: `20261120-175011-kevin`.

| Escenario | Tamaño de message | Corridas | Solicitudes |
| --- | --- | --- | --- |
| Secuencial, calentamiento | 100 bytes | 0 | 100 |
| Secuencial, medición | 100 bytes | 1 a 5 | 500 |
| Secuencial, calentamiento | 10240 bytes | 0 | 100 |
| Secuencial, medición | 10240 bytes | 1 a 5 | 500 |
| Concurrente | 100 bytes | 1 | 100 |
| Concurrente | 10240 bytes | 1 | 100 |

Se completaron 14 corridas y 1400 solicitudes con acuse. Los 28 CSV conservan las mediciones originales. Las dos corridas de calentamiento quedan identificadas con el número 0 y se excluyen de las estadísticas. La concurrencia se analiza por separado.

## Forma de medir

Cada solicitud abre una conexión TCP. La medición con `time.perf_counter()` empieza con la conexión ya establecida, antes de codificar y enviar el JSON, y termina después de leer y decodificar el acuse. Incluye la codificación JSON, el intercambio y la decodificación de la respuesta. La duración total de la corrida también incluye el establecimiento y cierre de las conexiones.

El modo `--sin-eventos` desactiva la impresión de eventos en los receptores durante estas mediciones. La ejecución de Lamport conserva su registro normal. Los valores de `timestamp` de las pruebas de latencia no se utilizan como evidencia de la prueba de Lamport.

En secuencial se repiten cinco veces las 20 rutas acordadas. En concurrencia se inician tres clientes como hilos del coordinador mediante una barrera: A envía 34 solicitudes a B, B envía 33 a C y C envía 33 a A. Los receptores siguen siendo tres procesos independientes. Los identificadores de muestra van del 1 al 100 sin repetirse.

## Archivos y validación

Los resultados están en `data/20261120-175011-kevin/sockets/latencia/`. Cada intento contiene `latencia.csv` y `duracion.csv`, con los encabezados de `docs/CONTRATO.md`. Un intento existente se conserva y se rechaza su sobrescritura. Una corrida incompleta conserva las muestras obtenidas y se registra como `fallida`.

La validación comprobó 100 muestras por corrida, numeración del 1 al 100, tiempos positivos y 100 acuses en cada archivo de duración. Las cinco pruebas automatizadas verificaron ambos tamaños, el rechazo de JSON inválido, la recepción por fragmentos, los CSV de ambos modos y el rechazo de acuses negativos. La prueba de Lamport volvió a producir 40 eventos, 20 pares válidos y 0 errores.

La ficha `data/maquina_kevin.json` registra el entorno detectado: Windows 11, Intel Core i5-1135G7, Python 3.13.5 y ejecución mediante procesos.

# Declaración de IA

Se utilizó ChatGPT Sol 6.1 mediante Codex como apoyo para preparar y revisar si la implementación de las mediciones TCP estaban bien. las pruebas y su documentación. Yo hice la revisión y ejecución real, validación de los CSV y comprobación del registro de Lamport.

Las instrucciones de ejecución están en `docs/GUIA-TCP-LATENCIA.md`.
