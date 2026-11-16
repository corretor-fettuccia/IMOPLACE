import hashlib,json,os,random,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image,ImageDraw
import core_google,gerador,imagens_adaptativas as adaptive,jxl_codec,paginas,validar
from tests.test_publicacao import item_feed,img_pend,CONF

class Jxl322(unittest.TestCase):
    def test_lossless_matriz_e_variantes_sem_cascata(self):
        with tempfile.TemporaryDirectory() as d:
            site=Path(d);source=Image.new('RGBA',(64,32))
            rng=random.Random(322);source.putdata([(rng.randrange(256),rng.randrange(256),rng.randrange(256),255) for _ in range(64*32)])
            ImageDraw.Draw(source).text((2,2),'Imoplace',fill='white')
            matrix=site/'matriz.jxl';jxl_codec.encode(source,matrix);before=matrix.read_bytes()
            self.assertTrue(jxl_codec.is_jxl(before));self.assertEqual(jxl_codec.decode(matrix).tobytes(),source.tobytes())
            out=adaptive.gerar({'arquivo':'foto.webp','matriz':'matriz.jxl'},site)
            self.assertEqual(matrix.read_bytes(),before)
            self.assertEqual(out['origem'],'jxl-lossless')
            for row in out['formatos']['jxl']:self.assertEqual(jxl_codec.decode(site/row['arquivo']).tobytes(),source.tobytes())
            self.assertEqual(out['social']['mime'],'image/jpeg')
            with Image.open(site/out['social']['arquivo']) as im:self.assertEqual(im.size,(1200,630))
            self.assertEqual(out,adaptive.gerar({'arquivo':'foto.webp','matriz':'matriz.jxl'},site))

    def test_publicacao_nativa_mantem_fallback_seo_e_matriz(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);site=root/'site';site.mkdir();drive=root/'drive';drive.mkdir()
            im=Image.new('RGBA',(80,40),(90,40,200,255));tmp=root/'matriz.jxl';jxl_codec.encode(im,tmp)
            img=img_pend('i000000000a','sala',1,tmp.read_bytes());img['formato']='jxl'
            (drive/(img['driveFileId']+'.jxl')).write_bytes(tmp.read_bytes())
            item=item_feed('1001','Casa JXL',[]);pend={'imovelId':'1001','versao':1,'status':'publicado','capaId':img['imagemId'],'imagens':[img]}
            with patch.dict(os.environ,{'DRIVE_FIXTURE':str(drive)}):report=gerador.montar([item],[pend],site,CONF)
            cat=json.loads((site/'catalogo.json').read_text());foto=cat['imoveis'][0]['imagens'][0]
            self.assertEqual((site/foto['matriz']).read_bytes(),tmp.read_bytes())
            with Image.open(site/foto['arquivo']) as fallback:self.assertEqual(fallback.format,'WEBP')
            html=(site/'imoveis'/cat['imoveis'][0]['codigo']/'index.html').read_text()
            self.assertIn('social.jpg',html);self.assertIn('image/jxl',html);self.assertIn('image/jpeg',html)
            self.assertTrue(paginas.imagem_seo(foto).endswith('.jpg'))
            self.assertEqual(validar.validar(site,CONF),[])
            self.assertEqual(report['transferidas'],1)
            # A second feed keeps the JXL matrix instead of deriving from the WebP fallback.
            fresh=dict(item,imagens=cat['imoveis'][0]['imagens'])
            gerador.montar([fresh],[],site,CONF)
            self.assertTrue((site/foto['matriz']).is_file())

    def test_formato_chega_no_manifesto(self):
        im={'ID':'1001','TITULO':'Casa','STATUS':'publicado','VERSAO':1}
        foto={'IMAGEM_ID':'i000000000a','IMOVEL_ID':'1001','VERSAO':1,'FORMATO':'jxl'}
        self.assertEqual(core_google._manifesto(im,[foto])['imagens'][0]['formato'],'jxl')

    def test_leitura_extra_preserva_privados_e_funciona_antes_da_migracao(self):
        calls=[]
        def request(url):
            calls.append(url)
            if '/values/' in url:return {'values':[['ID','TITULO']]}
            return {'valueRanges':[{'values':[['ID']]}]*6+[{'values':[core_google.EVENT_COLS]}]}
        with patch.object(core_google,'_request',side_effect=request),patch.dict(os.environ,{'PLANILHA_ID':'a'*25}):
            tables=core_google.ler_tabelas()
        self.assertIn('IMOVEIS',tables)
        self.assertFalse(any('BE1' in x for x in calls))
