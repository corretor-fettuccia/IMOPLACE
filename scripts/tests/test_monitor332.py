"""Monitor: exportação pública não publica dados privados e valida a URL."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import monitoramento

class MonitorPublico(unittest.TestCase):
    def publicar(self,rows):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(monitoramento,'_sheet_id',return_value='sheet'),patch.object(monitoramento,'_request',return_value={'values':rows}):
                monitoramento.publicar_config_monitor(Path(d))
            return json.loads((Path(d)/'monitor-config.json').read_text())
    def test_sem_config_desativado(self):
        self.assertEqual(self.publicar([['CHAVE','VALOR']]),{'ativo':False,'url':''})
    def test_so_exporta_url_e_ativacao(self):
        url='https://script.google.com/macros/s/monitor123/exec'
        cfg=self.publicar([['CHAVE','VALOR'],['MONITOR_ATIVO','SIM'],['MONITOR_API_URL',url],['GITHUB_TOKEN','nao-publicar'],['MONITOR_RETENCAO_DIAS','90']])
        self.assertEqual(cfg,{'ativo':True,'url':url})
    def test_url_arbitraria_rejeitada(self):
        with self.assertRaises(ValueError):self.publicar([['CHAVE','VALOR'],['MONITOR_API_URL','https://exemplo.com/exec']])
    def test_desativar_nao_exporta_url(self):
        self.assertEqual(self.publicar([['CHAVE','VALOR'],['MONITOR_ATIVO','NAO'],['MONITOR_API_URL','https://script.google.com/macros/s/monitor123/exec']]),{'ativo':False,'url':''})
