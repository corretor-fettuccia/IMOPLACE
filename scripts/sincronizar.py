#!/usr/bin/env python3
"""ImoPlace v2.3 — etapa [1/8] sincronizar."""
import sys
from comum import erro
from etapas import sincronizar

if __name__ == '__main__':
    try:
        sincronizar()
    except Exception as exc:
        erro('[1/8] ' + str(exc))
        sys.exit(1)
