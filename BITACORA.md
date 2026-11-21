# Bitácora del equipo GLMR — GA-SUM-02 / PE-U1

Cada integrante agrega SOLO sus propias entradas al final del archivo (no editar las de otros).
Una entrada por sesión de trabajo, con este formato:

## AAAA-MM-DD — Nombre del integrante (con quién estuvo, si fue en grupo)
- **Presentes:**
- **Realizado:**
- **Problemas encontrados:**
- **Solución:**


## 2026-11-17 — Carlos Manotoa
- **Realizado:** Revisión de los requisitos experimentales y definición del plan de ejecución
- **Problemas encontrados:** Falta revisar y confirmar la secuencia de ejecución del plan
- **Solución:** Se registraron como pendientes de revisión y confirmación


## 2026-11-18 — Kevin Leonel García Bazurto

- **Presentes:** Kevin Leonel García Bazurto.
- **Actividad:** primer avance de comunicación con sockets TCP.

### Trabajo realizado

- Se incorporaron `src/sockets/servidor.py` y
  `src/sockets/cliente.py` al repositorio.
- El cliente envía un mensaje JSON con los campos `sender`,
  `timestamp` y `message`.
- El servidor interpreta el mensaje, comprueba la presencia de
  los campos obligatorios y devuelve un acuse JSON.
- Se utilizó UTF-8 para codificar los mensajes y un salto de línea
  para indicar su final.
- Se documentaron en el README los comandos de ejecución,
  las salidas esperadas y el alcance del avance.

### Decisiones

- Se utiliza `127.0.0.1:5000` para el intercambio inicial.
- El cliente envía `timestamp = 1` como dato de prueba.
- La actualización del reloj de Lamport y los tres nodos
  se incorporarán en el siguiente avance.

### Problemas encontrados

- El contrato del equipo menciona `server.py` y `client.py`,
  mientras que los archivos actuales se llaman `servidor.py`
  y `cliente.py`.

### Solución y coordinación pendiente

- El README utiliza los nombres actuales de los archivos.
- Se debe acordar con el equipo la nomenclatura definitiva
  y actualizar el contrato o los archivos para que coincidan.

### Verificación
- Pendiente de registrar: comandos ejecutados en
  la computadora, resultado observado y problemas encontrados.

### Próximos pasos

- Integrar la configuración compartida del equipo.
- Ampliar el programa a tres nodos.
- Implementar las reglas del reloj de Lamport.
- Registrar los eventos en CSV según `docs/CONTRATO.md`.

### Uso de inteligencia artificial

Se utilizó ChatGPT Codex para preparar el código inicial,
y en base a eso ya realizar la práctica y explicar su funcionamiento, se usó también para ayudar con la documentación.

### Enlace al commit de código

Pendiente de añadir el enlace del primer avance TCP.

## 2026-11-18 — Carlos Manotoa
- **Presentes:** Carlos (registro del acuerdo del equipo)
- **Realizado:** Se incorporaron al contrato la secuencia de 20 intercambios, las carpetas por ejecución e intento y los encabezados de eventos, latencia y duración.
- **Problemas encontrados:** Al reiniciar los relojes se pueden repetir los identificadores. Una corrida reintentada también puede dejar varios CSV para la misma medición.
- **Solución:** Cada ejecución e intento conserva sus propios archivos. El coordinador reúne las muestras concurrentes y Eduardo usa un solo intento completo por corrida.
- **Uso de inteligencia artificial:** Usé ChatGPT (Codex) para aclarar el protocolo experimental y preparar la redacción del contrato a partir de los acuerdos del equipo.


## 2026-11-18 — Eduardo David Reinoso Vélez
- **Presentes:** Eduardo Reinoso.
- **Realizado:** Lector de CSV (`analysis/analisis.py`) que valida columnas y rutas contra el contrato y toma el intento completo de menor número por corrida. Cálculo de media, mediana, desviación estándar, p95 y mensajes por segundo por mecanismo, modo y tamaño, sin el calentamiento.
- **Problemas encontrados:** Todavía no hay CSV reales de TCP ni de gRPC. El contrato nombra `analisis.py` y el plan del equipo `analizar.py`.
- **Solución:** Se probó con datos de prueba locales, que no se suben al repositorio, y se contrastó una combinación con un cálculo independiente en numpy. Se mantiene `analisis.py`, el nombre del contrato.
- **Uso de inteligencia artificial:** indiqué a Claude (Sonnet 5.5) qué debía hacer cada script según las tareas del plan y Claude generó el código. Se probó con datos de prueba locales y con un cálculo independiente en numpy. El código pasó por mi revisión.
- **Commit del lector:** https://github.com/yaser-uwu/GA-SUM-02-PE-U1/commit/e26d2441f28a39a7db63cd3142639fa8c134c358


## 2026-11-18 — Bryan Humberto Lombeida Escaleras
- **Presentes:** Bryan Lombeida(sesión individual).
- **Realizado:**
  - Definí `proto/mensajes.proto` con `service Mensajeria`, `rpc EnviarMensaje(Mensaje) returns (Acuse)`, `Mensaje{sender, timestamp, message}` y `Acuse{ok, error}`, siguiendo la estructura del mensaje documentada en el README y los campos del contrato del equipo.
  - Generé `src/grpc/mensajes_pb2.py` y `src/grpc/mensajes_pb2_grpc.py` con `grpcio-tools` desde la raíz del repositorio.
  - Implementé `src/grpc/servidor_grpc.py` (escucha en `127.0.0.1:5000`, imprime emisor, reloj y mensaje, y devuelve `Acuse(ok=True)`) y `src/grpc/cliente_grpc.py` (envía `sender="nodo-A"`, `timestamp=1`, `message="Hola desde nodo-A"`, con timeout de 10 s y manejo de `grpc.RpcError`).
  - Verifiqué la llamada en dos terminales: el cliente recibió el acuse `ok=True` y el servidor mostró los tres campos del mensaje.
  - Tomé tres capturas en mi máquina (ambas terminales, servidor y cliente) y las guardé en `screenshots/`.
- **Problemas encontrados:**
  - El entorno no tenía `grpcio` ni `grpcio-tools`; el Python del sistema era 3.14 y no incluía esos paquetes.
  - El material de la actividad indicaba `mensajes.proto`, mientras que el contrato del equipo mencionaba `messaging.proto`.
  - El código generado puede fallar al importarse si los scripts se ejecutan como módulo (`python -m ...`).
- **Solución:**
  - Creé un entorno virtual con Python 3.12 e instalé `grpcio 1.85.3`, `grpcio-tools 1.85.3` y `protobuf 7.36.2`. El `.venv` está en `.gitignore` y no se versiona.
  - Mantuve `mensajes.proto`; queda pendiente coordinar con Carlos la actualización de `docs/CONTRATO.md` y `readme.md`.
  - Ejecuté los scripts directamente desde la raíz: `python src/grpc/servidor_grpc.py` y `python src/grpc/cliente_grpc.py`.
- **Uso de inteligencia artificial:**
  Utilicé el agente OpenCode (modelo DeepSeek V4.1 Flash Free) para preparar el `.proto`, el servidor y el cliente. Revisé y ejecuté el código en dos terminales antes de subirlo.

## 2026-11-19 — Carlos Manotoa
- **Realizado:** Se prepararon los scripts para registrar la máquina y generar las huellas SHA-256. En una prueba temporal en Linux (sistema operativo donde estoy trabajando), la ficha incluyó los cinco datos requeridos y las huellas detectaron el cambio en un CSV.
- **Problemas encontrados:** Falta confirmar la máquina oficial. En esta copia aún no están los CSV de una ejecución real de TCP y gRPC. Yaser confirmó que cambiará los nombres de los archivos TCP a `server.py` y `client.py`.
- **Solución:** Los comandos quedaron en el README. La ficha y el manifiesto oficiales se generarán con el equipo y los datos de la medición.
- **Pendiente de coordinación:** Confirmar la máquina para registrar su ficha y fijar las versiones exactas de las cinco dependencias. Cuando esté el cambio de Yaser, actualizar las instrucciones TCP. Cuando ambos mecanismos exporten los CSV, probar una ejecución Lamport de 20 pares y una corrida de latencia por mecanismo con Eduardo. Después, ejecutar las corridas oficiales, comprobar el empate de relojes, generar y verificar `data/SHA256SUMS` y tomar la captura del nodo C.
- **Verificación de integridad:** Se añadió `--verificar` al script SHA-256 para poder comprobar las huellas con Python. Las pruebas locales confirmaron que detecta cambios, archivos faltantes y CSV nuevos sin huella. Los archivos de prueba se usaron en una carpeta temporal.
- **Uso de inteligencia artificial:** Usé Codex para preparar y probar los scripts de registro de la máquina y de generación y verificación de huellas SHA-256.


## 2026-11-19 — Eduardo David Reinoso Vélez
- **Presentes:** Eduardo Reinoso.
- **Realizado:**
  - Agregué a `analysis/analisis.py` el diagrama de cajas de las latencias (300 DPI), las barras de latencia y de rendimiento con media ± 1 desviación estándar, y las tablas LaTeX `latencia.tex` y `rendimiento.tex`. Las figuras van a `docs/figures/` y las tablas a `docs/tablas/`.
  - Armé `docs/referencias.bib` con seis referencias IEEE: cuatro artículos con DOI, el RFC 9293 y Lamport (1978). Abrí cada DOI y comprobé título, autores, volumen, páginas y fecha.
  - Escribí en `docs/guia1_practica.tex` el marco conceptual, la arquitectura (diagrama de los tres nodos y contenido de `proto/mensajes.proto`) y el protocolo experimental. La carátula, el objetivo y la hipótesis son del 18 de noviembre; la hipótesis, que los sockets TCP tendrán menor latencia que gRPC, se escribió antes de medir.
- **Problemas encontrados:**
  - Una referencia, un libro, no tenía DOI y su ISBN solo se pudo comprobar en librerías.
  - El informe lee el `.proto` con la ruta `../proto/mensajes.proto`, así que solo compila desde `docs/`.
  - El diagrama de nodos sale del contrato y falta contrastarlo con el de FORM-TL-01.
- **Solución:**
  - Reemplacé el libro por un artículo con DOI verificado.
  - Se compila desde `docs/`, como indican las instrucciones del README.
  - Queda pendiente comparar el diagrama con el de FORM-TL-01.
- **Uso de inteligencia artificial:** usé Claude (Sonnet 5.5) como asistente. Yo definí qué debía calcular y graficar el script, escogí la hipótesis y decidí reemplazar la referencia sin DOI. A partir de esas instrucciones, Claude escribió el código del script, reescribió el texto de las secciones y buscó las referencias. Yo comprobé los DOI en el navegador y revisé el código y el texto.
- **Commits:** https://github.com/yaser-uwu/GA-SUM-02-PE-U1/commit/128534d y https://github.com/yaser-uwu/GA-SUM-02-PE-U1/commit/8cbc828

## 2026-11-19 — Bryan Humberto Lombeida Escaleras
- **Presentes:** Bryan Lombeida (sesión individual).
- **Realizado:**
  - Amplié `proto/mensajes.proto` con el servicio `Control` (`Reiniciar` y `OrdenarEnvio`) para que el coordinador pudiera ordenar los envíos sin mezclar esa comunicación con el mensaje de datos. El servicio `Mensajeria` y el mensaje `Mensaje{sender, timestamp, message}` se mantuvieron iguales.
  - Agregué `RUTAS_LAMPORT` en `src/common/config.py` con la secuencia del contrato: `A->B, B->C, C->A, A->C, C->B, B->A` tres veces y `A->B, B->C` al final, para un total de 20 rutas.
  - Implementé `src/grpc/nodo.py`: cada nodo abre su servidor gRPC en `127.0.0.1:5000`, `5001` o `5002`, mantiene su propio reloj de Lamport (incrementa antes de enviar y aplica `max(local, recibido) + 1` al recibir) y escribe sus eventos en un CSV por nodo.
  - Implementé `src/grpc/coordinador_lamport.py`: en modo automático lanza los tres nodos, espera a que estén listos, reinicia los relojes, ordena las 20 rutas, une los CSV por nodo en `eventos.csv`, ejecuta `analysis/verificar_lamport.py` y detiene los procesos. En modo `--manual` se conecta a nodos que ya están en marcha.
  - Regeneré `src/grpc/mensajes_pb2.py` y `src/grpc/mensajes_pb2_grpc.py` desde el `.proto` actualizado.
  - Comprobé que `src/grpc/servidor_grpc.py` y `src/grpc/cliente_grpc.py`, usados en la primera llamada, siguen funcionando con el `.proto` ampliado.
  - Ejecuté primero una prueba automática y después la corrida oficial en modo manual con la sesión `20261119-220530-bryan`. El coordinador completó los 20 pasos y generó `data/20261119-220530-bryan/grpc/eventos/lamport-01/eventos.csv` con 40 eventos: 20 envíos y 20 recepciones.
  - El verificador reportó 40 filas, 20 mensajes identificados, 20 pares válidos, 0 errores y `VERIFICACIÓN CORRECTA`.
  - Se agregaron cuatro capturas en `screenshots/`: los tres nodos en marcha y el coordinador con los 20 pasos y el resumen de verificación.
  - Documenté en `readme.md` los comandos para iniciar los tres nodos, ejecutar el coordinador en modo manual y automático, ubicar el CSV y verificarlo.
- **Problemas encontrados:**
  - El contrato del equipo todavía menciona `proto/messaging.proto` y los nombres `server_grpc.py`/`client_grpc.py`, mientras que el repositorio usa `proto/mensajes.proto` y los scripts nuevos `nodo.py`/`coordinador_lamport.py`.
- **Solución:**
  - Mantuve `mensajes.proto` para no romper la implementación ya probada y documenté los comandos nuevos en `readme.md`.
  - Queda pendiente coordinar con Carlos la actualización de `docs/CONTRATO.md` para que los nombres coincidan.
- **Uso de inteligencia artificial:**
  - Utilicé el agente OpenCode (modelo DeepSeek V4.1 Flash Free) para implementar los nodos, el coordinador y la integración del CSV. Revisé el código y ejecuté las pruebas antes de dejar este avance.
- **Aviso para Carlos Manotoa y el equipo:**
  - El CSV real de gRPC ya está disponible en `data/20261119-220530-bryan/grpc/eventos/lamport-01/eventos.csv`. Contiene los 20 intercambios Lamport (40 eventos) y pasó la verificación. Cualquiera que necesite este CSV para el análisis, las huellas SHA-256 o la comparación con TCP puede usarlo.

## 2026-11-19 — Kevin Leonel García Bazurto

- **Presentes:** Kevin Leonel García Bazurto.
- **Realizado:**
  - Renombré los archivos TCP a `client.py` y `server.py`, de acuerdo con el contrato.
  - Amplié el programa a tres nodos con relojes de Lamport independientes y ejecuté las 20 rutas acordadas, esperando el acuse antes de continuar con cada ruta.
  - Registré los envíos y recepciones en `data/20261119-222709-kevin/sockets/eventos/lamport-01/eventos.csv`.
  - Ejecuté el verificador: 40 eventos, 20 mensajes identificados, 20 pares válidos y 0 errores.
  - Subí la captura `screenshots/tcp-lamport-20-intercambios-kevin.jpeg`, que muestra la verificación, el usuario, el equipo, la fecha y la hora.
  - Incorporé `docs/AVANCE-TCP-LAMPORT.md` y actualicé mi sección TCP del README con los comandos y los enlaces a la evidencia.
- **Problemas encontrados:** Los nombres anteriores `cliente.py` y `servidor.py` no coincidían con el contrato.
- **Solución:** Renombré ambos archivos y actualicé las instrucciones con los nombres actuales.
- **Uso de inteligencia artificial:** Utilicé ChatGPT Sol 6.1 mediante Codex como apoyo para preparar parte del código y la documentación y como ayuda para revisar el contrato. Ejecuté el programa en mi equipo y comprobé el resultado del verificador.


## 2026-11-20 — Bryan Humberto Lombeida Escaleras
- **Presentes:** Bryan Lombeida (sesión individual).
- **Realizado:**
  - Agregué `--sin-eventos` a `src/grpc/nodo.py` para que los nodos atiendan las llamadas de latencia sin actualizar el reloj de Lamport ni escribir eventos. El modo normal de Lamport quedó igual.
  - Implementé `src/grpc/coordinador_latencia.py`: ejecuta 100 envíos secuenciales, repitiendo cinco veces las 20 rutas, mide el RTT de cada llamada con `time.perf_counter()` y escribe `latencia.csv` y `duracion.csv` en la ruta del contrato. Permite iniciar los nodos automáticamente o usar `--manual` con nodos ya iniciados.
  - Ejecuté el piloto de 100 bytes con la sesión `20261120-002144-bryan`, en `corrida-00` (calentamiento): 100/100 envíos, 100 filas únicas, duración `0.053090 s`, RTT mínimo `0.424 ms`, mediano `0.475 ms` y máximo `2.405 ms`; estado `completa` y verificación `CORRECTA`.
  - Los datos quedaron en `data/20261120-002144-bryan/grpc/latencia/secuencial/corto/corrida-00/intento-01/`. No es una corrida válida: es el calentamiento.
  - Probé también el modo manual, el tamaño largo de 10240 bytes y una corrida temporal de regresión de Lamport; los 20 pares de Lamport siguieron verificándose correctamente.
  - Documenté los comandos automático y manual en `readme.md`.
  - Se agregaron cinco capturas en `screenshots/`: los tres nodos con `--sin-eventos`, el coordinador del piloto y los CSV.
- **Problemas encontrados:**
  - El `.venv` local no tiene `matplotlib` ni `pandas`, así que no se pudo ejecutar `analysis/analisis.py`; validé la estructura y el contenido de los CSV con comprobaciones propias.
- **Solución:**
  - El piloto se validó con un chequeo de 100 filas, numeración del 1 al 100, RTT positivos y `duracion.csv` completa. El análisis gráfico queda para cuando el equipo tenga esas dependencias.
- **Pendiente de coordinación:**
  - Antes de las corridas oficiales, acordar con Carlos y Kevin la máquina y el mismo identificador de sesión para TCP y gRPC. Después se ejecutan las corridas `1` a `5` por tamaño y la prueba concurrente.
  - Cuando estén los CSV completos, entregarlos a Eduardo para el análisis y acordar con Carlos la ficha de la máquina y `data/SHA256SUMS`.
- **Uso de inteligencia artificial:**
  - Utilicé el agente OpenCode (modelo DeepSeek V4.1 Flash Free) como apoyo para preparar parte del código y la documentación, el modo de latencia, el coordinador, y como ayuda para revisar el contrato. Revisé el código y ejecuté el piloto y las pruebas de regresión.

## 2026-11-20 — Carlos Manotoa
- **Presentes:** Carlos.
- **Realizado:** Se verificaron los CSV de Lamport de TCP y gRPC. Cada ejecución revisada tuvo 20 pares válidos y cero errores. El piloto gRPC de 100 bytes tuvo 100 muestras positivas, numeradas del 1 al 100. Corresponde al calentamiento.
- **Evidencia del empate:** Se ejecutaron tres procesos TCP con relojes inicialmente en cero. A y B enviaron a C sin depender entre sí y registraron `nodo-A:1` y `nodo-B:1`, ambos con reloj 1. C registró las recepciones con reloj 3 para A y reloj 2 para B. El verificador aceptó los dos pares. [CSV de la ejecución](data/20261120-151615-carlos/sockets/eventos/empate-01/eventos.csv).
- **Captura del nodo C:** Tomé la captura en mi equipo durante una ejecución TCP. Se ven el usuario, el nombre de la máquina, la fecha y hora, el nodo C escuchando en el puerto 5002 y la recepción del mensaje `nodo-A:1` con reloj 2. [Captura](screenshots/TCP_nodo-C_Carlos_20261120.png).
- **Problemas encontrados:** Los 20 intercambios acordados se ejecutan en secuencia. Para demostrar el empate hacía falta una ejecución en la que los emisores fueran independientes. En esta copia aún faltan la medición de latencia TCP y la prueba concurrente de latencia.
- **Solución:** Se usó `analysis/comprobar_empate_tcp.py --sesion <sesion>` con dos envíos independientes al nodo C. La prueba de empate quedó separada de las mediciones de latencia.
- **Pendiente de coordinación:** Confirmar la máquina y la sesión comunes, completar el piloto TCP y los dos modos concurrentes, y generar las huellas cuando estén todos los CSV oficiales.
- **Uso de inteligencia artificial:** Usé Codex para revisar los CSV de Lamport y para preparar y ejecutar el script de la prueba de empate con los nodos TCP.


## 2026-11-20 — Eduardo David Reinoso Vélez
- **Presentes:** Eduardo Reinoso.
- **Realizado:**
  - Agregué `analysis/tabla_lamport.py`, que lee los CSV de eventos de TCP y gRPC y el del empate de relojes, y genera `docs/tablas/lamport_resumen.tex` y `docs/tablas/empate.tex`.
  - Escribí en `docs/guia1_practica.tex` la sección de verificación del reloj de Lamport, con los CSV de Kevin (TCP), Bryan (gRPC) y Carlos (empate). Las dos ejecuciones tienen 40 eventos, 20 pares y 0 violaciones; en el empate, nodo-A y nodo-B envían a nodo-C con reloj 1.
  - Agregué las secciones de implementación y discusión cualitativa (desarrollo, tipado y manejo de errores) con las amenazas a la validez.
- **Problemas encontrados:**
  - `listings` no aceptaba los acentos del `.proto` al incluirlo en el informe.
  - En el repositorio faltan las mediciones de latencia de TCP y las corridas oficiales de gRPC, por lo que todavía no se pueden escribir los resultados ni las conclusiones con cifras.
- **Solución:**
  - Configuré `listings` para que acepte los acentos y comprobé que el informe compila desde un clon limpio.
  - Los resultados quedan pendientes hasta que estén los CSV de latencia.
- **Uso de inteligencia artificial:** usé Claude (Sonnet 5.5) como herramienta de apoyo. Estructuré las secciones faltantes y diseñé la lógica del script de Lamport, usando la IA para pulir la redacción y generar la base del código. Luego revisé a fondo el texto y validé manualmente los resultados de las tablas contra los CSV.

## 2026-11-20 — Kevin Leonel García Bazurto

- **Presentes:** Kevin Leonel García Bazurto.
- **Realizado:**
  - Se incorporó `src/sockets/coordinador_latencia.py` para medir 100 solicitudes por corrida con mensajes de 100 y 10240 bytes, calentamiento, cinco repeticiones y tres clientes concurrentes.
  - Se añadió `--sin-eventos` al servidor TCP para desactivar la impresión de eventos durante las mediciones.
  - Se ejecutaron 14 corridas completas en la sesión `20261120-175011-kevin`: 1400 solicitudes con acuse y 28 CSV originales en `data/20261120-175011-kevin/sockets/latencia/`.
  - Se añadieron cinco pruebas automatizadas para ambos tamaños, mensajes fragmentados, JSON inválido, acuses negativos y CSV secuenciales y concurrentes. Todas pasaron.
  - Se repitió la verificación de Lamport: 40 eventos, 20 pares válidos y 0 errores.
  - Se publicó la ficha `data/maquina_kevin.json` y el manifiesto `data/SHA256SUMS`, con las huellas de los 28 CSV nuevos y los 12 CSV que ya estaban en el repositorio.
  - Se comprobó desde un clon limpio que las cinco pruebas pasan y que las huellas de los 40 CSV son correctas.
  - Se incorporaron `docs/TCP-LATENCIA.md` y `docs/GUIA-TCP-LATENCIA.md` con la descripción de la medición y sus instrucciones de ejecución.
- **Problemas encontrados:** El servidor imprimía los eventos durante la recepción. La carga automática de la carpeta completa de datos en GitHub falló.
- **Solución:** Se añadió un modo de medición sin impresión de eventos y se adjuntaron los CSV en las carpetas de cada corrida, conservando los originales y separando los calentamientos.
- **Uso de inteligencia artificial:** Se utilizó ChatGPT Sol 6.1 mediante Codex como apoyo para preparar y revisar la implementación, ya las pruebas las hice yo y la documentación la mejoré con la IA. La validación que hice incluyó ejecución real, comprobación de los CSV, verificación de Lamport y pruebas desde un clon limpio.

## 2026-11-20 — Bryan Humberto Lombeida Escaleras (preparación de la matriz gRPC)
- **Presentes:** Bryan Lombeida (sesión individual).
- **Realizado:**
  - Amplié el servicio `Control` en `proto/mensajes.proto` y regeneré los módulos Python. Cada nodo emisor invoca `EnviarMensaje` y mide el RTT entre la llamada y el acuse, sin incluir las órdenes del coordinador ni el arranque. Los nodos mantienen sus relojes de Lamport sin escribir eventos durante la medición.
  - Completé los modos secuencial y concurrente en `src/grpc/coordinador_latencia.py`. En concurrente, los tres clientes comparten una señal de inicio y reparten los 100 envíos en 34 de A a B, 33 de B a C y 33 de C a A. La opción `--matriz` ejecuta las 14 corridas para los tamaños de 100 y 10 240 bytes.
  - Documenté en [el README](readme.md#matriz-oficial-de-kevin-14-corridas) las versiones probadas, el comando de la matriz, los reintentos y cómo mostrar los CSV para las capturas.
- **Problemas encontrados:** El piloto enviaba desde el coordinador en lugar de hacerlo desde el nodo emisor, y repetir una corrida podía sobrescribir el intento anterior.
- **Solución y verificación:** Moví el envío y la medición al nodo emisor y reservé una carpeta nueva para cada intento. En una sesión local de prueba completé las 14 corridas y validé 1 400 muestras de RTT; también comprobé el reparto 34/33/33 en ambos tamaños. Un reintento conservó intacto el intento anterior y, en una prueba de fallo inducido, se guardó la muestra previa y el intento quedó marcado como `fallida`. La prueba de regresión de Lamport mantuvo los 20 pares válidos.
- **Pendiente de coordinación:** Kevin debe ejecutar la matriz y tomar las capturas en la misma máquina donde midió TCP, con la sesión `20261120-175011-kevin`. Los resultados oficiales quedarán en `data/20261120-175011-kevin/grpc/latencia/`. Las pruebas locales no sustituyen esas mediciones.
- **Uso de inteligencia artificial:** Usé OpenCode (modelo DeepSeek V4.1 Flash Free) como apoyo en la implementación, y la documentación de los pasos para Kevin.


## 2026-11-21 — Kevin Leonel García Bazurto

- **Presentes:** Kevin Leonel García Bazurto.
- **Realizado:**
  - Se preparó el entorno para ejecutar gRPC en la misma computadora utilizada para las mediciones TCP.
  - Se completaron las 14 corridas de gRPC con mensajes de 100 y 10240 bytes, incluyendo los calentamientos, cinco repeticiones por tamaño y las pruebas concurrentes.
  - Las corridas terminaron con 1400 envíos exitosos. Se publicaron los 28 CSV en `data/20261120-175011-kevin/grpc/latencia/`.
  - Se comprobó que cada corrida tuviera 100 muestras, números de envío del 1 al 100, tiempos positivos y estado `completa`.
  - Se ejecutó el análisis de Eduardo con los datos de TCP y gRPC. Se reconocieron las 28 corridas de ambos mecanismos sin avisos de corridas faltantes.
  - Se guardaron las versiones del entorno en `requirements.txt` y se actualizó `data/SHA256SUMS` con las huellas de los 68 CSV. Los datos anteriores conservaron su contenido.
- **Problemas encontrados:** Las versiones del entorno instalado no coincidían con las indicadas para ejecutar el código de gRPC.
- **Solución:** Se creó un entorno separado con las versiones comprobadas, sin cambiar la instalación anterior de Python.
- **Uso de inteligencia artificial:** Se utilizó ChatGPT Sol 6.1 mediante Codex como ayudante y guía para preparar el entorno, ejecutar las mediciones y comprobar los CSV y el análisis, así agilizaba este trabajo con la ayuda de la IA, También se utilizó como apoyo para redactar esta entrada de forma más clara.

## 2026-11-21 — Carlos Manotoa
- **Presentes:** Carlos (revisión de la copia local).
- **Realizado:** Se comprobó la sesión `20261120-175011-kevin`. TCP y gRPC tienen 14 corridas completas cada uno, con 100 muestras numeradas del 1 al 100 por corrida. Las 2800 muestras incluyen cuatro calentamientos que quedan fuera del análisis.
- **Problemas encontrados:** La comparación estaba pendiente hasta recibir los datos de gRPC obtenidos en el mismo equipo que TCP.
- **Solución:** Kevin publicó los CSV de ambos mecanismos bajo la misma sesión y registró la ficha en [`data/maquina_kevin.json`](data/maquina_kevin.json) y las cinco versiones exactas en [`requirements.txt`](requirements.txt). Se verificaron las 68 huellas de [`data/SHA256SUMS`](data/SHA256SUMS) con el script Python y con `sha256sum -c`, con cero diferencias.
- **Uso de inteligencia artificial:** Se usó ChatGPT mediante Codex (GPT-6 en la revisión final) como apoyo para aclarar el protocolo experimental, buscar y filtrar información, transformar rápidamente contenido entre formatos (de txt a tex o md) y apoyar en la resolución de los problemas encontrados. También se empleó para preparar la redacción del contrato y para desarrollar, revisar y probar el verificador de Lamport y los scripts de evidencia. No obstante, la redacción, la revisión final y la documentación fueron realizadas y revisadas por el estudiante. Los resultados se comprobaron ejecutando el verificador sobre los CSV reales de TCP y gRPC, reproduciendo el empate con tres nodos TCP y verificando las huellas SHA-256 de los archivos publicados.

## 2026-11-21 — Eduardo David Reinoso Vélez
- **Presentes:** Eduardo Reinoso.
- **Realizado:**
  - Ejecuté `analysis/analisis.py` en mi equipo sobre la sesión oficial `data/20261120-175011-kevin` y generé las tablas y figuras con las corridas oficiales de TCP y gRPC (`docs/tablas/` y `docs/figures/`).
  - Completé `docs/guia1_practica.tex` con los resultados, la discusión (latencia, rendimiento, hipótesis y escenario del PFC), las conclusiones con cifras, la tabla de aportes y la declaración de uso de IA.
  - Corregí el comando de análisis del README (el argumento es la carpeta `data/<sesión>`) y agregué la sección de informe y análisis.
  - Compilé el informe desde un clon limpio del repositorio: 13 páginas, sin errores ni avisos.
  - Tomé la captura de la ejecución del análisis con usuario, nombre de la máquina, fecha y hora visibles: [captura](screenshots/analisis_script_Eduardo-Reinoso_20261121.png).
- **Problemas encontrados:**
  - Al ejecutar el script, pandas mostraba `ChainedAssignmentError` por asignaciones encadenadas.
  - Mi primera captura no mostraba el nombre de la máquina ni la fecha y estaba partida en dos.
- **Solución:**
  - Cambié las asignaciones por `DataFrame.assign` en `analysis/analisis.py`; la ejecución ya no muestra avisos y las tablas salen con los mismos valores.
  - Repetí la captura con un comando que imprime usuario, equipo y fecha antes de ejecutar el análisis.
- **Uso de inteligencia artificial:** usé Claude (Sonnet 5.5) para corregir el script de análisis, pulir redacción de las secciones de resultados, discusión y conclusiones, y ordenar los commits. Yo ejecuté el análisis en mi equipo, comprobé que las cifras del informe coinciden con la salida del script y elegí el escenario del PFC.
