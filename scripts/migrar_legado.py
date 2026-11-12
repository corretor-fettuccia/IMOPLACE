#!/usr/bin/env python3
"""Migra URLs v2.2 /imovel/{categoria}/{slug}-{id}/ para /imoveis/{slug}-{id}/.

Mantém apenas HTML de redirecionamento das URLs antigas já publicadas; remove imagens antigas.
"""
import re
import shutil
import paginas
from comum import config, ler_json, log, site_dir

RE_ID = re.compile(r'-(\d+)$')

def executar(site=None, conf=None):
    site = site or site_dir()
    conf = conf or config()
    catalogo = ler_json(site / 'catalogo.json', {}) or {}
    ativos = {str(i['id']): i for i in catalogo.get('imoveis', [])}
    legado = site / 'imovel'
    if not legado.is_dir():
        return 0
    quantidade = 0
    for categoria in list(legado.iterdir()):
        if not categoria.is_dir():
            continue
        for pasta in list(categoria.iterdir()):
            if not pasta.is_dir():
                continue
            m = RE_ID.search(pasta.name)
            destino = ativos.get(m.group(1)) if m else None
            shutil.rmtree(pasta)
            if destino:
                from comum import gravar
                gravar(pasta / 'index.html', paginas.redirecionamento('imoveis/' + destino['codigo'] + '/', conf))
                quantidade += 1
        if not any(categoria.iterdir()):
            categoria.rmdir()
    log('migração', f'{quantidade} URL(s) antigas redirecionadas')
    return quantidade

if __name__ == '__main__':
    executar()
