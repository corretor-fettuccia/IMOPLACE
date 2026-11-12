"""ImoPlace — validação do feed público e das pendências (contrato imoplace-v1)."""
from comum import CATEGORIAS, CONTRATO, RE_ARQUIVO, RE_CODIGO, RE_DRIVE_ID, RE_ID, RE_SHA


class ContratoInvalido(ValueError):
    pass


def _exigir(cond, msg):
    if not cond:
        raise ContratoInvalido(msg)


def validar_feed(feed: dict) -> list:
    """Confere o feed inteiro; um imóvel inválido derruba a publicação (nada parcial vai ao ar)."""
    _exigir(isinstance(feed, dict) and feed.get('ok') is True, f'Feed recusado: {str(feed.get("erro", ""))[:120] if isinstance(feed, dict) else "formato"}')
    _exigir(feed.get('contrato') == CONTRATO, f'Contrato do feed diferente de {CONTRATO}. Publique nova versão da API pública.')
    _exigir(feed.get('snapshotCompleto') is True, 'Feed sem snapshotCompleto: nada é publicado.')
    itens = feed.get('imoveis')
    _exigir(isinstance(itens, list) and feed.get('total') == len(itens), 'Feed com total inconsistente.')
    vistos = set()
    for item in itens:
        validar_item(item)
        _exigir(item['id'] not in vistos, f'ID repetido no feed: {item["id"]}')
        vistos.add(item['id'])
    return itens


def validar_item(item: dict):
    _exigir(isinstance(item, dict), 'Imóvel fora do formato.')
    iid = str(item.get('id', ''))
    _exigir(RE_ID.match(iid), f'ID inválido: {iid!r}')
    _exigir(item.get('categoria') in CATEGORIAS, f'Categoria inválida no imóvel {iid}')
    codigo = item.get('codigo', '')
    _exigir(isinstance(codigo, str) and RE_CODIGO.match(codigo) and codigo.endswith('-' + iid), f'Código inválido no imóvel {iid}: {codigo!r}')
    caminho = f'imoveis/{codigo}/'
    _exigir(item.get('caminho') == caminho, f'Caminho inconsistente no imóvel {iid}')
    _exigir(isinstance(item.get('titulo'), str) and item['titulo'].strip(), f'Imóvel {iid} sem título')
    for img in item.get('imagens') or []:
        arq = str(img.get('arquivo', ''))
        _exigir(arq.startswith(caminho + 'imagens/') and RE_ARQUIVO.match(arq.rsplit('/', 1)[-1]), f'Imagem com caminho inválido no imóvel {iid}: {arq!r}')


def validar_pendencias(resp: dict) -> list:
    _exigir(isinstance(resp, dict) and resp.get('ok') is True, f'Integração recusou: {str(resp.get("erro", ""))[:160] if isinstance(resp, dict) else "formato"}')
    pend = resp.get('pendencias')
    _exigir(isinstance(pend, list), 'Pendências fora do formato.')
    _exigir(all(RE_ID.match(str(x)) for x in resp.get('aguardando') or []), 'Lista aguardando fora do formato.')
    for p in pend:
        iid = str(p.get('imovelId', ''))
        _exigir(RE_ID.match(iid), f'Pendência com ID inválido: {iid!r}')
        _exigir(isinstance(p.get('versao'), int) and p['versao'] >= 0, f'Pendência {iid} sem versão')
        for img in p.get('imagens') or []:
            if img.get('operacao') == 'excluir':
                continue
            _exigir(RE_DRIVE_ID.match(str(img.get('driveFileId', ''))), f'Foto {img.get("imagemId")} do imóvel {iid} sem driveFileId válido')
            _exigir(RE_SHA.match(str(img.get('sha256', ''))), f'Foto {img.get("imagemId")} do imóvel {iid} sem SHA-256')
            _exigir(RE_ARQUIVO.match(str(img.get('arquivo', ''))), f'Foto {img.get("imagemId")} do imóvel {iid} com nome inválido')
    return pend
