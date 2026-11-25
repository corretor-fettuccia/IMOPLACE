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
        self.assertIn('<script src="{RAIZ_REL}assets/js/avatar.js?v=2"></script>', src)

    def test_avatar_acompanha_o_botao_e_nao_tem_clique(self):
        js = (RAIZ / 'site/assets/js/avatar.js').read_text(encoding='utf-8')
        self.assertIn(".zap-flutuante", js)
        self.assertNotIn('addEventListener(\'click\'', js)
        for frase in ('Eu não mordo!', 'negócio verde', 'eu te ajudo também'):
            self.assertIn(frase, js)
        # versão em sprites: o estilo vem no próprio avatar.js e a folha é WebP
        self.assertIn('.imo-avatar{', js)
        self.assertIn('pointer-events:none', js)
        self.assertIn('tijolo-sprites.webp', js)
        folha = RAIZ / 'site/assets/img/tijolo-sprites.webp'
        self.assertTrue(folha.is_file())
        self.assertLess(folha.stat().st_size, 400_000)

    def test_whatsapp_flutuante_logo_e_pulso(self):
        py = (RAIZ / 'scripts/paginas.py').read_text(encoding='utf-8')
        js = (RAIZ / 'site/assets/js/imovel.js').read_text(encoding='utf-8')
        logo = 'viewBox="0 0 448 512" fill="currentColor"'
        self.assertIn(logo, py)
        self.assertIn(logo, js)
        css = (RAIZ / 'site/assets/css/style.css').read_text(encoding='utf-8')
        self.assertIn('.zap-flutuante{animation:zap-pulso', css)
        self.assertIn('prefers-reduced-motion:reduce){.zap-flutuante{animation:none}', css)


if __name__ == '__main__':
    unittest.main()
