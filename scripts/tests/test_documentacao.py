"""Documentação consistente com o código: arquivos citados existem, configurações do workflow estão no manual,
versões batem e nenhuma orientação antiga contradiz o comportamento atual."""
import re
import unittest
from pathlib import Path

GIT_PAGE = Path(__file__).resolve().parents[2]
PACOTE = GIT_PAGE.parent if (GIT_PAGE.parent / 'GOOGLE.APPSCRIPT').is_dir() else None  # no repositório GitHub não existe
DOCS = GIT_PAGE / 'docs'


def documentos_atuais():
    docs = list(GIT_PAGE.glob('*.md')) + list(DOCS.glob('*.md'))
    if PACOTE:
        docs += list(PACOTE.glob('*.md')) + list((PACOTE / 'GOOGLE.APPSCRIPT').glob('*.md'))
    return docs  # docs/historico/ fica de fora de propósito


class TestDocumentacao(unittest.TestCase):
    def test_arquivos_citados_existem(self):
        base = PACOTE or GIT_PAGE
        existentes = {p.name for p in base.rglob('*') if p.is_file()}
        faltando = []
        for doc in documentos_atuais():
            if doc.name.startswith('ALTERACOES_'):
                continue  # notas de versão citam arquivos removidos de propósito
            for nome in re.findall(r'`([^`\s]*?\.(?:md|sh|py))`', doc.read_text('utf-8')):
                nome = nome.rsplit('/', 1)[-1]
                if '<' in nome or (not PACOTE and doc.parent == GIT_PAGE.parent):
                    continue
                if not PACOTE and (nome in ('continuar_configuracao.sh', 'configurar_integracao.sh', 'atualizar.sh', 'GUIA_INSTALACAO.md')
                                   or 'GOOGLE.APPSCRIPT/' in doc.read_text('utf-8').split(nome)[0][-60:]):
                    continue  # arquivos de GOOGLE.APPSCRIPT/ ficam fora do repositório
                if nome not in existentes:
                    faltando.append(f'{doc.name}: {nome}')
        self.assertEqual(faltando, [])

    def test_manual_cobre_toda_configuracao_do_workflow(self):
        workflow = (GIT_PAGE / '.github/workflows/publicar.yml').read_text('utf-8')
        manual = (DOCS / 'MANUAL_INSTALACAO.md').read_text('utf-8')
        nomes = set(re.findall(r'(?:vars|secrets)\.([A-Z_]+)', workflow)) - {'GITHUB_TOKEN'}
        self.assertTrue(nomes)
        self.assertEqual(sorted(n for n in nomes if f'`{n}`' not in manual), [])

    def test_sem_orientacao_antiga_que_contradiz_o_codigo(self):
        for doc in documentos_atuais():
            texto = doc.read_text('utf-8')
            self.assertIsNone(re.search(r'ESCRITOR_URL`?[^\n]{0,40}opcional', texto), f'{doc.name}: ESCRITOR_URL é obrigatório')
            self.assertNotIn('Manual definitivo', texto, doc.name)

    def test_versao_e_notas_da_versao(self):
        versao = (GIT_PAGE / 'VERSAO').read_text('utf-8').strip()
        self.assertTrue((DOCS / f'ALTERACOES_{versao}.md').is_file(), 'falta docs/ALTERACOES_<versão>.md')
        self.assertEqual([p.name for p in DOCS.glob('ALTERACOES_*.md')], [f'ALTERACOES_{versao}.md'], 'antigas vão para historico/')
        self.assertIn(f'v{versao}', (GIT_PAGE / '.github/workflows/publicar.yml').read_text('utf-8').splitlines()[0])
        if PACOTE:
            self.assertEqual((PACOTE / 'VERSAO').read_text('utf-8').strip(), versao)
            self.assertIn(versao, (PACOTE / 'LEIA-ME.md').read_text('utf-8').splitlines()[0])


if __name__ == '__main__':
    unittest.main()
