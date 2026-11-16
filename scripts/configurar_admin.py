"""Atualiza os dois atalhos administrativos com a URL da NOVA implantação privada."""
import re
import sys
from pathlib import Path

def configurar(url):
    if not re.fullmatch(r'https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec',url):
        raise ValueError('Informe a URL /exec do aplicativo da Web privado.')
    raiz=Path(__file__).resolve().parent.parent
    for rel in ('adm/index.html','site/adm/index.html'):
        p=raiz/rel
        texto=p.read_text()
        novo,n=re.subn(r'https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec',url,texto)
        if not n: raise ValueError('Atalho sem destino conhecido: '+rel)
        p.write_text(novo)
    print('Atalhos administrativos atualizados. Envie os arquivos ao repositório e publique o site.')

if __name__=='__main__': configurar(sys.argv[1])
