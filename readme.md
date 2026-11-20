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
## Ejecución del primer avance con sockets TCP

Responsable: Kevin Leonel García Bazurto.

### Objetivo

Demostrar el envío de un mensaje JSON desde un cliente hacia un servidor
mediante una conexión TCP y recibir un acuse de recepción.

### Archivos

- `src/sockets/servidor.py`: recibe el mensaje, comprueba que contiene los
  campos obligatorios, muestra su contenido y devuelve el acuse.
- `src/sockets/cliente.py`: establece la conexión, envía el mensaje y muestra
  la respuesta recibida.

### Requisitos para este avance

- Python 3.11 o superior.
- Puerto TCP 5000 disponible.
- Ambos programas ejecutándose en la misma computadora.

Este avance utiliza los módulos `socket` y `json`, incluidos en Python.
Para ejecutar únicamente este intercambio no es necesario instalar paquetes
adicionales. Las dependencias generales de la práctica se encuentran en
`requirements.txt`.

### Preparación

Abre dos terminales en la raíz del repositorio, es decir, la carpeta que
contiene `src/`, `docs/` y `requirements.txt`.

Comprueba la versión de Python:

```bash
python --version
```

Si Windows reconoce el comando `py`, puedes utilizarlo en lugar de `python`
en los pasos siguientes.

### Paso 1. Iniciar el servidor

En la primera terminal ejecuta:

```bash
python src/sockets/servidor.py
```

Debe aparecer:

```text
Servidor TCP escuchando en 127.0.0.1:5000
```

Mantén esta terminal abierta mientras ejecutas el cliente.

### Paso 2. Ejecutar el cliente

En la segunda terminal ejecuta:

```bash
python src/sockets/cliente.py
```

El cliente envía este mensaje:

```json
{
  "sender": "nodo-A",
  "timestamp": 1,
  "message": "Hola desde nodo-A"
}
```

La salida esperada incluye:

```text
Mensaje enviado: {'sender': 'nodo-A', 'timestamp': 1, 'message': 'Hola desde nodo-A'}
Acuse recibido: {'ok': True}
```

### Paso 3. Revisar el servidor

En la primera terminal deben aparecer los campos recibidos:

```text
Emisor: nodo-A
Reloj de Lamport recibido: 1
Mensaje: Hola desde nodo-A
```

También aparece la dirección del cliente. El puerto temporal del cliente
puede variar entre ejecuciones.

Puedes volver a ejecutar el cliente para repetir el intercambio.
Para detener el servidor, pulsa Ctrl+C en su terminal.

### Formato de comunicación

El cliente y el servidor intercambian texto JSON codificado en UTF-8.

Cada mensaje termina con un salto de línea (`\n`). El receptor utiliza
`readline()` para leer hasta ese delimitador, porque TCP puede entregar
un mensaje en varios fragmentos.

El servidor comprueba que el JSON sea un objeto y contenga los campos
`sender`, `timestamp` y `message`.

Cuando acepta el mensaje, devuelve:

```json
{"ok": true}
```

Si recibe un JSON inválido o faltan campos obligatorios, intenta devolver:

```json
{"ok": false, "error": "Mensaje JSON inválido"}
```

El cliente espera hasta 10 segundos para las operaciones de conexión
y lectura. El servidor también limita a 10 segundos la espera de datos
en cada conexión aceptada.

### Alcance actual

- El servidor escucha en `127.0.0.1:5000`.
- El cliente se identifica como `nodo-A` dentro del mensaje.
- Cada ejecución del cliente envía un mensaje y recibe un acuse.
- El servidor permanece disponible para nuevas conexiones y las atiende
  una a la vez.
- `timestamp` tiene el valor fijo `1` como dato de prueba.

### Próximos avances

- Integrar la configuración compartida de `src/common/config.py`.
- Ejecutar nodo-A, nodo-B y nodo-C con sus propios relojes de Lamport.
- Incrementar el reloj antes de enviar y actualizarlo al recibir.
- Registrar los 20 intercambios y sus eventos en CSV.
- Medir la latencia y realizar las repeticiones, tamaños de mensaje
  y pruebas concurrentes del protocolo experimental.

Los formatos finales de nodos, mensajes y CSV están documentados en
`docs/CONTRATO.md`.

### Solución de problemas

| Problema | Qué revisar |
|---|---|
| Python no se reconoce | Prueba `py --version` y usa `py` en los comandos. |
| No se encuentra el archivo | Comprueba que la terminal está en la raíz del repositorio. |
| Conexión rechazada | Inicia primero el servidor y confirma que ambos archivos usan el mismo host y puerto. |
| Puerto 5000 ocupado | Detén la ejecución anterior del servidor o el proceso que esté utilizando ese puerto. |
| Tiempo de espera agotado | Comprueba que el otro programa sigue en ejecución y que el mensaje termina con `\n`. |

### Uso de inteligencia artificial en este avance

Se utilizó ChatGPT Codex para preparar el código inicial y ya con eso yo hacer la práctica y explicar
el intercambio TCP, el formato JSON y la delimitación de mensajes.


## Ejecución del análisis
TODO: comando del script de `analysis/` y archivos que genera.

## Verificación de la integridad de los datos

Antes de medir, registra la ficha en la máquina oficial. Usa el mismo usuario
que figura en el identificador de la sesión y el modo de ejecución acordado.

```bash
python analysis/registrar_maquina.py carlos procesos
```

Al terminar las corridas oficiales, genera el manifiesto desde la raíz del repositorio:

```bash
python analysis/generar_sha256.py
python analysis/generar_sha256.py --verificar
```

El manifiesto incluye los CSV de `data/` y se crea una sola vez. Si ya existe,
el generador avisa y conserva las huellas guardadas. La opción `--verificar`
avisa si cambió un CSV, si falta un archivo o si apareció un CSV sin huella.
Las huellas también se pueden comprobar con `sha256sum -c data/SHA256SUMS`.

## Compilación del documento
- Compilador: pdflatex + biber
- Archivo principal: `docs/guia1_practica.tex`
- Orden de comandos (desde `docs/`):
  1. `pdflatex guia1_practica.tex`
  2. `biber guia1_practica`
  3. `pdflatex guia1_practica.tex`
  4. `pdflatex guia1_practica.tex`
- Dependencias LaTeX: TODO (listar paquetes finales, p. ej. amsmath, booktabs, listings, graphicx, tikz, biblatex, hyperref)
