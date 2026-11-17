"""Constantes compartidas por sockets y gRPC (acordadas en docs/CONTRATO.md)."""

HOST = "127.0.0.1"

# Nodo -> puerto (los tres procesos corren en localhost)
NODOS = {
    "nodo-A": 5000,
    "nodo-B": 5001,
    "nodo-C": 5002,
}

N_INTERCAMBIOS = 20          # intercambios con reloj de Lamport
N_ENVIOS_LATENCIA = 100      # envíos por corrida
N_CORRIDAS = 5               # corridas medidas por mecanismo y tamaño (sin contar calentamiento)
TAMANOS_MENSAJE = {          # longitud (caracteres ASCII) del campo "message"
    "corto": 100,
    "largo": 10240,
}
