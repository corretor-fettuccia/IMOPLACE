#!/usr/bin/env python3
"""Valida nomenclatura e presença de configuração no workflow.

Contrato único:
- Actions Variables: API_PUBLICA_URL, API_INTEGRACAO_ACTIONS_URL, SITE_URL
- Actions Secrets: SEGREDO_INTEGRACAO, GOOGLE_CREDENTIALS

Em --workflow valida variáveis já resolvidas pelo GitHub Actions.
"""
import argparse
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / '.github' / 'workflows' / 'publicar.yml'
INTEGRACAO = ROOT / 'scripts' / 'integracao.py'
VARIABLES = ('API_PUBLICA_URL', 'API_INTEGRACAO_ACTIONS_URL', 'SITE_URL')
SECRETS = ('SEGREDO_INTEGRACAO', 'GOOGLE_CREDENTIALS')
LEGACY = ('FEED_URL', 'INTEGRACAO_URL', 'INTEGRACAO_SEGREDO', 'CONFERIR_URL')


def conferir_contrato():
    erros = []
    workflow = WORKFLOW.read_text('utf-8')
    integracao = INTEGRACAO.read_text('utf-8')
    for chave in VARIABLES:
        if not re.search(r'^\s*' + chave + r':\s*\$\{\{\s*vars\.' + chave + r'\s*\}\}', workflow, re.M):
            erros.append(f'Workflow: {chave} deve vir de vars.{chave} (aba Variables)')
    if not re.search(r'^\s*SEGREDO_INTEGRACAO:\s*\$\{\{\s*secrets\.SEGREDO_INTEGRACAO\s*\}\}', workflow, re.M):
        erros.append('Workflow: SEGREDO_INTEGRACAO deve vir de secrets.SEGREDO_INTEGRACAO (aba Secrets)')
    if not re.search(r'credentials_json:\s*\$\{\{\s*secrets\.GOOGLE_CREDENTIALS\s*\}\}', workflow):
        erros.append('Workflow: GOOGLE_CREDENTIALS deve vir da aba Secrets')
    for chave in ('API_PUBLICA_URL', 'API_INTEGRACAO_ACTIONS_URL', 'SEGREDO_INTEGRACAO'):
        if not re.search(r'\b' + chave + r'\b', integracao):
            erros.append('Cliente Python não utiliza: ' + chave)
    # Proibir referências obsoletas no código executável; documentação pode mencionar migração.
    for chave in LEGACY:
        if re.search(r'\b' + chave + r'\b', workflow + '\n' + integracao):
            erros.append(f'Nome antigo no código: {chave}. Migre no GitHub para os nomes v2.3.2.8.')
    return erros


def conferir_ambiente():
    erros = []
    for chave in VARIABLES[:2]:
        valor = os.getenv(chave, '').strip()
        if not valor:
            erros.append(f'Actions Variables: falta {chave} (Settings > Secrets and variables > Actions > Variables)')
        elif not re.fullmatch(r'https://script\.google\.com/macros/s/[^/\s?#]+/exec/?', valor):
            erros.append(f'Actions Variables: {chave} precisa ser URL /exec do Apps Script')
    url = os.getenv('SITE_URL', '').strip()
    if not url:
        erros.append('Actions Variables: falta SITE_URL (ex.: https://imoplace.com.br)')
    elif not re.fullmatch(r'https://[^/\s]+/?', url):
        erros.append('SITE_URL deve ser uma origem HTTPS sem caminho')
    segredo = os.getenv('SEGREDO_INTEGRACAO', '').strip()
    if not segredo:
        erros.append('Actions Secrets: falta SEGREDO_INTEGRACAO')
    elif len(segredo) < 32:
        erros.append('SEGREDO_INTEGRACAO precisa de 32+ caracteres')
    # As credenciais Drive sao necessárias para o download de imagens; não validar conteúdo para não exibir segredo.
    if not os.getenv('GOOGLE_CREDENTIALS', '').strip():
        erros.append('Actions Secrets: falta GOOGLE_CREDENTIALS (JSON da conta de serviço)')
    return erros


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workflow', action='store_true')
    args = ap.parse_args()
    erros = conferir_contrato()
    if args.workflow:
        erros.extend(conferir_ambiente())
    for erro in erros:
        print('ERRO:', erro)
    if erros:
        return 1
    print('OK: configuração GitHub padronizada' + (' e valores presentes' if args.workflow else ''))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
