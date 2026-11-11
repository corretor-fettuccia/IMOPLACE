"""Testa o motor novo [1/8] a [6/8] sem Google nem rede."""
import json
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import etapas
from comum import RAIZ, ler_json
from tests.test_publicacao import item_feed, feed, webp, img_pend

class TestEtapas(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.site = self.tmp/'site'
        shutil.copytree(RAIZ/'site', self.site)
        self.estado = self.tmp/'estado'
        self.estado.mkdir()
        self.drive = self.tmp/'drive'
        self.drive.mkdir()
        for k, v in {'SITE_DIR':str(self.site),'ESTADO_DIR':str(self.estado),'DRIVE_FIXTURE':str(self.drive),
                     'INTEGRACAO_FIXTURE':str(self.tmp),'FEED_FIXTURE':str(self.tmp/'feed.json')}.items():
            os.environ[k] = v
        self.setenv = ['SITE_DIR','ESTADO_DIR','DRIVE_FIXTURE','INTEGRACAO_FIXTURE','FEED_FIXTURE']

    def tearDown(self):
        for k in self.setenv: os.environ.pop(k,None)
        shutil.rmtree(self.tmp)

    def test_motor_completa_e_nao_retransmite_imagem(self):
        foto = webp('nova-foto')
        img = img_pend('i000000000a','sala',1,foto)
        (self.drive/(img['driveFileId']+'.webp')).write_bytes(foto)
        item = item_feed('1001','Casa Igara',[])
        (self.tmp/'feed.json').write_text(json.dumps(feed(item)))
        (self.tmp/'pendencias.json').write_text(json.dumps({'ok':True,'pendencias':[{'imovelId':'1001','versao':1,'status':'publicado','capaId':img['imagemId'],'imagens':[img]}]}))
        etapas.sincronizar()
        etapas.montar_catalogo()
        self.assertEqual(len(ler_json(self.estado/'catalogo-candidato.json')['imoveis']),1)
        etapas.montar_imoveis()
        etapas.montar_extras()
        from validar import validar
        self.assertEqual(validar(self.site, etapas.config()),[])
        etapas.montar_site()
        self.assertTrue((self.estado/'publicacao'/'imoveis'/'casa-igara-1001'/'index.html').exists())
        self.assertFalse((self.estado/'publicacao'/'scripts').exists())
        marker=ler_json(self.estado/'publicacao'/'publicacao.json')
        self.assertEqual(marker['jobId'],ler_json(self.estado/'job.json')['jobId'])
        self.assertEqual(marker['catalogoSha256'], hashlib.sha256((self.estado/'publicacao'/'catalogo.json').read_bytes()).hexdigest())
        self.assertEqual(ler_json(self.estado/'job.json')['relatorio']['transferidas'],1)

    def test_recusa_feed_com_versao_modificada_apos_reserva(self):
        item=item_feed('1001','Casa Igara',[],versao=9)
        (self.tmp/'feed.json').write_text(json.dumps(feed(item)))
        (self.tmp/'pendencias.json').write_text(json.dumps({'ok':True,'pendencias':[
            {'imovelId':'1001','versao':8,'status':'publicado','imagens':[]}]}))
        etapas.sincronizar()
        with self.assertRaisesRegex(RuntimeError,'Feed mais recente'):
            etapas.montar_catalogo()
        self.assertFalse((self.estado/'feed-snapshot.json').exists())

if __name__=='__main__': unittest.main()
