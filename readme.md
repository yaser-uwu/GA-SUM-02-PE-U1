<div align="center">

# GA-SUM-02 / PE-U1

**Práctica experimental: comunicación entre procesos con sockets TCP y gRPC**

![UTEQ](https://img.shields.io/badge/UTEQ-Ingenier%C3%ADa%20de%20Software-1f6feb?style=flat-square)
![Asignatura](https://img.shields.io/badge/Aplicaciones%20Distribuidas-ISR--701-8957e5?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![gRPC](https://img.shields.io/badge/gRPC-Protocol%20Buffers-244c5a?style=flat-square)
![Sockets](https://img.shields.io/badge/Sockets-TCP-0072B2?style=flat-square)
![Lamport](https://img.shields.io/badge/Relojes-Lamport-E69F00?style=flat-square)

</div>

---

Séptimo nivel, paralelo A · SPA 2026-2027 · Actividad grupal del grupo GLMR, que compara sockets TCP y gRPC con mediciones propias y comprueba el orden de eventos con relojes de Lamport.

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
- Python 3.11 o superior y `pip install -r requirements.txt`, desde la raíz del repo (terminal cmd.exe)

## Ejecución de los tres nodos con gRPC y reloj de Lamport

Responsable: Bryan Humberto Lombeida Escaleras.

Cada nodo mantiene su propio reloj de Lamport y escribe sus eventos en un CSV.
El coordinador ordena los 20 intercambios del contrato y reúne los archivos.

### Requisitos

- Haber instalado `requirements.txt` en el entorno que se usará.
- Ejecutar los comandos desde la raíz del repositorio.
- Los puertos `5000`, `5001` y `5002` deben estar libres.

### 1. Elegir el identificador de sesión

El identificador debe tener el formato `AAAAMMDD-HHMMSS-usuario`. Por ejemplo:

```bash
date '+%Y%m%d-%H%M%S'
```

Si devuelve `20261119-220530`, la sesión será `20261119-220530-bryan`.
Usa el mismo identificador en las cuatro terminales.

### 2. Iniciar los tres nodos

En tres terminales separadas, desde la raíz y con el entorno activado:

```bash
python src/grpc/nodo.py nodo-A --sesion 20261119-220530-bryan
```

```bash
python src/grpc/nodo.py nodo-B --sesion 20261119-220530-bryan
```

```bash
python src/grpc/nodo.py nodo-C --sesion 20261119-220530-bryan
```

Cada terminal debe mostrar su puerto:

```text
[nodo-A] escuchando en 127.0.0.1:5000 ...
[nodo-B] escuchando en 127.0.0.1:5001 ...
[nodo-C] escuchando en 127.0.0.1:5002 ...
```

### 3. Ejecutar el coordinador

En una cuarta terminal, desde la raíz:

```bash
python src/grpc/coordinador_lamport.py --manual --sesion 20261119-220530-bryan
```

El coordinador se conecta a los nodos que ya están en marcha, reinicia sus
relojes y ordena las 20 rutas del contrato. Al finalizar debe mostrar:

```text
Paso 20/20: nodo-B -> nodo-C OK
...
Pares válidos: 20
Errores: 0
Resultado: VERIFICACIÓN CORRECTA
```

El resultado queda en:

```text
data/<sesion>/grpc/eventos/lamport-01/eventos.csv
```

También se conservan los CSV individuales `nodo-A.csv`, `nodo-B.csv` y
`nodo-C.csv` en la misma carpeta.

### 4. Verificar el CSV

```bash
python analysis/verificar_lamport.py data/20261119-220530-bryan/grpc/eventos/lamport-01/eventos.csv 20
```

La verificación debe reportar 40 filas, 20 mensajes, 20 pares válidos y
0 errores. Para detener los nodos, pulsa `Ctrl+C` en cada una de las tres
terminales.

### Modo automático

El coordinador también puede lanzar y detener los tres nodos por sí solo:

```bash
python src/grpc/coordinador_lamport.py
```

En ese caso genera automáticamente un identificador de sesión y ejecuta la
misma secuencia de 20 intercambios.

## Medición de latencia gRPC

### Preparación

Desde la raíz del repositorio y con el entorno virtual activo, instala las
versiones probadas con Python 3.12:

```bash
python -m pip install grpcio==1.85.3 protobuf==7.36.2
python -m pip check
```

`grpcio-tools==1.85.3` solo se necesita para regenerar los módulos del `.proto`;
los módulos generados ya están en el repositorio.

### Matriz oficial de Kevin: 14 corridas

Usa la misma máquina y sesión que TCP; comprueba su ficha antes de medir y
detén los nodos TCP o gRPC anteriores para liberar los puertos `5000` a `5002`.
El coordinador inicia y detiene los tres procesos automáticamente:

```bash
python src/grpc/coordinador_latencia.py --sesion 20261120-175011-kevin --matriz
```

Por tamaño (`corto` = 100 bytes, `largo` = 10 240 bytes ASCII en `message`)
se hace un calentamiento secuencial (`00`), cinco corridas secuenciales
(`01` a `05`) y una concurrente (`01`). Cada corrida tiene 100 solicitudes
en total. La secuencial repite cinco veces las 20 rutas y espera cada acuse.
En concurrente los clientes comparten una hora de inicio: A→B envía 34,
B→C envía 33 y C→A envía 33.

El nodo emisor mide el RTT desde justo antes de invocar `EnviarMensaje`
hasta recibir el acuse. No incluye las órdenes del coordinador ni el arranque.
La duración total va del primer envío al último acuse en secuencial y de la
señal de inicio al último acuse de los tres clientes en concurrente.
Los nodos mantienen sus relojes de Lamport sin escribir eventos en este modo.

Cada intento escribe los dos archivos del contrato:

```text
data/<sesion>/grpc/latencia/<modo>/<tamano>/corrida-NN/intento-NN/latencia.csv
data/<sesion>/grpc/latencia/<modo>/<tamano>/corrida-NN/intento-NN/duracion.csv
```

Una corrida completa muestra `100/100 envíos OK` y `estado=completa`. Si
termina toda la matriz, la última línea es `Corridas completas: 14/14`.
Si una falla, se guardan las muestras recibidas con `estado=fallida` y la matriz
se detiene. No vuelvas a lanzar `--matriz` para continuar: repite solo la
corrida fallida y ejecuta las que falten. Por ejemplo:

```bash
python src/grpc/coordinador_latencia.py --sesion 20261120-175011-kevin --modo secuencial --tamano corto --corrida 3
python src/grpc/coordinador_latencia.py --sesion 20261120-175011-kevin --modo concurrente --tamano largo --corrida 1
```

Cada repetición sin `--intento` usa el siguiente número disponible. Si indicas
`--intento` y la carpeta existe, el programa se detiene sin sobrescribirla.
No incluyas los calentamientos en las estadísticas.

### Evidencias de la sesión oficial

En la máquina de medición, captura el resumen final que muestra el reparto
`34/34`, `33/33`, `33/33` y `Corridas completas: 14/14`. Para la captura de los
CSV, este comando muestra el número de muestras, el encabezado, una muestra y
la fila de duración del primer intento concurrente de tamaño largo:

```bash
python -c "from pathlib import Path; p = Path('data/20261120-175011-kevin/grpc/latencia/concurrente/largo/corrida-01/intento-01'); l = (p / 'latencia.csv').read_text().splitlines(); print(p); print('Filas de latencia:', len(l) - 1); print('\n'.join(l[:2])); print((p / 'duracion.csv').read_text())"
```

Si ese intento falló, cambia `intento-01` por el número del intento completo.
Conserva los CSV originales, incluidos los calentamientos e intentos fallidos.

### Modo manual para pruebas

Inicia los tres nodos en terminales separadas con `--sin-eventos` y un ID de
prueba nuevo, distinto de la sesión oficial:

```bash
python src/grpc/nodo.py nodo-A --sesion 20261120-190000-prueba-grpc --sin-eventos
python src/grpc/nodo.py nodo-B --sesion 20261120-190000-prueba-grpc --sin-eventos
python src/grpc/nodo.py nodo-C --sesion 20261120-190000-prueba-grpc --sin-eventos
```

En una cuarta terminal ejecuta el coordinador:

```bash
python src/grpc/coordinador_latencia.py --manual --sesion 20261120-190000-prueba-grpc --modo secuencial --tamano corto --corrida 0
```

## Ejecución de los tres nodos con sockets TCP y reloj de Lamport

Responsable: Kevin Leonel García Bazurto.

### Funcionamiento

Los nodos A, B y C se ejecutan como procesos independientes en `127.0.0.1`, en los puertos `5000`, `5001` y `5002`. Cada nodo mantiene su propio reloj de Lamport: incrementa antes de enviar y aplica `max(reloj_local, timestamp_recibido) + 1` al recibir. El acuse queda fuera del reloj lógico, según el contrato.

- `src/sockets/server.py`: envío, recepción, validación JSON y reloj de cada nodo.
- `src/sockets/client.py`: coordinación de los procesos, secuencia de 20 rutas y registro CSV.

### Ejecución

Python 3.11 o superior y los puertos `5000`, `5001` y `5002` disponibles. TCP y gRPC se ejecutan por separado porque utilizan los mismos puertos.

Comando desde la raíz del repositorio:

```bash
python src/sockets/client.py
```

El coordinador inicia los tres nodos, realiza los 20 intercambios del contrato, guarda los eventos, ejecuta el verificador y cierra los procesos.

### Registro y verificación

Cada sesión guarda sus eventos en `data/<sesion>/sockets/eventos/lamport-01/eventos.csv`. Las columnas son `nodo,tipo_evento,reloj,hora_real,contraparte,msg_id`. Envío y recepción se emparejan por `msg_id`.

Verificación del CSV de la prueba realizada:

```bash
python analysis/verificar_lamport.py data/20261119-222709-kevin/sockets/eventos/lamport-01/eventos.csv 20
```

Resultado obtenido: **40 eventos, 20 mensajes identificados, 20 pares válidos y 0 errores**.

### Documentación y evidencia

- [Guía TCP con Lamport](docs/AVANCE-TCP-LAMPORT.md).
- [CSV de los 20 intercambios](data/20261119-222709-kevin/sockets/eventos/lamport-01/eventos.csv).
- [Captura de la verificación con usuario, equipo, fecha y hora](screenshots/tcp-lamport-20-intercambios-kevin.jpeg).
- [Contrato del equipo](docs/CONTRATO.md).

Las solicitudes y los acuses usan JSON UTF-8 delimitado por un salto de línea. Se validan los campos del mensaje y se limita la espera de conexión y lectura. Un fallo detiene la secuencia y conserva los eventos registrados.

### Uso de inteligencia artificial

Se utilizó ChatGPT Sol 6.1 mediante Codex como apoyo para preparar el código y mejorar parte de la documentación y revisar el contrato. Yo ejecuté el programa en mi equipo y comprobé el resultado del verificador.

## Informe y análisis

Responsable: Eduardo David Reinoso Vélez.

### Compilar el informe

- Compilador: `pdflatex` con `biber` para la bibliografía IEEE (biblatex). En Windows se usó MiKTeX.
- Archivo principal: `docs/guia1_practica.tex`. El PDF resultante queda en `docs/guia1_practica.pdf`.
- Paquetes: `babel` (español), `biblatex`, `csquotes`, `graphicx`, `booktabs`, `amsmath`, `listings`, `tikz` e `hyperref`.
- Se compila desde la carpeta `docs/`, porque el informe incluye `../proto/mensajes.proto` con una ruta relativa.

Comandos, en este orden, desde la carpeta `docs/`:

```bash
pdflatex guia1_practica.tex
biber guia1_practica
pdflatex guia1_practica.tex
pdflatex guia1_practica.tex
```

### Generar tablas y figuras

Las tablas y gráficos del informe salen de los CSV, no se escriben a mano. Desde la raíz del repositorio, con `requirements.txt` instalado:

```bash
python analysis/analisis.py data/<sesion>
```

Lee `data/<sesion>/`, calcula media, mediana, desviación estándar, p95 y mensajes por segundo por mecanismo, modo y tamaño (sin el calentamiento), y escribe las figuras en `docs/figures/` y las tablas en `docs/tablas/`.

Las tablas de la verificación de Lamport se generan con los CSV de eventos de TCP y gRPC y el del empate:

```bash
python analysis/tabla_lamport.py --tcp <eventos.csv> --grpc <eventos.csv> --empate <eventos.csv>
```
