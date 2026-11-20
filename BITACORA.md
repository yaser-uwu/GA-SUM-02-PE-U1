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


<<<<<<< HEAD
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
=======
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
>>>>>>> 6b94022 (Implementación del sistema de nodos gRPC con reloj de Lamport)

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
