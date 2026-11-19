import grpc
from concurrent import futures

import mensajes_pb2
import mensajes_pb2_grpc

HOST = "127.0.0.1"
PORT = 5000


class ServicioMensajeria(mensajes_pb2_grpc.MensajeriaServicer):
    def EnviarMensaje(self, solicitud, contexto):
        print(f"Emisor: {solicitud.sender}")
        print(f"Reloj de Lamport recibido: {solicitud.timestamp}")
        print(f"Mensaje: {solicitud.message}", flush=True)
        return mensajes_pb2.Acuse(ok=True, error="")


def main():
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mensajes_pb2_grpc.add_MensajeriaServicer_to_server(ServicioMensajeria(), servidor)

    puerto = servidor.add_insecure_port(f"{HOST}:{PORT}")
    if puerto == 0:
        raise RuntimeError(f"No se pudo abrir {HOST}:{PORT}")

    servidor.start()
    print(f"Servidor gRPC escuchando en {HOST}:{PORT}", flush=True)
    try:
        servidor.wait_for_termination()
    except KeyboardInterrupt:
        servidor.stop(grace=0)
        print("\nServidor detenido.")


if __name__ == "__main__":
    main()
