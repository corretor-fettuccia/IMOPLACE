"""Validação independente das células e decisão de como cada mídia é renderizada.

4.3.1: qualquer URL HTTPS vira iframe renderizado direto na página (exceto o próprio
domínio); links de arquivo de vídeo tocam no player nativo; YouTube/Vimeo/Matterport
continuam convertidos para o player oficial. A planilha guarda só URL, nunca HTML.
"""
import html as _html
import json
import re
from urllib.parse import urlsplit, parse_qs, urlencode, urlunsplit, parse_qsl

TIPOS = ('iframe', 'video', 'video_360', 'tour_virtual', 'panorama_360', 'planta')
EXT_VIDEO = ('.mp4', '.webm', '.ogv', '.ogg', '.mov', '.m4v')
EXT_IMAGEM = ('.jpg', '.jpeg', '.png', '.webp', '.avif')
PRESETS = ('16/9', '4/3', '1/1', '9/16', '2/1', '21/9', '3/4')
DOMINIOS_PROPRIOS = ('imoplace.com.br',)
SANDBOX = 'allow-scripts allow-same-origin allow-presentation allow-popups allow-popups-to-escape-sandbox allow-forms'
ALLOW = 'autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture; web-share; accelerometer; gyroscope; xr-spatial-tracking'


def url_segura(value):
    try:
        u=urlsplit(str(value or ''))
        return str(value) if u.scheme=='https' and u.hostname and not u.username and not u.password and not any(c.isspace() or c in '\\<>"\'' for c in str(value)) else ''
    except ValueError:
        return ''


def extrair_iframe(value):
    """Aceita a URL ou o código <iframe ...> colado; devolve (url, proporcao)."""
    s=str(value or '').strip()
    if '<' not in s: return s, ''
    m=re.search(r'<iframe\b[^>]*?\ssrc\s*=\s*(["\'])(.*?)\1', s, re.I | re.S)
    if not m: return '', ''
    url=_html.unescape(m.group(2)).strip()
    w=re.search(r'\swidth\s*=\s*["\']?(\d{2,4})["\']?(?=[\s>/])', s, re.I)
    hh=re.search(r'\sheight\s*=\s*["\']?(\d{2,4})["\']?(?=[\s>/])', s, re.I)
    return url, (f'{int(w.group(1))}/{int(hh.group(1))}' if w and hh else '')


def proporcao_valida(value):
    m=re.fullmatch(r'\s*(\d{1,4})\s*[/:x×]\s*(\d{1,4})\s*', str(value or ''))
    if not m or not int(m.group(1)) or not int(m.group(2)): return ''
    return f'{int(m.group(1))}/{int(m.group(2))}'


def colecao(value, links=False):
    try:
        items=json.loads(value or '[]') if isinstance(value,str) else value or []
        if not isinstance(items,list): return []
        out=[]
        for i,x in enumerate(items[:40]):
            if not isinstance(x,dict): continue
            url,prop=extrair_iframe(x.get('url'))
            if not url_segura(url): continue
            if x.get('visivel') is False or str(x.get('visivel','')).upper()=='NAO': continue
            tipo='site_externo' if links else x.get('tipo','video')
            if not links and tipo not in TIPOS: continue
            try: ordem=float(x.get('ordem',i))
            except (ValueError,TypeError): ordem=i
            item=dict(tipo=tipo,url=url,titulo=str(x.get('titulo') or 'Ver conteúdo')[:120],descricao=str(x.get('descricao') or '')[:300],ordem=ordem,visivel=True)
            if not links:
                item['proporcao']=proporcao_valida(x.get('proporcao')) or prop
                item['capa']=url_segura(x.get('capa'))
            out.append(item)
        return sorted(out,key=lambda x:x['ordem'])
    except (ValueError,TypeError): return []


def embed(value):
    if not url_segura(value): return ''
    u=urlsplit(value);host=u.hostname
    if host in ('youtube.com','www.youtube.com','m.youtube.com','youtu.be','www.youtube-nocookie.com'):
        ident=u.path.strip('/') if host=='youtu.be' else (parse_qs(u.query).get('v',[''])[0] if u.path=='/watch' else u.path.split('/')[-1])
        if re.fullmatch(r'[A-Za-z0-9_-]{11}',ident): return 'https://www.youtube-nocookie.com/embed/'+ident
    if host in ('vimeo.com','www.vimeo.com','player.vimeo.com') and u.path.split('/')[-1].isdigit():
        return 'https://player.vimeo.com/video/'+u.path.split('/')[-1]
    if host=='my.matterport.com' and u.path=='/show/' and re.fullmatch(r'[A-Za-z0-9]+',parse_qs(u.query).get('m',[''])[0]):
        return 'https://my.matterport.com/show/?m='+parse_qs(u.query)['m'][0]
    return ''


def proprio(url, extras=()):
    host=(urlsplit(url).hostname or '').lower()
    return any(host==d or host.endswith('.'+d) for d in tuple(DOMINIOS_PROPRIOS)+tuple(extras) if d)


def alvo(x, extras=()):
    """Decide a renderização: ('iframe'|'video'|'panorama'|'imagem'|'link', src, proporcao)."""
    url=url_segura(x.get('url'))
    if not url: return ('link','','')
    caminho=urlsplit(url).path.lower();prop=proporcao_valida(x.get('proporcao'))
    oficial=embed(url)
    if oficial: return ('iframe',oficial,prop or '16/9')
    if caminho.endswith(EXT_VIDEO): return ('video',url,prop or '16/9')
    if caminho.endswith(EXT_IMAGEM):
        if x.get('tipo')=='panorama_360': return ('panorama',url,'2/1')
        return ('imagem',url,prop)
    if proprio(url, extras): return ('link',url,'')
    url,prop=facebook(url,prop)
    return ('iframe',url,prop or ('2/1' if x.get('tipo')=='panorama_360' else '16/9'))


def facebook(url, prop):
    """Plugin do Facebook sem width/height: fixa width na URL (padrão 500) e o tamanho em 16:9, para esticar no quadro."""
    u=urlsplit(url)
    if (u.hostname or '') not in ('www.facebook.com','facebook.com','web.facebook.com') or not u.path.startswith('/plugins/') or pixels(prop): return url,prop
    q=parse_qsl(u.query,keep_blank_values=True)
    try: w=int(dict(q).get('width') or 500)
    except ValueError: w=500
    w=min(max(w,200),750)
    q=[(k,v) for k,v in q if k not in ('width','height')]+[('width',str(w))]
    return urlunsplit((u.scheme,u.netloc,u.path,urlencode(q),u.fragment)),f'{w}/{int(w*9/16+0.5)}'


def pixels(prop):
    """Formato vindo de width/height de um <iframe> colado (não é preset): (largura, altura) em px."""
    if not prop or prop in PRESETS: return None
    w,hh=(int(x) for x in prop.split('/'))
    return (w,hh) if 80<=w<=1400 and 50<=hh<=2000 else None


def estilo(prop):
    """Todo quadro tem o mesmo tamanho padrão (16:9, no CSS); o conteúdo se ajusta dentro dele."""
    return ''
