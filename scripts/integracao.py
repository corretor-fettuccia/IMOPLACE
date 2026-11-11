"""ImoPlace — cliente da API de integração (Apps Script) e do feed público.

Assinatura: HMAC-SHA256(segredo, acao \\n ts \\n jobId \\n payload), payload = string JSON enviada.
Modo de teste/local: INTEGRACAO_FIXTURE=<pasta> lê pendencias.json e grava saida-<acao>.json;
FEED_FIXTURE=<arquivo> lê o feed de um arquivo.
"""
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from comum import UA, log


def _ler(req: Request, limite=20_000_000) -> dict:
    with urlopen(req, timeout=60) as r:
        bruto = r.read(limite + 1)
    if len(bruto) > limite:
        raise RuntimeError('Resposta grande demais')
    return json.loads(bruto.decode('utf-8-sig'))


def _tentar(fn, etapa, tentativas=3):
    ultimo = None
    for n in range(1, tentativas + 1):
        try:
            return fn()
        except (OSError, ValueError) as e:
            ultimo = e
            log(etapa, f'tentativa {n}/{tentativas} falhou: {e}')
            if n < tentativas:
                time.sleep(4 * n)
    raise RuntimeError(f'{etapa}: indisponível após {tentativas} tentativas ({ultimo})')


class Integracao:
    def __init__(self, url=None, segredo=None, fixture=None):
        self.fixture = Path(fixture or os.environ.get('INTEGRACAO_FIXTURE') or '') if (fixture or os.environ.get('INTEGRACAO_FIXTURE')) else None
        self.url = (url or os.environ.get('INTEGRACAO_URL', '')).strip()
        self.segredo = (segredo or os.environ.get('INTEGRACAO_SEGREDO', '')).strip()
        if not self.fixture:
            if not self.url.startswith('https://'):
                raise RuntimeError('Configure o secret INTEGRACAO_URL (URL /exec da API de integração).')
            if len(self.segredo) < 32:
                raise RuntimeError('Configure o secret INTEGRACAO_SEGREDO (32+ caracteres, igual ao do Apps Script).')

    @staticmethod
    def assinar(segredo: str, acao: str, ts: str, job_id: str, payload: str) -> str:
        msg = '\n'.join([acao, ts, job_id, payload]).encode('utf-8')
        return hmac.new(segredo.encode('utf-8'), msg, hashlib.sha256).hexdigest()

    def chamar(self, acao: str, job_id: str, dados: dict) -> dict:
        if self.fixture:
            if acao == 'pendencias':
                return json.loads((self.fixture / 'pendencias.json').read_text(encoding='utf-8'))
            (self.fixture / f'saida-{acao}.json').write_text(json.dumps({'jobId': job_id, **dados}, ensure_ascii=False, indent=2), encoding='utf-8')
            return {'ok': True}
        payload = json.dumps(dados, ensure_ascii=False, separators=(',', ':'))

        def enviar():
            ts = str(int(time.time()))  # nova assinatura a cada tentativa (o servidor recusa repetição)
            corpo = json.dumps({'acao': acao, 'ts': ts, 'jobId': job_id, 'payload': payload,
                                'assinatura': self.assinar(self.segredo, acao, ts, job_id, payload)}).encode('utf-8')
            req = Request(self.url, data=corpo, method='POST', headers={'Content-Type': 'application/json', 'User-Agent': UA})
            resp = _ler(req)
            if not isinstance(resp, dict) or resp.get('ok') is not True:
                raise ValueError(f'integração respondeu erro: {str(resp.get("erro") if isinstance(resp, dict) else resp)[:200]}')
            return resp
        return _tentar(enviar, f'integracao:{acao}')


def ler_feed(url=None) -> dict:
    fixture = os.environ.get('FEED_FIXTURE')
    if fixture:
        return json.loads(Path(fixture).read_text(encoding='utf-8'))
    url = (url or os.environ.get('FEED_URL', '')).strip()
    if not url.startswith('https://'):
        raise RuntimeError('Configure FEED_URL (URL /exec da API pública) em Settings > Secrets and variables > Actions > Variables.')
    partes = urlsplit(url)
    q = [(k, v) for k, v in parse_qsl(partes.query) if k != 'atual'] + [('atual', str(int(time.time())))]
    final = urlunsplit((partes.scheme, partes.netloc, partes.path, urlencode(q), ''))
    return _tentar(lambda: _ler(Request(final, headers={'User-Agent': UA, 'Accept': 'application/json', 'Cache-Control': 'no-cache'})), 'feed')
