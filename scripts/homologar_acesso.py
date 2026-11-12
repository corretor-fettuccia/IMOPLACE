#!/usr/bin/env python3
"""Homologa o acesso real das implantações /exec, como um visitante anônimo (sem login, sem segredo).

Confere:
  1. GET anônimo no escritor central (implantação POST do PainelPrivado) NÃO serve o painel.
  2. POST sem assinatura no escritor é recusado com JSON {ok:false} (implantação pública e protegida).
  3. POST sem assinatura na ponte IntegracaoActions chega ao escritor e volta recusado pelo HMAC.
  4. GET na ponte responde "Use POST assinado".

Uso:  python3 scripts/homologar_acesso.py [--escritor URL] [--ponte URL] [--ci]
Sem argumentos, lê GOOGLE.APPSCRIPT/.instalacao-local/URLs_APPSCRIPT.txt (gravado por continuar_configuracao.sh).
--ci (GitHub Actions, a cada execução): falha de rede vira aviso; implantação desprotegida derruba a execução.
Não envia segredo nenhum e não altera dados: as chamadas sem assinatura são recusadas antes de ler a planilha.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PACOTE = Path(__file__).resolve().parents[2]  # pasta do pacote (no repositório GitHub não existe)
RE_EXEC = re.compile(r'^(https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec|http://127\.0\.0\.1:\d+/[\w/]*)$')
SINAIS_PAINEL = ('ImoPlace — Painel', 'google.script.run', 'PainelJs')


def buscar(url, corpo=None):
    req = Request(url, data=corpo, method='POST' if corpo is not None else 'GET',
                  headers={'Content-Type': 'application/json', 'User-Agent': 'ImoPlace-Homologacao'})
    try:
        with urlopen(req, timeout=60) as r:
            return r.status, r.read(500_000).decode('utf-8', 'replace')
    except HTTPError as e:
        return e.code, e.read(500_000).decode('utf-8', 'replace')


def json_ou_none(texto):
    try:
        return json.loads(texto)
    except ValueError:
        return None


def urls_salvas():
    arq = PACOTE / 'GOOGLE.APPSCRIPT' / '.instalacao-local' / 'URLs_APPSCRIPT.txt'
    valores = {}
    if arq.is_file():
        for linha in arq.read_text(encoding='utf-8').splitlines():
            if '=' in linha:
                k, v = linha.split('=', 1)
                valores[k.strip()] = v.strip()
    return valores.get('imoplace-API-PainelPrivado-POST', ''), valores.get('imoplace-API-IntegracaoActions', '')


def homologar(escritor, ponte):
    """Devolve a lista de problemas (vazia = aprovado)."""
    problemas = []
    if escritor:
        _, html = buscar(escritor)
        if any(s in html for s in SINAIS_PAINEL):
            problemas.append('CRÍTICO: GET anônimo no escritor serviu o painel administrativo. Retire a implantação pública já.')
        else:
            print('[OK] GET anônimo no escritor não mostra o painel.')
        _, txt = buscar(escritor, b'{}')
        resp = json_ou_none(txt)
        if not isinstance(resp, dict):
            problemas.append('Escritor não respondeu JSON ao POST: a implantação POST precisa de "Quem pode acessar: qualquer pessoa".')
        elif resp.get('ok') is not False or 'malformada' not in str(resp.get('erro', '')):
            problemas.append(f'Escritor aceitou ou respondeu de forma inesperada a POST sem assinatura: {str(resp)[:160]}')
        else:
            print('[OK] Escritor recusa POST sem assinatura.')
    if ponte:
        _, txt = buscar(ponte)
        resp = json_ou_none(txt)
        if not (isinstance(resp, dict) and 'POST' in str(resp.get('erro', ''))):
            problemas.append(f'Ponte: GET inesperado (implantação pública da IntegracaoActions?): {txt[:120]!r}')
        else:
            print('[OK] Ponte responde somente a POST.')
        _, txt = buscar(ponte, b'{}')
        resp = json_ou_none(txt)
        erro = str(resp.get('erro', '')) if isinstance(resp, dict) else txt[:160]
        if isinstance(resp, dict) and resp.get('ok') is False and 'malformada' in erro:
            print('[OK] Ponte encaminha ao escritor e o HMAC recusa a chamada sem assinatura.')
        elif 'CENTRAL_WRITER_URL' in erro:
            problemas.append('Ponte sem CENTRAL_WRITER_URL válida: rode ./configurar_integracao.sh.')
        else:
            problemas.append(f'Ponte não chegou ao escritor: {erro}')
    return problemas


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--escritor', help='URL /exec da implantação POST do PainelPrivado')
    ap.add_argument('--ponte', help='URL /exec da IntegracaoActions')
    ap.add_argument('--ci', action='store_true', help='modo GitHub Actions')
    ap.add_argument('--exigir-ambos', action='store_true', help='impede publicação sem URLs de escritor e ponte')
    ap.add_argument('--falha-rede-bloqueia', action='store_true', help='reprova homologação indisponível')
    a = ap.parse_args()
    salvo_escritor, salvo_ponte = urls_salvas()
    escritor, ponte = (a.escritor or salvo_escritor).strip(), (a.ponte or salvo_ponte).strip()
    if a.exigir_ambos and (not escritor or not ponte):
        print('ERRO: Configure ESCRITOR_URL e API_INTEGRACAO_ACTIONS_URL antes da publicação.')
        return 2
    if not escritor and not ponte:
        print('Informe --escritor e/ou --ponte (ou rode ./continuar_configuracao.sh antes).')
        return 2
    for nome, u in (('escritor', escritor), ('ponte', ponte)):
        if u and not RE_EXEC.match(u):
            print(f'URL inválida para {nome}: use https://script.google.com/macros/s/.../exec')
            return 2
    try:
        problemas = homologar(escritor, ponte)
    except (URLError, OSError) as e:
        if a.ci and not a.falha_rede_bloqueia:  # modo legado: apenas diagnóstico sem bloquear
            print(f'::warning::Homologação adiada, sem conexão com o Google: {e}')
            return 0
        print(f'Sem conexão com o Google: {e}')
        return 1
    for p in problemas:
        print(('::error::' if a.ci else '[ERRO] ') + p)
    print('APROVADO: acesso anônimo bloqueado.' if not problemas else f'REPROVADO: {len(problemas)} problema(s).')
    return 0 if not problemas else 1


if __name__ == '__main__':
    sys.exit(main())
