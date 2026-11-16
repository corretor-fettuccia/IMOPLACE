"""Validação independente das células; somente provedores conhecidos são incorporados."""
import json
from urllib.parse import urlsplit, parse_qs

def url_segura(value):
    try:
        u=urlsplit(str(value or ''))
        return str(value) if u.scheme=='https' and u.hostname and not u.username and not u.password and not any(c.isspace() or c in '\\<>"\'' for c in str(value)) else ''
    except ValueError:
        return ''

def colecao(value, links=False):
    try:
        items=json.loads(value or '[]') if isinstance(value,str) else value or []
        if not isinstance(items,list): return []
        out=[]
        for i,x in enumerate(items[:40]):
            if not isinstance(x,dict) or not url_segura(x.get('url')): continue
            if x.get('visivel') is False or str(x.get('visivel','')).upper()=='NAO': continue
            tipo='site_externo' if links else x.get('tipo','video')
            if not links and tipo not in ('video','video_360','tour_virtual','panorama_360','planta'): continue
            try: ordem=float(x.get('ordem',i))
            except (ValueError,TypeError): ordem=i
            out.append(dict(tipo=tipo,url=x['url'],titulo=str(x.get('titulo') or 'Ver conteúdo')[:120],descricao=str(x.get('descricao') or '')[:300],ordem=ordem,visivel=True))
        return sorted(out,key=lambda x:x['ordem'])
    except (ValueError,TypeError): return []

def embed(value):
    import re
    if not url_segura(value): return ''
    u=urlsplit(value);host=u.hostname
    if host in ('youtube.com','www.youtube.com','m.youtube.com','youtu.be'):
        ident=u.path.strip('/') if host=='youtu.be' else (parse_qs(u.query).get('v',[''])[0] if u.path=='/watch' else u.path.split('/')[-1])
        if re.fullmatch(r'[A-Za-z0-9_-]{11}',ident): return 'https://www.youtube-nocookie.com/embed/'+ident
    if host in ('vimeo.com','www.vimeo.com','player.vimeo.com') and u.path.split('/')[-1].isdigit():
        return 'https://player.vimeo.com/video/'+u.path.split('/')[-1]
    if host=='my.matterport.com' and u.path=='/show/' and re.fullmatch(r'[A-Za-z0-9]+',parse_qs(u.query).get('m',[''])[0]):
        return 'https://my.matterport.com/show/?m='+parse_qs(u.query)['m'][0]
    return ''
