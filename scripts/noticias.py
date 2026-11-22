"""Blog estático: apenas matérias publicadas. Dados Push privados nunca são exportados."""
import html,json,re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import quote,urlsplit
from urllib.error import HTTPError
from xml.sax.saxutils import escape
from comum import gravar,gravar_json,ler_json,log
from core_google import _request,_sheet_id,API
from midias import url_segura
ROBOTS_INDEX='index,follow,max-image-preview:large'  # mesmo valor de paginas.ROBOTS_INDEX

COLS=['ID','SLUG','TITULO','RESUMO','CORPO','STATUS','CATEGORIA','TAGS','AUTOR','CAPA_URL','CAPA_ALT','SEO_TITULO','SEO_DESCRICAO','CRIADO_EM','ATUALIZADO_EM','PUBLICADO_EM','VERSAO','NOTIFICAR']

def tabela(nome):
    try:
        data=_request(f'{API}/{_sheet_id()}/values/{quote(nome+"!A1:Z",safe="")}').get('values') or []
    except HTTPError as exc:
        detail=exc.read(4000).decode('utf-8','replace')
        if exc.code in (400,404) and 'Unable to parse range' in detail:return None
        raise RuntimeError('Falha ao acessar a tabela '+nome) from None
    if not data:return []
    return [dict(zip(data[0],row+['']*max(0,len(data[0])-len(row))),_linha=i) for i,row in enumerate(data[1:],2) if row]

def push_config():
    rows=tabela('CONFIG_PUSH') or []
    return {str(x.get('CHAVE')):str(x.get('VALOR') or '') for x in rows}

def artigo(row):
    if str(row.get('STATUS'))!='publicado':return None
    iid=str(row.get('ID') or '');slug=str(row.get('SLUG') or '')
    if not re.fullmatch(r'n[a-z0-9]{12}',iid) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug):raise ValueError('ID/slug inválido em notícia publicada')
    title=str(row.get('TITULO') or '').strip()[:200];body=str(row.get('CORPO') or '').strip()[:30000]
    if not title or not body:raise ValueError('Notícia publicada sem título ou corpo')
    cover=url_segura(row.get('CAPA_URL'))
    if cover and urlsplit(cover).path.lower().endswith(('.jxl','.svg')):raise ValueError('Capa de notícia precisa de formato indexável como JPEG/PNG/WebP')
    return dict(id=iid,slug=slug,codigo=slug+'-'+iid,titulo=title,resumo=str(row.get('RESUMO') or '')[:400],corpo=body,categoria=str(row.get('CATEGORIA') or 'Novidades')[:80],tags=[x.strip() for x in str(row.get('TAGS') or '').split(',') if x.strip()][:20],autor=str(row.get('AUTOR') or 'Imoplace')[:120],capa=cover,capaAlt=str(row.get('CAPA_ALT') or title)[:200],seoTitulo=str(row.get('SEO_TITULO') or title)[:70],seoDescricao=str(row.get('SEO_DESCRICAO') or row.get('RESUMO') or body)[:160],publicadoEm=str(row.get('PUBLICADO_EM') or row.get('CRIADO_EM') or ''),atualizadoEm=str(row.get('ATUALIZADO_EM') or ''),versao=int(row.get('VERSAO') or 0),notificar=str(row.get('NOTIFICAR') or '')=='SIM')

h=lambda v:html.escape(str(v or ''),quote=True)
def corpo(text):
    # Escapar primeiro: o anunciante não injeta HTML ou scripts.
    out=[];paragraph=[];listing=False
    def flush():
        if paragraph:out.append('<p>'+'<br>'.join(paragraph)+'</p>');paragraph.clear()
    for raw in text.splitlines():
        line=h(raw.strip());line=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',line)
        if line.startswith('- '):
            flush()
            if not listing:out.append('<ul>');listing=True
            out.append('<li>'+line[2:]+'</li>');continue
        if listing:out.append('</ul>');listing=False
        if line.startswith('## '):flush();out.append('<h2>'+line[3:]+'</h2>')
        elif not line:flush()
        else:paragraph.append(line)
    flush()
    if listing:out.append('</ul>')
    return '\n'.join(out)

def data_label(value):
    try:return datetime.fromisoformat(value.replace('Z','+00:00')).strftime('%d/%m/%Y')
    except (ValueError,AttributeError):return ''

def shell(title,description,url,content,root,conf,schema=None,cover=''):
    ld=json.dumps(schema or {'@context':'https://schema.org','@type':'Blog','name':'Notícias Imoplace','url':url},ensure_ascii=False).replace('<','\\u003c')
    image=f'<meta property="og:image" content="{h(cover)}"><meta name="twitter:image" content="{h(cover)}">' if cover else ''
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><link rel="manifest" href="{root}manifest.webmanifest"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{h(title)} | Imoplace</title><meta name="description" content="{h(description)}"><meta name="robots" content="{ROBOTS_INDEX if conf['permitirIndexacao'] else 'noindex,follow'}"><link rel="canonical" href="{h(url)}"><meta property="og:type" content="{'article' if schema else 'website'}"><meta property="og:title" content="{h(title)}"><meta property="og:description" content="{h(description)}"><meta property="og:url" content="{h(url)}"><meta name="twitter:card" content="summary_large_image">{image}<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="stylesheet" href="{root}assets/css/style.css"><link rel="stylesheet" href="{root}assets/css/noticias.css"><link rel="alternate" type="application/rss+xml" href="{conf['urlPublica']}/noticias/feed.xml" title="Notícias Imoplace"><script type="application/ld+json">{ld}</script></head><body><header class="bar"><div class="wrap"><a class="logo" href="{root}index.html"><img src="{root}assets/img/logo.png" width="50" height="44" alt=""><span>Imoplace</span></a><nav aria-label="Principal"><a href="{root}index.html#imoveis">Imóveis</a><a href="{root}noticias/" aria-current="page">Notícias</a></nav><a class="btn btn-accent" href="{root}anunciar/">Anuncie seu imóvel</a></div></header><main class="wrap news-main">{content}</main><footer><div class="wrap"><span>Imoplace · Informação para morar e investir melhor.</span><a href="{root}noticias/avisos/">Gerenciar avisos</a></div></footer><script src="{root}assets/js/noticias-push.js" defer></script><script src="{root}assets/js/compartilhar.js" defer></script></body></html>'''

def compartilhar(url,titulo):
    """Botão só para celular (CSS .share-mobile); compartilhar.js abre o menu do aparelho."""
    return f'<button class="btn btn-line share-mobile news-share" type="button" data-compartilhar="{h(url)}" data-titulo="{h(titulo)}"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg><span>Compartilhar</span></button>'

def botao(scope='*'):
    return f'<div class="news-optin"><button class="btn btn-accent" type="button" data-push-scope="{h(scope)}">Notifique-me em caso de atualizações</button><p class="push-status" role="status" aria-live="polite"></p><p class="small-note">Avisos no seu navegador. Você escolhe permitir e pode cancelar a qualquer momento.</p></div>'

# ---------- Imóveis relacionados à matéria (carrossel no rodapé + card que desliza) ----------
import unicodedata
REL_MAX=6
REL_SIZES='(max-width: 768px) 72vw, 280px'

def _norm(v):
    v=unicodedata.normalize('NFKD',str(v or '')).encode('ascii','ignore').decode().lower()
    return ' '+re.sub(r'[^a-z0-9%]+',' ',v).strip()+' '

def _tem(texto,*termos):
    return any(_norm(t) in texto for t in termos)

# Assuntos: (termos na matéria, título do bloco, teste no imóvel). A ordem define a prioridade.
ASSUNTOS=[
    (('100% financiado','100 financiado'),'Imóveis 100% financiados',lambda i:'100%' in str(i.get('tag') or '') or '100% financ' in str(i.get('descricao') or '').lower()),
    (('parcelamento direto',),'Imóveis com parcelamento direto',lambda i:'parcelamento direto' in _norm(str(i.get('tag') or '')+' '+str(i.get('descricao') or ''))),
    (('na planta','incorporacao','memorial de incorporacao','incc'),'Imóveis na planta',lambda i:_norm(i.get('condicao'))==' na planta '),
    (('terreno','loteamento','lote'),'Terrenos e loteamentos',lambda i:_norm(i.get('tipo'))==' terreno '),
    (('lancamento','lancamentos'),'Lançamentos',lambda i:_norm(i.get('categoria'))==' lancamento ' or _norm(i.get('condicao')) in (' novo ',' na planta ')),
    (('imovel usado','imoveis usados'),'Imóveis usados',lambda i:_norm(i.get('condicao'))==' usado '),
    (('fgts','financiamento','financiado','minha casa minha vida','mcmv','credito imobiliario','credito habitacional','sfh'),'Imóveis que aceitam financiamento',lambda i:bool(i.get('financiamento'))),
]

def relacionados(artigo,imoveis):
    """Escolhe até REL_MAX imóveis publicados para a matéria. Retorna (título, lista, cidade|None)."""
    pub=[i for i in imoveis if str(i.get('status','publicado'))=='publicado' and i.get('codigo') and i.get('imagens')]
    if not pub:return '',[],None
    texto=_norm(' '.join([artigo.get('titulo',''),' '.join(artigo.get('tags') or [])]))
    cidades={}
    for i in pub:
        c=str((i.get('localizacao') or {}).get('cidade') or '').strip()
        if c and len(_norm(c).strip())>=4:cidades.setdefault(_norm(c),c)
    cidade=next((c for n,c in sorted(cidades.items(),key=lambda kv:-len(kv[0])) if n in texto),None)
    assunto=next((a for a in ASSUNTOS if _tem(texto,*a[0])),None)
    def ordem(i):return (not i.get('destaque'),i.get('ordem') if isinstance(i.get('ordem'),(int,float)) else 1e9)
    if cidade:
        nc=_norm(cidade);da=[i for i in pub if _norm((i.get('localizacao') or {}).get('cidade'))==nc]
        if assunto:da.sort(key=lambda i:(not assunto[2](i),)+ordem(i))
        else:da.sort(key=ordem)
        return 'Imóveis em '+cidade.strip().title().replace(' Da ',' da ').replace(' De ',' de ').replace(' Do ',' do '),da[:REL_MAX],cidade
    if assunto:
        da=sorted([i for i in pub if assunto[2](i)],key=ordem)
        if da:return assunto[1],da[:REL_MAX],None
    da=sorted(pub,key=ordem)
    return 'Imóveis em destaque',da[:REL_MAX],None

def _num(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and v>0

def _fmt(v):
    return str(int(v)) if float(v).is_integer() else str(v).replace('.',',')

def _dados(i):
    d=[]
    if _num(i.get('dormitorios')):d.append(_fmt(i['dormitorios'])+(' dorm.'))
    if _num(i.get('suites')):d.append(_fmt(i['suites'])+(' suíte' if i['suites']==1 else ' suítes'))
    if _num(i.get('vagas')):d.append(_fmt(i['vagas'])+(' vaga' if i['vagas']==1 else ' vagas'))
    area=i.get('areaUtil') if _num(i.get('areaUtil')) else i.get('areaTotal')
    if _num(area):d.append(_fmt(area)+' m²')
    return ' · '.join(d)

def _onde(i):
    x=i.get('localizacao') or {};return ' · '.join(str(x[k]).strip() for k in ('bairro','cidade') if x.get(k))

def _card_imovel(i):
    from paginas import picture,brl
    tag=f'<span class="rel-tag">{h(i["tag"])}</span>' if str(i.get('tag') or '').strip() else ''
    dados=_dados(i);dados=f'<span class="rel-dados">{h(dados)}</span>' if dados else ''
    onde=' · '.join(x for x in (str(i.get('tipo') or '').strip(),_onde(i)) if x)
    return (f'<a class="rel-card" href="../../imoveis/{h(i["codigo"])}/"><span class="rel-foto">{picture(i["imagens"][0],i,1,REL_SIZES)}{tag}</span>'
            f'<span class="rel-corpo"><span class="rel-onde">{h(onde)}</span><b class="rel-titulo">{h(i["titulo"])}</b>{dados}'
            f'<span class="rel-rodape"><b class="rel-preco">{h(brl(i.get("preco")))}</b><span class="rel-ver">Ver imóvel →</span></span></span></a>')

SETA_E='<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>'
SETA_D='<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>'
FECHAR='<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>'

def bloco_imoveis(artigo,imoveis):
    """HTML do carrossel e do card que desliza; vazio quando não há imóvel publicado."""
    titulo,lista,cidade=relacionados(artigo,imoveis)
    if not lista:return ''
    cards=''.join(_card_imovel(i) for i in lista)
    todos='Ver todos os imóveis'+(' em '+h(titulo[len('Imóveis em '):]) if cidade else '')+' →'
    primeiro=lista[0];from paginas import picture,brl
    rotulo=('Imóvel em '+titulo[len('Imóveis em '):]) if cidade else 'Imóvel relacionado'
    dados=_dados(primeiro)
    mini=(f'<aside class="rel-mini" aria-label="Imóvel relacionado à matéria" hidden><div class="rel-mini-topo"><span class="rel-mini-rotulo">{h(rotulo)}</span>'
          f'<button class="rel-mini-fechar" type="button" aria-label="Fechar sugestão">{FECHAR}</button></div>'
          f'<a class="rel-mini-link" href="../../imoveis/{h(primeiro["codigo"])}/"><span class="rel-mini-foto">{picture(primeiro["imagens"][0],primeiro,1,"120px")}</span>'
          f'<span class="rel-mini-texto"><b>{h(primeiro["titulo"])}</b>'+(f'<span class="rel-dados">{h(dados)}</span>' if dados else '')+
          f'<span class="rel-preco">{h(brl(primeiro.get("preco")))}</span></span></a><a class="rel-mini-ver" href="../../imoveis/{h(primeiro["codigo"])}/">Ver imóvel</a></aside>')
    return (f'<section class="rel-imoveis" aria-labelledby="rel-titulo"><div class="rel-cabeca"><div><span class="news-kicker">Imóveis relacionados a esta matéria</span><h2 id="rel-titulo">{h(titulo)}</h2></div>'
            f'<div class="rel-setas" hidden><button type="button" class="rel-seta" data-rel-dir="-1" aria-label="Imóveis anteriores">{SETA_E}</button><button type="button" class="rel-seta" data-rel-dir="1" aria-label="Próximos imóveis">{SETA_D}</button></div></div>'
            f'<div class="rel-faixa">{cards}</div><a class="news-read rel-todos" href="../../index.html#imoveis">{todos}</a></section>{mini}<script src="../../assets/js/noticias-imoveis.js" defer></script>')

def construir(site,conf,rows,config):
    site=Path(site);base=conf['urlPublica'].rstrip('/');anterior=ler_json(site/'noticias/catalogo.json',{}) or {}
    imoveis=(ler_json(site/'catalogo.json',{}) or {}).get('imoveis') or []
    if rows is None:
        if anterior.get('artigos'):log('noticias','Tabela ainda não disponível; mantidas matérias anteriores.');return anterior['artigos']
        rows=[]
    items=[artigo(x) for x in rows if str(x.get('STATUS'))=='publicado'];items.sort(key=lambda x:(x['publicadoEm'],x['id']),reverse=True)
    if len({x['id'] for x in items})!=len(items) or len({x['codigo'] for x in items})!=len(items):raise ValueError('Notícia repetida')
    public_url=config.get('URL_PUBLICA','');key=config.get('PUBLIC_KEY','')
    ready=bool(config.get('PRIVATE_JWK') and re.fullmatch(r'https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec',public_url) and re.fullmatch(r'B[A-Za-z0-9_-]{86}',key))
    gravar_json(site/'noticias/push-config.json',{'ativo':ready,'url':public_url if ready else '', 'publicKey':key if ready else ''})
    categories=sorted({x['categoria'] for x in items});buttons=''.join(f'<button class="news-filter" type="button" data-news-category="{h(x)}">{h(x)}</button>' for x in categories)
    cards=[]
    for x in items:
        image=f'<img src="{h(x["capa"])}" alt="{h(x["capaAlt"])}" width="720" height="450" loading="lazy">' if x['capa'] else '<div class="news-placeholder" aria-hidden="true">Imoplace<span>Leitura para o seu próximo passo</span></div>'
        cards.append(f'<article class="news-card" data-category="{h(x["categoria"])}"><a class="news-image" href="{x["codigo"]}/">{image}</a><div class="news-card-body"><span class="news-kicker">{h(x["categoria"])}</span><h2><a href="{x["codigo"]}/">{h(x["titulo"])}</a></h2><p>{h(x["resumo"])}</p><div class="news-meta">{h(data_label(x["publicadoEm"]))} · {max(1,len(x["corpo"].split())//200)} min de leitura</div><div class="news-card-actions"><a class="news-read" href="{x["codigo"]}/">Ler matéria →</a>{compartilhar(base+"/noticias/"+x["codigo"]+"/",x["titulo"])}</div></div></article>')
    empty='<div class="news-empty"><h2>Boas histórias começam com informação.</h2><p>Em breve, novidades para você morar e investir melhor.</p></div>'
    content=f'<section class="news-hero"><div><span class="news-kicker">Jornal Imoplace</span><h1>Seu próximo capítulo<br>começa com informação.</h1><p>Curiosidades, dicas e novidades sobre imóveis, bairros e o jeito de morar.</p></div>{botao()}</section><nav class="news-filters" aria-label="Categorias"><button type="button" class="news-filter active" data-news-category="">Todas</button>{buttons}</nav><section class="news-grid" aria-label="Matérias">'+(''.join(cards) if cards else empty)+'</section><script src="../assets/js/noticias-ui.js" defer></script>'
    gravar(site/'noticias/index.html',shell('Notícias, dicas e curiosidades','Informação sobre imóveis, bairros e moradia. Leia notícias, dicas e curiosidades no Imoplace.',base+'/noticias/',content,'../',dict(conf,permitirIndexacao=bool(conf['permitirIndexacao'] and items))))
    current={x['id']:x for x in items}
    for old in anterior.get('artigos',[]):
        if not re.fullmatch(r'[a-z0-9-]+-n[a-z0-9]{12}',str(old.get('codigo',''))):continue
        path=site/'noticias'/old['codigo']/'index.html';new=current.get(old['id'])
        if new and new['codigo']!=old['codigo']:
            from paginas import redirecionamento
            gravar(path,redirecionamento('noticias/'+new['codigo']+'/',conf))
        elif not new and path.is_file():path.unlink()
    for x in items:
        url=base+'/noticias/'+x['codigo']+'/'
        schema={'@context':'https://schema.org','@type':'BlogPosting','headline':x['titulo'],'description':x['seoDescricao'],'mainEntityOfPage':url,'url':url,'datePublished':x['publicadoEm'],'dateModified':x['atualizadoEm'],'author':{'@type':'Person','name':x['autor']},'publisher':{'@type':'Organization','name':'Imoplace','url':base,'logo':{'@type':'ImageObject','url':base+'/icon-512.png','width':512,'height':512}},'inLanguage':'pt-BR','keywords':x['tags']}
        if x['capa']:schema['image']=[x['capa']]
        rel=bloco_imoveis(x,imoveis)
        cover=f'<img class="article-cover" src="{h(x["capa"])}" alt="{h(x["capaAlt"])}" width="1200" height="750" fetchpriority="high">' if x['capa'] else ''
        content=f'<nav class="news-breadcrumb" aria-label="Você está aqui"><a href="../../">Início</a> / <a href="../">Notícias</a> / {h(x["categoria"])}</nav><article class="news-article"><header><span class="news-kicker">{h(x["categoria"])}</span><h1>{h(x["titulo"])}</h1><p class="news-deck">{h(x["resumo"])}</p><p class="news-meta">Por {h(x["autor"])} · {h(data_label(x["publicadoEm"]))}'+(f' · Atualizado em {h(data_label(x["atualizadoEm"]))}' if x['atualizadoEm']!=x['publicadoEm'] else '')+f'</p>{compartilhar(url,x["titulo"])}</header>{cover}<div class="article-body">{corpo(x["corpo"])}</div>'+rel+f'<aside class="news-follow"><h2>Acompanhe esta matéria</h2>{botao(x["id"])}</aside>'+('' if rel else '<a class="news-read" href="../../index.html#imoveis">Encontre seu próximo imóvel →</a>')+'</article>'
        gravar(site/'noticias'/x['codigo']/'index.html',shell(x['seoTitulo'],x['seoDescricao'],url,content,'../../',conf,schema,x['capa']))
    management='<section class="news-hero"><div><span class="news-kicker">Sua escolha</span><h1>Avisos do Imoplace</h1><p>Receba novidades no navegador. Cancele todos os avisos deste aparelho quando quiser.</p><p>Para entregar os avisos, guardamos a inscrição técnica deste navegador. Não pedimos e-mail.</p>'+botao()+'<button class="btn btn-line" type="button" data-push-cancelar>Cancelar avisos neste navegador</button><p class="push-status" role="status"></p></div></section>'
    gravar(site/'noticias/avisos/index.html',shell('Gerenciar avisos','Escolha receber ou cancelar avisos do Imoplace no seu navegador.',base+'/noticias/avisos/',management,'../../',dict(conf,permitirIndexacao=False)))
    # Excluir controles internos da representação pública, inclusive a escolha de disparo.
    public=[{k:v for k,v in x.items() if k!='notificar'} for x in items]
    gravar_json(site/'noticias/catalogo.json',{'artigos':public})
    rss=''.join('<item><guid>'+escape(base+'/noticias/'+x['codigo']+'/')+'</guid><title>'+escape(x['titulo'])+'</title><link>'+escape(base+'/noticias/'+x['codigo']+'/')+'</link><description>'+escape(x['resumo'])+'</description></item>' for x in items)
    gravar(site/'noticias/feed.xml','<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Notícias Imoplace</title><link>'+escape(base+'/noticias/')+'</link><description>Dicas e novidades para morar melhor.</description>'+rss+'</channel></rss>')
    return items

def main():
    import os
    from comum import config,site_dir,estado_dir
    conf=config();site=site_dir();rows=tabela('NOTICIAS');cfg=push_config();items=construir(site,conf,rows,cfg)
    from gerador import gravar_sitemap
    gravar_sitemap((ler_json(site/'catalogo.json',{}) or {}).get('imoveis',[]),site,conf)
    # Snapshot privado mínimo para conferir que a notificação corresponde à versão publicada.
    gravar_json(estado_dir()/'noticias-publicadas.json',{'artigos':[{'id':x['id'],'versao':x['versao'],'codigo':x['codigo']} for x in items]})
    log('noticias',str(len(items))+' matérias publicadas no artefato; nenhuma inscrição exportada.')

if __name__=='__main__':main()
