#!/usr/bin/env python3
"""ImoPlace v2.3 — etapa [6/8] montar_site."""
import sys
from comum import erro
from etapas import montar_site

if __name__ == '__main__':
    try:
        montar_site()
    except Exception as exc:
        erro('[6/8] ' + str(exc))
        sys.exit(1)
