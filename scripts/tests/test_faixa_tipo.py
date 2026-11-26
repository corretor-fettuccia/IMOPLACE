"""Faixa abaixo dos dados (tipo com ícone, código, localização e valor) e botão Salvar com coração."""
import json, re, subprocess, unittest
from pathlib import Path

import paginas
from paginas import detalhe, _faixa, tipo_icone, TIPO_ICONES

RAIZ = Path(__file__).resolve().parents[2]
BASE = {'id': '1011', 'codigo': 'sobrado-1011', 'titulo': 'Reservas Do Lago Sobrado 1011', 'tipo': 'Sobrado',
        'preco': 2790000, 'categoria': 'venda', 'imagens': [], 'descricao': 'x',
        'localizacao': {'bairro': 'Reservas do lago', 'cidade': 'Nova Santa Rita', 'uf': 'RS'}}


def item(**kw):
    d = json.loads(json.dumps(BASE)); d.update(kw); return d


def helpers_main():
    """Disponibilidade, tarja e preço moram no main.js (usados pela lista e pela página do imóvel)."""
    m = (RAIZ / 'site/assets/js/main.js').read_text(encoding='utf-8')
    return m[m.index('const TARJAS='):m.index('function cardHTML')]


def faixa_js(it):
    js = (RAIZ / 'site/assets/js/imovel.js').read_text(encoding='utf-8')
    ini = js.index('const ICONES='); fim = js.index('function faixaHTML')
    fim = js.index('\n}\n', fim) + 3
    script = ('const esc=v=>String(v??"").replace(/[&<>"\']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;","\'":"&#39;"}[c]));'
              'const brl=n=>n==null?"Sob consulta":"R$ "+Math.round(n).toLocaleString("pt-BR");'
              + helpers_main() + js[ini:fim] + '\nprocess.stdout.write(faixaHTML(' + json.dumps(it, ensure_ascii=False) + '));')
    r = subprocess.run(['node', '-e', script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


class Faixa(unittest.TestCase):
    def test_conteudo_e_ordem(self):
        f = _faixa(item())
        a = [f.index(m) for m in ('<b>Sobrado</b><span>Tipo</span>', '<b>1011</b><span>Código</span>',
                                  '<b>Reservas do lago</b><span>Nova Santa Rita, RS</span>', 'class="price">R$ 2.790.000</b><span>Venda</span>')]
        self.assertEqual(a, sorted(a))
        self.assertIn(TIPO_ICONES['sobrado'], f)

    def test_icone_de_cada_tipo_e_reserva(self):
        for tipo, chave in [('Casa', 'casa'), ('Apartamento', 'apartamento'), ('Terreno', 'terreno'), ('Sobrado', 'sobrado'),
                            ('Cobertura', 'cobertura'), ('Studio', 'studio'), ('Comercial', 'comercial'), ('Stúdio', 'studio')]:
            self.assertEqual(tipo_icone(tipo), TIPO_ICONES[chave], tipo)
        self.assertEqual(len(set(TIPO_ICONES.values())), 7)                  # sete desenhos diferentes
        self.assertEqual(tipo_icone('Chácara'), TIPO_ICONES['casa'])          # tipo novo não quebra
        self.assertIn('<b>Chácara</b>', _faixa(item(tipo='Chácara')))

    def test_campo_vazio_some(self):
        f = _faixa(item(tipo='', localizacao={}, categoria=''))
        self.assertNotIn('Tipo</span>', f); self.assertNotIn('fi-local', f); self.assertNotIn('Venda', f)
        self.assertIn('Código</span>', f); self.assertIn('class="price"', f)
        f = _faixa(item(localizacao={'cidade': 'Canoas', 'uf': 'RS'}))
        self.assertIn('<b>Canoas</b><span>RS</span>', f)

    def test_pagina(self):
        html = detalhe(item())
        a = [html.index(m) for m in ('class="stats"', 'class="faixa-info"', 'class="dhead"', 'imovel-layout')] if 'class="stats"' in html else \
            [html.index(m) for m in ('class="faixa-info"', 'class="dhead"', 'imovel-layout')]
        self.assertEqual(a, sorted(a))
        cab = html[html.index('class="dhead"'):html.index('imovel-layout')]
        self.assertIn('Reservas Do Lago Sobrado 1011', cab)             # título como cadastrado
        self.assertNotIn('class="where"', cab); self.assertNotIn('price big', cab)
        self.assertIn('Código do imóvel: 1011', html)                    # continua no contato

    def test_navegador_monta_a_mesma_faixa(self):
        for it in (item(), item(tipo='', categoria='lancamento'), item(localizacao={'cidade': 'Canoas'}, preco=None),
                   item(tipo='<b>x</b>')):
            self.assertEqual(faixa_js(it), _faixa(it), it.get('tipo'))

    def test_salvar_com_coracao_e_css(self):
        js = (RAIZ / 'site/assets/js/imovel.js').read_text(encoding='utf-8')
        self.assertIn('id="save" aria-pressed="false">${icone(CORACAO', js)
        self.assertIn('function marcarSalvo', js); self.assertNotIn('Salvo ✓', js)
        self.assertIn('${faixaHTML(item)}', js)
        css = (RAIZ / 'site/assets/css/style.css').read_text(encoding='utf-8')
        for sel in ('.faixa-info{', '.faixa-info .fi+.fi', '#save[aria-pressed="true"] svg'):
            self.assertIn(sel, css)

    def test_fonte_leve_so_no_celular(self):
        css = (RAIZ / 'site/assets/css/style.css').read_text(encoding='utf-8')
        bloco = css[css.index('Celular: fonte mais leve'):]
        self.assertTrue(bloco.split('\n', 1)[1].startswith('@media(max-width:820px){'))
        self.assertIn('.stats b,.faixa-info .fi b{font-family:var(--b);font-weight:600', bloco)
        self.assertIn('.dhead .dt{font-weight:700}', bloco)

    def test_publicados_tem_faixa(self):
        pags = [p for p in (RAIZ / 'site/imoveis').glob('*/index.html')] if (RAIZ / 'site/imoveis').exists() else []
        pags = [p for p in pags if 'imovel-layout' in p.read_text(encoding='utf-8')]
        if not pags:
            self.skipTest('pacote sem imóveis publicados')
        for p in pags:
            self.assertTrue('class="faixa-info"' in p.read_text(encoding='utf-8'), p.parent.name)


if __name__ == '__main__':
    unittest.main()
