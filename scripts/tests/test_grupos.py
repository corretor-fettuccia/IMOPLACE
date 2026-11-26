"""4.5.0: grupos de imóveis (sem limite por imóvel) — leitura no motor, catálogo, tabela "Unidades" (Python = JS) e estilo."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'scripts'))
import core_google  # noqa: E402
import gerador  # noqa: E402
import paginas  # noqa: E402

G = {'id': 'G1', 'nome': 'Reserva das Palmeiras', 'tipo': 'Condomínio fechado', 'titulo': ''}
CID = {'id': 'G2', 'nome': 'Atibaia', 'tipo': 'Cidade', 'titulo': 'Mais imóveis em Atibaia'}


def un(i, nome, preco, area=None, disp='in_stock', grupos=(G,), **extra):
    return dict({'id': str(i), 'codigo': f'lote-{i}', 'titulo': f'Terreno {nome}', 'tipo': 'Terreno', 'preco': preco,
                 'areaTotal': area, 'areaUtil': None, 'dormitorios': None, 'vagas': None, 'disponibilidade': disp,
                 'grupos': list(grupos), 'unidade': nome}, **extra)


TODOS = [un(101, 'Lote 12', 189000, 300, grupos=(G, CID)), un(102, 'Lote 14', 215000, 360), un(103, 'Lote 08', 172000, 280, 'sold'),
         un(104, 'Lote 03', None, 500, 'out_of_stock'), un(200, '', 100000, grupos=(CID,), titulo='Casa no centro'),
         un(300, 'Apto 1', 50000, grupos=({'id': 'G3', 'nome': 'Sozinho', 'tipo': 'Condomínio', 'titulo': ''},)),
         un(400, 'Avulso', 1, grupos=())]


def html_js(item, todos):
    m = (RAIZ / 'site/assets/js/main.js').read_text(encoding='utf-8')
    bloco = m[m.index('const TARJAS='):m.index('function cardHTML')]
    script = ('const esc=v=>String(v??"").replace(/[&<>"\']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;","\'":"&#39;"}[c]));'
              'const brl=n=>typeof n==="number"?"R$ "+Math.round(n).toLocaleString("pt-BR"):"Sob consulta";'
              'const SITE_ROOT="../../";function detailURL(i){return SITE_ROOT+"imoveis/"+encodeURIComponent(i.codigo)+"/";}'
              + bloco + f'\nprocess.stdout.write(unidadesHTML({json.dumps(item)},{json.dumps(todos)}));')
    r = subprocess.run(['node', '-e', script], capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stderr)
    return r.stdout


class Tabela(unittest.TestCase):
    def test_ordem_menor_preco_e_so_o_grupo(self):
        lista = paginas.unidades_grupo(TODOS[1], TODOS, 'G1')
        self.assertEqual([e['id'] for e in lista], ['103', '101', '102', '104'])   # sem preço no fim

    def test_uma_tabela_por_grupo(self):
        h = paginas.unidades_html(TODOS[0], TODOS)   # Lote 12 está no condomínio e na cidade
        self.assertEqual(h.count('<section class="box imovel-unidades"'), 2)
        self.assertTrue(h.startswith('<div class="imovel-unidades-lista">'))
        self.assertIn('>Reserva das Palmeiras</h3>', h)            # título = nome do grupo
        self.assertIn('>Mais imóveis em Atibaia</h3>', h)          # ou o título personalizado
        self.assertIn('Cidade · 2 imóveis', h)
        self.assertIn('Casa no centro', h)                         # sem nome de unidade: título do anúncio
        self.assertEqual(h.count('Você está aqui'), 2)
        self.assertEqual(paginas.unidades_html(TODOS[1], TODOS).count('<section'), 1)

    def test_sem_grupo_ou_sozinho_nao_aparece(self):
        self.assertEqual(paginas.unidades_html(TODOS[5], TODOS), '')
        self.assertEqual(paginas.unidades_html(TODOS[6], TODOS), '')
        self.assertEqual(paginas.unidades_html(TODOS[0], []), '')

    def test_destaque_vendido_links_e_colunas(self):
        h = paginas.unidades_html(TODOS[1], TODOS)
        self.assertEqual(h.count('class="un-linha'), 4)
        self.assertIn('<tr class="un-linha un-atual" aria-current="page">', h)
        self.assertIn('un-linha un-vendida', h); self.assertIn('<span class="un-selo">Vendido</span>', h)
        self.assertIn('un-linha un-indisponivel', h); self.assertIn('Indisponível', h)
        self.assertIn('href="../../imoveis/lote-101/"', h); self.assertNotIn('href="../../imoveis/lote-102/"', h)
        self.assertIn('Condomínio fechado · 4 imóveis', h)
        self.assertIn('<th scope="col">Área</th>', h)
        self.assertNotIn('Dorm.', h); self.assertNotIn('Vagas', h)   # coluna vazia não aparece
        self.assertNotIn('un-mais', h)
        self.assertIn('<span class="un-nome">Lote 14</span><span class="un-tipo">Terreno</span>', h)   # celular: só o tipo
        self.assertIn('<span class="un-longo">Ver anúncio →</span><span class="un-curto">Ver →</span>', h)

    def test_grupo_grande_mostra_8_e_botao(self):
        cidade = [un(500 + k, f'Casa {k}', 100000 + k * 1000, grupos=(CID,)) for k in range(12)]
        h = paginas.unidades_html(cidade[11], cidade)   # o mais caro: fica visível mesmo depois da 8ª linha
        self.assertEqual(h.count('un-extra'), 3)
        self.assertIn('un-linha un-atual"', h)
        self.assertIn('Mostrar todos os 12 ↓', h)

    def test_python_igual_ao_js(self):
        norm = lambda s: re.sub(r'\s', ' ', s)
        for k in range(5):
            self.assertEqual(norm(paginas.unidades_html(TODOS[k], TODOS)), norm(html_js(TODOS[k], TODOS)), k)
        apto = [un(1, 'Apto 31', 400000, dormitorios=2, vagas=1), un(2, 'Apto 42', 450000, dormitorios=3, vagas=None)]
        self.assertEqual(norm(paginas.unidades_html(apto[0], apto)), norm(html_js(apto[0], apto)))
        cidade = [un(500 + k, f'Casa {k}', 100000 + k, grupos=(CID,)) for k in range(10)]
        self.assertEqual(norm(paginas.unidades_html(cidade[9], cidade)), norm(html_js(cidade[9], cidade)))
        self.assertEqual(html_js(TODOS[6], TODOS), '')

    def test_pagina_coloca_depois_do_mapa(self):
        base = {'categoria': 'venda', 'status': 'publicado', 'descricao': 'x', 'imagens': [], 'feeds': {},
                'localizacao': {'cidade': 'Atibaia', 'uf': 'SP', 'endereco': 'Atibaia, SP'}, 'anunciante': {'nome': 'Imoplace'}}
        todos = [dict(base, **e) for e in TODOS[:3]]
        conf = {'urlPublica': 'https://imoplace.com.br', 'nome': 'Imoplace', 'permitirIndexacao': False}
        h = paginas.pagina(todos[0], conf, todos)
        self.assertLess(h.index('imovel-mapa'), h.index('imovel-unidades'))
        self.assertLess(h.index('imovel-unidades'), h.index('imovel-barra'))
        self.assertNotIn('imovel-unidades', paginas.pagina(todos[0], conf))   # sem catálogo: sem tabela

    def test_imovel_js_e_estilo(self):
        js = (RAIZ / 'site/assets/js/imovel.js').read_text(encoding='utf-8')
        self.assertIn('${unidadesHTML(item,todos)}', js)
        self.assertIn('detailsHTML(item,items)', js)
        self.assertIn("closest('.un-mais')", js)
        self.assertLess(js.index('imovel-mapa'), js.index('unidadesHTML(item,todos)'))
        css = (RAIZ / 'site/assets/css/style.css').read_text(encoding='utf-8')
        self.assertIn('"mapa barra" "unidades barra"', css)
        self.assertIn('.imovel-unidades-lista{grid-area:unidades', css)
        self.assertIn('.js .imovel-unidades:not(.aberto) .un-extra{display:none}', css)
        self.assertIn('.un-atual{background:#e3eefb;animation:un-respira 2s', css)
        self.assertIn('@keyframes un-respira{0%,100%{background:#e3eefb}50%{background:#cfe1f8}}', css)
        self.assertIn('.un-aqui i{width:8px;height:8px;border-radius:50%;background:#fff;animation:un-onda 1.8s', css)
        self.assertIn('box-shadow:inset 5px 0 0 #0a3a7a', css)
        self.assertIn('.un-nome,.un-longo,.un-vagas{display:none}', css)   # celular compacto
        self.assertIn('@media (prefers-reduced-motion:reduce){.un-atual,.un-aqui i{animation:none}}', css)


class Motor(unittest.TestCase):
    def test_feed_leva_grupo_e_unidade(self):
        im = {'ID': '7', 'CATEGORIA': 'venda', 'TITULO': 'Lote 12', 'STATUS': 'publicado', 'GRUPOS_IDS': 'G1, G9, G4,G1', 'UNIDADE_NOME': 'Lote 12'}
        sem = dict(im, ID='8', GRUPOS_IDS='G9')
        tb = {'IMOVEIS': [im, sem], 'IMAGENS': [], 'GRUPOS': [{'ID': 'G1', 'NOME': 'Reserva', 'TIPO': 'Loteamento', 'TITULO_SECAO': ''},
                                                         {'ID': 'G4', 'NOME': 'Atibaia', 'TIPO': 'Cidade', 'TITULO_SECAO': 'Em Atibaia'}, {'ID': 'G5', 'NOME': '', 'TIPO': 'x'}]}
        feed = {i['id']: i for i in core_google.montar_feed(tb, 'https://imoplace.com.br')['imoveis']}
        self.assertEqual([g['id'] for g in feed['7']['grupos']], ['G1', 'G4'])   # G9 não existe; G1 repetido
        self.assertEqual(feed['7']['grupos'][1], {'id': 'G4', 'nome': 'Atibaia', 'tipo': 'Cidade', 'titulo': 'Em Atibaia'})
        self.assertEqual(feed['7']['unidade'], 'Lote 12')
        self.assertEqual(feed['8']['grupos'], [])   # grupo apagado/inexistente: imóvel avulso
        self.assertEqual(core_google.montar_feed({'IMOVEIS': [im], 'IMAGENS': []}, '')['imoveis'][0]['grupos'], [])

    def test_catalogo_entrada(self):
        item = {'id': '7', 'codigo': 'lote-7', 'categoria': 'venda', 'titulo': 'x', 'unidade': 'Lote 12',
                'grupos': [{'id': 'G1', 'nome': 'R', 'tipo': 'Loteamento', 'titulo': ''}, {'id': 'G2', 'nome': ''}, None]}
        e = gerador._entrada(item, [])
        self.assertEqual([g['id'] for g in e['grupos']], ['G1']); self.assertEqual(e['unidade'], 'Lote 12')
        self.assertEqual(gerador._entrada(dict(item, grupos=None), [])['grupos'], [])

    def test_le_colunas_novas_pelo_cabecalho_e_aba_grupos(self):
        """Regressão 4.4.0: TARJA/VENDIDO_EM ficam depois da coluna BF e não eram lidas."""
        cab = (['ID', 'SLUG', 'CATEGORIA'] + [f'X{i}' for i in range(54)] + ['MIDIAS_JSON', 'LINKS_EXTERNOS_JSON', 'TARJA', 'TARJA_TEXTO',
               'PRECO_ANTERIOR', 'VENDIDO_EM', 'EXCLUIR_PENDENTE', 'GRUPOS_IDS', 'UNIDADE_NOME'])
        pedidos = []

        def req(url, **kw):
            pedidos.append(url)
            if 'fields=sheets' in url:
                return {'sheets': [{'properties': {'title': t}} for t in ('IMOVEIS', 'IMAGENS', 'FILA', 'RESULTADOS', 'GRUPOS')]}
            if 'IMOVEIS!1%3A1' in url or 'IMOVEIS%211%3A1' in url:
                return {'values': [cab]}
            if '1%3A1' in url:
                return {'values': [['IMAGEM_ID', 'FORMATO']]}
            faixas = re.findall(r'ranges=([^&]+)', url)
            from urllib.parse import unquote
            out = []
            for f in faixas:
                nome, intervalo = unquote(f).strip("'").split("'!")
                if nome == 'RESULTADOS':
                    out.append({'values': [list(core_google.EVENT_COLS)]})
                elif nome == 'GRUPOS':
                    out.append({'values': [['ID', 'NOME', 'TIPO', 'TITULO_SECAO'], ['G1', 'Reserva', 'Loteamento', '']]})
                elif nome == 'IMOVEIS' and intervalo.startswith('A1'):
                    out.append({'values': [['ID', 'SLUG', 'CATEGORIA'], ['7', 'lote', 'venda']]})
                elif nome == 'IMOVEIS':
                    col = intervalo.split('1:')[0]
                    n = 0
                    for ch in col:
                        n = n * 26 + ord(ch) - 64
                    nomecol = cab[n - 1] if n - 1 < len(cab) else ''
                    val = {'TARJA': 'black_friday', 'VENDIDO_EM': '2026-11-01', 'GRUPOS_IDS': 'G1, G4', 'UNIDADE_NOME': 'Lote 12'}.get(nomecol, '')
                    out.append({'values': [[nomecol], [val]]})
                else:
                    out.append({'values': [['A']]})
            return {'valueRanges': out}

        with patch.object(core_google, '_request', side_effect=req), patch.object(core_google, '_sheet_id', return_value='S'):
            tb = core_google.ler_tabelas()
        im = tb['IMOVEIS'][0]
        self.assertEqual(im['TARJA'], 'black_friday'); self.assertEqual(im['VENDIDO_EM'], '2026-11-01')
        self.assertEqual(im['GRUPOS_IDS'], 'G1, G4'); self.assertEqual(im['UNIDADE_NOME'], 'Lote 12')
        self.assertEqual(tb['GRUPOS'][0]['NOME'], 'Reserva')


if __name__ == '__main__':
    unittest.main()
