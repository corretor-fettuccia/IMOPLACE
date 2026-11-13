"""Carrega SITE_URL e LOTE_MAXIMO do Sheets, fonte operacional do único CORE."""
import json
import os
import re
from pathlib import Path
from urllib.parse import quote
from core_google import API, _sheet_id, _request


def carregar_configuracao():
    url = f'{API}/{_sheet_id()}/values/{quote("CONFIGURACOES!A1:B", safe="")}'
    rows = _request(url).get('values') or []
    if not rows or [str(x).upper() for x in rows[0]] != ['CHAVE','VALOR']:
        raise RuntimeError('Aba CONFIGURACOES inexistente: inicialize o CORE antes de rodar o Actions.')
    cfg = {str(r[0]):str(r[1]) for r in rows[1:] if len(r)>1}
    site = cfg.get('SITE_URL','').strip().rstrip('/')
    lote = cfg.get('LOTE_MAXIMO','').strip()
    if not re.fullmatch(r'https://[A-Za-z0-9.-]+', site):
        raise RuntimeError('SITE_URL inválida na aba CONFIGURACOES.')
    if not lote.isdigit() or not 1<=int(lote)<=100:
        raise RuntimeError('LOTE_MAXIMO inválido na aba CONFIGURACOES.')
    return site,lote


def main():
    site,lote=carregar_configuracao()
    raiz=Path(__file__).resolve().parent.parent
    conf=json.loads((raiz/'imoplace.json').read_text('utf-8'))
    conf['urlPublica']=site
    alvo=raiz/'estado'/'config-operacional.json'
    alvo.parent.mkdir(exist_ok=True)
    alvo.write_text(json.dumps(conf,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    env=os.environ.get('GITHUB_ENV')
    valores={'SITE_URL':site,'LOTE_MAXIMO':lote,'IMOPLACE_CONFIG':str(alvo)}
    if env:
        with open(env,'a',encoding='utf-8') as f:
            for k,v in valores.items(): f.write(f'{k}={v}\n')
    print('[core] Configuração operacional obtida do Sheets.')

if __name__=='__main__': main()
