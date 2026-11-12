#!/usr/bin/env python3
"""Configuração GitHub independente do instalador Google."""
import argparse, json, os, re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--diretorio', type=Path, required=True)
root = p.parse_args().diretorio
out = root / '.instalacao-local'
out.mkdir(exist_ok=True, mode=0o700)
os.chmod(out, 0o700)
old_file = out / 'configuracao.json'
old = json.loads(old_file.read_text('utf-8')) if old_file.exists() else {}
fields = [
    ('GITHUB_REPO', 'Repositório GitHub (usuario/repositorio)', ''),
    ('GITHUB_BRANCH', 'Branch principal', 'main'),
    ('SITE_URL', 'URL oficial do portal (igual à propriedade SITE_URL no Apps Script)', 'https://imoplace.com.br'),
    ('API_PUBLICA_URL', 'URL /exec de imoplace-API-Publica (Enter para depois)', ''),
    ('API_INTEGRACAO_ACTIONS_URL', 'URL /exec de imoplace-API-IntegracaoActions (Enter para depois)', ''),
]
values = {}
for key, label, default in fields:
    while True:
        previous = old.get(key, default)
        value = input(f'{label} [{previous or "preencher depois"}]: ').strip() or previous
        if key == 'GITHUB_REPO' and value and not re.fullmatch(r'[\w.-]+/[\w.-]+', value):
            print('Use usuario/repositorio.'); continue
        if key.endswith('_URL') and value and not value.startswith('https://'):
            print('Use HTTPS.'); continue
        if key in ('API_PUBLICA_URL', 'API_INTEGRACAO_ACTIONS_URL') and value and not re.fullmatch(r'https://script\.google\.com/macros/s/[^/]+/exec', value):
            print('Use o endereço de implantação do Apps Script terminado em /exec.'); continue
        values[key] = value
        break

def save(name, content):
    path = out / name
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    os.chmod(path, 0o600)

save('configuracao.json', json.dumps(values, ensure_ascii=False, indent=2) + '\n')
save('GITHUB_CONFIGURACAO.txt', (
    '# IMOPLACE 2.3.2.8 — GITHUB ACTIONS\n'
    '# Repositório: ' + (values['GITHUB_REPO'] or '<PREENCHER>') + '\n'
    '# Branch: ' + values['GITHUB_BRANCH'] + '\n'
    '# Settings > Secrets and variables > Actions\n\n'
    '# VARIABLES\n'
    'API_PUBLICA_URL=' + (values['API_PUBLICA_URL'] or '<URL_EXEC_API_PUBLICA>') + '\n'
    'API_INTEGRACAO_ACTIONS_URL=' + (values['API_INTEGRACAO_ACTIONS_URL'] or '<URL_EXEC_API_INTEGRACAO_ACTIONS>') + '\n'
    'SITE_URL=' + values['SITE_URL'] + '\n\n'
    '# SECRETS: insira os valores diretamente no GitHub\n'
    'SEGREDO_INTEGRACAO=<MESMO_SEGREDO_INTEGRACAO_DO_APPS_SCRIPT_PRIVADO>\n'
    'GOOGLE_CREDENTIALS=<JSON_CONTA_SERVICO_DRIVE>\n\n'
    '# No Apps Script imoplace-API-IntegracaoActions:\n'
    '# CENTRAL_WRITER_URL=<URL_EXEC_POST_ASSINADO_DO_PAINEL_PRIVADO>\n'
    '# CENTRAL_WRITER_URL e API_INTEGRACAO_ACTIONS_URL são URLs distintas.\n'
))
save('CHECKLIST.txt', '''[ ] imoplace-API-Publica possui /exec
[ ] imoplace-API-IntegracaoActions possui /exec
[ ] API_PUBLICA_URL e API_INTEGRACAO_ACTIONS_URL em Actions Variables
[ ] SITE_URL igual no GitHub e no Apps Script
[ ] SEGREDO_INTEGRACAO igual no painel e no Actions Secrets
[ ] GOOGLE_CREDENTIALS possui leitura no Google Drive
[ ] GitHub Pages publicado via Actions
[ ] ./verificar.sh passou
''')
print('Configuração preparada em .instalacao-local/GITHUB_CONFIGURACAO.txt')
print('Nenhum projeto Google Apps Script foi modificado.')

print('\nCONFIGURAÇÃO OBRIGATÓRIA NO GITHUB PAGES:')
print('  Settings > Pages > Build and deployment > Source: GitHub Actions')
print('  NÃO escolha main → /(root) nem main → /docs.')
print('  main contém o código; site/ é publicado pelo workflow como / do domínio.')
print('  Exemplo: site/catalogo.json -> https://imoplace.com.br/catalogo.json')
