"""Ícones do site (favicon e afins): quadrados, fundo opaco e arte com margem, para o Google exibir sem cortar."""
import unittest
from pathlib import Path
from PIL import Image, ImageChops

SITE=Path(__file__).resolve().parents[2]/'site'
ICONES=['favicon.ico','favicon-96x96.png','icon.png','icon-192.png','icon-512.png','apple-touch-icon.png']


class Icones(unittest.TestCase):
    def test_quadrados_opacos_e_com_margem(self):
        for nome in ICONES:
            with self.subTest(nome), Image.open(SITE/nome) as im:
                if im.format=='ICO':
                    self.assertIn((48,48),im.ico.sizes())   # Google pede múltiplo de 48
                    im=im.ico.getimage((48,48))
                w,h=im.size;self.assertEqual(w,h,'ícone não é 1:1')
                rgba=im.convert('RGBA');self.assertEqual(rgba.getchannel('A').getextrema()[0],255,'fundo transparente')
                fundo=Image.new('RGB',im.size,rgba.getpixel((0,0))[:3])
                arte=ImageChops.difference(rgba.convert('RGB'),fundo).point(lambda v:255 if v>24 else 0).convert('L').getbbox()
                margem=min(arte[0],arte[1],w-arte[2],h-arte[3])/w
                self.assertGreaterEqual(margem,0.08,'arte encosta na borda: o recorte circular do Google corta')


if __name__=='__main__':
    unittest.main()
