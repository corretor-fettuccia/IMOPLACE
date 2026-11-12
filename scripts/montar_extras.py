#!/usr/bin/env python3
"""ImoPlace v2.3 — etapa [4/8] montar_extras."""
import sys
from comum import erro
from etapas import montar_extras

if __name__ == '__main__':
    try:
        montar_extras()
    except Exception as exc:
        erro('[4/8] ' + str(exc))
        sys.exit(1)
