import argparse
import csv
import json
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'sockets'))
import coordinador_latencia as tcp


class PruebaTCP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = argparse.Namespace(host='127.0.0.1', puerto_base=5000)
        cls.procesos = tcp.iniciar_nodos(cls.args.host, cls.args.puerto_base)

    @classmethod
    def tearDownClass(cls):
        tcp.detener_nodos(cls.procesos)

    def test_acuse_con_ambos_tamanos(self):
        for tamano in (100, 10240):
            with self.subTest(tamano=tamano):
                rtt = tcp.medir_solicitud('127.0.0.1', 5001, 'nodo-A', 1, 'x' * tamano)
                self.assertGreater(rtt, 0)

    def test_json_invalido_recibe_rechazo(self):
        with socket.create_connection(('127.0.0.1', 5001), timeout=5) as conexion:
            conexion.sendall(b'{"sender":"nodo-A","timestamp":true,"message":"x"}\n')
            with conexion.makefile('rb') as entrada:
                acuse = tcp.leer_json(entrada)
            self.assertIs(acuse['ok'], False)

    def test_mensaje_fragmentado_se_reconstruye_hasta_salto(self):
        datos = json.dumps({'sender': 'nodo-A', 'timestamp': 2, 'message': 'x' * 10240}).encode() + b'\n'
        with socket.create_connection(('127.0.0.1', 5001), timeout=5) as conexion:
            for inicio in range(0, len(datos), 73):
                conexion.sendall(datos[inicio:inicio+73])
            with conexion.makefile('rb') as entrada:
                self.assertIs(tcp.leer_json(entrada)['ok'], True)

    def test_csv_secuencial_y_concurrente_completos(self):
        for modo, tamano in [('secuencial', 'corto'), ('concurrente', 'largo')]:
            with self.subTest(modo=modo), tempfile.TemporaryDirectory() as temporal:
                carpeta = Path(temporal) / 'intento-01'
                self.assertTrue(tcp.medir_corrida(self.args, tamano, modo, 1, carpeta))
                with (carpeta / 'latencia.csv').open(newline='', encoding='utf-8') as archivo:
                    filas = list(csv.DictReader(archivo))
                self.assertEqual([int(f['envio_n']) for f in filas], list(range(1, 101)))
                self.assertTrue(all(float(f['rtt_s']) > 0 for f in filas))
                with (carpeta / 'duracion.csv').open(newline='', encoding='utf-8') as archivo:
                    resumen = list(csv.DictReader(archivo))
                self.assertEqual(len(resumen), 1)
                self.assertEqual(resumen[0]['estado'], 'completa')
                self.assertEqual(resumen[0]['envios_ok'], '100')
                with self.assertRaises(FileExistsError):
                    tcp.medir_corrida(self.args, tamano, modo, 1, carpeta)

    def test_acuse_negativo_no_se_cuenta_como_exito(self):
        with socket.socket() as servidor:
            servidor.bind(('127.0.0.1', 0))
            servidor.listen()
            def rechazar():
                conexion, _ = servidor.accept()
                with conexion, conexion.makefile('rb') as entrada:
                    entrada.readline()
                    conexion.sendall(b'{"ok":false,"error":"rechazo de prueba"}\n')
            hilo = threading.Thread(target=rechazar)
            hilo.start()
            try:
                with self.assertRaisesRegex(ValueError, 'Acuse rechazado'):
                    tcp.medir_solicitud('127.0.0.1', servidor.getsockname()[1], 'nodo-A', 1, 'x')
            finally:
                hilo.join(timeout=6)


if __name__ == '__main__':
    unittest.main(verbosity=2)
