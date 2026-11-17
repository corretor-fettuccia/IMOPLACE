"""Reaplica marketing a todas as páginas, inclusive sem fila de imóveis."""
import json,re
from pathlib import Path
from urllib.parse import quote
DEFAULT={'gtm':{'ativo':True,'id':'GTM-MKJDSLPS'}}
START='<!-- IMOPLACE MARKETING START -->'
END='<!-- IMOPLACE MARKETING END -->'
def carregar(site):
 from core_google import API,_sheet_id,_request
 rows=_request(f'{API}/{_sheet_id()}/values/{quote("CONFIGURACOES!A1:B",safe="")}').get('values') or []
 cfg={str(r[0]):str(r[1]) for r in rows[1:] if len(r)>1}
 data=json.loads(cfg.get('MARKETING_JSON') or json.dumps(DEFAULT))
 (site/'marketing-config.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
 return data

def aplicar(site,data=None):
 site=Path(site)
 if data is None:
  path=site/'marketing-config.json'
  data=json.loads(path.read_text()) if path.exists() else DEFAULT
 # Reject malformed IDs even if the sheet was edited outside the authenticated panel.
 for key,pat in [('gtm',r'GTM-[A-Z0-9]+'),('analytics',r'G-[A-Z0-9]+'),('conversao',r'AW-\d+')]:
  obj=data.get(key,{})
  if obj.get('ativo') and not re.fullmatch(pat,obj.get('id','')):raise ValueError('ID inválido: '+key)
 payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
 block=START+'\n<script>window.imoplaceMarketing='+payload+';</script>\n<script defer src="/assets/js/marketing.js"></script>\n'+END
 count=0
 for path in site.rglob('*.html'):
  if 'adm' in path.relative_to(site).parts:continue
  s=path.read_text(encoding='utf-8')
  if not re.search(r'<head\b[^>]*>',s,re.I):continue
  s=re.sub(r'\n?'+re.escape(START)+r'.*?'+re.escape(END),'',s,flags=re.S)
  # Migrate the exact manual installation from the previous turn.
  s=re.sub(r'<!-- Google Tag Manager -->.*?<!-- End Google Tag Manager -->','',s,flags=re.S)
  s=re.sub(r'<head\b[^>]*>',lambda m:m.group(0)+'\n'+block,s,count=1,flags=re.I)
  if s!=path.read_text(encoding='utf-8'):path.write_text(s,encoding='utf-8');count+=1
 return count
if __name__=='__main__':
 import sys
 print('Marketing: páginas atualizadas:',aplicar(Path(sys.argv[1] if len(sys.argv)>1 else 'site')))
