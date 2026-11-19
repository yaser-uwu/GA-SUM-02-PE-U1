import grpc

import mensajes_pb2
import mensajes_pb2_grpc

HOST = "127.0.0.1"
PORT = 5000
TIMEOUT_S = 10


def main():
    mensaje = mensajes_pb2.Mensaje(
        sender="nodo-A",
        timestamp=1,
        message="Hola desde nodo-A",
    )

    try:
        with grpc.insecure_channel(f"{HOST}:{PORT}") as canal:
            stub = mensajes_pb2_grpc.MensajeriaStub(canal)
            print(
                f"Mensaje enviado: sender={mensaje.sender}, "
                f"timestamp={mensaje.timestamp}, message={mensaje.message}",
                flush=True,
            )
            acuse = stub.EnviarMensaje(mensaje, timeout=TIMEOUT_S)
    except grpc.RpcError as error:
        print(f"No se completó la llamada: {error.code().name}: {error.details()}")
        raise SystemExit(1)

    print(f"Acuse recibido: ok={acuse.ok}, error='{acuse.error}'")


if __name__ == "__main__":
    main()
