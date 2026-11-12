"""Regressão: variáveis do GitHub, scripts e validador usam um contrato só."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verificar_configuracao as cfg

VALID = {
    'API_PUBLICA_URL':'https://script.google.com/macros/s/AKfycb1234/exec',
    'API_INTEGRACAO_ACTIONS_URL':'https://script.google.com/macros/s/AKfycb5678/exec',
    'SITE_URL':'https://imoplace.com.br',
    'SEGREDO_INTEGRACAO':'a'*64,
    'GOOGLE_CREDENTIALS':'{"type":"service_account"}',
}

class TestConfiguracaoGitHub(unittest.TestCase):
    def test_workflow_e_codigo_seguem_mesmo_contrato(self):
        self.assertEqual(cfg.conferir_contrato(), [])

    def test_valores_corretos(self):
        with patch.dict(os.environ, VALID, clear=True):
            self.assertEqual(cfg.conferir_ambiente(), [])

    def test_ausentes_indicam_aba_correta(self):
        with patch.dict(os.environ, {}, clear=True):
            errors = cfg.conferir_ambiente()
        self.assertTrue(any('Actions Variables' in e and 'API_PUBLICA_URL' in e for e in errors))
        self.assertTrue(any('Actions Variables' in e and 'API_INTEGRACAO_ACTIONS_URL' in e for e in errors))
        self.assertTrue(any('Actions Secrets' in e and 'SEGREDO_INTEGRACAO' in e for e in errors))
        self.assertTrue(any('Actions Secrets' in e and 'GOOGLE_CREDENTIALS' in e for e in errors))

    def test_variaveis_antigas_nao_substituem_as_novas(self):
        with patch.dict(os.environ, {'FEED_URL':VALID['API_PUBLICA_URL'], 'INTEGRACAO_URL':VALID['API_INTEGRACAO_ACTIONS_URL']}, clear=True):
            errors=cfg.conferir_ambiente()
        self.assertTrue(any('API_PUBLICA_URL' in e for e in errors))
        self.assertTrue(any('API_INTEGRACAO_ACTIONS_URL' in e for e in errors))

    def test_url_invalida_gera_erro(self):
        with patch.dict(os.environ, {**VALID,'API_PUBLICA_URL':'https://exemplo.com/sem-exec'}, clear=True):
            self.assertTrue(any('API_PUBLICA_URL' in e for e in cfg.conferir_ambiente()))

if __name__=='__main__': unittest.main()
