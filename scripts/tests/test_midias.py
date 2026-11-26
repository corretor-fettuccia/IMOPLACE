import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
import core_google
import midias
import paginas
import imagens_adaptativas as adapt

class Evolucao(unittest.TestCase):
    def test_celula_insegura_nao_vaza_para_publicacao(self):
        arr=[{'url':'javascript:alert(1)','titulo':'X'}, {'url':'https://x.example/','visivel':False}, {'url':'https://x.example/','titulo':'<script>x</script>','ordem':3}]
        items=midias.colecao(json.dumps(arr))
        self.assertEqual(len(items),1)
        html=paginas.multimidia({'midias':items,'links_externos':items})
        self.assertNotIn('<script>',html)
        self.assertNotIn('javascript:',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertIn('data-open-links',html)
        self.assertIn('<iframe src="https://x.example/"',html)
        self.assertIn('sandbox=',html)
        self.assertNotIn('data-embed',html)
        self.assertNotIn('Carregar player',html)

    def test_embed_valida_host_e_identificador(self):
        self.assertEqual(midias.embed('https://youtu.be/abcdefghijk'),'https://www.youtube-nocookie.com/embed/abcdefghijk')
        self.assertEqual(midias.embed('https://youtube.com.evil.test/watch?v=abcdefghijk'),'')
        self.assertEqual(midias.embed('https://usuario@youtube.com/watch?v=abcdefghijk'),'')
        self.assertEqual(midias.embed('https://my.matterport.com/show/?m=ABC123'),'https://my.matterport.com/show/?m=ABC123')

    def test_foto_pequena_sem_ampliar_e_com_cache(self):
        with tempfile.TemporaryDirectory() as d:
            site=Path(d);src=site/'foto.webp';Image.new('RGB',(600,400),'green').save(src)
            f={'arquivo':'foto.webp'};before=src.read_bytes();result=adapt.gerar(f,site)
            self.assertEqual(src.read_bytes(),before)
            for rows in result['formatos'].values():
                for row in rows:
                    with Image.open(site/row['arquivo']) as im:
                        self.assertLessEqual(im.width,600)
                        self.assertAlmostEqual(im.width/im.height,1.5,places=2)
                        self.assertNotIn('exif',im.info)
            self.assertEqual(result,adapt.gerar(f,site))
            self.assertIn('srcset=',paginas.picture({'arquivo':'foto.webp','adaptativas':result},{'titulo':'Foto'},0))

    def test_transparencia_preservada_no_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);Image.new('RGBA',(32,16),(0,0,0,0)).save(p/'foto.webp')
            out=adapt.gerar({'arquivo':'foto.webp'},p)
            self.assertIn('png',out['formatos']);self.assertNotIn('jpg',out['formatos'])
            with Image.open(p/out['formatos']['png'][0]['arquivo']) as im:self.assertEqual(im.getpixel((0,0))[3],0)

    def test_novas_colunas_passam_no_feed(self):
        im={'ID':'1001','CATEGORIA':'venda','TITULO':'Casa','MIDIAS_JSON':json.dumps([{'tipo':'tour_virtual','url':'https://example.org/tour','titulo':'Tour'}])}
        out=core_google._publico(im,[],'https://imoplace.com.br')
        self.assertEqual(out['midias'][0]['titulo'],'Tour')
        self.assertEqual(out['links_externos'],[])

    def test_iframe_colado_vira_url_e_formato(self):
        cod='<iframe src="https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fx&amp;show_text=true&amp;width=500" width="500" height="463" style="border:none" allowfullscreen="true"></iframe>'
        x=midias.colecao(json.dumps([{'tipo':'iframe','url':cod,'titulo':'Post'}]))[0]
        self.assertEqual(x['url'],'https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fx&show_text=true&width=500')
        self.assertEqual(x['proporcao'],'500/463')
        html=paginas.multimidia({'midias':[x],'links_externos':[]})
        self.assertIn('loading="lazy"',html)
        self.assertIn('aspect-ratio:500/463;max-width:500px',html)
        self.assertNotIn('style="border:none"',html)
        self.assertEqual(midias.colecao(json.dumps([{'url':'<iframe srcdoc="<script>x</script>"></iframe>'}])),[])

    def test_video_por_arquivo_e_regras(self):
        v={'tipo':'video','url':'https://cdn.example.org/tour.mp4?x=1','titulo':'Tour','capa':'https://cdn.example.org/capa.jpg'}
        x=midias.colecao(json.dumps([v]))[0]
        self.assertEqual(midias.alvo(x)[0],'video')
        html=paginas.multimidia({'midias':[x],'links_externos':[]})
        self.assertIn('<video src="https://cdn.example.org/tour.mp4?x=1" controls playsinline preload="metadata" poster="https://cdn.example.org/capa.jpg"',html)
        self.assertEqual(midias.alvo({'tipo':'video','url':'https://youtu.be/abcdefghijk'})[:2],('iframe','https://www.youtube-nocookie.com/embed/abcdefghijk'))
        self.assertEqual(midias.alvo({'tipo':'panorama_360','url':'https://x.example/p.jpg'})[0],'panorama')
        self.assertEqual(midias.alvo({'tipo':'iframe','url':'https://www.imoplace.com.br/adm/'})[0],'link')
        self.assertEqual(midias.alvo({'tipo':'iframe','url':'https://kuula.co/share/abc'}),('iframe','https://kuula.co/share/abc','16/9'))

    def test_frontend_real_em_node(self):
        import subprocess
        subprocess.run(['node',str(Path(__file__).with_name('test_midias_node.js'))],check=True,capture_output=True,text=True)
