import io,os,sys,tempfile,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import formatos_imagens as formatos
import core_configurar,gerador,validar
from tests.test_publicacao import item_feed,img_pend,CONF

class Formatos331(unittest.TestCase):
    def test_default_alias_e_rejeicao(self):
        self.assertEqual(formatos.normalizar_formato(''),'webp')
        self.assertEqual(formatos.normalizar_formato('JPG'),'jpeg')
        for f in ('webp','jpeg','png','jxl'):self.assertEqual(formatos.normalizar_formato(f),f)
        with self.assertRaises(ValueError):formatos.normalizar_formato('gif')

    def test_configuracao_ausente_usa_webp(self):
        rows={'values':[['CHAVE','VALOR'],['SITE_URL','https://imoplace.com.br'],['LOTE_MAXIMO','20']]}
        with patch.object(core_configurar,'_sheet_id',return_value='a'*25),patch.object(core_configurar,'_request',return_value=rows):
            self.assertEqual(core_configurar.carregar_formato_padrao(),'webp')

    def test_picture_prioriza_escolha_com_fallback(self):
        fmts={'jxl':[1],'webp':[1],'jpg':[1],'png':[1]}
        self.assertEqual(formatos.ordem_formatos(fmts)[0],'webp')
        self.assertEqual(formatos.ordem_formatos(fmts,'jpeg')[0],'jpg')
        self.assertEqual(formatos.ordem_formatos(fmts,'png')[0],'png')
        self.assertEqual(formatos.ordem_formatos(fmts,'jxl')[0],'jxl')

    def test_jpeg_png_chegam_integros_e_geram_webp_compativel(self):
        for formato in ('jpeg','png'):
            with self.subTest(formato=formato),tempfile.TemporaryDirectory() as d:
                root=Path(d);site=root/'site';site.mkdir();drive=root/'drive';drive.mkdir()
                image=Image.new('RGBA' if formato=='png' else 'RGB',(80,40),(120,30,180,128) if formato=='png' else (120,30,180))
                output=io.BytesIO();image.save(output,'PNG' if formato=='png' else 'JPEG');data=output.getvalue()
                self.assertEqual(formatos.detectar_formato(data),formato)
                img=img_pend('i000000000a','sala',1,data);img['formato']=formato
                (drive/(img['driveFileId']+'.'+formato)).write_bytes(data)
                item=item_feed('1001','Casa Formato',[])
                pend={'imovelId':'1001','versao':1,'status':'publicado','capaId':img['imagemId'],'imagens':[img]}
                with patch.dict(os.environ,{'DRIVE_FIXTURE':str(drive),'FORMATO_PADRAO_IMAGENS':'webp'}):
                    gerador.montar([item],[pend],site,CONF)
                import json
                cat=json.loads((site/'catalogo.json').read_text());foto=cat['imoveis'][0]['imagens'][0]
                self.assertTrue(foto['matriz'].endswith('.'+formato));self.assertEqual((site/foto['matriz']).read_bytes(),data)
                with Image.open(site/foto['arquivo']) as fallback:self.assertEqual(fallback.format,'WEBP')
                self.assertEqual(foto['adaptativas']['preferido'],'webp')
                self.assertEqual(validar.validar(site,CONF),[])

    def test_addon_e_aplicador_reais_em_node(self):
        import subprocess
        result=subprocess.run(['node',str(Path(__file__).with_name('test_formatos331_node.cjs'))],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
