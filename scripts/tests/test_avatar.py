"""Avatar do cachorrinho: só aparece ao lado do WhatsApp flutuante, sem clique nem botão próprio."""
import unittest
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]


class TestAvatar(unittest.TestCase):
    def test_paginas_publicadas_carregam_avatar_depois_do_imovel_js(self):
        for pagina in sorted((RAIZ / 'site/imoveis').glob('*/index.html')):
            html = pagina.read_text(encoding='utf-8')
            if 'assets/js/imovel.js' not in html:
                continue  # redirecionamento de endereço antigo
            self.assertLess(html.index('assets/js/imovel.js'), html.index('assets/js/avatar.js'), pagina.parent.name)

    def test_modelo_tem_script_do_avatar(self):
        src = (RAIZ / 'scripts/paginas.py').read_text(encoding='utf-8')
        self.assertIn('<script src="{RAIZ_REL}assets/js/avatar.js"></script>', src)

    def test_avatar_acompanha_o_botao_e_nao_tem_clique(self):
        js = (RAIZ / 'site/assets/js/avatar.js').read_text(encoding='utf-8')
        self.assertIn(".zap-flutuante", js)
        self.assertNotIn('addEventListener(\'click\'', js)
        for frase in ('Eu não mordo!', 'negócio verde', 'eu te ajudo também'):
            self.assertIn(frase, js)
        css = (RAIZ / 'site/assets/css/style.css').read_text(encoding='utf-8')
        self.assertIn('.imo-avatar{', css)
        self.assertIn('pointer-events:none', css)


if __name__ == '__main__':
    unittest.main()
