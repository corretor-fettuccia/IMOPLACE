"""Botão Compartilhar: em cada notícia (página e card) e no imóvel, visível só em celular."""
import re,tempfile,unittest
from pathlib import Path
import noticias
from tests.test_noticias330 import CONF,row

RAIZ=Path(__file__).resolve().parents[2]


class Compartilhar(unittest.TestCase):
    def test_noticia_e_card_tem_botao_com_link_da_materia(self):
        with tempfile.TemporaryDirectory() as d:
            site=Path(d);noticias.construir(site,CONF,[row()],{})
            url='https://imoplace.com.br/noticias/curiosidade-n123456abcdef/'
            pagina=(site/'noticias/curiosidade-n123456abcdef/index.html').read_text(encoding='utf-8')
            lista=(site/'noticias/index.html').read_text(encoding='utf-8')
            for html in (pagina,lista):
                self.assertIn(f'data-compartilhar="{url}"',html)
                self.assertIn('class="btn btn-line share-mobile news-share"',html)
                self.assertIn('assets/js/compartilhar.js',html)
                self.assertIn('<svg viewBox="0 0 24 24" aria-hidden="true"',html)  # ícone
                self.assertIn('<span>Compartilhar</span>',html)

    def test_so_celular(self):
        css=(RAIZ/'site/assets/css/style.css').read_text(encoding='utf-8')
        self.assertRegex(css,r'\.btn\.share-mobile\{display:none;background:#1461bb;[^}]*\}@media \(pointer:coarse\)\{\.btn\.share-mobile\{display:inline-flex\}\}')
        self.assertIn('.dact #share{background:#1461bb',css)  # azul também no imóvel
        self.assertIn('class="btn btn-line share-mobile" id="share"><svg',(RAIZ/'site/assets/js/imovel.js').read_text(encoding='utf-8'))
        self.assertTrue((RAIZ/'site/assets/js/compartilhar.js').is_file())


if __name__=='__main__':
    unittest.main()
