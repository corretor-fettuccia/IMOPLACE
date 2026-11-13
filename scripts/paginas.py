"""ImoPlace — HTML das páginas dos imóveis (layout do ImoPlace v2.1, sem dados de demonstração)."""
import html
import json
from urllib.parse import quote

RAIZ_REL = '../../'


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
            f'<img loading="{"eager" if k == 0 else "lazy"}" decoding="async" width="960" height="600" src="{RAIZ_REL}{h(f["arquivo"])}" alt="{h(f.get("alt") or item["titulo"])}">'
            f'<span>{h(f.get("legenda") or "Foto")}</span>{extra}</button>')
    return f'<div class="gal{" single" if len(fotos) == 1 else ""}" id="gal">{"".join(botoes)}</div>'


def detalhe(item):
    def m2(v):
        return f'{v} m²' if v is not None else None
    valores = [(item.get('dormitorios'), 'Dormitórios'), (item.get('suites'), 'Suítes'), (item.get('banheiros'), 'Banheiros'),
               (item.get('vagas'), 'Vagas'), (m2(item.get('areaTotal')), 'Área total'), (m2(item.get('areaUtil')), 'Área útil')]
    stats = ''.join(f'<div><b>{h(v if v is not None else "Não informado")}</b><span>{h(r)}</span></div>' for v, r in valores)

    def lista(arr):
        return ''.join(f'<li>{h(x)}</li>' for x in (arr or [])) or '<li>Não informado</li>'
    anunc = item.get('anunciante') or {}
    zap = ''.join(c for c in str(anunc.get('whatsapp') or '') if c.isdigit())
    if len(zap) >= 10:
        texto = quote(f'Olá! Tenho interesse no imóvel {item["id"]} anunciado no Imoplace.')
        contato = f'<a class="btn btn-accent" id="whatsapp" href="https://wa.me/{zap}?text={texto}" target="_blank" rel="noopener noreferrer">Chamar no WhatsApp</a>'
        nota = 'Solicite mais informações diretamente ao anunciante.'
    else:
        contato = '<button class="btn btn-accent" disabled>Contato indisponível</button>'
        nota = 'Contato não informado para este anúncio.'
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
<div class="dhead"><div><h1 class="dt">{h(item['titulo'])}</h1><div class="where">{h(item.get('tipo'))} · {h(local(item))}</div></div><div class="dr"><div class="price big">{brl(item.get('preco'))}</div></div></div>
<div class="dgrid"><div>
<div class="stats">{stats}</div>
<div class="box"><h3>Sobre o imóvel</h3><p style="white-space:pre-line">{h(item.get('descricao') or 'Descrição não cadastrada.')}</p></div>
<div class="box"><h3>Características</h3><div class="cols"><div><h4>No imóvel</h4><ul class="feat">{lista(item.get('caracteristicasImovel'))}</ul></div><div><h4>No condomínio</h4><ul class="feat">{lista(item.get('caracteristicasCondominio'))}</ul></div></div></div>
<div class="box"><h3>Valores</h3><dl class="vals"><dt>Preço</dt><dd>{brl(item.get('preco'))}</dd>{m2preco}<dt>Condomínio</dt><dd>{brl(item.get('condominio'))}</dd><dt>IPTU anual</dt><dd>{brl(item.get('iptuAnual'))}</dd></dl></div>
<div class="box"><h3>Localização</h3>{mapa}<div class="where">{h(endereco)}</div></div></div>
<aside class="aside box"><div class="adv"><div class="av">I</div><div><b>{h(anunc.get('nome') or 'Imoplace')}</b>{creci}</div></div><p class="small-note">{h(nota)}</p>{contato}<div class="ref">Código do imóvel: {h(item['id'])}</div></aside></div>'''


def pagina(item, conf):
    base = conf['urlPublica']
    url = f'{base}/imoveis/{item["codigo"]}/'
    seo = item.get('seo') or {}
    titulo = f'{seo.get("titulo") or item["titulo"]} | {conf["nome"]}'
    descricao = (seo.get('descricao') or item.get('descricao') or f'{item.get("tipo", "")} em {local(item)}').strip()[:160]
    indexar = conf['permitirIndexacao']
    fotos = item.get('imagens') or []
    og = f'\n<meta property="og:image" content="{h(base + "/" + fotos[0]["arquivo"])}">' if fotos else ''
    schema = {
        '@context': 'https://schema.org', '@type': 'RealEstateListing', 'name': item['titulo'], 'description': descricao,
        'url': url, 'image': [f'{base}/{f["arquivo"]}' for f in fotos], 'dateModified': item.get('atualizadoEm') or None,
        'offers': {'@type': 'Offer', 'priceCurrency': 'BRL', 'price': item.get('preco'), 'availability': 'https://schema.org/InStock'},
        'address': {'@type': 'PostalAddress', 'addressLocality': (item.get('localizacao') or {}).get('cidade', ''),
                    'addressRegion': (item.get('localizacao') or {}).get('uf', ''), 'addressCountry': 'BR'},
    }
    ld = json.dumps({k: v for k, v in schema.items() if v is not None}, ensure_ascii=False).replace('<', '\\u003c')
    return f'''<!doctype html>
<html lang="pt-BR" data-root="{RAIZ_REL}" data-codigo="{h(item['codigo'])}">
<head>
<meta charset="utf-8">
<link rel="icon" type="image/png" href="{RAIZ_REL}icon.png">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{h(titulo)}</title>
<meta name="description" content="{h(descricao)}">
<meta name="robots" content="{'index,follow' if indexar else 'noindex,follow'}">
<link rel="canonical" href="{h(url)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{h(url)}">
<meta property="og:title" content="{h(titulo)}">
<meta property="og:description" content="{h(descricao)}">{og}
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700;800&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{RAIZ_REL}assets/css/style.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<header class="bar"><div class="wrap">
<a href="{RAIZ_REL}index.html" class="logo" aria-label="Imoplace, página inicial"><img src="{RAIZ_REL}assets/img/logo.png" alt="" width="50" height="44"><span>Imoplace</span></a>
<nav aria-label="Principal"><a href="{RAIZ_REL}index.html#imoveis">Comprar</a><a href="{RAIZ_REL}index.html?categoria=lancamento#imoveis">Lançamentos</a></nav>
<div class="actions"><a class="btn btn-accent" href="{RAIZ_REL}anunciar/">Anuncie seu imóvel</a></div>
</div></header>
<main class="wrap" id="det">{detalhe(item)}</main>
<footer><div class="wrap"><span>© {h(conf.get('ano', '2026'))} Imoplace · imoplace.com.br</span><span>Informações sujeitas a confirmação com o anunciante.</span></div></footer>
<script src="{RAIZ_REL}assets/js/main.js"></script>
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
