"""Constantes compartidas por sockets y gRPC (acordadas en docs/CONTRATO.md)."""

HOST = "127.0.0.1"

# Nodo -> puerto (los tres procesos corren en localhost)
NODOS = {
    "nodo-A": 5000,
    "nodo-B": 5001,
    "nodo-C": 5002,
}

# Secuencia de 20 intercambios acordada en docs/CONTRATO.md:
# A->B, B->C, C->A, A->C, C->B, B->A (tres veces) y A->B, B->C.
_CICLO_LAMPORT = [
    ("nodo-A", "nodo-B"),
    ("nodo-B", "nodo-C"),
    ("nodo-C", "nodo-A"),
    ("nodo-A", "nodo-C"),
    ("nodo-C", "nodo-B"),
    ("nodo-B", "nodo-A"),
]
RUTAS_LAMPORT = _CICLO_LAMPORT * 3 + [
    ("nodo-A", "nodo-B"),
    ("nodo-B", "nodo-C"),
]

N_INTERCAMBIOS = 20          # intercambios con reloj de Lamport
N_ENVIOS_LATENCIA = 100      # envíos por corrida
N_CORRIDAS = 5               # corridas medidas por mecanismo y tamaño (sin contar calentamiento)
TAMANOS_MENSAJE = {          # longitud (caracteres ASCII) del campo "message"
    "corto": 100,
    "largo": 10240,
}
