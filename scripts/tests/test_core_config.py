"""Valida bootstrap de parâmetros operacionais do CORE, sem rede."""
import unittest
from unittest.mock import patch
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core_configurar
import core_google

class ConfigCore(unittest.TestCase):
    def test_site_e_lote_do_sheets(self):
        with patch.object(core_configurar,'_sheet_id',return_value='a'*30),patch.object(core_configurar,'_request',return_value={'values':[['CHAVE','VALOR'],['SITE_URL','https://imoplace.com.br'],['LOTE_MAXIMO','20']]}):
            self.assertEqual(core_configurar.carregar_configuracao(),('https://imoplace.com.br','20'))
    def test_rejeita_configuracao_insegura(self):
        with patch.object(core_configurar,'_sheet_id',return_value='a'*30),patch.object(core_configurar,'_request',return_value={'values':[['CHAVE','VALOR'],['SITE_URL','http://inseguro'],['LOTE_MAXIMO','99999']]}):
            with self.assertRaises(RuntimeError): core_configurar.carregar_configuracao()
    def test_mantem_foto_antiga_ate_ack(self):
        im={'ID':'1001','TITULO':'Casa','SLUG':'casa','IMAGEM_CAPA_ID':'i000000000a'}
        fotos=[{'IMAGEM_ID':'i000000000a','IMOVEL_ID':'1001','NOME':'sala','VERSAO':3,'VERSAO_PUBLICADA':2,'OPERACAO':'excluir'}]
        anterior=core_google._fotos(im,fotos)
        novo=core_google._fotos(im,fotos,pendente=True)
        self.assertEqual(anterior[0]['versao'],2)
        self.assertEqual(novo,[])
