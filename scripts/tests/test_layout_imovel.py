"""Página do imóvel: mosaico de 5 fotos + faixa, dados abaixo das fotos, Sobre/Valores/Localização em 2/3,
barra 1/3 com características e contato, WhatsApp flutuante. Construtor (paginas.py) e navegador (imovel.js) iguais."""
import json,re,subprocess,unittest
from pathlib import Path
from paginas import detalhe

RAIZ=Path(__file__).resolve().parents[2]


def item(n_fotos=13, **extra):
    base={'id':'1008','codigo':'apto-1008','titulo':'Apartamento','tipo':'Apartamento','preco':299000,'areaTotal':43.29,
          'dormitorios':2,'banheiros':1,'vagas':1,'descricao':'Texto do anúncio.',
          'imagens':[{'arquivo':f'imoveis/apto-1008/imagens/f{k}.webp','legenda':f'Foto {k}'} for k in range(n_fotos)],
          'localizacao':{'bairro':'Petrópolis','cidade':'Porto Alegre','uf':'RS','endereco':'Av. Protásio Alves, 7738'},
          'anunciante':{'nome':'Roberto','creci':'83599F','whatsapp':'5551999999999'},
          'caracteristicasImovel':[f'Item imóvel {k}' for k in range(21)],'caracteristicasCondominio':[f'Item condomínio {k}' for k in range(26)]}
    base.update(extra);return base


def ordem(html,*marcas):
    return [html.index(m) for m in marcas]


class LayoutImovel(unittest.TestCase):
    def test_galeria_mosaico_e_faixa(self):
        html=detalhe(item())
        self.assertEqual(html.count('<button class="ph'),5)
        self.assertEqual(html.count('class="gal-mini"'),8)
        self.assertIn('<em>13 fotos</em>',html)
        self.assertIn('data-k="12"',html)
        self.assertEqual(html.count('class="gal-mini so-cel"'),4)   # fotos 2–5: faixa só no celular
        h5=detalhe(item(n_fotos=5));self.assertIn('class="gal-faixa so-cel"',h5);self.assertNotIn('class="gal-mini"',h5)
        self.assertNotIn('gal-faixa',detalhe(item(n_fotos=1)))
        css=(RAIZ/'site/assets/css/style.css').read_text(encoding='utf-8')
        self.assertIn('.gal-mini.so-cel,.gal-faixa.so-cel{display:none}',css)
        self.assertIn('.gal:not(.single) .ph:not(.main){display:none}',css)

    def test_ordem_e_colunas(self):
        html=detalhe(item())
        a=ordem(html,'id="gal"','class="stats"','class="dhead"','imovel-layout','imovel-sobre','imovel-valores','imovel-mapa','imovel-barra')
        self.assertEqual(a,sorted(a))
        barra=html[html.index('imovel-barra'):]
        self.assertLess(barra.index('class="box carac"'),barra.index('id="whatsapp"'))
        self.assertLess(barra.index('id="whatsapp"'),barra.index('data-lead-property="1008"'))
        self.assertIn('Código do imóvel: 1008',barra)
        self.assertNotIn('Ver no mapa',html);self.assertNotIn('aproximada',html)

    def test_caracteristicas_recolhidas_em_6(self):
        html=detalhe(item())
        self.assertIn('No imóvel (21)',html);self.assertIn('No condomínio (26)',html)
        self.assertEqual(html.count('<li class="extra">'),(21-6)+(26-6))
        self.assertIn('Mostrar todos os 21 ↓',html);self.assertIn('Mostrar todos os 26 ↓',html)
        self.assertNotIn('carac-mais',detalhe(item(caracteristicasImovel=['A','B'],caracteristicasCondominio=[])))

    def test_valores_sem_repetir_preco_e_sem_linha_vazia(self):
        html=detalhe(item())
        valores=html[html.index('imovel-valores'):html.index('imovel-mapa')]
        self.assertIn('Preço por m²',valores);self.assertNotIn('<dt>Preço</dt>',valores)
        self.assertNotIn('Condomínio',valores);self.assertNotIn('Sob consulta',html)
        self.assertNotIn('imovel-valores',detalhe(item(areaTotal=None)))

    def test_whatsapp_flutuante_so_com_numero(self):
        html=detalhe(item())
        self.assertRegex(html,r'<a class="zap-flutuante" href="https://wa\.me/5551999999999\?text=[^"]+"[^>]*aria-label="Chamar no WhatsApp"[^>]*hidden>')
        self.assertNotIn('zap-flutuante',detalhe(item(anunciante={'nome':'Roberto'})))

    def test_campo_vazio_continua_invisivel(self):
        html=detalhe(item(suites=None,caracteristicasImovel=[],caracteristicasCondominio=[]))
        self.assertNotIn('Suítes',html);self.assertNotIn('Características',html);self.assertNotIn('nformado',html)

    def test_imovel_js_monta_a_mesma_estrutura(self):
        js=(RAIZ/'site/assets/js/imovel.js').read_text(encoding='utf-8')
        fim=js.index('det.addEventListener(\'focusin\'')
        script=('const document={documentElement:{dataset:{codigo:"x"},classList:{add(){}}}};const $=()=>({addEventListener(){}});const $$=()=>[];'
                'const SITE_ROOT="../../";const esc=v=>String(v??"").replace(/[&<>"\']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;","\'":"&#39;"}[c]));'
                'const brl=n=>"R$ "+Math.round(n).toLocaleString("pt-BR");const local=i=>[i.localizacao?.bairro,i.localizacao?.cidade,i.localizacao?.uf].filter(Boolean).join(", ");'
                'const ImoplaceMidias={picture:(f,item,k,cls,sizes)=>`<picture data-sizes="${sizes||""}"></picture>`,html:()=>\'<div id="multimidia"></div>\'};'
                +js[js.index("let selectedIndex"):fim]+'\nprocess.stdout.write(detailsHTML('+json.dumps(item(),ensure_ascii=False)+'));')
        r=subprocess.run(['node','-e',script],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        html=r.stdout
        self.assertEqual(html.count('class="ph'),5);self.assertEqual(html.count('class="gal-mini"'),8);self.assertEqual(html.count('gal-mini so-cel'),4)
        self.assertEqual(html.count('data-sizes="132px"'),12)
        a=ordem(html,'id="gal"','class="stats"','class="dhead"','imovel-layout','imovel-sobre','imovel-valores','imovel-mapa','imovel-barra')
        self.assertEqual(a,sorted(a))
        for marca in ('No imóvel (21)','Mostrar todos os 26 ↓','Preço por m²','id="whatsapp"','data-lead-property="1008"','class="zap-flutuante"','id="viewer-thumbs"'):
            self.assertIn(marca,html)
        self.assertEqual(html.count('<li class="extra">'),35)
        self.assertNotIn('Sob consulta',html)

    def test_css_layout_e_ordem_no_celular(self):
        css=(RAIZ/'site/assets/css/style.css').read_text(encoding='utf-8')
        self.assertIn('grid-template-columns:minmax(0,2fr) minmax(0,1fr);grid-template-areas:"sobre barra" "valores barra" "mapa barra"',css)
        self.assertIn('grid-template-areas:"sobre" "valores" "barra" "mapa"',css)   # celular: mapa depois da barra
        self.assertIn('.zap-flutuante{position:fixed',css);self.assertIn('border-radius:50%;background:#16803d',css)
        self.assertNotIn('dgrid',css)

    def test_paginas_publicadas_no_layout_novo(self):
        cat=json.loads((RAIZ/'site/catalogo.json').read_text(encoding='utf-8'))['imoveis']
        for i in cat:
            pagina=RAIZ/'site/imoveis'/i['codigo']/'index.html'
            if pagina.is_file():
                with self.subTest(i['codigo']):self.assertIn('class="imovel-layout"',pagina.read_text(encoding='utf-8'))


if __name__=='__main__':
    unittest.main()
