"""ImoPlace — HTML das páginas dos imóveis (layout do ImoPlace v2.1, sem dados de demonstração)."""
from midias import colecao, embed
from formatos_imagens import ordem_formatos
import html
import json
from urllib.parse import quote

RAIZ_REL = '../../'
# Permite ao Google exibir fotos grandes nos resultados e no Discover.
ROBOTS_INDEX = 'index,follow,max-image-preview:large'

# Tipo do imóvel no painel → tipo schema.org. Terreno não é moradia, então fica como Place.
TIPOS_SCHEMA = {'casa': 'SingleFamilyResidence', 'sobrado': 'SingleFamilyResidence',
                'apartamento': 'Apartment', 'terreno': 'Place'}


def h(v):
    return html.escape(str(v if v is not None else ''), quote=True)


def brl(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return 'R$ ' + f'{float(v):,.0f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return 'Sob consulta'


def local(item):
    x = item.get('localizacao') or {}
    return ', '.join(str(x[k]) for k in ('bairro', 'cidade', 'uf') if x.get(k))


def _galeria(item):
    fotos = item.get('imagens') or []
    if not fotos:
        return (f'<div class="gal single"><div class="ph main"><img src="{RAIZ_REL}assets/img/sem-imagem.svg" alt="Imagem indisponível" width="960" height="600">'
                '<span>Imagem indisponível</span></div></div>')
    botoes = []
    for k, f in enumerate(fotos[:5]):
        extra = f'<em>+{len(fotos) - 5} fotos</em>' if k == 4 and len(fotos) > 5 else ''
        botoes.append(
            f'<button class="ph{" main" if k == 0 else ""}" type="button" data-k="{k}" aria-label="{h(f.get("legenda") or "Foto")}">'
            f'{picture(f, item, k)}'
            f'<span>{h(f.get("legenda") or "Foto")}</span>{extra}</button>')
    return f'<div class="gal{" single" if len(fotos) == 1 else ""}" id="gal">{"".join(botoes)}</div>'


def detalhe(item):
    def m2(v):
        return f'{v} m²' if v is not None else None
    valores = [(item.get('dormitorios'), 'Dormitórios'), (item.get('suites'), 'Suítes'), (item.get('banheiros'), 'Banheiros'),
               (item.get('vagas'), 'Vagas'), (m2(item.get('areaTotal')), 'Área total'), (m2(item.get('areaUtil')), 'Área útil')]
    # Campo vazio não aparece (antes: "Não informado").
    stats = ''.join(f'<div><b>{h(v)}</b><span>{h(r)}</span></div>' for v, r in valores if v is not None)
    stats = f'<div class="stats">{stats}</div>' if stats else ''

    def coluna(titulo, arr):
        itens = ''.join(f'<li>{h(x)}</li>' for x in (arr or []))
        return f'<div><h4>{titulo}</h4><ul class="feat">{itens}</ul></div>' if itens else ''
    colunas = coluna('No imóvel', item.get('caracteristicasImovel')) + coluna('No condomínio', item.get('caracteristicasCondominio'))
    caracteristicas = f'<div class="box"><h3>Características</h3><div class="cols">{colunas}</div></div>' if colunas else ''
    anunc = item.get('anunciante') or {}
    zap = ''.join(c for c in str(anunc.get('whatsapp') or '') if c.isdigit())
    if len(zap) >= 10:
        texto = quote(f'Olá! Tenho interesse no imóvel {item["id"]} anunciado no Imoplace.')
        contato = f'<a class="btn btn-accent" id="whatsapp" href="https://wa.me/{zap}?text={texto}" target="_blank" rel="noopener noreferrer">Chamar no WhatsApp</a>'
        nota = 'Solicite mais informações diretamente ao anunciante.'
    else:
        contato = '<button class="btn btn-accent" disabled>Contato indisponível</button>'
        nota = ''
    creci = f'<span class="where">CRECI {h(anunc["creci"])}</span>' if anunc.get('creci') else ''
    endereco = (item.get('localizacao') or {}).get('endereco') or local(item)
    consulta_mapa = str(endereco or '').strip()
    mapa = (
        '<div class="map"><iframe title="Mapa da localização do imóvel" '
        'src="https://www.google.com/maps?q=' + h(quote(consulta_mapa + ', Brasil', safe='')) + '&amp;output=embed" '
        'loading="lazy" referrerpolicy="no-referrer-when-downgrade" '
        'allowfullscreen></iframe></div>'
    ) if consulta_mapa else ''
    m2preco = ''
    if isinstance(item.get('preco'), (int, float)) and item.get('areaTotal'):
        m2preco = f'<dt>Preço por m²</dt><dd>{brl(item["preco"] / item["areaTotal"])}</dd>'
    return f'''<a class="back" href="{RAIZ_REL}index.html#imoveis">← Voltar aos resultados</a>
{_galeria(item)}
{multimidia(item)}
<div class="dhead"><div><h1 class="dt">{h(item['titulo'])}</h1><div class="where">{h(item.get('tipo'))} · {h(local(item))}</div></div><div class="dr"><div class="price big">{brl(item.get('preco'))}</div></div></div>
<div class="dgrid dgrid-lead"><div class="imovel-info">
{stats}
<div class="box"><h3>Sobre o imóvel</h3><p style="white-space:pre-line">{h(item.get('descricao') or 'Descrição não cadastrada.')}</p></div>
{caracteristicas}
<div class="box"><h3>Valores</h3><dl class="vals"><dt>Preço</dt><dd>{brl(item.get('preco'))}</dd>{m2preco}<dt>Condomínio</dt><dd>{brl(item.get('condominio'))}</dd><dt>IPTU anual</dt><dd>{brl(item.get('iptuAnual'))}</dd></dl></div>
<div class="box"><h3>Localização</h3>{mapa}<div class="where">{h(endereco)}</div></div></div>
<div class="imovel-contato"><aside class="aside box"><div class="adv"><div class="av">I</div><div><b>{h(anunc.get('nome') or 'Imoplace')}</b>{creci}</div></div>{f'<p class="small-note">{h(nota)}</p>' if nota else ''}{contato}<div class="ref">Código do imóvel: {h(item['id'])}</div></aside><div class="box imoplace-lead" data-lead-property="{h(item['id'])}" hidden></div></div></div>'''


def _numero(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
        return None
    return int(v) if float(v).is_integer() else v


def dados_estruturados(item, conf, url, descricao):
    """JSON-LD do anúncio: RealEstateListing (a página) + o imóvel em si + trilha de navegação."""
    base = conf['urlPublica']
    loc = item.get('localizacao') or {}
    fotos = [f'{base}/{imagem_seo(f)}' for f in (item.get('imagens') or [])]
    tipo = TIPOS_SCHEMA.get(str(item.get('tipo') or '').strip().lower(), 'Accommodation')
    endereco = {'@type': 'PostalAddress', 'addressLocality': loc.get('cidade'), 'addressRegion': loc.get('uf'),
                'addressCountry': 'BR'}
    imovel = {'@type': tipo, 'name': item['titulo'], 'address': {k: v for k, v in endereco.items() if v}}
    if fotos:
        imovel['image'] = fotos
    lat, lng = loc.get('lat'), loc.get('lng')
    if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
        imovel['geo'] = {'@type': 'GeoCoordinates', 'latitude': lat, 'longitude': lng}
    if tipo != 'Place':
        for campo, prop in (('dormitorios', 'numberOfBedrooms'), ('banheiros', 'numberOfBathroomsTotal')):
            if _numero(item.get(campo)) is not None:
                imovel[prop] = _numero(item.get(campo))
        area = _numero(item.get('areaUtil')) or _numero(item.get('areaTotal'))
        if area is not None:
            imovel['floorSize'] = {'@type': 'QuantitativeValue', 'value': area, 'unitCode': 'MTK'}
    anuncio = {'@type': 'RealEstateListing', '@id': url + '#anuncio', 'url': url, 'name': item['titulo'],
               'description': descricao, 'inLanguage': 'pt-BR', 'mainEntity': imovel}
    if fotos:
        anuncio['image'] = fotos
    if item.get('atualizadoEm'):
        anuncio['dateModified'] = item['atualizadoEm']
    preco = _numero(item.get('preco'))
    if preco is not None:
        anunc = item.get('anunciante') or {}
        oferta = {'@type': 'Offer', 'price': preco, 'priceCurrency': 'BRL', 'url': url,
                  'availability': 'https://schema.org/InStock'}
        if anunc.get('nome'):
            oferta['seller'] = {'@type': 'RealEstateAgent' if anunc.get('creci') else 'Person', 'name': anunc['nome']}
        anuncio['offers'] = oferta
    trilha = {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Início', 'item': base + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': item['titulo'], 'item': url}]}
    return {'@context': 'https://schema.org', '@graph': [anuncio, trilha]}


def pagina(item, conf):
    base = conf['urlPublica']
    url = f'{base}/imoveis/{item["codigo"]}/'
    seo = item.get('seo') or {}
    titulo = f'{seo.get("titulo") or item["titulo"]} | {conf["nome"]}'
    descricao = (seo.get('descricao') or item.get('descricao') or f'{item.get("tipo", "")} em {local(item)}').strip()[:160]
    indexar = conf['permitirIndexacao']
    fotos = item.get('imagens') or []
    og = f'\n<meta property="og:image" content="{h(base + "/" + imagem_social(fotos[0]))}">' if fotos else ''
    ld = json.dumps(dados_estruturados(item, conf, url, descricao), ensure_ascii=False).replace('<', '\\u003c')
    return f'''<!doctype html>
<html lang="pt-BR" data-root="{RAIZ_REL}" data-codigo="{h(item['codigo'])}">
<head>
<meta charset="utf-8">
<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{h(titulo)}</title>
<meta name="description" content="{h(descricao)}">
<meta name="robots" content="{ROBOTS_INDEX if indexar else 'noindex,follow'}">
<link rel="canonical" href="{h(url)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{h(url)}">
<meta property="og:title" content="{h(titulo)}">
<meta property="og:description" content="{h(descricao)}">{og}
<meta name="twitter:card" content="summary_large_image">
{social_tags(fotos,base)}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700;800&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{RAIZ_REL}assets/css/style.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<header class="bar"><div class="wrap">
<a href="{RAIZ_REL}index.html" class="logo" aria-label="Imoplace, página inicial"><img src="{RAIZ_REL}assets/img/logo.png" alt="" width="50" height="44"><span>Imoplace</span></a>
<nav aria-label="Principal"><a href="{RAIZ_REL}noticias/">Notícias</a><a href="{RAIZ_REL}index.html#imoveis">Comprar</a><a href="{RAIZ_REL}index.html?categoria=lancamento#imoveis">Lançamentos</a></nav>
<div class="actions"><a class="btn btn-accent" href="{RAIZ_REL}anunciar/">Anuncie seu imóvel</a></div>
</div></header>
<main class="wrap" id="det">{detalhe(item)}</main>
<footer><div class="wrap"><span>© {h(conf.get('ano', '2026'))} Imoplace · imoplace.com.br</span><span>Informações sujeitas a confirmação com o anunciante.</span></div></footer>
<script src="{RAIZ_REL}assets/js/protecao.js"></script>
<script src="{RAIZ_REL}assets/js/main.js"></script>
<script src="{RAIZ_REL}assets/js/midias.js"></script>
<span id="monitor-imovel" data-imovel="{h(item['id'])}" hidden></span>
<script src="{RAIZ_REL}assets/js/imovel-lead.js"></script>
<script src="{RAIZ_REL}assets/js/imovel.js"></script>
</body></html>
'''


def redirecionamento(destino_rel: str, conf) -> str:
    """Página antiga (slug ou categoria mudou) → nova URL, sem perder quem tinha o link."""
    url = f'{conf["urlPublica"]}/{destino_rel}'
    return f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Imóvel mudou de endereço</title>
<meta name="robots" content="noindex,follow"><link rel="canonical" href="{h(url)}">
<meta http-equiv="refresh" content="0; url={h(url)}"></head>
<body><p>Este imóvel mudou de endereço: <a href="{h(url)}">{h(url)}</a></p></body></html>
'''


def picture(f,item,k):
    data=f.get('adaptativas') or {};fmts=data.get('formatos') or {}
    fallback=fmts.get('jpg') or fmts.get('png') or []
    src=RAIZ_REL+(fallback[-1]['arquivo'] if fallback else f['arquivo'])
    sources=''.join('<source type="'+rows[0]['mime']+'" srcset="'+h(', '.join(RAIZ_REL+x['arquivo']+' '+str(x['largura'])+'w' for x in rows))+'" sizes="(max-width: 768px) 100vw, 60vw">' for ext in ordem_formatos(fmts,data.get('preferido','webp')) for rows in [fmts[ext]])
    srcset=' srcset="'+h(', '.join(RAIZ_REL+x['arquivo']+' '+str(x['largura'])+'w' for x in fallback))+'" sizes="(max-width: 768px) 100vw, 60vw"' if fallback else ''
    return '<picture>'+sources+'<img src="'+h(src)+'"'+srcset+' width="'+str(data.get('largura',960))+'" height="'+str(data.get('altura',600))+'" alt="'+h(f.get('alt') or item['titulo'])+'" loading="'+('eager' if k==0 else 'lazy')+'" '+('fetchpriority="high" ' if k==0 else '')+'decoding="async"></picture>'


def multimidia(item):
    medias=colecao(item.get('midias')); links=colecao(item.get('links_externos'),links=True)
    cards=[]
    for x in medias:
        target=embed(x['url']);action=''
        if target: action='<button type="button" class="btn btn-line" data-embed="'+h(target)+'">Carregar player</button>'
        elif x['tipo']=='panorama_360': action='<button type="button" class="btn btn-line" data-panorama="'+h(x['url'])+'">Explorar em 360°</button>'
        cards.append('<article class="midia-card"><h3>'+h(x['titulo'])+'</h3><p>'+h(x['descricao'])+'</p>'+action+' <a href="'+h(x['url'])+'" target="_blank" rel="noopener noreferrer">Abrir em nova aba ↗</a><div data-player></div></article>')
    result='<section class="box" aria-label="Vídeos e tours"><h2>Vídeos e tours</h2>'+''.join(cards)+'</section>' if cards else ''
    if links:
        result+='<button class="btn btn-line" type="button" data-open-links>Mais links ↗</button><dialog id="external-links" aria-labelledby="links-title"><h2 id="links-title">Acessos externos</h2><button type="button" class="btn btn-line" data-close-links>Fechar ✕</button>'+''.join('<p><a href="'+h(x['url'])+'" target="_blank" rel="noopener noreferrer">'+h(x['titulo'])+' ↗</a><br>'+h(x['descricao'])+'</p>' for x in links)+'</dialog>'
    return '<div id="multimidia">'+result+'</div>'


def imagem_seo(f):
    formats=(f.get('adaptativas') or {}).get('formatos') or {}
    rows=formats.get('jpg') or formats.get('png') or []
    return rows[-1]['arquivo'] if rows else f['arquivo']


def imagem_social(f):
    return ((f.get('adaptativas') or {}).get('social') or {}).get('arquivo') or imagem_seo(f)


def social_tags(fotos,base):
    if not fotos:return ''
    social=(fotos[0].get('adaptativas') or {}).get('social') or {}
    url=h(base+'/'+imagem_social(fotos[0]))
    tags=f'<meta name="twitter:image" content="{url}">\n<meta property="og:image:alt" content="{h(fotos[0].get("alt") or "Imóvel")}">'
    if social:tags+='\n<meta property="og:image:type" content="image/jpeg">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">'
    return tags
