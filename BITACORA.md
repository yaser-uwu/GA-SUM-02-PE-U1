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
