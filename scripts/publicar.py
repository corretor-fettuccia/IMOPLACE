#!/usr/bin/env python3
"""ImoPlace — orquestrador chamado pelo workflow (.github/workflows/publicar.yml).

  python scripts/publicar.py pendencias   consulta a fila (marca em_processamento) → estado/job.json
  python scripts/publicar.py gerar        feed + fotos novas do Drive → site/ (catálogo, páginas, feeds)
  python scripts/publicar.py conferir     espera o site no ar refletir este job
  python scripts/publicar.py confirmar    ACK das versões publicadas (+ falhas isoladas)
  python scripts/publicar.py falha        registra falha geral do job (itens voltam a pendente/erro)

Variáveis: INTEGRACAO_URL, INTEGRACAO_SEGREDO, FEED_URL, GOOGLE_ACCESS_TOKEN, FORCAR, CONFERIR_URL.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import contrato
import gerador
from comum import UA, config, erro, estado_dir, gravar_json, ler_json, log, saida_github, site_dir
from integracao import Integracao, ler_feed

JOB = 'job.json'


def _job_id():
    run = os.environ.get('GITHUB_RUN_ID')
    if run:
        return f'gh-{run}-{os.environ.get("GITHUB_RUN_ATTEMPT", "1")}'
    return 'local-' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')


def _job():
    job = ler_json(estado_dir() / JOB)
    if not job:
        raise RuntimeError('estado/job.json ausente: rode "pendencias" antes.')
    return job


def cmd_pendencias():
    forcar = os.environ.get('FORCAR', '').lower() in ('true', '1', 'sim')
    job_id = _job_id()
    resp = Integracao().chamar('pendencias', job_id, {'forcar': forcar, 'motivo': os.environ.get('MOTIVO', '')[:60]})
    pend = contrato.validar_pendencias(resp)
    gravar_json(estado_dir() / JOB, {'jobId': job_id, 'forcar': forcar, 'pendencias': pend, 'inicio': time.time()})
    log('fila', f'job {job_id}: {len(pend)} imóvel(is) na fila {[p["imovelId"] for p in pend]}' + (' (reconstrução forçada)' if forcar else ''))
    saida_github('tem', 'true' if (pend or forcar) else 'false')


def cmd_gerar():
    job = _job()
    conf = config()
    itens = contrato.validar_feed(ler_feed())
    log('feed', f'{len(itens)} imóvel(is) publicados no feed')
    relatorio = gerador.montar(itens, job['pendencias'], site_dir(), conf)
    job['relatorio'] = relatorio
    gravar_json(estado_dir() / JOB, job)


def _buscar(url, metodo='GET'):
    req = Request(url, method=metodo, headers={'User-Agent': UA, 'Cache-Control': 'no-cache'})
    with urlopen(req, timeout=30) as r:
        return r.status, (r.read(2_000_000) if metodo == 'GET' else b'')


def cmd_conferir():
    job = _job()
    rel = job.get('relatorio') or {}
    base = (os.environ.get('CONFERIR_URL') or config()['urlPublica']).rstrip('/')
    import hashlib
    alvo = job['jobId']
    hash_local = hashlib.sha256((estado_dir() / 'publicacao' / 'catalogo.json').read_bytes()).hexdigest()
    fim = time.time() + 300
    while True:
        try:
            _, bruto = _buscar(f'{base}/publicacao.json?v={int(time.time())}')
            marker = json.loads(bruto.decode('utf-8'))
            if marker.get('jobId') == alvo and marker.get('catalogoSha256') == hash_local:
                _, corpo = _buscar(f'{base}/catalogo.json?v={int(time.time())}')
                if hashlib.sha256(corpo).hexdigest() == hash_local:
                    break
        except (OSError, ValueError, HTTPError, URLError) as e:
            log('conferir', f'aguardando implantação: {e}')
        if time.time() > fim:
            raise RuntimeError(f'O site {base} não refletiu o deployment {alvo} em 5 minutos; nada foi confirmado.')
        time.sleep(15)
    for c in rel.get('conferir', []):
        for caminho in filter(None, [c.get('pagina')] + c.get('fotos', [])):
            status, _ = _buscar(f'{base}/{caminho}', 'HEAD')
            if status != 200:
                raise RuntimeError(f'{base}/{caminho} respondeu HTTP {status}')
    log('conferir', f'OK — {base} serve a implantação {alvo}')


def cmd_confirmar():
    job = _job()
    rel = job.get('relatorio') or {}
    cli = Integracao()
    if rel.get('falhas'):
        cli.chamar('falha', job['jobId'], {'erro': 'Falha em parte dos imóveis', 'imoveis': rel['falhas']})
        log('confirmar', f'{len(rel["falhas"])} imóvel(is) com falha registrados para nova tentativa')
    dur = int(time.time() - job.get('inicio', time.time()))
    conf = rel.get('confirmar') or {'imoveis': [], 'imagens': []}
    cli.chamar('confirmar', job['jobId'], {**conf, 'transferidas': rel.get('transferidas', 0), 'bytes': rel.get('bytes', 0),
                                           'detalhe': f'{len(conf["imoveis"])} confirmados, {rel.get("transferidas", 0)} fotos, {dur}s'})
    log('confirmar', f'ACK enviado: {[(i["imovelId"], i["versao"]) for i in conf["imoveis"]]}')


def cmd_falha():
    job = ler_json(estado_dir() / JOB)
    if not job:
        log('falha', 'sem job registrado; nada a informar')
        return
    motivo = os.environ.get('MOTIVO_FALHA') or 'Execução do GitHub Actions falhou (veja o log do workflow).'
    Integracao().chamar('falha', job['jobId'], {'erro': motivo[:300]})
    log('falha', f'job {job["jobId"]}: falha registrada; itens voltam para a próxima execução')




def cmd_validar_reserva():
    job = _job()
    rel = job.get('relatorio') or {}
    itens = rel.get('confirmar', {}).get('imoveis') or []
    if not itens:
        raise RuntimeError('Sem confirmação candidata; não publicar.')
    Integracao().chamar('validar', job['jobId'], {'imoveis': itens})
    log('validar-reserva', 'Versões atuais conferidas no escritor central antes do deploy')

COMANDOS = {'pendencias': cmd_pendencias, 'gerar': cmd_gerar, 'conferir': cmd_conferir, 'confirmar': cmd_confirmar, 'falha': cmd_falha, 'validar-reserva': cmd_validar_reserva}

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in COMANDOS:
        print(__doc__)
        sys.exit(2)
    try:
        COMANDOS[sys.argv[1]]()
    except Exception as e:  # noqa: BLE001 — mensagem curta no log do Actions
        erro(f'{sys.argv[1]}: {e}')
        sys.exit(1)
