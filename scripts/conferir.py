#!/usr/bin/env python3
"""ImoPlace v2.3 — etapa [7/8] conferir."""
import sys
from comum import erro
from etapas import conferir

if __name__ == '__main__':
    try:
        conferir()
    except Exception as exc:
        erro('[7/8] ' + str(exc))
        sys.exit(1)
