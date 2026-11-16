"""Deriva cada formato diretamente dos pixels da matriz. Nunca deriva JXL de JPEG/WebP novo."""
import hashlib
import io
import json
import os
from PIL import Image,ImageOps,features
from jxl_codec import decode as decode_jxl,encode as encode_jxl
WIDTHS=(480,768,1200,1600)

def abrir_matriz(src):
    if src.suffix.lower()=='.jxl': return decode_jxl(src)
    with Image.open(src) as original:
        if original.width*original.height>50_000_000:raise ValueError('Imagem acima de 50 megapixels')
        image=ImageOps.exif_transpose(original)
        if image.info.get('icc_profile'):
            from PIL import ImageCms
            image=ImageCms.profileToProfile(image,ImageCms.ImageCmsProfile(io.BytesIO(image.info['icc_profile'])),ImageCms.createProfile('sRGB'),outputMode='RGBA' if 'A' in image.getbands() else 'RGB')
        return image.copy()

def gerar(foto,site):
    native=bool(foto.get('matriz'));src=site/(foto.get('matriz') or foto['arquivo'])
    key='v322-'+hashlib.sha256(src.read_bytes()).hexdigest()[:16]+'-a'+str(int(os.environ.get('IMOPLACE_AVIF')=='1'))+'-j'+str(int(os.environ.get('IMOPLACE_JXL')=='1'))
    folder=src.parent/'adaptativas'/key;manifest=folder/'manifesto.json'
    if manifest.is_file():
        cached=json.loads(manifest.read_text());rows=[x for items in cached.get('formatos',{}).values() for x in items]+[cached.get('social',{})]
        if rows and all((site/row.get('arquivo','')).is_file() for row in rows):return cached
    image=abrir_matriz(src)
    if image.width*image.height>50_000_000:raise ValueError('Imagem acima de 50 megapixels')
    alpha='A' in image.getbands() and image.getchannel('A').getextrema()[0]<255
    formats=[('png','PNG',None),('webp','WEBP',80)] if alpha else [('jpg','JPEG',84),('webp','WEBP',80)]
    if os.environ.get('IMOPLACE_AVIF')=='1' and features.check('avif'):formats.append(('avif','AVIF',55))
    widths=sorted(set(min(w,image.width) for w in WIDTHS));folder.mkdir(parents=True,exist_ok=True)
    result={'largura':image.width,'altura':image.height,'formatos':{},'versaoConteudo':key,'origem':'jxl-lossless' if native else 'webp-legado'}
    for ext,fmt,quality in formats:
        variants=[]
        for w in widths:
            im=image.resize((w,max(1,round(image.height*w/image.width))),Image.Resampling.LANCZOS)
            if not alpha:im=im.convert('RGB')
            im.info={};path=folder/f'{w}.{ext}';im.save(path,fmt,**({'quality':quality} if quality else {}))
            variants.append(dict(arquivo=path.relative_to(site).as_posix(),largura=im.width,altura=im.height,bytes=path.stat().st_size,mime=Image.MIME[fmt]))
        result['formatos'][ext]=variants
    if native or os.environ.get('IMOPLACE_JXL')=='1':
        variants=[]
        for w in widths:
            im=image.resize((w,max(1,round(image.height*w/image.width))),Image.Resampling.LANCZOS)
            path=folder/f'{w}.jxl';encode_jxl(im,path)
            variants.append(dict(arquivo=path.relative_to(site).as_posix(),largura=im.width,altura=im.height,bytes=path.stat().st_size,mime='image/jxl'))
        result['formatos']={'jxl':variants,**result['formatos']}
    # JPEG social com área fixa, sem cortar a marca ou depender de suporte JXL.
    social=Image.new('RGB',(1200,630),'white');preview=image.copy();preview.thumbnail((1200,630),Image.Resampling.LANCZOS)
    if 'A' in preview.getbands():social.paste(preview,((1200-preview.width)//2,(630-preview.height)//2),preview.getchannel('A'))
    else:social.paste(preview.convert('RGB'),((1200-preview.width)//2,(630-preview.height)//2))
    path=folder/'social.jpg';social.save(path,'JPEG',quality=88)
    result['social']=dict(arquivo=path.relative_to(site).as_posix(),largura=1200,altura=630,bytes=path.stat().st_size,mime='image/jpeg')
    manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2));return result

def enriquecer(entradas,site):
    for item in entradas:
        for foto in item.get('imagens',[]):
            if not foto.get('matriz'):
                foto.pop('adaptativas',None)
                continue
            if os.environ.get('IMOPLACE_IMAGENS_ADAPTATIVAS')=='0':foto.pop('adaptativas',None);continue
            try:foto['adaptativas']=gerar(foto,site)
            except Exception as exc:
                if foto.get('matriz'):raise RuntimeError('Falha ao gerar formatos compatíveis da matriz JXL: '+foto['arquivo']) from exc
                print('[imagens] Mantido fallback legado:',foto['arquivo'],type(exc).__name__)
