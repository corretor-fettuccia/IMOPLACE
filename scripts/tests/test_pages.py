"""Evita regressões na origem do Pages e na raiz do artefato público."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verificar_publicacao as pages

class TestGitHubPages(unittest.TestCase):
    def test_workflow_publica_conteudo_de_site_na_raiz(self):
        self.assertEqual(pages.verificar_estrutura(), [])
        txt = pages.WORKFLOW.read_text('utf-8')
        self.assertIn('path: ./estado/publicacao', txt)
        self.assertNotIn('path: ./site\n', txt)  # publica cópia validada, não diretório intermediário

    def test_artefato_tem_index_na_raiz_e_marcador_valido(self):
        with tempfile.TemporaryDirectory() as d:
            art = Path(d)
            (art / 'index.html').write_text('<h1>ImoPlace</h1>')
            (art / 'catalogo.json').write_text('{"imoveis": []}')
            sha = hashlib.sha256((art / 'catalogo.json').read_bytes()).hexdigest()
            (art / 'publicacao.json').write_text(json.dumps({'jobId':'gh-teste','catalogoSha256':sha}))
            with patch.object(pages, 'ARTEFATO', art):
                self.assertEqual(pages.verificar_artefato(), [])
                (art / 'site').mkdir()
                self.assertTrue(any('pasta site/' in e for e in pages.verificar_artefato()))

if __name__ == '__main__':
    unittest.main()
