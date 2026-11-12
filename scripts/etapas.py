"""Motor v2.3 — etapas independentes com estado privado e rollback por ausência de deploy."""
import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen

import contrato
import gerador
import paginas
import publicar
from comum import config, estado_dir, gravar_json, ler_json, log, site_dir
from integracao import ler_feed


def job():
    return publicar._job()


def salvar(j):
    gravar_json(estado_dir() / 'job.json', j)


def sincronizar():
    publicar.cmd_pendencias()
    log('1/8', 'Fila consultada; prosseguir somente se tem=true')


def montar_catalogo():
    """Prepara o snapshot validado e o catálogo candidato, sem baixar nenhuma foto."""
    j = job()
    itens = contrato.validar_feed(ler_feed())
    versoes = {str(p['imovelId']): int(p['versao']) for p in j['pendencias']}
    for i in itens:
        if i['id'] in versoes and int(i.get('versao', -1)) != versoes[i['id']]:
            raise RuntimeError('Feed mais recente que a fila para imóvel ' + i['id'] + '; reinicie a execução.')
    j['feedSnapshot'] = 'feed-snapshot.json'
    salvar(j)
    gravar_json(estado_dir() / j['feedSnapshot'], {'imoveis': itens})
    manifestos = {p['imovelId']: p for p in j['pendencias']}
    entradas = []
    for i in itens:
        p = manifestos.get(i['id'])
        if p:
            fotos = gerador._fotos_manifesto(i, p)
        else:
            fotos = i.get('imagens', [])
        entradas.append(gerador._entrada(i, fotos))
    entradas.sort(key=lambda e: (-int(bool(e['destaque'])), e.get('ordem') or 0, -int(e['id'])))
    gravar_json(estado_dir() / 'catalogo-candidato.json', {'schemaVersao': 2, 'contrato': 'imoplace-v1', 'total': len(entradas), 'imoveis': entradas})
    log('2/8', f'Catálogo candidato gerado para {len(entradas)} imóveis publicados; fotos ainda não baixadas')


def montar_imoveis():
    """Baixa fotos somente quando SHA mudou e finaliza catálogo/páginas após resolução de falhas."""
    j = job()
    snapshot = ler_json(estado_dir() / j['feedSnapshot'])
    if not snapshot:
        raise RuntimeError('Snapshot da etapa 2 ausente')
    rel = gerador.montar(snapshot['imoveis'], j['pendencias'], site_dir(), config(), set(j.get('aguardando') or []))
    if rel['falhas']:
        raise RuntimeError(f'Falha de sincronização em {len(rel["falhas"])} imóvel(is); publicação bloqueada integralmente: {rel["falhas"]}')
    import migrar_legado
    migrar_legado.executar(site_dir(), config())
    j['relatorio'] = rel
    salvar(j)
    log('3/8', f'{len(rel["confirmar"]["imoveis"])} confirmáveis, {len(rel["falhas"])} falhas, {rel["transferidas"]} fotos transferidas')


def montar_extras():
    cat = ler_json(site_dir() / 'catalogo.json')
    if not cat:
        raise RuntimeError('Catálogo final da etapa 3 ausente')
    conf = config()
    gerador.indexacao_home(site_dir(), conf)
    gerador.gravar_sitemap(cat['imoveis'], site_dir(), conf)
    gerador.gravar_feeds(cat['imoveis'], site_dir(), conf)
    log('4/8', 'Sitemap, robots, feeds e indexação da home atualizados')


def montar_site():
    """Separa apenas arquivos públicos do build (nada de scripts, secrets ou docs)."""
    import shutil
    destino = estado_dir() / 'publicacao'
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(site_dir(), destino)
    # Marcador exclusivo do deploy para evitar confirmação falsa por cache de um catálogo idêntico.
    import hashlib
    j = job()
    conteudo = (destino / 'catalogo.json').read_bytes()
    gravar_json(destino / 'publicacao.json', {
        'jobId': j['jobId'], 'catalogoSha256': hashlib.sha256(conteudo).hexdigest()
    })
    proibidos = {'scripts', 'docs', '.github', '.env', '.git', 'estado'}
    for p in destino.iterdir():
        if p.name in proibidos or p.name.startswith('.clasp'):
            raise RuntimeError('Artefato público contém conteúdo privado: ' + p.name)
    log('6/8', f'Artefato público criado em {destino}')


def conferir():
    publicar.cmd_conferir()
    log('7/8', 'Catálogo e arquivos alterados verificados no site público')


def confirmar():
    publicar.cmd_confirmar()
    log('8/8', 'ACK de versões enviado ao Apps Script')


def falha():
    publicar.cmd_falha()
