import tempfile,unittest
from pathlib import Path
from marketing import aplicar
class Marketing340(unittest.TestCase):
 def test_republicacao_desativacao_e_admin(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'adm').mkdir();(root/'imoveis/a').mkdir(parents=True)
   html='<html><head><title>Imóvel</title></head><body>Descrição</body></html>'
   for path in ['index.html','adm/index.html','imoveis/a/index.html']:(root/path).write_text(html)
   self.assertEqual(aplicar(root),2);self.assertEqual(aplicar(root),0)
   self.assertEqual((root/'adm/index.html').read_text(),html)
   aplicar(root,{'gtm':{'ativo':False,'id':'GTM-MKJDSLPS'}})
   text=(root/'index.html').read_text();self.assertIn('"ativo": false',text);self.assertEqual(text.count('IMOPLACE MARKETING START'),1)
   self.assertIn('<body>Descrição</body>',text)
 def test_id_invalido(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):aplicar(Path(d),{'gtm':{'ativo':True,'id':'invalid'}})
