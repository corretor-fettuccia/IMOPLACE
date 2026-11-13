"""ImoPlace CORE: integração direta pelo Google Sheets API (sem Web App público).

CORE é o único Apps Script, privado. O Actions usa token OAuth da conta de serviço
para LER FILA/IMOVEIS/IMAGENS e ACRESCENTAR RESULTADOS. Nunca escreve em IMOVEIS/FILA.
"""
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

from comum import CONTRATO

API = 'https://sheets.googleapis.com/v4/spreadsheets'
COLUMNS = ('IMOVEIS', 'IMAGENS', 'FILA', 'RESULTADOS')
EVENT_COLS = ['EVENTO_ID','JOB_ID','IMOVEL_ID','VERSAO','OPERACAO','STATUS','CODIGO',
              'MENSAGEM','URL','GITHUB_RUN_ID','DATA','IMAGENS_JSON']


def _sheet_id():
    sid = os.environ.get('PLANILHA_ID', '').strip()
    if not re.fullmatch(r'[a-zA-Z0-9_-]{20,}', sid):
        raise RuntimeError('Configure PLANILHA_ID no Secret/Variable do GitHub Actions.')
    return sid


def _token():
    token = os.environ.get('GOOGLE_ACCESS_TOKEN', '').strip()
    if not token:
        raise RuntimeError('GOOGLE_ACCESS_TOKEN ausente: autentique a conta Google com Sheets e Drive.')
    return token


def _request(url, *, method='GET', body=None):
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
    req = Request(url, data=data, method=method, headers={
        'Authorization': 'Bearer ' + _token(),
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
    })
    with urlopen(req, timeout=45) as r:
        return json.loads(r.read(20_000_000).decode('utf-8'))


def ler_tabelas():
    """Lê faixas por coluna, sem trazer proprietário privado nem miniatura Base64.

    O esquema de colunas é o da v3.0.0. Campos internos e MINIATURA não
    entram no workflow. A primeira linha de cada faixa contém o cabeçalho.
    """
    sid = _sheet_id()
    specs = [
        ('IMOVEIS', 'A1:AO'), ('IMOVEIS', 'AT1:AT'), ('IMOVEIS', 'AV1:BA'),
        ('IMAGENS', 'A1:K'), ('IMAGENS', 'M1:Q'),
        ('FILA', 'A1:I'), ('RESULTADOS', 'A1:L'),
    ]
    ranges = '&'.join('ranges=' + quote("'" + nome + "'!" + faixa, safe='') for nome, faixa in specs)
    ret = _request(f'{API}/{sid}/values:batchGet?{ranges}&valueRenderOption=UNFORMATTED_VALUE')
    vr = ret.get('valueRanges') or []
    if len(vr) != len(specs):
        raise RuntimeError('Leitura parcial do Google Sheets: faltam intervalos essenciais.')
    parts = {}
    for (nome, faixa), retorno in zip(specs, vr):
        linhas = retorno.get('values') or []
        if not linhas:
            raise RuntimeError(f'Aba {nome} vazia ou sem cabeçalho: execute a preparação do CORE.')
        cabecalho = [str(c).strip().upper() for c in linhas[0]]
        parts.setdefault(nome, []).append((cabecalho, linhas[1:]))
    saida = {}
    for nome, grupos in parts.items():
        cabecalho = [h for headers, _ in grupos for h in headers]
        qtd = max((len(rows) for _,rows in grupos), default=0)
        saida[nome] = []
        for i in range(qtd):
            registro = {}
            for headers, rows in grupos:
                v = rows[i] if i < len(rows) else []
                registro.update(zip(headers, v + ['']*max(0,len(headers)-len(v))))
            if any(x != '' for x in registro.values()):
                saida[nome].append(registro)
    if set(saida) != set(COLUMNS):
        raise RuntimeError('Acesso insuficiente às quatro abas principais do CORE.')
    if not set(EVENT_COLS).issubset(set(parts['RESULTADOS'][0][0])):
        raise RuntimeError('Aba RESULTADOS sem colunas necessárias ao feedback por imóvel.')
    return saida


def registrar_eventos(eventos):
    if not eventos:
        return
    url = f'{API}/{_sheet_id()}/values/{quote("RESULTADOS!A:L", safe="")}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS'
    agora = datetime.now(timezone.utc).isoformat()
    linhas = []
    for e in eventos:
        e = dict(e)
        e.setdefault('DATA', agora)
        e.setdefault('EVENTO_ID', f'{e.get("JOB_ID", "")}-{e.get("IMOVEL_ID", "")}-{e.get("STATUS", "")}')
        linhas.append([str(e.get(col, '')) for col in EVENT_COLS])
    _request(url, method='POST', body={'majorDimension':'ROWS', 'values':linhas})


def _n(v, padrao=0):
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return padrao


def _numero(v):
    if v is None or v == '':
        return None
    try:
        return float(str(v).replace(',', '.'))
    except ValueError:
        return None


def _flag(v):
    return str(v).upper() in ('SIM', 'TRUE', '1')


def _slug(v):
    import unicodedata
    s = ''.join(c for c in unicodedata.normalize('NFD', str(v or '')) if unicodedata.category(c) != 'Mn')
    return re.sub(r'(^-+|-+$)', '', re.sub('[^a-z0-9]+', '-', s.lower()))[:60].rstrip('-') or 'imovel'


def _lista(v):
    return [x.strip() for x in re.split(r'[,;\n]', str(v or '')) if x.strip()][:40]


def _fotos(im, rows, pendente=False):
    iid = str(im['ID']); capa = str(im.get('IMAGEM_CAPA_ID', ''))
    # No feed, foto marcada para exclusão ainda existe no site até confirmação.
    # No manifesto candidato, a exclusão deve ser aplicada.
    fotografias = [f for f in rows if str(f.get('IMOVEL_ID')) == iid and (not pendente or f.get('OPERACAO') != 'excluir')]
    fotografias.sort(key=lambda f: (str(f.get('IMAGEM_ID')) != capa, _n(f.get('ORDEM')), str(f.get('IMAGEM_ID'))))
    fotos = []
    for n, f in enumerate(fotografias, 1):
        versao = _n(f.get('VERSAO' if pendente else 'VERSAO_PUBLICADA'))
        if not versao:
            continue
        name = (_slug(re.sub(r'\.[a-z0-9]+$', '', str(f.get('NOME','')), flags=re.I))[:40] or 'foto')
        if name == 'imovel': name = 'foto'
        imagem_id = str(f['IMAGEM_ID'])
        nome = f'{name}-{imagem_id.lower()}.v{versao}.webp'
        fotos.append({'id': imagem_id, 'versao': versao, 'arquivo': f'imoveis/{_slug(im.get("SLUG") or im.get("TITULO"))}-{iid}/imagens/{nome}',
                      'legenda':str(f.get('LEGENDA') or f'Foto {n}')[:80], 'alt':str(f.get('ALT') or f'{im.get("TITULO")} — foto {n}')[:160]})
    return fotos


def _publico(im, imagens, site):
    iid = str(im['ID']); codigo = _slug(im.get('SLUG') or im.get('TITULO')) + '-' + iid
    caminho = f'imoveis/{codigo}/'; titulo = str(im.get('TITULO',''))[:160]
    fotos = _fotos(im, imagens)
    def txt(key, limite=200): return str(im.get(key) or '')[:limite]
    item = dict(id=iid, versao=_n(im.get('VERSAO')), versaoPublicada=_n(im.get('VERSAO_PUBLICADA')),
        codigo=codigo,categoria=str(im.get('CATEGORIA','')),status='publicado',tipo=txt('TIPO',40),condicao=txt('CONDICAO',20),
        destaque=_flag(im.get('DESTAQUE')),tag=txt('TAG',30),ordem=_n(im.get('ORDEM')),titulo=titulo,
        descricao=txt('DESCRICAO',8000),seo={'titulo':txt('TITULO_SEO',70) or titulo,'descricao':txt('DESCRICAO_SEO',170) or txt('DESCRICAO',160)},
        preco=_numero(im.get('PRECO')),condominio=_numero(im.get('CONDOMINIO')),iptuAnual=_numero(im.get('IPTU_ANUAL')),
        financiamento=_flag(im.get('FINANCIAMENTO')),permuta=_flag(im.get('PERMUTA')),
        documentacaoEmDia=_flag(im.get('DOCUMENTACAO_OK')),dormitorios=_numero(im.get('DORMITORIOS')),
        suites=_numero(im.get('SUITES')),banheiros=_numero(im.get('BANHEIROS')),
        vagas=_numero(im.get('VAGAS')),areaTotal=_numero(im.get('AREA_TOTAL')),areaUtil=_numero(im.get('AREA_UTIL')),
        localizacao={'bairro':txt('BAIRRO',80),'cidade':txt('CIDADE',80),'uf':txt('UF',2).upper(),
                     'endereco':txt('ENDERECO_PUBLICO',160),'lat':_numero(im.get('LAT')),'lng':_numero(im.get('LNG'))},
        comodidades=_lista(im.get('COMODIDADES')),caracteristicasImovel=_lista(im.get('CARACT_IMOVEL')),
        caracteristicasCondominio=_lista(im.get('CARACT_CONDOMINIO')),
        anunciante={'nome':txt('ANUNCIANTE_NOME',80),'creci':txt('CRECI',30),'whatsapp':re.sub(r'\D','',txt('WHATSAPP'))[:15]},
        feeds={'google':_flag(im.get('PUBLICAR_GOOGLE')),'meta':_flag(im.get('PUBLICAR_META')),
               'disponibilidade':str(im.get('DISPONIBILIDADE') or 'in_stock')},
        imagemCapaId=fotos[0]['id'] if fotos else '', imagens=fotos,
        caminho=caminho,url=site.rstrip('/')+'/'+caminho,atualizadoEm=str(im.get('ATUALIZADO_EM') or ''))
    return item


def _manifesto(im, fotos):
    iid=str(im['ID']); codigo=_slug(im.get('SLUG') or im.get('TITULO'))+'-'+iid
    lista=[]
    for f in fotos:
        if str(f.get('IMOVEL_ID')) != iid: continue
        versao=_n(f.get('VERSAO'))
        imagem_id=str(f.get('IMAGEM_ID'))
        base=_slug(re.sub(r'\.[a-z0-9]+$', '', str(f.get('NOME','')), flags=re.I))[:40]
        if base=='imovel': base='foto'
        lista.append(dict(imagemId=imagem_id,driveFileId=str(f.get('DRIVE_FILE_ID','')),
            nome=str(f.get('NOME','')),legenda=str(f.get('LEGENDA','')),alt=str(f.get('ALT','')),
            ordem=_n(f.get('ORDEM')),versao=versao,versaoPublicada=_n(f.get('VERSAO_PUBLICADA')),
            sha256=str(f.get('SHA256','')).lower(),bytes=_n(f.get('BYTES')),operacao=str(f.get('OPERACAO','')),
            arquivo=f'{base}-{imagem_id.lower()}.v{versao}.webp'))
    return {'imovelId':iid,'versao':_n(im.get('VERSAO')),'status':str(im.get('STATUS')),
            'caminho':f'imoveis/{codigo}/','capaId':str(im.get('IMAGEM_CAPA_ID','')),'imagens':lista}


MAX_TENTATIVAS = 3          # tentativas automáticas por imóvel/versão; depois, só "Sincronizar agora"
ESPERA_APOS_ERRO_MIN = 30   # intervalo entre uma falha e a próxima tentativa automática
RESERVA_ATIVA_MIN = 40      # workflow expira após 30 min; margem para o envio do resultado


def _ultimo_por_versao(resultados):
    """Retorno antigo não encerra uma tentativa posterior do mesmo imóvel/versão."""
    ult, ativos = {}, {}
    for e in resultados:
        key=(str(e.get('IMOVEL_ID')), _n(e.get('VERSAO')))
        st=str(e.get('STATUS',''))
        job=str(e.get('JOB_ID',''))
        if st == 'PROCESSANDO':
            ativos[key]=job
            ult[key]=e
        elif st in ('ERRO','PUBLICADO','DESPUBLICADO') and (key not in ativos or job == ativos[key]):
            ult[key]=e
    return ult


def _tentativas_por_versao(resultados):
    """Só uma tentativa por JOB_ID; repetição de eventos não esgota a fila."""
    tent, jobs = {}, {}
    for i,e in enumerate(resultados):
        if str(e.get('STATUS')) != 'PROCESSANDO':
            continue
        key=(str(e.get('IMOVEL_ID')), _n(e.get('VERSAO')))
        job=str(e.get('JOB_ID') or 'evento-'+str(i))
        vistos=jobs.setdefault(key,set())
        if job not in vistos:
            vistos.add(job)
            tent[key]=len(vistos)
    return tent


def _minutos_desde(data, agora):
    try:
        quando=datetime.fromisoformat(str(data).replace('Z','+00:00'))
        if quando.tzinfo is None:
            quando=quando.replace(tzinfo=timezone.utc)
        return (agora-quando).total_seconds()/60
    except ValueError:
        return float('inf')  # data ilegível não pode travar a fila


def selecionar_job(tabelas, job_id, forcar=False, limite=20, agora=None):
    """Escolhe o lote. Falha não para a fila: o imóvel é tentado de novo sozinho, até MAX_TENTATIVAS, com
    ESPERA_APOS_ERRO_MIN entre as tentativas. Esgotadas, só "Sincronizar agora" (forcar) tenta de novo, e o
    CORE avisa o operador por e-mail."""
    agora=agora or datetime.now(timezone.utc)
    imoveis={str(i['ID']):i for i in tabelas['IMOVEIS']}
    ult=_ultimo_por_versao(tabelas['RESULTADOS'])
    tentativas=_tentativas_por_versao(tabelas['RESULTADOS'])
    elegiveis=[]; aguardando=[]
    for f in tabelas['FILA']:
        iid=str(f.get('IMOVEL_ID')); vers=_n(f.get('VERSAO'))
        im=imoveis.get(iid)
        if not im or _n(im.get('VERSAO'))!=vers: continue
        last=ult.get((iid,vers),{})
        status=str(last.get('STATUS',''))
        if status in ('PUBLICADO','DESPUBLICADO'): continue
        # Não reservar um imóvel que ainda pode estar sendo publicado, nem com 'forcar'.
        if status == 'PROCESSANDO' and _minutos_desde(last.get('DATA'), agora) < RESERVA_ATIVA_MIN: continue
        if not forcar:
            if tentativas.get((iid,vers),0) >= MAX_TENTATIVAS: continue
            if status == 'ERRO' and _minutos_desde(last.get('DATA'), agora) < ESPERA_APOS_ERRO_MIN: continue
        elegiveis.append((iid,vers,im,f))
    elegiveis.sort(key=lambda x:str(x[3].get('SOLICITADO_EM','')))
    escolhidas=elegiveis[:limite]
    aguardando=[p[0] for p in elegiveis[limite:]]
    pend=[]
    for iid,vers,im,f in escolhidas:
        p=_manifesto(im,tabelas['IMAGENS']);p['versao']=vers;p['motivo']=str(f.get('MOTIVO',''))
        pend.append(p)
    return {'ok':True,'jobId':job_id,'contrato':CONTRATO,'pendencias':pend,'aguardando':aguardando}


def montar_feed(tabelas, url):
    publicados=[]
    for im in tabelas['IMOVEIS']:
        if str(im.get('STATUS'))!='publicado': continue
        iid=str(im.get('ID',''))
        if not iid.isdigit() or im.get('CATEGORIA') not in ('venda','lancamento') or not im.get('TITULO'):
            raise RuntimeError(f'Cadastro publicado incompleto no Sheets: imóvel {iid}')
        publicados.append(_publico(im,tabelas['IMAGENS'],url))
    publicados.sort(key=lambda x:(-int(x['destaque']), x['ordem'], -int(x['id'])))
    return {'ok':True,'contrato':CONTRATO,'snapshotCompleto':True,'total':len(publicados),'imoveis':publicados}


def validar_reserva(job_id, dados):
    tbl=ler_tabelas()
    selecionadas={p['imovelId']:p for p in dados.get('imoveis',[])}
    for iid,p in selecionadas.items():
        im=next((x for x in tbl['IMOVEIS'] if str(x['ID'])==iid),None)
        fila=next((x for x in tbl['FILA'] if str(x.get('IMOVEL_ID'))==iid),None)
        if not im or not fila or _n(im.get('VERSAO'))!=_n(p['versao']) or _n(fila.get('VERSAO'))!=_n(p['versao']):
            raise RuntimeError(f'Versão da fila alterada para imóvel {iid}; deploy cancelado.')
        atual = _ultimo_por_versao(tbl['RESULTADOS']).get((iid, _n(p['versao'])), {})
        if str(atual.get('JOB_ID')) != job_id or str(atual.get('STATUS')) != 'PROCESSANDO':
            raise RuntimeError(f'A reserva de {iid} não pertence mais ao job {job_id}; deploy cancelado.')
    return {'ok':True}


def reportar(job_id, status, dados):
    import json as _json
    from comum import estado_dir, ler_json
    j=ler_json(estado_dir()/'job.json') or {}
    if str(j.get('jobId'))!=str(job_id): raise RuntimeError('JOB_ID não corresponde ao estado local.')
    versoes={str(p['imovelId']):p for p in j.get('pendencias',[])}
    if status=='ERRO':
        especificos={str(e['imovelId']):e.get('erro','') for e in dados.get('imoveis',[])}
        ids=especificos.keys() if especificos else versoes.keys()
        entries=[{'JOB_ID':job_id,'IMOVEL_ID':iid,'VERSAO':versoes[iid]['versao'],
                  'OPERACAO':versoes[iid]['motivo'],'STATUS':'ERRO','CODIGO':'DEPLOY_FAILED',
                  'MENSAGEM':str(especificos.get(iid) or dados.get('erro') or 'Falha de publicação')[:300],
                  'GITHUB_RUN_ID':os.environ.get('GITHUB_RUN_ID','')} for iid in ids if iid in versoes]
    else:
        entries=[]
        fotos_por_id={}
        for f in dados.get('imagens',[]):
            # imagens confirmadas podem ter seu IMOVEL_ID apenas no manifesto
            for p in versoes.values():
                if any(str(i['imagemId'])==str(f.get('imagemId')) for i in p.get('imagens',[])):
                    fotos_por_id.setdefault(p['imovelId'],[]).append(f)
                    break
        for c in dados.get('imoveis',[]):
            iid=str(c.get('imovelId'))
            p=versoes.get(iid)
            if not p or _n(c.get('versao'))!=_n(p['versao']): continue
            no_site=bool(c.get('noSite'))
            entries.append({'JOB_ID':job_id,'IMOVEL_ID':iid,'VERSAO':p['versao'],
                  'OPERACAO':str(p.get('motivo','')),'STATUS':'PUBLICADO' if no_site else 'DESPUBLICADO',
                  'CODIGO':'PUBLISHED_OK' if no_site else 'UNPUBLISHED_OK',
                  'MENSAGEM':'Publicação verificada no GitHub Pages',
                  'URL':os.environ.get('SITE_URL','').rstrip('/')+'/'+p.get('caminho','') if no_site else '',
                  'GITHUB_RUN_ID':os.environ.get('GITHUB_RUN_ID',''),
                  'IMAGENS_JSON':_json.dumps(fotos_por_id.get(iid,[]),ensure_ascii=False,separators=(',',':'))})
    registrar_eventos(entries)
    return {'ok':True,'resultados':[{'imovelId':e['IMOVEL_ID'],'codigo':e['CODIGO']} for e in entries]}
