#!/usr/bin/env python3
"""ImoPlace v2.3 — etapa [3/8] montar_imoveis."""
import sys
from comum import erro
from etapas import montar_imoveis

if __name__ == '__main__':
    try:
        montar_imoveis()
    except Exception as exc:
        erro('[3/8] ' + str(exc))
        sys.exit(1)
