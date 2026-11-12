import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import homologar_acesso as h  # noqa: E402

ESTADO = {'painel_vaza': False, 'ponte_sem_url': False}


class Falso(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def responder(self, corpo, tipo='application/json'):
        dados = corpo.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', tipo)
        self.send_header('Content-Length', str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        if self.path.startswith('/escritor'):
            html = '<title>ImoPlace — Painel</title><script>google.script.run</script>' if ESTADO['painel_vaza'] else 'Exception: Acesso negado.'
            self.responder(html, 'text/html')
        else:
            self.responder(json.dumps({'ok': False, 'erro': 'Use POST assinado.'}))

    def do_POST(self):
        self.rfile.read(int(self.headers.get('Content-Length') or 0))
        if self.path.startswith('/ponte') and ESTADO['ponte_sem_url']:
            self.responder(json.dumps({'ok': False, 'erro': 'CENTRAL_WRITER_URL ausente ou inválida'}))
        else:
            self.responder(json.dumps({'ok': False, 'erro': 'Requisição malformada.'}))


class TestHomologar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(('127.0.0.1', 0), Falso)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{cls.srv.server_port}'
        cls.escritor, cls.ponte = base + '/escritor', base + '/ponte'

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        ESTADO.update(painel_vaza=False, ponte_sem_url=False)

    def test_aprova_implantacao_protegida(self):
        self.assertEqual(h.homologar(self.escritor, self.ponte), [])

    def test_reprova_painel_servido_a_anonimo(self):
        ESTADO['painel_vaza'] = True
        self.assertTrue(any('CRÍTICO' in p for p in h.homologar(self.escritor, '')))

    def test_reprova_ponte_sem_url(self):
        ESTADO['ponte_sem_url'] = True
        self.assertTrue(any('configurar_integracao' in p for p in h.homologar('', self.ponte)))


if __name__ == '__main__':
    unittest.main()
