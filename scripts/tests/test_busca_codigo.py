"""Página principal: busca pelo código do imóvel."""
import json, re, shutil, subprocess, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
HOME_JS = (RAIZ / 'site/assets/js/home.js').read_text(encoding='utf-8')


def achar(entrada, itens):
    """Roda codigoBusca/codigoDe do home.js no node e devolve os códigos que casam."""
    defs = '\n'.join(l for l in HOME_JS.splitlines() if l.startswith(('const codigoBusca', 'const codigoDe')))
    script = (f'const $=s=>s==="#cod"?{{value:{json.dumps(entrada)}}}:null;\n{defs}\n'
              f'const cod=codigoBusca();process.stdout.write(JSON.stringify({json.dumps(itens)}.filter(i=>codigoDe(i).startsWith(cod)).map(i=>i.codigo)));')
    r = subprocess.run(['node', '-e', script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@unittest.skipUnless(shutil.which('node'), 'node ausente')
class BuscaCodigo(unittest.TestCase):
    ITENS = [{'id': '1011', 'codigo': 'sobrado-nsr-1011'}, {'id': '1012', 'codigo': 'casa-1012'},
             {'id': '', 'codigo': 'terreno-2030'}, {'id': '1101', 'codigo': 'apto-1101'}]

    def test_codigo_exato_e_formatos(self):
        for entrada in ('1011', ' 1011 ', '#1011', 'Cód. 1011'):
            self.assertEqual(achar(entrada, self.ITENS), ['sobrado-nsr-1011'], entrada)

    def test_enquanto_digita_e_sem_id(self):
        self.assertEqual(achar('101', self.ITENS), ['sobrado-nsr-1011', 'casa-1012'])
        self.assertEqual(achar('2030', self.ITENS), ['terreno-2030'])   # sem id: usa o número final do código
        self.assertEqual(achar('9999', self.ITENS), [])

    def test_codigo_ignora_outros_filtros(self):
        corpo = HOME_JS[HOME_JS.index('function matches(item) {'):]
        self.assertTrue(corpo.split('\n')[1].strip().startswith('const cod=codigoBusca();'))
        self.assertIn('if (cod) return codigoDe(item).startsWith(cod);', corpo.split('\n')[2])

    def test_campo_na_pagina_e_ligacoes(self):
        html = (RAIZ / 'site/index.html').read_text(encoding='utf-8')
        self.assertIn('<label for="cod">Código do imóvel</label><input id="cod" inputmode="numeric"', html)
        self.assertLess(html.index('id="q"'), html.index('id="cod"'))
        self.assertLess(html.index('id="cod"'), html.index('id="t"'))
        self.assertIn("$('#cod').addEventListener('input',apply);", HOME_JS)
        self.assertIn("params.get('codigo')", HOME_JS)
        self.assertIn('Nenhum imóvel com o código', HOME_JS)
        css = (RAIZ / 'site/assets/css/style.css').read_text(encoding='utf-8')
        self.assertIn('.fields{display:grid;grid-template-columns:2.2fr .8fr 1fr 1fr 1fr auto auto;', css)


if __name__ == '__main__':
    unittest.main()
