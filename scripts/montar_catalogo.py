#!/usr/bin/env python3
"""ImoPlace v2.3 — etapa [2/8] montar_catalogo."""
import sys
from comum import erro
from etapas import montar_catalogo

if __name__ == '__main__':
    try:
        montar_catalogo()
    except Exception as exc:
        erro('[2/8] ' + str(exc))
        sys.exit(1)
