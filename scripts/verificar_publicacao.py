#!/usr/bin/env python3
"""Contrato de publicação do GitHub Pages: / do domínio == conteúdo de site/.

Não faz chamadas externas nem requer credenciais. No workflow usa --estrutura e --artefato.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / '.github' / 'workflows' / 'publicar.yml'
PUBLICO = ROOT / 'site'
ARTEFATO = ROOT / 'estado' / 'publicacao'


def verificar_estrutura():
    erros = []
    if not WORKFLOW.is_file():
        return ['Workflow .github/workflows/publicar.yml não encontrado']
    texto = WORKFLOW.read_text(encoding='utf-8')
    # Conferências limitadas aos valores literais usados pelo nosso workflow.
    for chave, regex in [
        ('upload-pages-artifact', r'uses:\s*actions/upload-pages-artifact@v\d+'),
        ('deploy-pages', r'uses:\s*actions/deploy-pages@v\d+'),
        ('origem do upload', r'path:\s*[.\/]*estado/publicacao\s*(?:\n|$)'),
        ('gerador do artefato', r'run:\s*python -u scripts/montar_site\.py'),
    ]:
        if not re.search(regex, texto):
            erros.append('Workflow não contém a configuração esperada: ' + chave)
    if not re.search(r'(?m)^\s*pages:\s*write\s*$', texto):
        erros.append('Workflow sem permissão pages: write')
    if not re.search(r'(?m)^\s*id-token:\s*write\s*$', texto):
        erros.append('Workflow sem permissão id-token: write')
    for nome in ('index.html', 'catalogo.json', '.nojekyll'):
        if not (PUBLICO / nome).is_file():
            erros.append('Arquivo ausente na raiz de site/: ' + nome)
    if (ROOT / 'index.html').exists():
        erros.append('index.html está na raiz do repositório; manter apenas em site/')
    return erros


def verificar_artefato():
    erros = verificar_estrutura()
    for nome in ('index.html', 'catalogo.json', 'publicacao.json'):
        if not (ARTEFATO / nome).is_file():
            erros.append('Artefato não contém na RAIZ: ' + nome)
    if (ARTEFATO / 'site').exists():
        erros.append('Artefato contém pasta site/ adicional (publicaria /site/ em vez de /)')
    for nome in ('scripts', 'docs', '.github', 'estado'):
        if (ARTEFATO / nome).exists():
            erros.append('Arquivo administrativo indevido no artefato: ' + nome)
    if (ARTEFATO / 'publicacao.json').is_file() and (ARTEFATO / 'catalogo.json').is_file():
        import hashlib
        try:
            m = json.loads((ARTEFATO / 'publicacao.json').read_text('utf-8'))
            esperado = hashlib.sha256((ARTEFATO / 'catalogo.json').read_bytes()).hexdigest()
            if m.get('catalogoSha256') != esperado or not m.get('jobId'):
                erros.append('publicacao.json não coincide com o catálogo da execução')
        except (OSError, ValueError):
            erros.append('publicacao.json inválido')
    return erros


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument('--estrutura', action='store_true')
    grupo.add_argument('--artefato', action='store_true')
    args = parser.parse_args()
    erros = verificar_artefato() if args.artefato else verificar_estrutura()
    for erro in erros:
        print('ERRO: ' + erro, file=sys.stderr)
    if erros:
        return 1
    print('OK: site/index.html é /index.html no Pages; catálogo é /catalogo.json; scripts privados excluídos.')
    print('ATENÇÃO: no GitHub Settings > Pages > Source selecione GitHub Actions (não Deploy from a branch).')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
