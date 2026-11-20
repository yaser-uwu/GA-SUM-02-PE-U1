import json
import socket

HOST = "127.0.0.1"
PORT = 5000


def main():
    mensaje = {
        "sender": "nodo-A",
        "timestamp": 1,
        "message": "Hola desde nodo-A",
    }

    try:
        with socket.create_connection((HOST, PORT), timeout=10) as cliente:
            cliente.sendall(json.dumps(mensaje).encode("utf-8") + b"\n")
            print(f"Mensaje enviado: {mensaje}")

            with cliente.makefile("rb") as entrada:
                linea = entrada.readline()
            if not linea:
                raise ConnectionError("El servidor cerró sin enviar un acuse")

            respuesta = json.loads(linea.decode("utf-8"))
            if not isinstance(respuesta, dict) or respuesta.get("ok") is not True:
                raise ValueError(f"El servidor rechazó el mensaje: {respuesta}")
            print(f"Acuse recibido: {respuesta}")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        print(f"No se completó el intercambio: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
