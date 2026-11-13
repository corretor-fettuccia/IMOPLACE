"""Regressões: CORE único, seleção por versão e feedback individual."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core_google as cg


class TestCore(unittest.TestCase):
    def setUp(self):
        self.im = {'ID':'1001','VERSAO':4,'VERSAO_PUBLICADA':3,'STATUS':'publicado',
                   'TITULO':'Casa Modelo','SLUG':'casa-modelo','CATEGORIA':'venda',
                   'PROPRIETARIO':'NÃO PUBLICAR ESTE DADO',
                   'ENDERECO_INTERNO':'NÃO PUBLICAR ENDEREÇO'}
        self.tab = {'IMOVEIS':[self.im], 'IMAGENS':[],
                    'FILA':[{'IMOVEL_ID':'1001','VERSAO':4,'MOTIVO':'publicar','ESTADO':'pendente','SOLICITADO_EM':'2026-11-10'}],
                    'RESULTADOS':[]}

    def test_feed_nao_expoe_dados_privados(self):
        feed=cg.montar_feed(self.tab,'https://imoplace.com.br')
        self.assertEqual(feed['total'],1)
        self.assertNotIn('NÃO PUBLICAR',json.dumps(feed,ensure_ascii=False))
        self.assertEqual(feed['imoveis'][0]['caminho'],'imoveis/casa-modelo-1001/')

    def test_versao_e_lote(self):
        job=cg.selecionar_job(self.tab,'gh-123-1',limite=20)
        self.assertEqual(job['pendencias'][0]['versao'],4)
        self.tab['RESULTADOS']=[{'IMOVEL_ID':'1001','VERSAO':4,'STATUS':'PUBLICADO'}]
        self.assertEqual(cg.selecionar_job(self.tab,'gh-124-1')['pendencias'],[])

    def test_regressoes_rejeitam_fila_obsoleta(self):
        self.tab['FILA'][0]['VERSAO']=3
        self.assertEqual(cg.selecionar_job(self.tab,'gh-123-1')['pendencias'],[])

    def _evento(self, status, minutos_atras, versao=4, iid='1001'):
        from datetime import datetime, timedelta, timezone
        data = (datetime(2026, 11, 12, 20, 0, tzinfo=timezone.utc) - timedelta(minutes=minutos_atras)).isoformat()
        return {'IMOVEL_ID': iid, 'VERSAO': versao, 'STATUS': status, 'DATA': data}

    def _sel(self, forcar=False):
        from datetime import datetime, timezone
        agora = datetime(2026, 11, 12, 20, 0, tzinfo=timezone.utc)
        return [p['imovelId'] for p in cg.selecionar_job(self.tab, 'gh-1', forcar=forcar, agora=agora)['pendencias']]

    def test_falha_e_tentada_de_novo_sozinha_apos_30_minutos(self):
        # Antes: ERRO parava a fila até o botão "Sincronizar agora".
        self.tab['RESULTADOS'] = [self._evento('PROCESSANDO', 50), self._evento('ERRO', 10)]
        self.assertEqual(self._sel(), [], 'espera 30 min antes de tentar de novo')
        self.tab['RESULTADOS'][-1] = self._evento('ERRO', 31)
        self.assertEqual(self._sel(), ['1001'], 'execução agendada tenta de novo sozinha')

    def test_para_apos_3_tentativas_e_so_o_botao_tenta_de_novo(self):
        self.tab['RESULTADOS'] = [e for m in (300, 200, 100) for e in (self._evento('PROCESSANDO', m), self._evento('ERRO', m - 5))]
        self.assertEqual(self._sel(), [], '3 tentativas esgotadas')
        self.assertEqual(self._sel(forcar=True), ['1001'], '"Sincronizar agora" sempre tenta')

    def test_execucao_cancelada_conta_como_tentativa_e_e_retomada(self):
        self.tab['RESULTADOS'] = [self._evento('PROCESSANDO', 20)]  # ainda dentro do lease de 40 min
        self.assertEqual(self._sel(), [], 'não disputar com execução ativa')
        self.tab['RESULTADOS'] = [self._evento('PROCESSANDO', 45)]
        self.assertEqual(self._sel(), ['1001'], 'lease expirado libera reprocessamento')
        self.tab['RESULTADOS'] = [self._evento('PROCESSANDO', m) for m in (90, 60, 30)]
        self.assertEqual(self._sel(), [], 'cancelada 3 vezes: para de tentar sozinha')

    def test_versao_nova_recomeca_as_tentativas(self):
        self.tab['RESULTADOS'] = [e for m in (300, 200, 100) for e in (self._evento('PROCESSANDO', m, versao=3), self._evento('ERRO', m - 5, versao=3))]
        self.assertEqual(self._sel(), ['1001'], 'edição gera versão 4: contagem nova')

    def test_falha_de_um_imovel_nao_atrasa_outro(self):
        self.tab['IMOVEIS'].append(dict(self.im, ID='1002', VERSAO=1))
        self.tab['FILA'].append({'IMOVEL_ID': '1002', 'VERSAO': 1, 'MOTIVO': 'publicar', 'ESTADO': 'pendente', 'SOLICITADO_EM': '2026-11-11'})
        self.tab['RESULTADOS'] = [self._evento('ERRO', 5)]
        self.assertEqual(self._sel(), ['1002'])

    def test_resultado_individual_nao_confirma_outro_imovel(self):
        with tempfile.TemporaryDirectory() as folder:
            state=Path(folder)
            (state/'job.json').write_text(json.dumps({'jobId':'gh-123-1', 'pendencias':[{'imovelId':'1001','versao':4,'motivo':'publicar','caminho':'imoveis/casa-1001/','imagens':[]}]}))
            with patch.object(cg,'registrar_eventos') as append:
                with patch.dict(os.environ, {'ESTADO_DIR':str(state),'SITE_URL':'https://imoplace.com.br'}):
                    cg.reportar('gh-123-1','SUCESSO',{'imoveis':[{'imovelId':'1001','versao':4,'noSite':True},{'imovelId':'1002','versao':9,'noSite':True}]})
                eventos=append.call_args[0][0]
                self.assertEqual(len(eventos),1)
                self.assertEqual(eventos[0]['IMOVEL_ID'],'1001')
                self.assertEqual(eventos[0]['CODIGO'],'PUBLISHED_OK')

    @unittest.skipUnless((Path(__file__).resolve().parents[3] / 'CORE').is_dir(), 'pasta CORE/ fica fora do repositório GitHub')
    def test_uma_unica_api_privada(self):
        raiz=Path(__file__).resolve().parents[3]
        self.assertTrue((raiz/'CORE'/'Painel.html').exists())
        self.assertFalse((raiz/'GOOGLE.APPSCRIPT').exists())
        arquivo='\n'.join(x.read_text(encoding='utf8') for x in (raiz/'CORE').glob('*.gs'))
        self.assertNotIn('function doPost(',arquivo)


# Testes isolados do contrato de reserva e da correspondência JOB_ID.
class TestReservaCorrigida(unittest.TestCase):
    def setUp(self):
        from datetime import datetime, timezone
        self.now=datetime(2026,11,12,20,0,tzinfo=timezone.utc)
        self.tb={'IMOVEIS':[{'ID':'1001','VERSAO':4,'STATUS':'publicado'}], 'IMAGENS':[],
                 'FILA':[{'IMOVEL_ID':'1001','VERSAO':4,'MOTIVO':'publicar'}], 'RESULTADOS':[]}

    def ev(self, job, status, minutos):
        from datetime import timedelta
        return {'IMOVEL_ID':'1001','VERSAO':4,'JOB_ID':job,'STATUS':status,'DATA':(self.now-timedelta(minutes=minutos)).isoformat()}

    def sel(self, force=False):
        return cg.selecionar_job(self.tb,'gh-new',forcar=force,agora=self.now)['pendencias']

    def test_reserva_ativa_nao_duplica_mesmo_forcada(self):
        self.tb['RESULTADOS']=[self.ev('gh-1','PROCESSANDO',1)]
        self.assertFalse(self.sel())
        self.assertFalse(self.sel(True))

    def test_reserva_expirada_pode_ser_recuperada(self):
        self.tb['RESULTADOS']=[self.ev('gh-1','PROCESSANDO',41)]
        self.assertEqual(len(self.sel()),1)

    def test_resposta_antiga_atrasada_nao_encerra_job_novo(self):
        self.tb['RESULTADOS']=[self.ev('gh-1','PROCESSANDO',45),self.ev('gh-2','PROCESSANDO',1),self.ev('gh-1','ERRO',0)]
        self.assertFalse(self.sel())
        self.assertEqual(cg._ultimo_por_versao(self.tb['RESULTADOS'])[('1001',4)]['JOB_ID'],'gh-2')

    def test_resultado_do_job_atual_encerra(self):
        self.tb['RESULTADOS']=[self.ev('gh-1','PROCESSANDO',45),self.ev('gh-2','PROCESSANDO',15),self.ev('gh-2','PUBLICADO',1)]
        self.assertFalse(self.sel())
        self.assertEqual(cg._ultimo_por_versao(self.tb['RESULTADOS'])[('1001',4)]['STATUS'],'PUBLICADO')

    def test_validar_reserva_recusa_job_antigo_mesma_versao(self):
        self.tb['RESULTADOS']=[self.ev('gh-1','PROCESSANDO',50),self.ev('gh-2','PROCESSANDO',1)]
        with patch.object(cg,'ler_tabelas',return_value=self.tb):
            with self.assertRaisesRegex(RuntimeError,'não pertence mais'):
                cg.validar_reserva('gh-1',{'imoveis':[{'imovelId':'1001','versao':4}]})
            self.assertEqual(cg.validar_reserva('gh-2',{'imoveis':[{'imovelId':'1001','versao':4}]}),{'ok':True})

    def test_validar_reserva_recusa_alteracao_durante_deploy(self):
        self.tb['RESULTADOS']=[self.ev('gh-1','PROCESSANDO',1)]
        self.tb['IMOVEIS'][0]['VERSAO']=5
        with patch.object(cg,'ler_tabelas',return_value=self.tb):
            with self.assertRaisesRegex(RuntimeError,'Versão da fila alterada'):
                cg.validar_reserva('gh-1',{'imoveis':[{'imovelId':'1001','versao':4}]})

    def test_evento_repetido_mesmo_job_nao_esgota_tentativas(self):
        self.tb['RESULTADOS']=[self.ev('gh-1','PROCESSANDO',60),self.ev('gh-1','PROCESSANDO',59),self.ev('gh-1','ERRO',40)]
        self.assertEqual(cg._tentativas_por_versao(self.tb['RESULTADOS'])[('1001',4)],1)
        self.assertEqual(len(self.sel()),1)

if __name__=='__main__': unittest.main()
