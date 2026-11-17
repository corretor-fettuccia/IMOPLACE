"""Publica somente a URL e ativação do monitor. Nenhuma credencial ou contador."""
import json
import re
from urllib.parse import quote
from core_google import API, _sheet_id, _request

def publicar_config_monitor(site):
    url=f'{API}/{_sheet_id()}/values/{quote("CONFIGURACOES!A1:B",safe="")}'
    rows=_request(url).get('values') or []
    cfg={str(r[0]):str(r[1]) for r in rows[1:] if len(r)>1}
    api=cfg.get('MONITOR_API_URL','').strip()
    if api and not re.fullmatch(r'https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec',api):
        raise ValueError('URL da API Monitor inválida.')
    ativo=cfg.get('MONITOR_ATIVO')=='SIM' and bool(api)
    site.mkdir(parents=True,exist_ok=True)
    (site/'monitor-config.json').write_text(json.dumps({'ativo':ativo,'url':api if ativo else ''},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
