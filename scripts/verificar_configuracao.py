#!/usr/bin/env python3
"""Verifica o contrato de nomes e, no workflow, a existência das configurações."""
import argparse, os, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ('API_PUBLICA_URL', 'API_INTEGRACAO_ACTIONS_URL', 'SEGREDO_INTEGRACAO')
LEGACY = ('FEED_URL', 'INTEGRACAO_URL', 'INTEGRACAO_SEGREDO', 'CONFERIR_URL')

def conferir_contrato():
    sources = [(ROOT / '.github/workflows/publicar.yml').read_text('utf8'),
               (ROOT / 'scripts/integracao.py').read_text('utf8')]
    failures = []
    for key in REQUIRED:
        if not all(re.search(r'\b' + key + r'\b', src) for src in sources):
            failures.append('Nomenclatura divergente: ' + key)
    for key in LEGACY:
        if any(re.search(r'\b' + key + r'\b', src) for src in sources):
            failures.append('Nome obsoleto no código: ' + key)
    return failures

def conferir_ambiente():
    failures = []
    for key in REQUIRED:
        v = os.getenv(key, '').strip()
        if not v:
            failures.append('GitHub Actions: configurar ' + key)
        elif key.endswith('_URL') and not re.fullmatch(r'https://script\.google\.com/macros/s/[^/]+/exec', v):
            failures.append('URL /exec inválida em ' + key)
        elif key == 'SEGREDO_INTEGRACAO' and len(v) < 32:
            failures.append('SEGREDO_INTEGRACAO necessita de 32+ caracteres')
    return failures

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workflow', action='store_true')
    args = parser.parse_args()
    errors = conferir_contrato() + (conferir_ambiente() if args.workflow else [])
    for error in errors: print('ERRO:', error)
    if errors: raise SystemExit(1)
    print('OK: nomes de integração consistentes' + (' e configurações presentes' if args.workflow else ''))
