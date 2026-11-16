"""Entrega Web Push apenas após conferir a versão da notícia no site publicado."""
import base64,hashlib,json,os,re,time
from datetime import datetime,timezone
from urllib.parse import quote,urlsplit
from urllib.request import Request,urlopen
from cryptography.hazmat.primitives.asymmetric import ec
from py_vapid import Vapid
import requests
from pywebpush import webpush,WebPushException
from comum import config,estado_dir,ler_json,log
from core_google import _request,_sheet_id,API
from noticias import tabela,push_config,artigo

ALLOWED={'fcm.googleapis.com','android.googleapis.com','updates.push.services.mozilla.com','web.push.apple.com'}

def endpoint_valido(endpoint):
    try:
        u=urlsplit(endpoint)
        return u.scheme=='https' and not u.username and not u.password and u.port in (None,443) and (u.hostname in ALLOWED or bool(re.fullmatch(r'[a-z0-9-]+\.notify\.windows\.com',u.hostname or ''))) and len(endpoint)<=2048
    except (ValueError,TypeError):return False

def b64(value):return base64.urlsafe_b64decode(value+'='*((4-len(value)%4)%4))
def vapid_key(cfg):
    key=json.loads(cfg['PRIVATE_JWK']);private=ec.derive_private_key(int.from_bytes(b64(key['d']),'big'),ec.SECP256R1())
    numbers=private.public_key().public_numbers()
    if numbers.x!=int.from_bytes(b64(key['x']),'big') or numbers.y!=int.from_bytes(b64(key['y']),'big'):raise ValueError('Par de chaves inválido')
    expected=b'\x04'+numbers.x.to_bytes(32,'big')+numbers.y.to_bytes(32,'big')
    if b64(cfg['PUBLIC_KEY'])!=expected:raise ValueError('Chave pública diferente da privada')
    return Vapid(private_key=private)

class NoRedirect(requests.Session):
    def post(self,*args,**kwargs):kwargs['allow_redirects']=False;return super().post(*args,**kwargs)

def append_delivery(event,sub,status):
    url=f'{API}/{_sheet_id()}/values/{quote("PUSH_ENTREGAS!A:D",safe="")}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS'
    _request(url,method='POST',body={'values':[[event,sub,status,datetime.now(timezone.utc).isoformat()]]})

def live_news(base):
    request=Request(base+'/noticias/catalogo.json?publicacao='+quote(os.environ.get('GITHUB_RUN_ID','manual')),headers={'Cache-Control':'no-cache'})
    with urlopen(request,timeout=25) as response:return json.loads(response.read(5_000_000))

def timestamp(value):
    try:return datetime.fromisoformat(str(value).replace('Z','+00:00')).astimezone(timezone.utc)
    except (ValueError,TypeError):return None

def entregar(rows,subs,ledger,live,snapshot,cfg,base,send=webpush,record=append_delivery,deactivate=None,limit=100):
    key=vapid_key(cfg);done={(x.get('EVENTO_ID'),x.get('INSCRICAO_ID')) for x in ledger if x.get('STATUS') in ('enviado','expirado')}
    online={x['id']:x for x in live.get('artigos',[])};built={x['id']:x['versao'] for x in snapshot.get('artigos',[])};sent=0;attempted=0
    session=NoRedirect()
    for row in rows:
        n=artigo(row)
        if not n or not n['notificar']:continue
        event=n['id']+':'+str(n['versao']);public=online.get(n['id'])
        if not public or public.get('versao')!=n['versao'] or built.get(n['id'])!=n['versao']:continue
        if any(public.get(k)!=n[k] for k in ('codigo','titulo','resumo')):continue
        url=base+'/noticias/'+n['codigo']+'/'
        payload=json.dumps({'title':n['titulo'][:100],'body':n['resumo'][:200],'url':url,'tag':'noticia-'+n['id']},ensure_ascii=False)
        for idx,sub in enumerate(subs,2):
            if attempted>=limit:return sent
            if str(sub.get('ATIVO'))!='SIM' or (event,sub.get('ID')) in done:continue
            try:scopes=json.loads(sub.get('ESCOPOS') or '[]')
            except (ValueError,TypeError):continue
            if '*' not in scopes and n['id'] not in scopes:continue
            created=timestamp(sub.get('CRIADO_EM'));updated=timestamp(n['atualizadoEm'])
            if not created or not updated or updated<created:continue
            if not endpoint_valido(sub.get('ENDPOINT')):continue
            info={'endpoint':sub['ENDPOINT'],'keys':{'p256dh':sub.get('P256DH'),'auth':sub.get('AUTH')}}
            attempted+=1
            try:
                response=send(subscription_info=info,data=payload,vapid_private_key=key,vapid_claims={'sub':cfg.get('CONTATO') or 'mailto:contato@imoplace.com.br'},ttl=86400,timeout=15,headers={'Topic':hashlib.sha256(event.encode()).hexdigest()[:32]},requests_session=session)
                code=getattr(response,'status_code',201)
                if not 200<=code<300:continue
                record(event,sub['ID'],'enviado');done.add((event,sub['ID']));sent+=1
            except WebPushException as exc:
                code=getattr(exc.response,'status_code',0)
                if code in (404,410):
                    record(event,sub['ID'],'expirado');done.add((event,sub['ID']))
                    if deactivate:deactivate(int(sub.get('_linha') or idx))
                log('push','Assinatura expirada.' if code in (404,410) else 'Falha temporária no serviço de avisos; nova tentativa em publicação futura.')
            except requests.RequestException:log('push','Serviço de avisos temporariamente indisponível.')
            except (ValueError,TypeError):
                record(event,sub['ID'],'expirado')
                if deactivate:deactivate(int(sub.get('_linha') or idx))
                log('push','Assinatura inválida desativada.')
    return sent

def desativar(linha):
    url=f'{API}/{_sheet_id()}/values/{quote("PUSH_INSCRICOES!G"+str(linha),safe="")}?valueInputOption=RAW'
    _request(url,method='PUT',body={'values':[['NAO']]})

def main():
    cfg=push_config();snapshot=ler_json(estado_dir()/'noticias-publicadas.json',{}) or {}
    if not cfg.get('PRIVATE_JWK') or not snapshot.get('artigos'):log('push','Nenhum aviso pendente para envio.');return
    rows=tabela('NOTICIAS') or [];subs=tabela('PUSH_INSCRICOES') or [];ledger=tabela('PUSH_ENTREGAS') or []
    live=live_news(config()['urlPublica'])
    sent=entregar(rows,subs,ledger,live,snapshot,cfg,config()['urlPublica'],deactivate=desativar)
    log('push',str(sent)+' aviso(s) aceito(s) pelo serviço de notificações.')

if __name__=='__main__':main()
