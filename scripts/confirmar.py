#!/usr/bin/env python3
"""ImoPlace v2.3 — etapa [8/8] confirmar."""
import sys
from comum import erro
from etapas import confirmar

if __name__ == '__main__':
    try:
        confirmar()
    except Exception as exc:
        erro('[8/8] ' + str(exc))
        sys.exit(1)
