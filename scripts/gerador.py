"""ImoPlace — monta o site a partir do feed público + pendências da fila.

Regras:
- Imóvel na fila: usa as fotos da versão ATUAL (manifesto da integração) e baixa só o que falta.
- Imóvel fora da fila: usa as fotos já publicadas (feed), que já estão no repositório.
- Falha num imóvel isola só ele: mantém a versão anterior no site (se houver) e não confirma.
- Pastas e fotos que nenhum imóvel do catálogo usa são removidas; URL antiga vira redirecionamento.
"""
import hashlib
import re
import shutil
from datetime import datetime, timezone
from xml.sax.saxutils import escape as xml_esc

import drive
import paginas
from comum import CONTRATO, RE_ARQUIVO, aviso, dentro, eh_webp, gravar, gravar_json, ler_json, log

RE_PASTA_ID = re.compile(r'-(\d+)$')


def _fotos_manifesto(item, pend):
    """Fotos ativas da versão atual, na ordem do site (capa primeiro)."""
    ativas = [i for i in pend.get('imagens') or [] if i.get('operacao') != 'excluir']
    capa = pend.get('capaId') or ''
    ativas.sort(key=lambda i: (0 if i['imagemId'] == capa else 1, i.get('ordem') or 0, i['imagemId']))
    fotos = []
    for n, i in enumerate(ativas, 1):
        fotos.append({
            'arquivo': f'{item["caminho"]}imagens/{i["arquivo"]}',
            'legenda': (i.get('legenda') or '').strip()[:80] or f'Foto {n}',
            'alt': (i.get('alt') or '').strip()[:160] or f'{item["titulo"]} — foto {n}',
            '_img': i,
        })
    return fotos


def _entrada(item, fotos):
    """Formato que a vitrine (main.js / home.js / imovel.js) lê."""
    loc = item.get('localizacao') or {}
    return {
        'id': item['id'], 'codigo': item['codigo'], 'categoria': item['categoria'], 'status': 'publicado',
        'url': item.get('url') or '', 'destaque': bool(item.get('destaque')), 'tag': item.get('tag') or '',
        'ordem': item.get('ordem') or 0, 'atualizadoEm': item.get('atualizadoEm') or '',
        'tipo': item.get('tipo') or '', 'condicao': item.get('condicao') or '', 'titulo': item['titulo'],
        'descricao': item.get('descricao') or '', 'seo': item.get('seo') or {},
        'localizacao': {k: loc.get(k) for k in ('bairro', 'cidade', 'uf', 'endereco', 'lat', 'lng')},
        'preco': item.get('preco'), 'condominio': item.get('condominio'), 'iptuAnual': item.get('iptuAnual'),
        'financiamento': bool(item.get('financiamento')), 'permuta': bool(item.get('permuta')),
        'documentacaoEmDia': bool(item.get('documentacaoEmDia')),
        'dormitorios': item.get('dormitorios'), 'suites': item.get('suites'), 'banheiros': item.get('banheiros'),
        'vagas': item.get('vagas'), 'areaTotal': item.get('areaTotal'), 'areaUtil': item.get('areaUtil'),
        'comodidades': item.get('comodidades') or [], 'caracteristicasImovel': item.get('caracteristicasImovel') or [],
        'caracteristicasCondominio': item.get('caracteristicasCondominio') or [],
        'anunciante': {k: (item.get('anunciante') or {}).get(k) or '' for k in ('nome', 'creci', 'whatsapp')},
        'feeds': item.get('feeds') or {},
        'imagens': [{'arquivo': f['arquivo'], 'legenda': f['legenda'], 'alt': f['alt']} for f in fotos],
    }


def baixar_fotos(fotos, site, stats):
    """Garante cada foto da versão atual no disco. Erro levanta FalhaDownload."""
    for f in fotos:
        img = f['_img']
        alvo = site / f['arquivo']
        if not dentro(site, alvo):
            raise drive.FalhaDownload(f'caminho inseguro: {f["arquivo"]}')
        if alvo.is_file() and hashlib.sha256(alvo.read_bytes()).hexdigest() == img['sha256']:
            continue
        dados = drive.baixar(img['driveFileId'])
        if not eh_webp(dados):
            raise drive.FalhaDownload(f'foto {img["imagemId"]} não é WebP')
        if hashlib.sha256(dados).hexdigest() != img['sha256']:
            raise drive.FalhaDownload(f'foto {img["imagemId"]} chegou diferente do enviado (hash não confere); será tentada de novo')
        gravar(alvo, dados)
        stats['transferidas'] += 1
        stats['bytes'] += len(dados)


def montar(feed_itens, pendencias, site, conf):
    """Gera catalogo.json, páginas, limpeza, sitemap, robots e feeds. Devolve o relatório do job."""
    anterior = {i.get('id'): i for i in (ler_json(site / 'catalogo.json', {}) or {}).get('imoveis', []) if isinstance(i, dict)}
    pend = {p['imovelId']: p for p in pendencias}
    stats = {'transferidas': 0, 'bytes': 0}
    falhas, ok_ids, entradas = {}, set(), []

    for item in feed_itens:
        iid = item['id']
        if iid in pend:
            fotos = _fotos_manifesto(item, pend[iid])
            try:
                if not fotos:
                    raise drive.FalhaDownload('imóvel publicado sem fotos ativas')
                baixar_fotos(fotos, site, stats)
                entradas.append(_entrada(item, fotos))
                ok_ids.add(iid)
            except drive.FalhaDownload as e:
                falhas[iid] = str(e)
                aviso(f'Imóvel {iid}: {e}')
                if iid in anterior and all((site / f['arquivo']).is_file() for f in anterior[iid].get('imagens', [])):
                    entradas.append(anterior[iid])
                    log('site', f'imóvel {iid}: mantida a versão anterior no site')
        else:
            fotos = [{'arquivo': f['arquivo'], 'legenda': f.get('legenda') or '', 'alt': f.get('alt') or ''} for f in item.get('imagens') or []]
            faltando = [f['arquivo'] for f in fotos if not (site / f['arquivo']).is_file()]
            if faltando:
                raise drive.FalhaDownload(f'Imóvel {iid}: {len(faltando)} foto(s) publicada(s) ausente(s): {faltando[:3]}. Interrompido para evitar anúncio incompleto.')
            entradas.append(_entrada(item, fotos))

    # Pendências que não estão no feed: saíram do site (baixado, rascunho, arquivado ou apagado).
    no_feed = {i['id'] for i in feed_itens}
    for iid, p in pend.items():
        if iid not in no_feed:
            if p.get('status') == 'publicado':
                falhas[iid] = 'imóvel publicado não apareceu no feed (dados mínimos ausentes?)'
            else:
                ok_ids.add(iid)

    entradas.sort(key=lambda e: (-int(bool(e['destaque'])), e.get('ordem') or 0, -int(e['id'])))
    # Publicação deve identificar uma execução nova, inclusive quando somente os arquivos do site mudarem.
    # O conteúdo permanece estável se a lista não mudou: evita commits desnecessários.
    anterior_catalogo = ler_json(site / 'catalogo.json', {}) or {}
    conteudo_estavel = anterior_catalogo.get('imoveis') == entradas
    publicado_em = (anterior_catalogo.get('geradoEm') if conteudo_estavel else None) or datetime.now(timezone.utc).isoformat(timespec='microseconds')
    catalogo = {'schemaVersao': 2, 'contrato': CONTRATO, 'geradoEm': publicado_em,
                'total': len(entradas), 'imoveis': entradas}
    gravar_json(site / 'catalogo.json', catalogo)

    for e in entradas:
        gravar(site / 'imoveis' / e['codigo'] / 'index.html', paginas.pagina(e, conf))
    limpar(entradas, site, conf)
    # Extras gerados na etapa [4/8] montar_extras.py.

    confirmar = {'imoveis': [], 'imagens': []}
    for iid in sorted(ok_ids):
        p = pend[iid]
        confirmar['imoveis'].append({'imovelId': iid, 'versao': p['versao'], 'noSite': iid in no_feed})
        for i in p.get('imagens') or []:
            if i.get('operacao') == 'excluir':
                confirmar['imagens'].append({'imagemId': i['imagemId'], 'versao': i['versao'], 'excluida': True})
            elif iid not in no_feed:
                confirmar['imagens'].append({'imagemId': i['imagemId'], 'versao': i['versao'], 'foraDoSite': True})
            else:
                confirmar['imagens'].append({'imagemId': i['imagemId'], 'versao': i['versao']})
    log('site', f'{len(entradas)} imóveis no catálogo; {len(ok_ids)} confirmáveis; {len(falhas)} com falha; '
                f'{stats["transferidas"]} foto(s) baixada(s), {stats["bytes"] / 1048576:.1f} MB')
    return {'confirmar': confirmar, 'falhas': [{'imovelId': k, 'erro': v} for k, v in sorted(falhas.items())],
            'transferidas': stats['transferidas'], 'bytes': stats['bytes'], 'geradoEm': catalogo['geradoEm'],
            'conferir': [{'pagina': f'imoveis/{e["codigo"]}/', 'fotos': [f['arquivo'] for f in e['imagens']]}
                         for e in entradas if e['id'] in ok_ids]}


def limpar(entradas, site, conf):
    """Limpa imagens órfãs; redireciona slugs antigos; elimina anúncios despublicados.

    Nunca altera arquivos fora da pasta controlada imoveis/.
    """
    base = site / 'imoveis'
    if not base.is_dir():
        return
    usados = {e['codigo']: e for e in entradas}
    por_id = {str(e['id']): e for e in entradas}
    for pasta in list(base.iterdir()):
        if not pasta.is_dir():
            continue
        if pasta.name in usados:
            refs = {f['arquivo'].rsplit('/', 1)[-1] for f in usados[pasta.name]['imagens']}
            imgs = pasta / 'imagens'
            if imgs.is_dir():
                for arquivo in imgs.iterdir():
                    if arquivo.is_file() and arquivo.name not in refs:
                        arquivo.unlink()
            for extra in pasta.iterdir():
                if extra.name not in ('index.html', 'imagens'):
                    shutil.rmtree(extra) if extra.is_dir() else extra.unlink()
            continue
        m = RE_PASTA_ID.search(pasta.name)
        novo = por_id.get(m.group(1)) if m else None
        shutil.rmtree(pasta)
        if novo:
            destino = f'imoveis/{novo["codigo"]}/'
            gravar(pasta / 'index.html', paginas.redirecionamento(destino, conf))
            log('limpeza', f'{pasta.name} → redirecionamento para {destino}')
        else:
            log('limpeza', f'{pasta.name}: despublicado e removido')


def indexacao_home(site, conf):
    home = site / 'index.html'
    if not home.is_file():
        return
    txt = home.read_text(encoding='utf-8')
    alvo = 'index,follow' if conf['permitirIndexacao'] else 'noindex,follow'
    novo = re.sub(r'<meta name="robots" content="[^"]*">', f'<meta name="robots" content="{alvo}">', txt, count=1)
    gravar(home, novo)


def gravar_sitemap(entradas, site, conf):
    base = conf['urlPublica']
    if conf['permitirIndexacao']:
        urls = [f'{base}/'] + [f'{base}/imoveis/{e["codigo"]}/' for e in entradas]
        corpo = '\n'.join(f'  <url><loc>{xml_esc(u)}</loc></url>' for u in urls)
        gravar(site / 'sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + corpo + '\n</urlset>\n')
        gravar(site / 'robots.txt', f'User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n')
    else:
        (site / 'sitemap.xml').unlink(missing_ok=True)
        gravar(site / 'robots.txt', 'User-agent: *\nDisallow: /\n')


def _item_feed(e, conf, meta):
    base = conf['urlPublica']
    fotos = [f'{base}/{f["arquivo"]}' for f in e['imagens']]
    disp = (e.get('feeds') or {}).get('disponibilidade') or 'in_stock'
    if meta:
        disp = 'in stock' if disp == 'in_stock' else 'out of stock'
    cond = 'used' if e.get('condicao') == 'Usado' else 'new'
    desc = (e.get('descricao') or e['titulo'])[:4900]
    extras = ''.join(f'<g:additional_image_link>{xml_esc(u)}</g:additional_image_link>' for u in fotos[1:11])
    return (f'<item><g:id>{xml_esc(e["id"])}</g:id><title>{xml_esc(e["titulo"][:150])}</title>'
            f'<description>{xml_esc(desc)}</description><link>{xml_esc(base + "/imoveis/" + e["codigo"] + "/")}</link>'
            f'<g:image_link>{xml_esc(fotos[0])}</g:image_link>{extras}<g:availability>{disp}</g:availability>'
            f'<g:price>{e["preco"]:.2f} BRL</g:price><g:condition>{cond}</g:condition>'
            f'<g:brand>{xml_esc((e.get("anunciante") or {}).get("nome") or conf["nome"])}</g:brand>'
            f'<g:product_type>{xml_esc("Imóveis > " + (e.get("tipo") or "Imóvel"))}</g:product_type></item>')


def gravar_feeds(entradas, site, conf):
    """Google Merchant e Meta (RSS 2.0 com namespace g:). Entra só imóvel marcado, com preço e foto."""
    for arquivo, chave, meta in (('merchant-produtos.xml', 'google', False), ('meta-produtos.xml', 'meta', True)):
        itens = [e for e in entradas if (e.get('feeds') or {}).get(chave) and isinstance(e.get('preco'), (int, float))
                 and e['preco'] > 0 and e['imagens']]
        corpo = '\n'.join(_item_feed(e, conf, meta) for e in itens)
        gravar(site / arquivo, '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">\n'
               f'<channel><title>{xml_esc(conf["nome"])}</title><link>{xml_esc(conf["urlPublica"])}/</link>'
               f'<description>Imóveis {xml_esc(conf["nome"])}</description>\n{corpo}\n</channel></rss>\n')
        log('feeds', f'{arquivo}: {len(itens)} imóvel(is)')


def arquivo_valido(nome: str) -> bool:
    return bool(RE_ARQUIVO.match(nome))
