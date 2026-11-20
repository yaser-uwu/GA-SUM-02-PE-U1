import json
import socket

HOST = "127.0.0.1"
PORT = 5000


def atender_cliente(conexion):
    # El salto de línea delimita el mensaje dentro del flujo TCP.
    with conexion.makefile("rb") as entrada:
        linea = entrada.readline()
        if not linea:
            return

        try:
            mensaje = json.loads(linea.decode("utf-8"))
            campos = ("sender", "timestamp", "message")
            if not isinstance(mensaje, dict) or not all(
                campo in mensaje for campo in campos
            ):
                raise ValueError("Faltan campos obligatorios")

            print(f"Emisor: {mensaje['sender']}")
            print(f"Reloj de Lamport recibido: {mensaje['timestamp']}")
            print(f"Mensaje: {mensaje['message']}", flush=True)
            respuesta = {"ok": True}
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            print(f"Mensaje rechazado: {error}", flush=True)
            respuesta = {"ok": False, "error": "Mensaje JSON inválido"}

        conexion.sendall(json.dumps(respuesta).encode("utf-8") + b"\n")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PORT))
        servidor.listen()
        print(f"Servidor TCP escuchando en {HOST}:{PORT}", flush=True)

        try:
            while True:
                conexion, direccion = servidor.accept()
                conexion.settimeout(10)
                print(f"\nCliente conectado: {direccion}", flush=True)
                with conexion:
                    try:
                        atender_cliente(conexion)
                    except OSError as error:
                        print(f"Error de conexión: {error}", flush=True)
        except KeyboardInterrupt:
            print("\nServidor detenido.")


if __name__ == "__main__":
    main()
