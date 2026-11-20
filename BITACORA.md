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
