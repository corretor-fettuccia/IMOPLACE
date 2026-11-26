"""Formatos da matriz e preferência de exibição. WebP é o padrão."""
import os
from PIL import Image, ImageOps
FORMATOS=('webp','jpeg','png','jxl')

def normalizar_formato(value='webp'):
    value=str(value or 'webp').strip().lower()
    if value=='jpg':value='jpeg'
    if value not in FORMATOS:raise ValueError('FORMATO_PADRAO_IMAGENS deve ser webp, jpeg, png ou jxl.')
    return value

def formato_padrao():
    return normalizar_formato(os.environ.get('FORMATO_PADRAO_IMAGENS','webp'))

def detectar_formato(data):
    if data[:12]==b'\x00\x00\x00\x0cJXL \x0d\x0a\x87\x0a' or data[:2]==b'\xff\x0a':return 'jxl'
    if data[:8]==b'\x89PNG\r\n\x1a\n':return 'png'
    if data[:3]==b'\xff\xd8\xff':return 'jpeg'
    if data[:4]==b'RIFF' and data[8:12]==b'WEBP':return 'webp'
    raise ValueError('Assinatura de imagem não reconhecida')

def abrir_pixels(path):
    if path.suffix.lower()=='.jxl':
        from jxl_codec import decode
        return decode(path)
    with Image.open(path) as image:
        if image.width*image.height>50_000_000:raise ValueError('Imagem acima de 50 megapixels')
        return ImageOps.exif_transpose(image).copy()

def ordem_formatos(formats, preferido='webp'):
    preferido=normalizar_formato(preferido)
    chave='jpg' if preferido=='jpeg' else preferido
    # Somente o formato escolhido vem antes de WebP; JPEG/PNG seguem como fallback.
    return [x for x in dict.fromkeys([chave,'webp','avif','jxl']) if formats.get(x)]

def aplicar_preferencia_catalogo(site,conf,formato):
    """Atualiza só metadados/HTML. Não abre, reconverte ou substitui fotos existentes."""
    import json
    from comum import gravar,gravar_json
    from paginas import pagina
    path=site/'catalogo.json'
    if not path.is_file():return
    catalogo=json.loads(path.read_text(encoding='utf-8'))
    mudou=False
    for item in catalogo.get('imoveis',[]):
        for foto in item.get('imagens',[]):
            data=foto.get('adaptativas')
            if data and data.get('preferido')!=formato:
                data['preferido']=formato;mudou=True
    if mudou:gravar_json(path,catalogo)
    for item in catalogo.get('imoveis',[]):
        gravar(site/'imoveis'/item['codigo']/'index.html',pagina(item,conf,catalogo.get('imoveis',[])))
