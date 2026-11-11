"""ImoPlace — download de fotos pela Drive API (somente leitura).

Token: GOOGLE_ACCESS_TOKEN, gerado no workflow pela action google-github-actions/auth
(conta de serviço com leitura apenas na pasta ImoPlace/Imoveis). Nada de link público do Drive.
Teste/local: DRIVE_FIXTURE=<pasta> com arquivos <driveFileId>.webp.
"""
import os
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from comum import MAX_FOTO_BYTES, RE_DRIVE_ID, UA, log


class FalhaDownload(RuntimeError):
    pass


def baixar(file_id: str) -> bytes:
    if not RE_DRIVE_ID.match(file_id or ''):
        raise FalhaDownload(f'driveFileId inválido: {file_id!r}')
    fixture = os.environ.get('DRIVE_FIXTURE')
    if fixture:
        alvo = Path(fixture) / f'{file_id}.webp'
        if not alvo.is_file():
            raise FalhaDownload(f'arquivo {file_id} não encontrado no Drive (fixture)')
        return alvo.read_bytes()
    token = os.environ.get('GOOGLE_ACCESS_TOKEN', '').strip()
    if not token:
        raise FalhaDownload('GOOGLE_ACCESS_TOKEN ausente: confira o secret GOOGLE_CREDENTIALS e o passo de autenticação.')
    url = f'https://www.googleapis.com/drive/v3/files/{quote(file_id)}?alt=media&supportsAllDrives=true'
    ultimo = None
    for n in range(1, 4):
        try:
            req = Request(url, headers={'Authorization': f'Bearer {token}', 'User-Agent': UA})
            with urlopen(req, timeout=90) as r:
                dados = r.read(MAX_FOTO_BYTES + 1)
            if len(dados) > MAX_FOTO_BYTES:
                raise FalhaDownload(f'arquivo {file_id} maior que {MAX_FOTO_BYTES // 1048576} MB')
            return dados
        except HTTPError as e:
            if e.code in (401, 403, 404):
                raise FalhaDownload(f'Drive recusou {file_id} (HTTP {e.code}): a pasta Imoveis está compartilhada com a conta de serviço?') from e
            ultimo = e
        except OSError as e:
            ultimo = e
        log('drive', f'{file_id}: tentativa {n}/3 falhou ({ultimo})')
        time.sleep(3 * n)
    raise FalhaDownload(f'download de {file_id} falhou: {ultimo}')
