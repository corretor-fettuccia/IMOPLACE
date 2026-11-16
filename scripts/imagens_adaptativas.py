"""Conversão prévia reversível. Preserva cada URL WebP já publicada e registra variantes."""
import hashlib
import io
import os
import shutil
import subprocess
import json
from pathlib import Path
from PIL import Image, ImageOps, features

WIDTHS=(480,768,1200,1600)

def gerar(foto,site):
    src=site/foto['arquivo']
    key=hashlib.sha256(src.read_bytes()).hexdigest()[:16]+'-a'+str(int(os.environ.get('IMOPLACE_AVIF')=='1'))+'-j'+str(int(os.environ.get('IMOPLACE_JXL')=='1'))
    folder=src.parent/'adaptativas'/key
    manifest=folder/'manifesto.json'
    if manifest.is_file():
        cached=json.loads(manifest.read_text())
        cached.pop('sha256',None)
        if all((site/row['arquivo']).is_file() for rows in cached.get('formatos',{}).values() for row in rows):
            return cached
    with Image.open(src) as original:
        if original.width*original.height>50_000_000: raise ValueError('Imagem acima de 50 megapixels')
        image=ImageOps.exif_transpose(original)
        if image.info.get('icc_profile'):
            from PIL import ImageCms
            image=ImageCms.profileToProfile(image,ImageCms.ImageCmsProfile(io.BytesIO(image.info['icc_profile'])),ImageCms.createProfile('sRGB'),outputMode='RGBA' if 'A' in image.getbands() else 'RGB')
        alpha='A' in image.getbands()
        formats=[('webp','WEBP',80),('png','PNG',None)] if alpha else [('jpg','JPEG',84),('webp','WEBP',80)]
        if os.environ.get('IMOPLACE_AVIF') == '1' and features.check('avif'): formats.append(('avif','AVIF',55))
        widths=sorted(set(min(w,image.width) for w in WIDTHS))
        result={'largura':image.width,'altura':image.height,'formatos':{},'versaoConteudo':key}
        folder.mkdir(parents=True,exist_ok=True)
        for ext,fmt,quality in formats:
            variants=[]
            for w in widths:
                im=image.resize((w,max(1,round(image.height*w/image.width))),Image.Resampling.LANCZOS)
                if not alpha: im=im.convert('RGB')
                im.info={}
                path=folder/f'{w}.{ext}'
                im.save(path,fmt,**({'quality':quality} if quality else {}))
                variants.append({'arquivo':path.relative_to(site).as_posix(),'largura':im.width,'altura':im.height,'bytes':path.stat().st_size,'mime':Image.MIME[fmt]})
            result['formatos'][ext]=variants
        if os.environ.get('IMOPLACE_JXL')=='1' and shutil.which('cjxl') and not alpha:
            rows=[]
            for source in result['formatos']['jpg']:
                target=site/source['arquivo'];dest=target.with_suffix('.jxl')
                subprocess.run(['cjxl',str(target),str(dest),'--lossless_jpeg=0','-q','80','-e','3'],check=True,capture_output=True,timeout=60)
                rows.append(dict(arquivo=dest.relative_to(site).as_posix(),largura=source['largura'],altura=source['altura'],bytes=dest.stat().st_size,mime='image/jxl'))
            result['formatos']={'jxl':rows,**result['formatos']}
        manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2))
        return result

def enriquecer(entradas,site):
    if os.environ.get('IMOPLACE_IMAGENS_ADAPTATIVAS')=='0':
        for item in entradas:
            for foto in item.get('imagens',[]): foto.pop('adaptativas',None)
        return
    for item in entradas:
        for foto in item.get('imagens',[]):
            try: foto['adaptativas']=gerar(foto,site)
            except Exception as exc:
                print('[imagens] Mantido fallback original:',foto['arquivo'],type(exc).__name__)
