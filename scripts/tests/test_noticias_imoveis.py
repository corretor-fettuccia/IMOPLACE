"""Imóveis relacionados nas notícias: escolha, HTML do carrossel/card e páginas publicadas."""
import json, re, shutil, subprocess, unittest
from pathlib import Path

import noticias

RAIZ = Path(__file__).resolve().parents[2]
FOTO = {'arquivo': 'imoveis/x/imagens/f.webp', 'alt': 'foto'}


def imovel(cod, cidade='Canoas', **kw):
    base = dict(codigo=cod, titulo='Imóvel ' + cod, status='publicado', tipo='Apartamento', preco=300000.0,
                localizacao={'bairro': 'Centro', 'cidade': cidade}, imagens=[FOTO], destaque=False, ordem=1,
                condicao='Usado', financiamento=False, tag='', descricao='', categoria='venda')
    base.update(kw)
    return base


def artigo(titulo, tags=()):
    return {'titulo': titulo, 'tags': list(tags)}


class Escolha(unittest.TestCase):
    def test_cidade_tem_prioridade_e_destaque_primeiro(self):
        ims = [imovel('a-1', 'Nova Santa Rita'), imovel('b-2', 'Nova Santa Rita', destaque=True), imovel('c-3')]
        titulo, lista, cidade = noticias.relacionados(artigo('La Salle em Nova Santa Rita'), ims)
        self.assertEqual(titulo, 'Imóveis em Nova Santa Rita')
        self.assertEqual([i['codigo'] for i in lista], ['b-2', 'a-1'])
        self.assertEqual(cidade, 'Nova Santa Rita')

    def test_cidade_sem_acento_e_caixa(self):
        ims = [imovel('a-1', 'Nova santa rita')]
        titulo, lista, _ = noticias.relacionados(artigo('x', ['NOVA SANTA RITA']), ims)
        self.assertEqual(titulo, 'Imóveis em Nova Santa Rita')
        self.assertEqual(len(lista), 1)

    def test_assuntos(self):
        ims = [imovel('p-1', condicao='Na planta'), imovel('t-2', tipo='Terreno'), imovel('u-3'),
               imovel('d-4', descricao='Aceita parcelamento direto'), imovel('f-5', tag='NA PLANTA 100% FINANCIADO')]
        casos = {'Comprar imóvel na planta é bom negócio?': ('Imóveis na planta', 'p-1'),
                 'Aquisição de terreno e construção': ('Terrenos e loteamentos', 't-2'),
                 'Parcelamento direto sem banco': ('Imóveis com parcelamento direto', 'd-4'),
                 'Imóvel 100% financiado': ('Imóveis 100% financiados', 'f-5')}
        for t, (titulo, primeiro) in casos.items():
            got = noticias.relacionados(artigo(t), ims)
            self.assertEqual((got[0], got[1][0]['codigo']), (titulo, primeiro), t)

    def test_sem_relacao_mostra_destaques(self):
        ims = [imovel('a-1'), imovel('b-2', destaque=True)]
        titulo, lista, _ = noticias.relacionados(artigo('Reforma tributária'), ims)
        self.assertEqual(titulo, 'Imóveis em destaque')
        self.assertEqual(lista[0]['codigo'], 'b-2')

    def test_maximo_seis_e_so_publicados_com_foto(self):
        ims = [imovel(f'i-{n}') for n in range(10)] + [imovel('x-1', status='rascunho'), imovel('y-2', imagens=[])]
        _, lista, _ = noticias.relacionados(artigo('qualquer'), ims)
        self.assertEqual(len(lista), 6)
        self.assertNotIn('x-1', [i['codigo'] for i in lista])
        self.assertNotIn('y-2', [i['codigo'] for i in lista])


class Html(unittest.TestCase):
    def test_bloco_completo(self):
        ims = [imovel('casa-10', 'Nova Santa Rita', dormitorios=3.0, suites=1.0, vagas=0.0, areaUtil=None, areaTotal=120.0, tag='Exclusividade')]
        h = noticias.bloco_imoveis(artigo('Nova Santa Rita'), ims)
        self.assertIn('class="rel-imoveis"', h)
        self.assertIn('href="../../imoveis/casa-10/"', h)
        self.assertIn('<span class="rel-tag">Exclusividade</span>', h)
        self.assertIn('3 dorm. · 1 suíte · 120 m²', h)
        self.assertNotIn('0 vaga', h)               # card resume só o que existe
        self.assertIn('R$ 300.000', h)
        self.assertRegex(h, r'<aside class="rel-mini"[^>]*hidden>')   # card que desliza começa oculto
        self.assertIn('Ver todos os imóveis em Nova Santa Rita', h)
        self.assertIn('assets/js/noticias-imoveis.js', h)

    def test_sem_imovel_sem_bloco(self):
        self.assertEqual(noticias.bloco_imoveis(artigo('x'), []), '')

    def test_texto_escapado(self):
        h = noticias.bloco_imoveis(artigo('x'), [imovel('a-1', titulo='<b>x</b>', tag='"><script>')])
        self.assertNotIn('<script>', h.replace('<script src="../../assets/js/noticias-imoveis.js" defer></script>', ''))
        self.assertNotIn('<b>x</b>', h)


class Publicado(unittest.TestCase):
    def test_noticias_publicadas_tem_carrossel(self):
        cat = RAIZ / 'site/noticias/catalogo.json'
        imv = RAIZ / 'site/catalogo.json'
        artigos = (json.loads(cat.read_text(encoding='utf-8')) if cat.exists() else {}).get('artigos') or []
        imoveis = (json.loads(imv.read_text(encoding='utf-8')) if imv.exists() else {}).get('imoveis') or []
        if not artigos or not imoveis:
            self.skipTest('pacote sem notícias ou imóveis publicados')
        for a in artigos:
            t = (RAIZ / 'site/noticias' / a['codigo'] / 'index.html').read_text(encoding='utf-8')
            self.assertIn('class="rel-imoveis"', t, a['codigo'])
            self.assertLess(t.index('class="article-body"'), t.index('class="rel-imoveis"'))
            self.assertLess(t.index('class="rel-imoveis"'), t.index('class="news-follow"'))

    def test_css_e_js(self):
        css = (RAIZ / 'site/assets/css/noticias.css').read_text(encoding='utf-8')
        for sel in ('.rel-faixa', '.rel-card', '.rel-mini', '.rel-mini.visivel'):
            self.assertIn(sel, css)
        js = RAIZ / 'site/assets/js/noticias-imoveis.js'
        self.assertTrue(js.exists())
        node = shutil.which('node')
        if node:
            r = subprocess.run([node, '--check', str(js)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
        txt = js.read_text(encoding='utf-8')
        self.assertIn('sessionStorage', txt)
        self.assertIn('IntersectionObserver', txt)


if __name__ == '__main__':
    unittest.main()
