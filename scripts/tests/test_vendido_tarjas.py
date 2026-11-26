"""4.4.0: disponibilidade (vendido/indisponível), tarjas, preço anterior, feeds e cachorrinho."""
import json, subprocess, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paginas, gerador, core_google  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]


def item(**k):
    base = {'id': '1001', 'codigo': 'casa-1001', 'titulo': 'Casa', 'tipo': 'Casa', 'categoria': 'venda', 'preco': 500000,
            'imagens': [{'arquivo': 'imoveis/casa-1001/imagens/a.webp', 'legenda': 'Frente', 'alt': 'Frente'}],
            'localizacao': {'cidade': 'Canoas', 'uf': 'RS'}, 'anunciante': {'nome': 'Roberto', 'whatsapp': '5551999999999'}}
    base.update(k)
    return base


def selo_js(it):
    m = (RAIZ / 'site/assets/js/main.js').read_text(encoding='utf-8')
    bloco = m[m.index('const TARJAS='):m.index('function cardHTML')]
    script = ('const esc=v=>String(v??"");const brl=n=>"R$ "+Math.round(n).toLocaleString("pt-BR");' + bloco +
              f'\nconst it={json.dumps(it, ensure_ascii=False)};process.stdout.write(JSON.stringify([selo(it),precoHTML(it),estadoClasse(it)]));')
    r = subprocess.run(['node', '-e', script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


class VendidoTarjas(unittest.TestCase):
    def test_prioridade_das_tarjas(self):
        self.assertEqual(paginas.selo(item(tarja='black_friday')), ('black_friday', 'BLACK FRIDAY'))
        self.assertEqual(paginas.selo(item(tarja='black_friday', disponibilidade='sold')), ('vendido', 'VENDIDO'))
        self.assertEqual(paginas.selo(item(tarja='oportunidade', disponibilidade='out_of_stock')), ('indisponivel', 'INDISPONÍVEL'))
        self.assertEqual(paginas.selo(item(tarja='personalizada', tarjaTexto='Últimas unidades disponíveis já')), ('personalizada', 'ÚLTIMAS UNIDADES DIS'))
        self.assertIsNone(paginas.selo(item(tarja='personalizada')))
        self.assertIsNone(paginas.selo(item(tarja='xx')))
        self.assertEqual(paginas.selo(item(feeds={'disponibilidade': 'sold'})), ('vendido', 'VENDIDO'))

    def test_navegador_igual_ao_python(self):
        casos = [item(), item(tarja='baixou_preco', precoAnterior=520000), item(disponibilidade='sold', precoAnterior=520000),
                 item(disponibilidade='out_of_stock'), item(tarja='personalizada', tarjaTexto='feirão'), item(tarja='lancamento')]
        for it in casos:
            s, preco, cls = selo_js(it)
            self.assertEqual(tuple(s) if s else None, paginas.selo(it))
            self.assertEqual(preco, paginas.preco_html(it))
            self.assertEqual(cls, paginas.estado_classe(it))

    def test_preco(self):
        self.assertEqual(paginas.preco_html(item(disponibilidade='sold')), '<b class="price price-vendido">Vendido</b>')
        self.assertIn('<s class="price-old">R$ 520.000</s>', paginas.preco_html(item(precoAnterior=520000)))
        self.assertNotIn('price-old', paginas.preco_html(item(precoAnterior=480000)))

    def test_pagina_do_vendido(self):
        conf = {'urlPublica': 'https://imoplace.com.br', 'nome': 'Imoplace', 'permitirIndexacao': True}
        h = paginas.pagina(item(disponibilidade='sold', tarja='black_friday'), conf)
        self.assertIn('class="wrap estado-vendido" id="det"', h)
        self.assertIn('<span class="tarja tarja--vendido">VENDIDO</span>', h)
        self.assertNotIn('tarja--black_friday', h)
        self.assertIn('https://schema.org/SoldOut', h)
        self.assertIn('Este imóvel já foi vendido', h)
        h2 = paginas.pagina(item(tarja='black_friday'), conf)
        self.assertIn('class="wrap " id="det"', h2)
        self.assertIn('tarja--black_friday', h2)
        self.assertIn('https://schema.org/InStock', h2)

    def test_feeds_vendido_sai_indisponivel(self):
        conf = {'urlPublica': 'https://imoplace.com.br', 'nome': 'Imoplace'}
        e = {'id': '1', 'titulo': 'Casa', 'codigo': 'casa-1', 'preco': 1.0, 'imagens': [{'arquivo': 'a.webp'}], 'feeds': {'disponibilidade': 'sold'}}
        self.assertIn('<g:availability>out_of_stock</g:availability>', gerador._item_feed(e, conf, False))
        self.assertIn('<g:availability>out of stock</g:availability>', gerador._item_feed(e, conf, True))

    def test_core_google_leva_campos_novos(self):
        im = {'ID': '1001', 'TITULO': 'Casa', 'SLUG': 'casa', 'DISPONIBILIDADE': 'sold', 'VENDIDO_EM': '2026-11-26T12:00:00Z',
              'TARJA': 'black_friday', 'TARJA_TEXTO': 'x', 'PRECO_ANTERIOR': '520000'}
        p = core_google._publico(im, [], 'https://imoplace.com.br')
        self.assertEqual((p['disponibilidade'], p['vendidoEm'], p['tarja'], p['precoAnterior']), ('sold', '2026-11-26T12:00:00Z', 'black_friday', 520000))
        self.assertEqual(p['feeds']['disponibilidade'], 'sold')
        p2 = core_google._publico(dict(im, DISPONIBILIDADE='lixo', TARJA='hack'), [], '')
        self.assertEqual((p2['disponibilidade'], p2['vendidoEm'], p2['tarja']), ('in_stock', '', ''))
        e = gerador._entrada(p, [])
        self.assertEqual((e['disponibilidade'], e['tarja'], e['precoAnterior']), ('sold', 'black_friday', 520000))

    def test_lista_poe_vendido_no_fim_e_card(self):
        home = (RAIZ / 'site/assets/js/home.js').read_text(encoding='utf-8')
        self.assertIn('const pos={in_stock:0,out_of_stock:1,sold:2};', home)
        main = (RAIZ / 'site/assets/js/main.js').read_text(encoding='utf-8')
        self.assertIn('<article class="card ${estadoClasse(item)}"', main)
        self.assertIn('${tarjaHTML(item)}', main)
        css = (RAIZ / 'site/assets/css/style.css').read_text(encoding='utf-8')
        for regra in ('.tarja.tarja--black_friday,.tarja.tarja--personalizada{background:#111}', '.tarja.tarja--vendido{background:#c62828}',
                      '#det.estado-vendido .gal img', 'filter:grayscale(1)'):
            self.assertIn(regra, css)

    def test_cachorrinho_frase_e_ritmo(self):
        js = (RAIZ / 'site/assets/js/avatar.js').read_text(encoding='utf-8')
        self.assertIn('não uivo não', js)
        self.assertIn('var CICLO = 16000;', js)
        self.assertIn("window.addEventListener('scroll', reagir, { passive: true });", js)
        self.assertIn('zap-chamando', js)


if __name__ == '__main__':
    unittest.main()
