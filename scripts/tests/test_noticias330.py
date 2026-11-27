import base64,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from pywebpush import webpush,WebPushException
import http_ece,requests
import noticias,push_notificar as push,imagens_adaptativas as adaptive,gerador,validar

CONF={'urlPublica':'https://imoplace.com.br','nome':'Imoplace','permitirIndexacao':True,'ano':'2026'}
def row(**kwargs):
    return dict(ID='n123456abcdef',SLUG='curiosidade',TITULO='Uma boa pergunta sobre seu bairro',RESUMO='Uma leitura para conhecer melhor o lugar onde morar.',CORPO='## O que observar\n\nTexto de teste.\n\n- Um ponto\n- Outro ponto',STATUS='publicado',CATEGORIA='Bairros',AUTOR='Imoplace',PUBLICADO_EM='2026-11-16T13:00:00Z',ATUALIZADO_EM='2026-11-16T13:00:00Z',VERSAO=2,NOTIFICAR='SIM',**kwargs)
def b64(x):return base64.urlsafe_b64encode(x).decode().rstrip('=')
def cfg():
    key=ec.generate_private_key(ec.SECP256R1());n=key.private_numbers();p=n.public_numbers
    jwk={'kty':'EC','crv':'P-256','d':b64(n.private_value.to_bytes(32,'big')),'x':b64(p.x.to_bytes(32,'big')),'y':b64(p.y.to_bytes(32,'big'))}
    return {'PRIVATE_JWK':json.dumps(jwk),'PUBLIC_KEY':b64(key.public_key().public_bytes(Encoding.X962,PublicFormat.UncompressedPoint)),'URL_PUBLICA':'https://script.google.com/macros/s/TESTE/exec','CONTATO':'mailto:contato@imoplace.com.br'}
def sub():
    receiver=ec.generate_private_key(ec.SECP256R1());auth=os.urandom(16)
    return receiver,auth,{'ID':'inscricao-teste','ENDPOINT':'https://fcm.googleapis.com/fcm/send/TESTE','P256DH':b64(receiver.public_key().public_bytes(Encoding.X962,PublicFormat.UncompressedPoint)),'AUTH':b64(auth),'ESCOPOS':'["*"]','CRIADO_EM':'2026-11-16T12:00:00Z','ATIVO':'SIM'}

class Noticias330(unittest.TestCase):
    def test_webp_legado_nao_e_reconvertido(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);f=p/'foto.webp';Image.new('RGB',(300,200),'red').save(f);before=f.read_bytes()
            entrada=[{'imagens':[{'arquivo':'foto.webp','adaptativas':{'antigo':True}}]}]
            with patch.object(adaptive,'gerar',side_effect=AssertionError('Não converter legado')):adaptive.enriquecer(entrada,p)
            self.assertEqual(before,f.read_bytes());self.assertFalse((p/'adaptativas').exists());self.assertNotIn('adaptativas',entrada[0]['imagens'][0])

    def test_blog_estatico_seo_e_dados_privados_fora_do_site(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);secret=cfg();n=row();n['CORPO']+='<script>alert(1)</script>'
            items=noticias.construir(p,CONF,[n,dict(n,ID='n123456abcdee',SLUG='rascunho',STATUS='rascunho')],secret)
            self.assertEqual(len(items),1)
            text=(p/'noticias'/items[0]['codigo']/'index.html').read_text()
            self.assertIn('NewsArticle',text);self.assertIn('rel="canonical"',text);self.assertIn('data-push-scope="n123456abcdef"',text)
            self.assertNotIn('<script>alert(1)</script>',text);self.assertIn('&lt;script&gt;',text)
            for f in p.rglob('*'):
                if f.is_file():self.assertNotIn(secret['PRIVATE_JWK'],f.read_text())
            conf=json.loads((p/'noticias/push-config.json').read_text());self.assertTrue(conf['ativo']);self.assertNotIn('PRIVATE_JWK',conf)
            gerador.gravar_sitemap([],p,CONF);self.assertIn('/noticias/curiosidade-n123456abcdef/',(p/'sitemap.xml').read_text())
            self.assertIn('feed.xml',(p/'noticias/index.html').read_text())

    def test_retirada_e_troca_de_slug_sao_explicitas(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);n=row();items=noticias.construir(p,CONF,[n],{})
            old=p/'noticias'/items[0]['codigo']/'index.html'
            n['SLUG']='novo-endereco';items=noticias.construir(p,CONF,[n],{})
            self.assertIn('http-equiv="refresh"',old.read_text())
            target=p/'noticias'/items[0]['codigo']/'index.html';noticias.construir(p,CONF,[dict(n,STATUS='arquivado')],{});self.assertFalse(target.exists())

    def test_chaves_incompletas_desativam_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);noticias.construir(p,CONF,[],{'PUBLIC_KEY':cfg()['PUBLIC_KEY'],'URL_PUBLICA':'https://script.google.com/macros/s/TESTE/exec'})
            self.assertFalse(json.loads((p/'noticias/push-config.json').read_text())['ativo'])

    def test_notificacao_so_para_versao_publicada_e_deduplicada(self):
        _,_,s=sub();n=row();config=cfg();record=[];calls=[]
        live={'artigos':[noticias.artigo(n)]};snapshot={'artigos':[noticias.artigo(n)]}
        sender=lambda **kw:calls.append(kw)
        self.assertEqual(push.entregar([n],[s],[],{'artigos':[]},snapshot,config,CONF['urlPublica'],send=sender,record=lambda *x:record.append(x)),0)
        self.assertEqual(push.entregar([n],[s],[],live,snapshot,config,CONF['urlPublica'],send=sender,record=lambda *x:record.append(x)),1)
        self.assertEqual(len(calls),1);self.assertIn('/noticias/',json.loads(calls[0]['data'])['url'])
        ledger=[{'EVENTO_ID':record[0][0],'INSCRICAO_ID':record[0][1],'STATUS':'enviado'}]
        self.assertEqual(push.entregar([n],[s],ledger,live,snapshot,config,CONF['urlPublica'],send=sender,record=lambda *x:None),0)

    def test_cancelamento_tema_e_data_da_inscricao(self):
        _,_,s=sub();n=row();online={'artigos':[noticias.artigo(n)]};config=cfg()
        for changed in [dict(s,ATIVO='NAO'),dict(s,ESCOPOS='["n000000000000"]'),dict(s,CRIADO_EM='2026-11-17T00:00:00Z')]:
            self.assertEqual(push.entregar([n],[changed],[],online,online,config,CONF['urlPublica'],send=lambda **kw:self.fail('não deveria enviar')),0)

    def test_endpoint_privado_e_redirecionamentos_nao_sao_aceitos(self):
        for endpoint in ['http://fcm.googleapis.com/a','https://127.0.0.1/a','https://fcm.googleapis.com.evil.org/a','https://user@fcm.googleapis.com/a','https://fcm.googleapis.com:444/a']:
            self.assertFalse(push.endpoint_valido(endpoint))
        self.assertTrue(push.endpoint_valido('https://web.push.apple.com/TESTE'))

    def test_criptografia_webpush_real_sem_rede(self):
        receiver,auth,s=sub();n=row();config=cfg();captured={}
        class Session:
            def post(self,url,data,headers,**kwargs):
                captured['data']=data;captured['headers']=headers
                response=requests.Response();response.status_code=201;response._content=b'';return response
        def send(**kwargs):kwargs['requests_session']=Session();return webpush(**kwargs)
        online={'artigos':[noticias.artigo(n)]}
        self.assertEqual(push.entregar([n],[s],[],online,online,config,CONF['urlPublica'],send=send,record=lambda *x:None),1)
        decoded=http_ece.decrypt(captured['data'],private_key=receiver,auth_secret=auth,version='aes128gcm')
        self.assertEqual(json.loads(decoded)['title'],n['TITULO']);self.assertIn('authorization',{x.lower() for x in captured['headers']})
        self.assertNotIn(n['TITULO'].encode(),captured['data'])

    def test_assinatura_expirada_e_desativada(self):
        _,_,s=sub();s['_linha']=7;n=row();online={'artigos':[noticias.artigo(n)]};events=[];deactivated=[]
        def send(**kwargs):
            response=requests.Response();response.status_code=410;raise WebPushException('expired',response=response)
        self.assertEqual(push.entregar([n],[s],[],online,online,cfg(),CONF['urlPublica'],send=send,record=lambda *x:events.append(x),deactivate=deactivated.append),0)
        self.assertEqual(deactivated,[7]);self.assertEqual(events[0][-1],'expirado')

    @unittest.skipUnless((Path(__file__).resolve().parents[3]/'CORE').is_dir(),'CORE fora do repositório')
    def test_roteador_apps_script_real(self):
        import subprocess
        subprocess.run(['node',str(Path(__file__).with_name('test_push_core_node.js'))],check=True,capture_output=True,text=True)
