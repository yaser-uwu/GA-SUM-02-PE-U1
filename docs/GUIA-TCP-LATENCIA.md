# Ejecución de las mediciones TCP

Desde la raíz del repositorio, con Python 3.11 o superior y los puertos 5000, 5001 y 5002 disponibles:

```powershell
python src/sockets/coordinador_latencia.py
```

El programa inicia los tres nodos, realiza el calentamiento y las cinco corridas secuenciales por tamaño, y ejecuta una corrida concurrente por tamaño. Genera una sesión nueva dentro de `data/` y cierra sus nodos al terminar.

Para ejecutar una corrida concreta:

```powershell
python src/sockets/coordinador_latencia.py --modo secuencial --tamano corto --corrida 1
python src/sockets/coordinador_latencia.py --modo concurrente --tamano largo --corrida 1
```

Para compartir el identificador de una sesión con el equipo:

```powershell
python src/sockets/coordinador_latencia.py --sesion AAAAMMDD-HHMMSS-kevin
```

Sustituir `AAAAMMDD-HHMMSS` por la fecha y hora de la sesión. Si se repite una corrida de esa sesión, aumentar `--intento`, por ejemplo `--intento 2`. El programa conserva los archivos de los intentos anteriores.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

## CSV

Cada carpeta `data/<sesion>/sockets/latencia/<modo>/<tamano>/corrida-XX/intento-XX/` contiene:

- `latencia.csv`: una fila por acuse exitoso.
- `duracion.csv`: duración total, cantidad de acuses y estado de la corrida.

El formato y la asignación de muestras están definidos en `docs/CONTRATO.md`. El calentamiento se conserva como corrida 0 y se excluye de las estadísticas. Los intentos fallidos se conservan con ese estado.
