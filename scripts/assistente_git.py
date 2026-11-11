#!/usr/bin/env python3
from pathlib import Path
import json,os,argparse,re
ap=argparse.ArgumentParser();ap.add_argument('--diretorio',required=True,type=Path);root=ap.parse_args().diretorio
folder=root/'.instalacao-local';folder.mkdir(exist_ok=True,mode=0o700);os.chmod(folder,0o700)
previous=folder/'configuracao.json'
old=json.loads(previous.read_text('utf8')) if previous.exists() else {}
fields=[('GITHUB_REPO','Repositório GitHub (usuario/repositorio)',''),('GITHUB_BRANCH','Branch do GitHub','main'),('SITE_URL','URL pública do portal','https://imoplace.com.br'),('FEED_URL','URL /exec da API pública A (opcional agora)',''),('INTEGRACAO_URL','URL /exec da integração C (opcional agora)',''),('CONFERIR_URL','URL de conferência do Pages (opcional agora)','')]
values={}
for k,label,default in fields:
 while True:
  value=input(f'{label} [{old.get(k,default) or "preencher depois"}]: ').strip() or old.get(k,default)
  if k=='GITHUB_REPO' and value and not re.fullmatch(r'[\w.-]+/[\w.-]+',value):print('Formato esperado: usuario/repositorio');continue
  if k.endswith('URL') and value and not value.startswith('https://'):print('Use HTTPS');continue
  if k in ('FEED_URL','INTEGRACAO_URL') and value and not value.endswith('/exec'):print('URL deve terminar em /exec');continue
  values[k]=value;break
values['CONFERIR_URL']=values['CONFERIR_URL'] or values['SITE_URL']
def write(name,s):
 p=folder/name;fd=os.open(str(p),os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
 with os.fdopen(fd,'w',encoding='utf8') as f:f.write(s)
 os.chmod(p,0o600)
write('configuracao.json',json.dumps(values,ensure_ascii=False,indent=2)+'\n')
write('GITHUB_CONFIGURACAO.txt', '# Repositório: '+(values['GITHUB_REPO'] or '<PREENCHER>')+'\n# Branch: '+values['GITHUB_BRANCH']+'\n# GitHub > Settings > Secrets and variables > Actions\n\n# Variables\nFEED_URL='+(values['FEED_URL'] or '<URL_API_A>')+'\nCONFERIR_URL='+values['CONFERIR_URL']+'\n\n# Secrets: preencha diretamente no GitHub\nINTEGRACAO_URL=<URL_API_C>\nINTEGRACAO_SEGREDO=<SEGREDO_HMAC_DO_APPS_SCRIPT>\nGOOGLE_CREDENTIALS=<JSON_CONTA_SERVICO_DRIVE>\n')
write('CHECKLIST.txt',"""[ ] Enviar GIT-PAGE para a raiz do repositório
[ ] Pages Source = GitHub Actions
[ ] Configurar secrets e variables
[ ] Conta de serviço Google com acesso leitura às fotos
[ ] Testar workflow e publicação
[ ] Integrar os ambientes segundo ../GUIA_INTEGRACAO.md
""")
print('Pronto: .instalacao-local/GITHUB_CONFIGURACAO.txt')
print('Nenhum projeto Apps Script foi alterado.')
