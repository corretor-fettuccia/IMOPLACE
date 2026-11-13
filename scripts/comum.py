"""ImoPlace — utilidades comuns dos geradores (somente biblioteca padrão do Python 3.12)."""
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = 'imoplace-v1'
CATEGORIAS = ('venda', 'lancamento')
RE_CODIGO = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*-\d+$')
RE_ID = re.compile(r'^\d{1,12}$')
RE_ARQUIVO = re.compile(r'^[a-z0-9-]+-i[0-9a-f]{10}\.v\d{1,6}\.webp$')
RE_DRIVE_ID = re.compile(r'^[A-Za-z0-9_-]{10,200}$')
RE_SHA = re.compile(r'^[0-9a-f]{64}$')
MAX_FOTO_BYTES = 10 * 1024 * 1024
UA = 'ImoPlace-Publicador/3.0.0'

# Campos que jamais podem aparecer em nada que vá para o site.
PROIBIDOS = {
    'proprietario', 'telefoneproprietario', 'telefone_proprietario', 'enderecointerno', 'endereco_interno',
    'obsinterna', 'obs_interna', 'drivefileid', 'drive_file_id', 'drivepastaid', 'drive_pasta_id', 'sha256',
}


def site_dir() -> Path:
    return Path(os.environ.get('SITE_DIR') or RAIZ / 'site').resolve()


def estado_dir() -> Path:
    d = Path(os.environ.get('ESTADO_DIR') or RAIZ / 'estado').resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


def config() -> dict:
    caminho = Path(os.environ.get('IMOPLACE_CONFIG') or RAIZ / 'imoplace.json')
    conf = json.loads(caminho.read_text(encoding='utf-8'))
    url = str(conf.get('urlPublica', '')).strip().rstrip('/')
    if not re.match(r'^https://[a-z0-9.-]+$', url):
        raise ValueError('imoplace.json: urlPublica deve ser https://dominio (sem barra no fim).')
    conf['urlPublica'] = url
    conf['permitirIndexacao'] = bool(conf.get('permitirIndexacao'))
    conf.setdefault('nome', 'Imoplace')
    return conf


def ler_json(caminho: Path, padrao=None):
    try:
        return json.loads(Path(caminho).read_text(encoding='utf-8'))
    except FileNotFoundError:
        return padrao


def gravar(caminho: Path, conteudo) -> bool:
    """Escrita atômica; devolve True se mudou."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = conteudo.encode('utf-8') if isinstance(conteudo, str) else conteudo
    if caminho.exists() and caminho.read_bytes() == dados:
        return False
    tmp = caminho.with_name(caminho.name + '.tmp')
    tmp.write_bytes(dados)
    tmp.replace(caminho)
    return True


def gravar_json(caminho: Path, obj) -> bool:
    return gravar(caminho, json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def dentro(base: Path, alvo: Path) -> bool:
    try:
        Path(alvo).resolve().relative_to(Path(base).resolve())
        return True
    except ValueError:
        return False


def eh_webp(dados: bytes) -> bool:
    return len(dados) >= 16 and dados[:4] == b'RIFF' and dados[8:12] == b'WEBP'


def log(etapa: str, msg: str):
    print(f'[{etapa}] {msg}', flush=True)


def aviso(msg: str):
    print(f'::warning::{msg}', flush=True)


def erro(msg: str):
    print(f'::error::{msg}', file=sys.stderr, flush=True)


def saida_github(chave: str, valor: str):
    arq = os.environ.get('GITHUB_OUTPUT')
    if arq:
        with open(arq, 'a', encoding='utf-8') as f:
            f.write(f'{chave}={valor}\n')
    log('saida', f'{chave}={valor}')
