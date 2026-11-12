#!/usr/bin/env python3
"""ImoPlace — validação independente do site gerado. Qualquer erro impede a publicação.

Confere: catalogo.json no contrato, nenhum campo privado, páginas e fotos existentes (WebP real),
caminhos seguros, sitemap apontando só para páginas que existem, pastas órfãs.
"""
import json
import re
import sys

from comum import CATEGORIAS, CONTRATO, PROIBIDOS, RE_ARQUIVO, RE_CODIGO, aviso, config, dentro, eh_webp, erro, log, site_dir

# GitHub Pages: site publicado de no máximo 1 GB. Aviso antes, para dar tempo de planejar.
AVISO_BYTES = 800 * 1024 ** 2
LIMITE_BYTES = 1024 ** 3


def _chaves(obj, saida):
    if isinstance(obj, dict):
        for k, v in obj.items():
            saida.add(str(k).lower())
            _chaves(v, saida)
    elif isinstance(obj, list):
        for v in obj:
            _chaves(v, saida)
    return saida


def validar(site=None, conf=None) -> list:
    site = site or site_dir()
    conf = conf or config()
    problemas = []
    try:
        cat = json.loads((site / 'catalogo.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        return [f'catalogo.json ilegível: {e}']
    if cat.get('contrato') != CONTRATO or not isinstance(cat.get('imoveis'), list) or cat.get('total') != len(cat['imoveis']):
        problemas.append('catalogo.json fora do contrato')
        return problemas
    vazados = _chaves(cat, set()) & PROIBIDOS
    if vazados:
        problemas.append(f'catalogo.json contém campos privados: {sorted(vazados)}')
    texto = (site / 'catalogo.json').read_text(encoding='utf-8')
    if 'drive.google.com' in texto or 'googleusercontent' in texto:
        problemas.append('catalogo.json contém link do Google Drive')
    codigos, paginas_ok = set(), set()
    for e in cat['imoveis']:
        cod, catg = e.get('codigo', ''), e.get('categoria')
        if not RE_CODIGO.match(cod) or catg not in CATEGORIAS or not cod.endswith('-' + str(e.get('id'))):
            problemas.append(f'imóvel com código/categoria inválidos: {cod!r}')
            continue
        if cod in codigos:
            problemas.append(f'código repetido: {cod}')
        codigos.add(cod)
        rel = f'imoveis/{cod}/'
        pagina = site / rel / 'index.html'
        if not pagina.is_file() or f'data-codigo="{cod}"' not in pagina.read_text(encoding='utf-8'):
            problemas.append(f'página ausente ou incorreta: {rel}')
        paginas_ok.add(rel)
        for f in e.get('imagens') or []:
            arq = str(f.get('arquivo', ''))
            nome = arq.rsplit('/', 1)[-1]
            alvo = site / arq
            if not arq.startswith(rel + 'imagens/') or not RE_ARQUIVO.match(nome) or not dentro(site, alvo):
                problemas.append(f'caminho de foto inválido: {arq}')
            elif not alvo.is_file():
                problemas.append(f'foto ausente: {arq}')
            elif not eh_webp(alvo.read_bytes()[:16]):
                problemas.append(f'foto não é WebP: {arq}')
    base = site / 'imoveis'
    if base.is_dir():
        for pagina in base.glob('*/index.html'):
            rel = str(pagina.parent.relative_to(site)).replace('\\', '/') + '/'
            if rel not in paginas_ok and 'http-equiv="refresh"' not in pagina.read_text(encoding='utf-8'):
                problemas.append(f'página órfã (fora do catálogo): {rel}')
    sm = site / 'sitemap.xml'
    if sm.is_file():
        for url in re.findall(r'<loc>([^<]+)</loc>', sm.read_text(encoding='utf-8')):
            rel = url.replace(conf['urlPublica'] + '/', '', 1)
            if rel and rel not in paginas_ok:
                problemas.append(f'sitemap aponta para página inexistente: {url}')
    if not conf['permitirIndexacao'] and sm.exists():
        problemas.append('sitemap.xml existe com indexação desligada')
    total = sum(f.stat().st_size for f in site.rglob('*') if f.is_file())
    mb = f'{total / 1024 ** 2:.0f} MB'
    if total > LIMITE_BYTES:
        problemas.append(f'site com {mb}: passa do limite de 1 GB do GitHub Pages; o deploy seria recusado. '
                         'Reduza fotos ou leve as imagens para outro armazenamento (docs/OPERACAO.md).')
    elif total > AVISO_BYTES:
        aviso(f'Site com {mb}, perto do limite de 1 GB do GitHub Pages. Planeje reduzir fotos ou mudar o armazenamento.')
    else:
        log('validar', f'tamanho do site: {mb} de 1024 MB')
    return problemas


def main():
    problemas = validar()
    if problemas:
        for p in problemas:
            erro(f'validar: {p}')
        sys.exit(1)
    log('validar', 'OK — catálogo, páginas, fotos e sitemap consistentes')


if __name__ == '__main__':
    main()
