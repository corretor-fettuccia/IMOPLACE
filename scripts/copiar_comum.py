#!/usr/bin/env python3
"""Copia apps-script/comum/*.gs para os projetos privado, publico e integracao.
Rode depois de editar qualquer arquivo em apps-script/comum/ e antes do clasp push."""
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2] / 'GOOGLE.APPSCRIPT'
PROJETOS = ('imoplace-API-PainelPrivado', 'imoplace-API-Publica', 'imoplace-API-IntegracaoActions')

if __name__ == '__main__':
    for arq in sorted((RAIZ / 'COMUM').glob('*.gs')):
        for p in PROJETOS:
            shutil.copyfile(arq, RAIZ / p / arq.name)
            print(f'{arq.name} -> {p}/')
