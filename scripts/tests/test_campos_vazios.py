"""Campo vazio não aparece na página do imóvel (nada de "Não informado")."""
import unittest
from paginas import detalhe


def item(**extra):
    base = {'id': '1001', 'codigo': 'casa-1001', 'titulo': 'Casa', 'tipo': 'Casa', 'imagens': [],
            'localizacao': {'cidade': 'Canoas', 'uf': 'RS'}, 'anunciante': {}}
    base.update(extra)
    return base


class CamposVazios(unittest.TestCase):
    def test_vazio_some_e_zero_aparece(self):
        html = detalhe(item(dormitorios=3, suites=None, vagas=0, caracteristicasImovel=[], caracteristicasCondominio=[]))
        self.assertNotIn('nformado', html)
        self.assertNotIn('Suítes', html)
        self.assertIn('<b>3</b><span>Dormitórios</span>', html)
        self.assertIn('<b>0</b><span>Vagas</span>', html)   # zero é informação, não campo vazio
        self.assertNotIn('Características', html)

    def test_tudo_vazio_sem_quadros_vazios(self):
        html = detalhe(item(caracteristicasImovel=['Churrasqueira']))
        self.assertNotIn('class="stats"', html)
        self.assertIn('No imóvel', html)
        self.assertNotIn('No condomínio', html)
        self.assertIn('Contato indisponível', html)
        self.assertNotIn('small-note', html)


if __name__ == '__main__':
    unittest.main()
