import subprocess
import unittest
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / 'CORE'  # só existe no pacote; o repositório GitHub tem apenas GITHUB/


@unittest.skipUnless(CORE.is_dir(), 'pasta CORE/ fica fora do repositório GitHub')
class CoreJavaScript(unittest.TestCase):
    def test_feedback_real_em_node(self):
        arquivo=Path(__file__).with_name('test_core_node.js')
        subprocess.run(['node',str(arquivo)],check=True, capture_output=True, text=True)

    def test_regressoes_421_em_node(self):
        arquivo=Path(__file__).with_name('test_core421_node.js')
        r=subprocess.run(['node',str(arquivo)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)

    def test_noticias_sem_push_422_em_node(self):
        arquivo=Path(__file__).with_name('test_noticias422_node.cjs')
        r=subprocess.run(['node',str(arquivo)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)
