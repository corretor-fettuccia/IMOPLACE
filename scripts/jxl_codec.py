"""Lossless matrix codec, using the same pinned libjxl WASM as the uploader."""
import struct
import subprocess
import tempfile
from pathlib import Path
import pillow_jxl  # registers the maintained libjxl decoder in Pillow
from PIL import Image
CLI=Path(__file__).with_suffix('.mjs')

def is_jxl(data):
    return data[:2]==b'\xff\x0a' or data[:12]==b'\x00\x00\x00\x0cJXL \x0d\x0a\x87\x0a'

def decode(path):
    with Image.open(path) as image:
        if image.width*image.height>50_000_000:raise ValueError('JXL acima de 50 megapixels')
        return image.convert('RGBA')

def encode(image,path):
    image=image.convert('RGBA')
    with tempfile.TemporaryDirectory() as d:
        raw=Path(d)/'source.rgba';raw.write_bytes(struct.pack('<II',*image.size)+image.tobytes())
        subprocess.run(['node',str(CLI),'encode',str(raw),str(Path(path).resolve())],check=True,capture_output=True,timeout=120)
