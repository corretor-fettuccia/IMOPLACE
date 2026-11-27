"""Google Notícias: sitemap de notícias (/noticias/news.xml) e feed RSS (/noticias/feed.xml)."""
import tempfile,unittest
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
import noticias,gerador

CONF={'urlPublica':'https://imoplace.com.br','nome':'ImoPlace','permitirIndexacao':True,'ano':'2026'}
NS={'s':'http://www.sitemaps.org/schemas/sitemap/0.9','n':'http://www.google.com/schemas/sitemap-news/0.9',
    'content':'http://purl.org/rss/1.0/modules/content/','media':'http://search.yahoo.com/mrss/','atom':'http://www.w3.org/2005/Atom'}
AGORA=datetime(2026,11,27,12,0,tzinfo=timezone.utc)

def row(i,slug,pub,**kw):
    return dict(ID=i,SLUG=slug,TITULO='Título & teste '+slug,RESUMO='Resumo '+slug,CORPO='## Seção\n\nTexto **forte**.\n\n- item',STATUS='publicado',
                CATEGORIA='Mercado',TAGS='FGTS, Canoas',AUTOR='Imoplace',CAPA_URL='https://images.unsplash.com/photo-1?w=1200',
                PUBLICADO_EM=pub,ATUALIZADO_EM=pub,VERSAO=1,**kw)

class GoogleNews(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
        self.rows=[row('n000000000001','nova','2026-11-27T10:00:00.123Z'),row('n000000000002','ontem','2026-11-26T09:00:00Z'),
                   row('n000000000003','antiga','2026-11-20T09:00:00Z'),row('n000000000004','rascunho','2026-11-27T09:00:00Z',)]
        self.rows[3]['STATUS']='rascunho'
    def tearDown(self):self.tmp.cleanup()

    def test_news_sitemap_so_ultimos_dois_dias_com_tags_obrigatorias(self):
        items=noticias.construir(self.p,CONF,self.rows,{})
        noticias.gravar_news_sitemap(self.p,CONF,items,AGORA)
        root=ET.parse(self.p/'noticias/news.xml').getroot()
        urls=root.findall('s:url',NS);locs=[u.find('s:loc',NS).text for u in urls]
        self.assertEqual(locs,['https://imoplace.com.br/noticias/nova-n000000000001/','https://imoplace.com.br/noticias/ontem-n000000000002/'])
        n=urls[0].find('n:news',NS)
        self.assertEqual(n.find('n:publication/n:name',NS).text,'ImoPlace')
        self.assertEqual(n.find('n:publication/n:language',NS).text,'pt')
        self.assertEqual(n.find('n:publication_date',NS).text,'2026-11-27T10:00:00Z')
        self.assertEqual(n.find('n:title',NS).text,'Título & teste nova')

    def test_news_sitemap_nunca_fica_sem_url_e_some_sem_indexacao(self):
        items=noticias.construir(self.p,CONF,self.rows[1:3],{})
        noticias.gravar_news_sitemap(self.p,CONF,items,datetime(2026,12,10,tzinfo=timezone.utc))
        locs=[u.find('s:loc',NS).text for u in ET.parse(self.p/'noticias/news.xml').getroot().findall('s:url',NS)]
        self.assertEqual(locs,['https://imoplace.com.br/noticias/ontem-n000000000002/'])
        noticias.gravar_news_sitemap(self.p,CONF,[],AGORA)
        self.assertEqual(ET.parse(self.p/'noticias/news.xml').getroot().findall('s:url',NS),[])
        noticias.gravar_news_sitemap(self.p,dict(CONF,permitirIndexacao=False),items,AGORA)
        self.assertFalse((self.p/'noticias/news.xml').exists())

    def test_robots_aponta_para_news_sitemap(self):
        noticias.construir(self.p,CONF,self.rows,{});gerador.gravar_sitemap([],self.p,CONF)
        self.assertIn('Sitemap: https://imoplace.com.br/noticias/news.xml',(self.p/'robots.txt').read_text())

    def test_feed_rss_padrao_google_news(self):
        noticias.construir(self.p,CONF,self.rows,{})
        texto=(self.p/'noticias/feed.xml').read_text();ch=ET.fromstring(texto).find('channel')
        self.assertEqual(ch.find('language').text,'pt-BR')
        self.assertEqual(ch.find('atom:link',NS).get('href'),'https://imoplace.com.br/noticias/feed.xml')
        itens=ch.findall('item');self.assertEqual(len(itens),3)
        i=itens[0]
        self.assertEqual(i.find('pubDate').text,'Fri, 27 Nov 2026 10:00:00 +0000')
        self.assertEqual(i.find('guid').get('isPermaLink'),'true')
        self.assertIn('<h2>Seção</h2>',i.find('content:encoded',NS).text)
        self.assertEqual(i.find('media:content',NS).get('url'),'https://images.unsplash.com/photo-1?w=1200')
        self.assertGreater(len(i.find('content:encoded',NS).text),len(i.find('description').text))
        # Sem horário de geração: duas execuções iguais não geram commit.
        noticias.construir(self.p,CONF,self.rows,{});self.assertEqual(texto,(self.p/'noticias/feed.xml').read_text())

    def test_matéria_usa_newsarticle(self):
        items=noticias.construir(self.p,CONF,self.rows,{})
        self.assertIn('"@type": "NewsArticle"',(self.p/'noticias'/items[0]['codigo']/'index.html').read_text())

if __name__=='__main__':unittest.main()
