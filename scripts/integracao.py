"""Ponte interna CORE ↔ Google Sheets API.

Não existe API pública Apps Script. O transporte autentica via OAuth da conta
Google do Actions e acessa exclusivamente o banco Sheets e as fotos pelo Drive.
Fixtures locais usam INTEGRACAO_FIXTURE / FEED_FIXTURE para testes do gerador.
"""
import json
import os
from pathlib import Path


class Integracao:
    def __init__(self, fixture=None, **_):
        caminho = fixture or os.environ.get('INTEGRACAO_FIXTURE')
        self.fixture = Path(caminho) if caminho else None

    def chamar(self, acao: str, job_id: str, dados: dict) -> dict:
        if self.fixture:
            if acao == 'pendencias':
                return json.loads((self.fixture / 'pendencias.json').read_text(encoding='utf-8'))
            (self.fixture / f'saida-{acao}.json').write_text(
                json.dumps({'jobId': job_id, **dados}, ensure_ascii=False, indent=2), encoding='utf-8')
            return {'ok': True}
        if os.environ.get('CORE_GOOGLE') != '1':
            raise RuntimeError('CORE_GOOGLE não ativado; o Actions precisa usar a Google Sheets API.')
        import core_google
        if acao == 'pendencias':
            resp = core_google.selecionar_job(
                core_google.ler_tabelas(), job_id,
                forcar=bool(dados.get('forcar')),
                limite=int(os.environ.get('LOTE_MAXIMO','20')))
            if resp['pendencias']:
                core_google.registrar_eventos([{'JOB_ID':job_id,'IMOVEL_ID':p['imovelId'],
                    'VERSAO':p['versao'],'OPERACAO':p.get('motivo',''),
                    'STATUS':'PROCESSANDO','CODIGO':'PROCESSING',
                    'MENSAGEM':'GitHub Actions iniciou o processamento.',
                    'GITHUB_RUN_ID':os.environ.get('GITHUB_RUN_ID','')}
                    for p in resp['pendencias']])
            return resp
        if acao == 'validar':
            return core_google.validar_reserva(job_id, dados)
        if acao == 'confirmar':
            return core_google.reportar(job_id, 'SUCESSO', dados)
        if acao == 'falha':
            return core_google.reportar(job_id, 'ERRO', dados)
        raise RuntimeError('Ação não reconhecida pelo CORE: ' + acao)


def ler_feed(url=None) -> dict:
    fixture = os.environ.get('FEED_FIXTURE')
    if fixture:
        return json.loads(Path(fixture).read_text(encoding='utf-8'))
    if os.environ.get('CORE_GOOGLE') != '1':
        raise RuntimeError('CORE_GOOGLE não ativado; feed não disponível.')
    import core_google
    return core_google.montar_feed(core_google.ler_tabelas(), os.environ.get('SITE_URL') or 'https://imoplace.com.br')
