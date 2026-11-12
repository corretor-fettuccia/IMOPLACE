"""Testes sem rede: contrato, publicação incremental ponta a ponta, isolamento de falhas, limpeza e validação."""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

import contrato  # noqa: E402
import gerador  # noqa: E402
import validar  # noqa: E402
from comum import RAIZ, RE_ARQUIVO  # noqa: E402
from integracao import Integracao  # noqa: E402

CONF = {'nome': 'Imoplace', 'urlPublica': 'https://imoplace.com.br', 'permitirIndexacao': True, 'ano': '2026'}
# Testes cruzados exigem Node E o código-fonte Apps Script, ausente no repositório GIT-PAGE.
CAMINHO_ESQUEMA = RAIZ.parent / 'GOOGLE.APPSCRIPT' / 'COMUM' / 'Esquema.gs'
NODE = shutil.which('node') if CAMINHO_ESQUEMA.is_file() else None


def webp(semente: str) -> bytes:
    corpo = b'VP8 ' + hashlib.sha256(semente.encode()).digest() * 4
    return b'RIFF' + (len(corpo) + 4).to_bytes(4, 'little') + b'WEBP' + corpo


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def item_feed(iid, titulo, imagens, categoria='venda', **extra):
    slug = titulo.lower().replace(' ', '-')
    codigo = f'{slug}-{iid}'
    caminho = f'imoveis/{codigo}/'
    base = {
        'id': iid, 'versao': int(extra.get('versao', 1)), 'codigo': codigo, 'categoria': categoria, 'status': 'publicado', 'tipo': 'Casa', 'condicao': 'Usado',
        'destaque': False, 'tag': '', 'ordem': 0, 'titulo': titulo, 'descricao': 'Descrição <b>segura</b>',
        'seo': {'titulo': titulo, 'descricao': 'Resumo'}, 'preco': 550000, 'condominio': None, 'iptuAnual': 1200,
        'financiamento': True, 'permuta': False, 'documentacaoEmDia': True, 'dormitorios': 3, 'suites': 1,
        'banheiros': 2, 'vagas': 2, 'areaTotal': 130, 'areaUtil': None,
        'localizacao': {'bairro': 'Igara', 'cidade': 'Canoas', 'uf': 'RS', 'endereco': 'Igara, Canoas', 'lat': None, 'lng': None},
        'comodidades': ['Piscina'], 'caracteristicasImovel': ['Pátio'], 'caracteristicasCondominio': [],
        'anunciante': {'nome': 'Fettuccia', 'creci': '12345', 'whatsapp': '5551999999999'},
        'feeds': {'google': True, 'meta': True, 'disponibilidade': 'in_stock'},
        'imagemCapaId': imagens[0]['id'] if imagens else '', 'caminho': caminho,
        'url': f'https://imoplace.com.br/{caminho}', 'atualizadoEm': '2026-11-10T21:30:00Z',
        'imagens': [{'id': i['id'], 'arquivo': caminho + 'imagens/' + i['arquivo'], 'legenda': i.get('legenda', 'Foto'),
                     'alt': 'alt', 'versao': i['versao']} for i in imagens],
    }
    base.update(extra)
    return base


def feed(*itens):
    return {'ok': True, 'contrato': 'imoplace-v1', 'geradoEm': 'x', 'snapshotCompleto': True, 'total': len(itens), 'imoveis': list(itens)}


def img_pend(imagem_id, nome, versao, dados, ordem=1, operacao='incluir', publicada=0):
    return {'imagemId': imagem_id, 'driveFileId': 'drv_' + imagem_id + '_v' + str(versao), 'nome': nome, 'legenda': nome.title(),
            'alt': '', 'ordem': ordem, 'versao': versao, 'versaoPublicada': publicada, 'sha256': sha(dados), 'bytes': len(dados),
            'operacao': operacao, 'arquivo': f'{nome}-{imagem_id}.v{versao}.webp'}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.site = self.tmp / 'site'
        shutil.copytree(RAIZ / 'site', self.site)
        self.drive = self.tmp / 'drive'
        self.drive.mkdir()
        os.environ['DRIVE_FIXTURE'] = str(self.drive)

    def tearDown(self):
        os.environ.pop('DRIVE_FIXTURE', None)
        shutil.rmtree(self.tmp)

    def no_drive(self, img, dados):
        (self.drive / f'{img["driveFileId"]}.webp').write_bytes(dados)

    def catalogo(self):
        return json.loads((self.site / 'catalogo.json').read_text(encoding='utf-8'))


class TestContrato(unittest.TestCase):
    def test_feed_valido_e_invalidos(self):
        it = item_feed('1001', 'Casa Igara', [{'id': 'i0000000001', 'arquivo': 'sala-i0000000001.v1.webp', 'versao': 1}])
        contrato.validar_feed(feed(it))
        for mexer in (lambda f: f.update(contrato='outro'), lambda f: f.update(snapshotCompleto=False),
                      lambda f: f.update(total=9), lambda f: f['imoveis'][0].update(categoria='aluguel'),
                      lambda f: f['imoveis'][0].update(codigo='../../etc-1001'),
                      lambda f: f['imoveis'][0]['imagens'][0].update(arquivo='imoveis/x/imagens/../../a.webp')):
            f = feed(copy.deepcopy(it))
            mexer(f)
            with self.assertRaises(contrato.ContratoInvalido):
                contrato.validar_feed(f)

    def test_assinatura_hmac_estavel(self):
        a = Integracao.assinar('s' * 40, 'pendencias', '1762800000', 'gh-1-1', '{"forcar":false}')
        self.assertEqual(len(a), 64)
        self.assertNotEqual(a, Integracao.assinar('s' * 40, 'confirmar', '1762800000', 'gh-1-1', '{"forcar":false}'))


class TestPublicacao(Base):
    def test_ponta_a_ponta_incremental(self):
        sala, cozinha = webp('sala-v1'), webp('cozinha-v1')
        p_sala = img_pend('i000000000a', 'sala', 1, sala, 1)
        p_coz = img_pend('i000000000b', 'cozinha', 1, cozinha, 2)
        for i, d in ((p_sala, sala), (p_coz, cozinha)):
            self.no_drive(i, d)
        pend = [{'imovelId': '1001', 'versao': 5, 'motivo': 'publicar', 'status': 'publicado', 'capaId': 'i000000000b',
                 'caminho': 'imoveis/casa-igara-1001/', 'imagens': [p_sala, p_coz]}]
        it = item_feed('1001', 'Casa Igara', [])
        rel = gerador.montar(contrato.validar_feed(feed(it)), pend, self.site, CONF)

        cat = self.catalogo()
        self.assertEqual(cat['total'], 1)
        e = cat['imoveis'][0]
        self.assertEqual(e['codigo'], 'casa-igara-1001')
        self.assertTrue(e['imagens'][0]['arquivo'].endswith('cozinha-i000000000b.v1.webp'), 'foto destaque primeiro')
        pagina = (self.site / 'imoveis/casa-igara-1001/index.html').read_text(encoding='utf-8')
        self.assertIn('Descrição &lt;b&gt;segura&lt;/b&gt;', pagina)
        self.assertIn('index,follow', pagina)
        self.assertEqual(rel['transferidas'], 2)
        self.assertEqual(rel['confirmar']['imoveis'], [{'imovelId': '1001', 'versao': 5, 'noSite': True}])
        self.assertEqual(len(rel['confirmar']['imagens']), 2)
        self.assertEqual(validar.validar(self.site, CONF), [])
        gerador.indexacao_home(self.site, CONF)
        gerador.gravar_sitemap(cat['imoveis'], self.site, CONF)
        gerador.gravar_feeds(cat['imoveis'], self.site, CONF)
        self.assertIn('casa-igara-1001', (self.site / 'sitemap.xml').read_text(encoding='utf-8'))
        self.assertIn('<g:price>550000.00 BRL</g:price>', (self.site / 'merchant-produtos.xml').read_text(encoding='utf-8'))
        self.assertIn('in stock', (self.site / 'meta-produtos.xml').read_text(encoding='utf-8'))

        # Segunda execução: só a sala muda (v2). Cozinha não é baixada de novo; sala v1 sai do site.
        sala2 = webp('sala-v2')
        p_sala2 = img_pend('i000000000a', 'sala', 2, sala2, 1, operacao='atualizar', publicada=1)
        self.no_drive(p_sala2, sala2)
        (self.drive / f'{p_coz["driveFileId"]}.webp').unlink()  # prova: cozinha não pode ser baixada
        p_coz_pub = dict(p_coz, versaoPublicada=1, operacao='')
        pend2 = [dict(pend[0], versao=6, imagens=[p_sala2, p_coz_pub])]
        rel2 = gerador.montar(contrato.validar_feed(feed(it)), pend2, self.site, CONF)
        self.assertEqual(rel2['transferidas'], 1)
        pasta = self.site / 'imoveis/casa-igara-1001/imagens'
        self.assertEqual(sorted(p.name for p in pasta.iterdir()), ['cozinha-i000000000b.v1.webp', 'sala-i000000000a.v2.webp'])
        self.assertEqual(validar.validar(self.site, CONF), [])

    def test_so_preco_nao_baixa_foto(self):
        foto = webp('f')
        it = item_feed('1002', 'Apto Centro', [{'id': 'i00000000cc', 'arquivo': 'fachada-i00000000cc.v1.webp', 'versao': 1}])
        alvo = self.site / it['imagens'][0]['arquivo']
        alvo.parent.mkdir(parents=True)
        alvo.write_bytes(foto)
        p = img_pend('i00000000cc', 'fachada', 1, foto, operacao='', publicada=1)
        pend = [{'imovelId': '1002', 'versao': 9, 'motivo': 'editar', 'status': 'publicado', 'capaId': 'i00000000cc',
                 'caminho': it['caminho'], 'imagens': [p]}]
        rel = gerador.montar([dict(it, preco=499000)], pend, self.site, CONF)
        self.assertEqual(rel['transferidas'], 0)
        self.assertEqual(self.catalogo()['imoveis'][0]['preco'], 499000)

    def test_falha_isola_imovel_e_mantem_versao_anterior(self):
        foto = webp('ok')
        it_ok = item_feed('1002', 'Apto Centro', [{'id': 'i00000000cc', 'arquivo': 'fachada-i00000000cc.v1.webp', 'versao': 1}])
        (self.site / it_ok['imagens'][0]['arquivo']).parent.mkdir(parents=True)
        (self.site / it_ok['imagens'][0]['arquivo']).write_bytes(foto)
        gerador.montar([it_ok], [], self.site, CONF)  # estado anterior publicado
        ruim = img_pend('i00000000cc', 'fachada', 2, webp('novo'), operacao='atualizar', publicada=1)
        self.no_drive(ruim, webp('ADULTERADO'))  # hash não confere
        pend = [{'imovelId': '1002', 'versao': 3, 'status': 'publicado', 'capaId': 'i00000000cc', 'caminho': it_ok['caminho'], 'imagens': [ruim]}]
        rel = gerador.montar([dict(it_ok, titulo='Apto Centro NOVO')], pend, self.site, CONF)
        self.assertEqual([f['imovelId'] for f in rel['falhas']], ['1002'])
        self.assertEqual(rel['confirmar']['imoveis'], [])
        e = self.catalogo()['imoveis'][0]
        self.assertEqual(e['titulo'], 'Apto Centro', 'versão anterior continua no ar')
        self.assertEqual(validar.validar(self.site, CONF), [])

    def test_despublicar_remove_e_troca_de_slug_redireciona(self):
        foto = webp('x')
        a = item_feed('1003', 'Casa Velha', [{'id': 'i00000000dd', 'arquivo': 'a-i00000000dd.v1.webp', 'versao': 1}])
        b = item_feed('1004', 'Some Daqui', [{'id': 'i00000000ee', 'arquivo': 'b-i00000000ee.v1.webp', 'versao': 1}])
        for it in (a, b):
            (self.site / it['imagens'][0]['arquivo']).parent.mkdir(parents=True)
            (self.site / it['imagens'][0]['arquivo']).write_bytes(foto)
        gerador.montar([a, b], [], self.site, CONF)
        # 1003 mudou o título/slug e a categoria; 1004 foi baixado (sai do feed).
        novo = item_feed('1003', 'Casa Reformada', [], categoria='lancamento')
        p = img_pend('i00000000dd', 'a', 1, foto, operacao='', publicada=1)
        self.no_drive(p, foto)
        pend = [{'imovelId': '1003', 'versao': 4, 'status': 'publicado', 'capaId': 'i00000000dd', 'caminho': novo['caminho'], 'imagens': [p]},
                {'imovelId': '1004', 'versao': 7, 'status': 'baixado', 'imagens': [img_pend('i00000000ee', 'b', 1, foto, operacao='', publicada=1)]}]
        rel = gerador.montar([novo], pend, self.site, CONF)
        self.assertFalse((self.site / 'imoveis/some-daqui-1004').exists())
        antigo = (self.site / 'imoveis/casa-velha-1003/index.html').read_text(encoding='utf-8')
        self.assertIn('imoveis/casa-reformada-1003/', antigo)
        self.assertFalse((self.site / 'imoveis/casa-velha-1003/imagens').exists())
        conf_1004 = [i for i in rel['confirmar']['imoveis'] if i['imovelId'] == '1004'][0]
        self.assertFalse(conf_1004['noSite'])
        self.assertEqual(rel['confirmar']['imagens'][-1], {'imagemId': 'i00000000ee', 'versao': 1, 'foraDoSite': True})
        self.assertEqual(validar.validar(self.site, CONF), [])

    def test_validar_pega_vazamento_e_foto_falsa(self):
        it = item_feed('1005', 'Teste', [{'id': 'i00000000ff', 'arquivo': 'c-i00000000ff.v1.webp', 'versao': 1}])
        alvo = self.site / it['imagens'][0]['arquivo']
        alvo.parent.mkdir(parents=True)
        alvo.write_bytes(webp('c'))
        gerador.montar([it], [], self.site, CONF)
        cat = self.catalogo()
        cat['imoveis'][0]['proprietario'] = 'Fulano'
        (self.site / 'catalogo.json').write_text(json.dumps(cat), encoding='utf-8')
        alvo.write_bytes(b'<html>nao e imagem</html>')
        problemas = ' '.join(validar.validar(self.site, CONF))
        self.assertIn('campos privados', problemas)
        self.assertIn('não é WebP', problemas)

    def test_indexacao_desligada(self):
        conf = dict(CONF, permitirIndexacao=False)
        gerador.montar([], [], self.site, conf)
        self.assertFalse((self.site / 'sitemap.xml').exists())
        self.assertIn('Disallow: /', (self.site / 'robots.txt').read_text())
        self.assertIn('noindex,follow', (self.site / 'index.html').read_text(encoding='utf-8'))


class TestOrquestrador(Base):
    def test_cli_com_fixtures(self):
        integ = self.tmp / 'integ'
        integ.mkdir()
        foto = webp('cli')
        p = img_pend('i0000000123', 'quarto', 1, foto)
        self.no_drive(p, foto)
        (integ / 'pendencias.json').write_text(json.dumps({'ok': True, 'pendencias': [
            {'imovelId': '1010', 'versao': 2, 'status': 'publicado', 'capaId': p['imagemId'], 'caminho': 'imoveis/sobrado-1010/', 'imagens': [p]}]}))
        (self.tmp / 'feed.json').write_text(json.dumps(feed(item_feed('1010', 'Sobrado', []))))
        (self.tmp / 'conf.json').write_text(json.dumps(CONF))
        env = dict(os.environ, SITE_DIR=str(self.site), ESTADO_DIR=str(self.tmp / 'estado'), INTEGRACAO_FIXTURE=str(integ),
                   FEED_FIXTURE=str(self.tmp / 'feed.json'), IMOPLACE_CONFIG=str(self.tmp / 'conf.json'), GITHUB_OUTPUT=str(self.tmp / 'out'))
        cli = [sys.executable, str(RAIZ / 'scripts' / 'publicar.py')]
        for cmd in ('pendencias', 'gerar'):
            subprocess.run(cli + [cmd], env=env, check=True, capture_output=True)
        self.assertIn('tem=true', (self.tmp / 'out').read_text())
        subprocess.run([sys.executable, str(RAIZ / 'scripts' / 'validar.py')], env=env, check=True, capture_output=True)
        subprocess.run(cli + ['confirmar'], env=env, check=True, capture_output=True)
        ack = json.loads((integ / 'saida-confirmar.json').read_text())
        self.assertEqual(ack['imoveis'], [{'imovelId': '1010', 'versao': 2, 'noSite': True}])
        self.assertEqual(ack['transferidas'], 1)


@unittest.skipUnless(NODE, 'node indisponível')
class TestCompatibilidadeAppsScript(unittest.TestCase):
    """O feed gerado pelo Apps Script (Esquema.gs) precisa passar no contrato do Python."""

    def node(self, cmd, entrada):
        r = subprocess.run([NODE, str(AQUI / 'apoio.js'), cmd], input=json.dumps(entrada), capture_output=True, text=True, check=True)
        return json.loads(r.stdout)

    def test_feed_do_apps_script_passa_no_contrato(self):
        linha = {'ID': '1020', 'CATEGORIA': 'venda', 'TITULO': 'Casa Nova em São Leopoldo', 'TIPO': 'Casa', 'PRECO': '480.000,00',
                 'IMAGEM_CAPA_ID': 'i00000000a2', 'PROPRIETARIO': 'NÃO PODE SAIR', 'CIDADE': 'São Leopoldo', 'UF': 'rs'}
        imgs = [{'IMAGEM_ID': 'i00000000a1', 'NOME': 'Fachada.jpg', 'ORDEM': 1, 'versao': 2},
                {'IMAGEM_ID': 'i00000000a2', 'NOME': 'Sala Ampla', 'ORDEM': 2, 'versao': 1}]
        item = self.node('serializar', {'imovel': linha, 'imagens': imgs, 'siteUrl': 'https://imoplace.com.br'})
        contrato.validar_item(item)
        self.assertEqual(item['preco'], 480000)
        self.assertEqual(item['localizacao']['uf'], 'RS')
        self.assertNotIn('NÃO PODE SAIR', json.dumps(item, ensure_ascii=False))
        self.assertTrue(item['imagens'][0]['arquivo'].endswith('sala-ampla-i00000000a2.v1.webp'))

    def test_assinatura_igual_nos_dois_lados(self):
        e = {'acao': 'confirmar', 'ts': '1762800000', 'jobId': 'gh-9-1', 'payload': '{"imoveis":[]}'}
        msg = self.node('assinar', e)['mensagem']
        self.assertEqual(msg, '\n'.join([e['acao'], e['ts'], e['jobId'], e['payload']]))

    def test_nome_de_foto_igual_ao_regex_do_python(self):
        n = self.node('nome', {'img': {'NOME': 'Área de Lazer!.png', 'IMAGEM_ID': 'i1a2b3c4d5e'}, 'versao': 12})['nome']
        self.assertRegex(n, RE_ARQUIVO)

    def test_testes_js(self):
        subprocess.run([NODE, str(AQUI / 'test_apps_script.js')], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
