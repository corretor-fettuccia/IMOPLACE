"""ImoPlace — HTML das páginas dos imóveis (layout do ImoPlace v2.1, sem dados de demonstração)."""
from midias import colecao, alvo, estilo, pixels, ALLOW, SANDBOX
from formatos_imagens import ordem_formatos
import hashlib
import html
import json
from pathlib import Path
from urllib.parse import quote

RAIZ_REL = '../../'
SITE = Path(__file__).resolve().parent.parent / 'site'


def ativo(rel):
    """Endereço do arquivo com a versão (hash do conteúdo): cada publicação força o navegador e a CDN a baixar o novo."""
    try: v = hashlib.sha256((SITE / rel).read_bytes()).hexdigest()[:10]
    except OSError: return RAIZ_REL + rel
    return f'{RAIZ_REL}{rel}?v={v}'
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


ICONES = {
    'dormitorios': 'M2 18V6M2 14h20v4M22 14v-2a3 3 0 0 0-3-3h-8v5M6 11.5a1.5 1.5 0 1 0 0-.01',
    'suites': 'M5 21V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v17M3 21h18M14 12h.01',
    'banheiros': 'M4 12h16v3a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5zM6 12V5a2 2 0 0 1 4 0M7 20l-1 2M17 20l1 2',
    'vagas': 'M5 16h14M6 16l1.5-5h9L18 16M5 16v3M19 16v3',
    'area': 'M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7',
}
TIPO_ICONES = {
    'casa': 'M3 11l9-7 9 7M5 9.5V20h14V9.5M10 20v-5h4v5',
    'apartamento': 'M5 21V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v17M3 21h18M9 7h1M14 7h1M9 11h1M14 11h1M9 15h1M14 15h1',
    'terreno': 'M3 7V3h4M17 3h4v4M21 17v4h-4M7 21H3v-4M10 16V8l6 2.5-6 2.5',
    'sobrado': 'M4 21V10l8-7 8 7v11M2 21h20M9 21v-4h6v4M9 10h1M14 10h1',
    'cobertura': 'M6 21V9h12v12M4 21h16M4 9h16M8 9V6h8v3M10 13h1M13 13h1M10 17h1M13 17h1',
    'studio': 'M4 11V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3M2 13a2 2 0 0 1 4 0v2h12v-2a2 2 0 0 1 4 0v4H2zM5 17v2M19 17v2',
    'comercial': 'M3 9l2-5h14l2 5M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0M5 12v9h14v-9M10 21v-5h4v5',
}
TIPO_SINONIMOS = {'estudio': 'studio', 'stúdio': 'studio', 'kitnet': 'studio', 'loja': 'comercial', 'sala': 'comercial', 'sala comercial': 'comercial', 'lote': 'terreno'}
FAIXA_ICONES = {'local': 'M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21zM12 7.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4z'}
CATEGORIAS = {'venda': 'Venda', 'lancamento': 'Lançamento', 'aluguel': 'Aluguel', 'locacao': 'Locação'}
# Logo do WhatsApp do botão flutuante: ícone 'fab fa-whatsapp' do Font Awesome Free 6.7.2 (CC BY 4.0), embutido sem carregar a biblioteca.
ZAP_FAB = '<svg class="zap-ico" width="30" height="30" viewBox="0 0 448 512" fill="currentColor" aria-hidden="true"><path d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222 0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157zm-157 341.6c-33.2 0-65.7-8.9-94-25.7l-6.7-4-69.8 18.3L72 359.2l-4.4-7c-18.5-29.4-28.2-63.3-28.2-98.2 0-101.7 82.8-184.5 184.6-184.5 49.3 0 95.6 19.2 130.4 54.1 34.8 34.9 56.2 81.2 56.1 130.5 0 101.8-84.9 184.6-186.6 184.6zm101.2-138.2c-5.5-2.8-32.8-16.2-37.9-18-5.1-1.9-8.8-2.8-12.5 2.8-3.7 5.6-14.3 18-17.6 21.8-3.2 3.7-6.5 4.2-12 1.4-32.6-16.3-54-29.1-75.5-66-5.7-9.8 5.7-9.1 16.3-30.3 1.8-3.7.9-6.9-.5-9.7-1.4-2.8-12.5-30.1-17.1-41.2-4.5-10.8-9.1-9.3-12.5-9.5-3.2-.2-6.9-.2-10.6-.2-3.7 0-9.7 1.4-14.8 6.9-5.1 5.6-19.4 19-19.4 46.3 0 27.3 19.9 53.7 22.6 57.4 2.8 3.7 39.1 59.7 94.8 83.8 35.2 15.2 49 16.5 66.6 13.9 10.7-1.6 32.8-13.4 37.4-26.4 4.6-13 4.6-24.1 3.2-26.4-1.3-2.5-5-3.9-10.5-6.6z"/></svg>'
CARAC_VISIVEIS = 6
MINI = '132px'   # largura da miniatura na faixa: o navegador baixa a versão pequena da foto
MOSAICO_PEQ = '(max-width: 820px) 96px, 30vw'  # fotos 2–5: ocultas no celular, baixa a menor versão


def tipo_icone(tipo):
    t = str(tipo or '').strip().lower()
    t = TIPO_SINONIMOS.get(t, t)
    return TIPO_ICONES.get(t, TIPO_ICONES['casa'])


TARJAS = {'black_friday': 'BLACK FRIDAY', 'oportunidade': 'OPORTUNIDADE', 'baixou_preco': 'BAIXOU O PREÇO', 'lancamento': 'LANÇAMENTO'}


def disponibilidade(item):
    v = item.get('disponibilidade') or (item.get('feeds') or {}).get('disponibilidade') or 'in_stock'
    return v if v in ('in_stock', 'out_of_stock', 'sold') else 'in_stock'


def selo(item):
    """Tarja diagonal: vendido e indisponível têm prioridade sobre a tarja de destaque."""
    d = disponibilidade(item)
    if d == 'sold': return ('vendido', 'VENDIDO')
    if d == 'out_of_stock': return ('indisponivel', 'INDISPONÍVEL')
    t = str(item.get('tarja') or '')
    if t in TARJAS: return (t, TARJAS[t])
    texto = str(item.get('tarjaTexto') or '').strip().upper()[:20]
    if t == 'personalizada' and texto: return ('personalizada', texto)
    return None


def tarja_html(item):
    s = selo(item)
    return f'<span class="tarja tarja--{s[0]}">{h(s[1])}</span>' if s else ''


def estado_classe(item):
    return {'sold': 'estado-vendido', 'out_of_stock': 'estado-indisponivel'}.get(disponibilidade(item), '')


def preco_html(item):
    if disponibilidade(item) == 'sold':
        return '<b class="price price-vendido">Vendido</b>'
    ant, atual = item.get('precoAnterior'), item.get('preco')
    velho = f'<s class="price-old">{brl(ant)}</s>' if isinstance(ant, (int, float)) and isinstance(atual, (int, float)) and ant > atual else ''
    return f'{velho}<b class="price">{brl(atual)}</b>'


def _faixa(item):
    """Faixa abaixo dos dados: tipo, código, localização e valor. Campo vazio não aparece."""
    partes = []
    tipo = str(item.get('tipo') or '').strip()
    if tipo:
        partes.append(f'<div class="fi">{icone(tipo_icone(tipo))}<b>{h(tipo)}</b><span>Tipo</span></div>')
    ref = str(item.get('id') or '').strip()
    if ref:
        partes.append(f'<div class="fi fi-codigo"><b>{h(ref)}</b><span>Código</span></div>')
    x = item.get('localizacao') or {}
    nomes = [str(x[k]).strip() for k in ('bairro', 'cidade', 'uf') if str(x.get(k) or '').strip()]
    if nomes:
        partes.append(f'<div class="fi fi-local">{icone(FAIXA_ICONES["local"])}<b>{h(nomes[0])}</b><span>{h(", ".join(nomes[1:]))}</span></div>')
    cat = CATEGORIAS.get(str(item.get('categoria') or '').strip().lower(), '')
    partes.append(f'<div class="fi-valor">{preco_html(item)}' + (f'<span>{h(cat)}</span>' if cat else '') + '</div>')
    return '<div class="faixa-info">' + ''.join(partes) + '</div>'


def icone(caminho, tam=20, cls='ico'):
    return (f'<svg class="{cls}" width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{caminho}"/></svg>')


def _galeria(item):
    fotos = item.get('imagens') or []
    if not fotos:
        return (f'<div class="gal single"><div class="ph main"><img src="{RAIZ_REL}assets/img/sem-imagem.svg" alt="Imagem indisponível" width="960" height="600">'
                '<span>Imagem indisponível</span></div></div>')
    legenda = lambda k: h(fotos[k].get('legenda') or f'Foto {k + 1}')
    total = f'<em>{len(fotos)} fotos</em>' if len(fotos) > 1 else ''
    mosaico = ''.join(
        f'<button class="ph{" main" if k == 0 else ""}" type="button" data-k="{k}" aria-label="Ampliar foto {k + 1}: {legenda(k)}">'
        f'{picture(fotos[k], item, k) if k == 0 else picture(fotos[k], item, k, MOSAICO_PEQ)}<span>{legenda(k)}</span>{total if k == 0 else ""}{tarja_html(item) if k == 0 else ""}</button>' for k in range(min(5, len(fotos))))
    # No celular, as fotos 2 a 5 saem do mosaico e entram na faixa (classe so-cel, oculta no computador).
    faixa = ''.join(
        f'<button class="gal-mini{" so-cel" if k < 5 else ""}" type="button" data-k="{k}" aria-label="Ampliar foto {k + 1}: {legenda(k)}">{picture(fotos[k], item, k, MINI)}</button>'
        for k in range(1, len(fotos)))
    faixa = f'<div class="gal-faixa{" so-cel" if len(fotos) <= 5 else ""}" role="group" aria-label="Mais fotos">{faixa}</div>' if faixa else ''
    return f'<div class="gal{" single" if len(fotos) == 1 else ""}" id="gal">{mosaico}</div>{faixa}'


def _carac_grupo(titulo, arr):
    itens = [x for x in (arr or []) if str(x).strip()]
    if not itens:
        return ''
    lis = ''.join(f'<li class="extra">{h(x)}</li>' if k >= CARAC_VISIVEIS else f'<li>{h(x)}</li>' for k, x in enumerate(itens))
    mais = (f'<button type="button" class="carac-mais" data-total="{len(itens)}" aria-expanded="false">Mostrar todos os {len(itens)} ↓</button>'
            if len(itens) > CARAC_VISIVEIS else '')
    return f'<div class="carac-grupo"><h3>{titulo} ({len(itens)})</h3><ul class="feat">{lis}</ul>{mais}</div>'


def detalhe(item):
    def m2(v):
        return f'{v} m²' if v is not None else None
    valores = [(item.get('dormitorios'), 'Dormitórios', 'dormitorios'), (item.get('suites'), 'Suítes', 'suites'),
               (item.get('banheiros'), 'Banheiros', 'banheiros'), (item.get('vagas'), 'Vagas', 'vagas'),
               (m2(item.get('areaTotal')), 'Área total', 'area'), (m2(item.get('areaUtil')), 'Área útil', 'area')]
    # Campo vazio não aparece (antes: "Não informado").
    stats = ''.join(f'<div>{icone(ICONES[i])}<b>{h(v)}</b><span>{h(r)}</span></div>' for v, r, i in valores if v is not None)
    stats = f'<div class="stats">{stats}</div>' if stats else ''
    grupos = _carac_grupo('No imóvel', item.get('caracteristicasImovel')) + _carac_grupo('No condomínio', item.get('caracteristicasCondominio'))
    caracteristicas = f'<aside class="box carac" aria-label="Características"><h2>Características</h2>{grupos}</aside>' if grupos else ''
    anunc = item.get('anunciante') or {}
    zap = ''.join(c for c in str(anunc.get('whatsapp') or '') if c.isdigit())
    flutuante = ''
    if len(zap) >= 10:
        texto = quote(f'Olá! Tenho interesse no imóvel {item["id"]} anunciado no Imoplace.')
        link = f'https://wa.me/{zap}?text={texto}'
        contato = f'<a class="btn btn-accent" id="whatsapp" href="{link}" target="_blank" rel="noopener noreferrer">Chamar no WhatsApp</a>'
        nota = ('Este imóvel já foi vendido. Procurando algo parecido? Fale com a gente.' if disponibilidade(item) == 'sold'
                else 'Solicite mais informações diretamente ao anunciante.')
        # Botão fixo: fica sempre na tela (o imovel.js só esconde com o visualizador de fotos aberto).
        flutuante = (f'<a class="zap-flutuante" href="{link}" target="_blank" rel="noopener noreferrer" aria-label="Chamar no WhatsApp" '
                     f'title="Chamar no WhatsApp">{ZAP_FAB}</a>')
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
    localizacao = f'<div class="box imovel-mapa"><h3>Localização</h3>{mapa}<div class="where">{h(endereco)}</div></div>' if consulta_mapa else ''
    # Valores: o preço já está no topo; linha sem valor não aparece, e o quadro some se não sobrar nenhuma.
    linhas = []
    if isinstance(item.get('preco'), (int, float)) and item.get('areaTotal'):
        linhas.append(('Preço por m²', brl(item['preco'] / item['areaTotal'])))
    for campo, rotulo in (('condominio', 'Condomínio'), ('iptuAnual', 'IPTU anual')):
        if isinstance(item.get(campo), (int, float)) and not isinstance(item.get(campo), bool):
            linhas.append((rotulo, brl(item[campo])))
    valores_box = ('<div class="box imovel-valores"><h3>Valores</h3><dl class="vals">' + ''.join(f'<dt>{r}</dt><dd>{v}</dd>' for r, v in linhas) + '</dl></div>') if linhas else ''
    return f'''<a class="back" href="{RAIZ_REL}index.html#imoveis">← Voltar aos resultados</a>
{_galeria(item)}
{stats}
{_faixa(item)}
<div class="dhead"><h1 class="dt">{h(item['titulo'])}</h1></div>
<div class="imovel-layout">
<div class="box imovel-sobre"><h3>Sobre o imóvel</h3><p style="white-space:pre-line">{h(item.get('descricao') or 'Descrição não cadastrada.')}</p></div>
{valores_box}
{multimidia(item)}
{localizacao}
<div class="imovel-barra">{caracteristicas}<aside class="aside box"><div class="adv"><div class="av">I</div><div><b>{h(anunc.get('nome') or 'Imoplace')}</b>{creci}</div></div>{f'<p class="small-note">{h(nota)}</p>' if nota else ''}{contato}<div class="ref">Código do imóvel: {h(item['id'])}</div></aside><div class="box imoplace-lead" data-lead-property="{h(item['id'])}" hidden></div></div>
</div>{flutuante}'''


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
                  'availability': 'https://schema.org/' + {'sold': 'SoldOut', 'out_of_stock': 'OutOfStock'}.get(disponibilidade(item), 'InStock')}
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
<link rel="stylesheet" href="{ativo("assets/css/style.css")}">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<header class="bar"><div class="wrap">
<a href="{RAIZ_REL}index.html" class="logo" aria-label="Imoplace, página inicial"><img src="{RAIZ_REL}assets/img/logo.png" alt="" width="50" height="44"><span>Imoplace</span></a>
<nav aria-label="Principal"><a href="{RAIZ_REL}noticias/">Notícias</a><a href="{RAIZ_REL}index.html#imoveis">Comprar</a><a href="{RAIZ_REL}index.html?categoria=lancamento#imoveis">Lançamentos</a></nav>
<div class="actions"><a class="btn btn-accent" href="{RAIZ_REL}anunciar/">Anuncie seu imóvel</a></div>
</div></header>
<main class="wrap {estado_classe(item)}" id="det">{detalhe(item)}</main>
<footer><div class="wrap"><span>© {h(conf.get('ano', '2026'))} Imoplace · imoplace.com.br</span><span>Informações sujeitas a confirmação com o anunciante.</span></div></footer>
<script src="{ativo("assets/js/protecao.js")}"></script>
<script src="{ativo("assets/js/main.js")}"></script>
<script src="{ativo("assets/js/midias.js")}"></script>
<span id="monitor-imovel" data-imovel="{h(item['id'])}" hidden></span>
<script src="{ativo("assets/js/imovel-lead.js")}"></script>
<script src="{ativo("assets/js/imovel.js")}"></script>
<script src="{ativo("assets/js/avatar.js")}"></script>
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


def picture(f,item,k,sizes="(max-width: 768px) 100vw, 60vw"):
    data=f.get('adaptativas') or {};fmts=data.get('formatos') or {}
    fallback=fmts.get('jpg') or fmts.get('png') or []
    src=RAIZ_REL+(fallback[-1]['arquivo'] if fallback else f['arquivo'])
    sources=''.join('<source type="'+rows[0]['mime']+'" srcset="'+h(', '.join(RAIZ_REL+x['arquivo']+' '+str(x['largura'])+'w' for x in rows))+'" sizes="'+sizes+'">' for ext in ordem_formatos(fmts,data.get('preferido','webp')) for rows in [fmts[ext]])
    srcset=' srcset="'+h(', '.join(RAIZ_REL+x['arquivo']+' '+str(x['largura'])+'w' for x in fallback))+'" sizes="'+sizes+'"' if fallback else ''
    return '<picture>'+sources+'<img src="'+h(src)+'"'+srcset+' width="'+str(data.get('largura',960))+'" height="'+str(data.get('altura',600))+'" alt="'+h(f.get('alt') or item['titulo'])+'" loading="'+('eager' if k==0 else 'lazy')+'" '+('fetchpriority="high" ' if k==0 else '')+'decoding="async"></picture>'


def midia_player(x):
    """Renderiza direto, sem botão: iframe com loading=lazy, vídeo nativo, panorama ou imagem."""
    modo,src,prop=alvo(x);st=estilo(prop);titulo=h(x['titulo'])
    if modo=='iframe':
        px=pixels(prop)
        escala=f' data-escala="{px[0]}x{px[1]}"' if px else ''
        tam=f' style="width:{px[0]}px;height:{px[1]}px"' if px else ''
        return f'<div class="midia-quadro"{escala}><iframe src="{h(src)}" title="{titulo}"{tam} loading="lazy" allow="{ALLOW}" allowfullscreen sandbox="{SANDBOX}" referrerpolicy="strict-origin-when-cross-origin"></iframe></div>'
    if modo=='video':
        capa=f' poster="{h(x["capa"])}"' if x.get('capa') else ''
        return f'<div class="midia-quadro"><video src="{h(src)}" controls playsinline preload="metadata"{capa}>Seu navegador não reproduz este vídeo.</video></div>'
    if modo=='panorama':
        return f'<div class="midia-quadro midia-panorama" data-panorama="{h(src)}"></div>'
    if modo=='imagem':
        return f'<div class="midia-quadro midia-imagem"><img src="{h(src)}" alt="{titulo}" loading="lazy" decoding="async"></div>'
    return ''


def carrossel(cards):
    """Um item: card simples. Dois ou mais: carrossel com setas ‹ › e contador."""
    if len(cards)<2: return ''.join(cards)
    n=len(cards)
    return ('<div class="midia-carrossel" data-carrossel><div class="mc-trilho" tabindex="0" aria-label="Mídias do imóvel, use as setas para navegar">'+''.join(cards)+'</div>'
            '<button type="button" class="mc-nav mc-prev" data-mc="-1" aria-label="Mídia anterior">‹</button>'
            '<button type="button" class="mc-nav mc-next" data-mc="1" aria-label="Próxima mídia">›</button>'
            f'<div class="mc-contador" aria-live="polite"><span data-mc-atual>1</span> / {n}</div></div>')


def multimidia(item):
    medias=colecao(item.get('midias')); links=colecao(item.get('links_externos'),links=True)
    cards=[]
    for x in medias:
        cards.append('<article class="midia-card"><h3>'+h(x['titulo'])+'</h3>'+('<p>'+h(x['descricao'])+'</p>' if x['descricao'] else '')+midia_player(x)+'<a class="midia-abrir" href="'+h(x['url'])+'" target="_blank" rel="noopener noreferrer">Abrir em nova aba ↗</a></article>')
    result='<section class="box" aria-label="Vídeos e tours"><h3>Vídeos e tours</h3>'+carrossel(cards)+'</section>' if cards else ''
    if links:
        result+='<button class="btn btn-line" type="button" data-open-links>Mais links ↗</button><dialog id="external-links" aria-labelledby="links-title"><h2 id="links-title">Acessos externos</h2><button type="button" class="btn btn-line" data-close-links>Fechar ✕</button>'+''.join('<p><a href="'+h(x['url'])+'" target="_blank" rel="noopener noreferrer">'+h(x['titulo'])+' ↗</a><br>'+h(x['descricao'])+'</p>' for x in links)+'</dialog>'
    return '<div id="multimidia" class="imovel-midias">'+result+'</div>'


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
