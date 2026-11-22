/* Detalhes: HTML estático inicial gerado pelo build, atualizado dinamicamente do catalogo.json. */
'use strict';
const det=$('#det');
const code=document.documentElement.dataset.codigo;
let selectedIndex=0;
let currentItem=null;
/* Campo vazio não aparece (antes: "Não informado"). */
const vazio = n => n===null || n===undefined || n==='';
document.documentElement.classList.add('js');   /* com JS, as listas longas começam recolhidas */
const ICONES={dormitorios:'M2 18V6M2 14h20v4M22 14v-2a3 3 0 0 0-3-3h-8v5M6 11.5a1.5 1.5 0 1 0 0-.01',suites:'M5 21V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v17M3 21h18M14 12h.01',
  banheiros:'M4 12h16v3a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5zM6 12V5a2 2 0 0 1 4 0M7 20l-1 2M17 20l1 2',vagas:'M5 16h14M6 16l1.5-5h9L18 16M5 16v3M19 16v3',area:'M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7'};
const ZAP_ICONE='M21 11.5a8.4 8.4 0 0 1-12.4 7.4L3 21l2.1-5.4A8.4 8.4 0 1 1 21 11.5z';
const CARAC_VISIVEIS=6;
const icone=(d,tam=20,cls='ico')=>`<svg class="${cls}" width="${tam}" height="${tam}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${d}"/></svg>`;
const TIPO_ICONES={'casa': 'M3 11l9-7 9 7M5 9.5V20h14V9.5M10 20v-5h4v5', 'apartamento': 'M5 21V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v17M3 21h18M9 7h1M14 7h1M9 11h1M14 11h1M9 15h1M14 15h1', 'terreno': 'M3 7V3h4M17 3h4v4M21 17v4h-4M7 21H3v-4M10 16V8l6 2.5-6 2.5', 'sobrado': 'M4 21V10l8-7 8 7v11M2 21h20M9 21v-4h6v4M9 10h1M14 10h1', 'cobertura': 'M6 21V9h12v12M4 21h16M4 9h16M8 9V6h8v3M10 13h1M13 13h1M10 17h1M13 17h1', 'studio': 'M4 11V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v3M2 13a2 2 0 0 1 4 0v2h12v-2a2 2 0 0 1 4 0v4H2zM5 17v2M19 17v2', 'comercial': 'M3 9l2-5h14l2 5M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0M5 12v9h14v-9M10 21v-5h4v5'};
const TIPO_SINONIMOS={'estudio': 'studio', 'stúdio': 'studio', 'kitnet': 'studio', 'loja': 'comercial', 'sala': 'comercial', 'sala comercial': 'comercial', 'lote': 'terreno'};
const FAIXA_ICONES={'local': 'M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21zM12 7.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4z'};
const CATEGORIAS={'venda': 'Venda', 'lancamento': 'Lançamento', 'aluguel': 'Aluguel', 'locacao': 'Locação'};
const CORACAO='M12 20s-7-4.4-9.2-8.6A5 5 0 0 1 12 6a5 5 0 0 1 9.2 5.4C19 15.6 12 20 12 20z';
const tipoIcone=t=>{t=String(t??'').trim().toLowerCase();t=TIPO_SINONIMOS[t]||t;return TIPO_ICONES[t]||TIPO_ICONES.casa;};
/* Faixa abaixo dos dados: tipo, código, localização e valor (igual a paginas._faixa). */
function faixaHTML(item){
  const p=[];const tipo=String(item.tipo??'').trim();
  if(tipo)p.push(`<div class="fi">${icone(tipoIcone(tipo))}<b>${esc(tipo)}</b><span>Tipo</span></div>`);
  const ref=String(item.id??'').trim();
  if(ref)p.push(`<div class="fi fi-codigo"><b>${esc(ref)}</b><span>Código</span></div>`);
  const x=item.localizacao||{};const nomes=['bairro','cidade','uf'].map(k=>String(x[k]??'').trim()).filter(Boolean);
  if(nomes.length)p.push(`<div class="fi fi-local">${icone(FAIXA_ICONES.local)}<b>${esc(nomes[0])}</b><span>${esc(nomes.slice(1).join(', '))}</span></div>`);
  const cat=CATEGORIAS[String(item.categoria??'').trim().toLowerCase()]||'';
  p.push(`<div class="fi-valor"><b class="price">${brl(item.preco)}</b>${cat?`<span>${esc(cat)}</span>`:''}</div>`);
  return `<div class="faixa-info">${p.join('')}</div>`;
}
function caracGrupo(titulo,arr){
  const itens=(arr||[]).filter(x=>String(x??'').trim());
  if(!itens.length)return '';
  const mais=itens.length>CARAC_VISIVEIS?`<button type="button" class="carac-mais" data-total="${itens.length}" aria-expanded="false">Mostrar todos os ${itens.length} ↓</button>`:'';
  return `<div class="carac-grupo"><h3>${titulo} (${itens.length})</h3><ul class="feat">${itens.map((x,k)=>`<li${k>=CARAC_VISIVEIS?' class="extra"':''}>${esc(x)}</li>`).join('')}</ul>${mais}</div>`;
}
function imgTag(item,index,cls='',sizes) {
  const image=item.imagens?.[index];
  return ImoplaceMidias.picture(image||{},item,index,cls,sizes);
}
/* Galeria: as 5 primeiras em mosaico; as demais numa faixa de miniaturas. Qualquer foto abre o visualizador. */
function galleryHTML(item) {
  const imgs=item.imagens||[];
  if (!imgs.length) return `<div class="gal single"><div class="ph main">${imgTag(item,0)}<span>Imagem indisponível</span></div></div>`;
  const legenda=k=>esc(imgs[k].legenda||'Foto '+(k+1));
  const mosaico=imgs.slice(0,5).map((_,k)=>`<button type="button" class="ph${k===0?' main':''}" data-k="${k}" aria-label="Ampliar foto ${k+1}: ${legenda(k)}">${k===0?imgTag(item,k):imgTag(item,k,'','(max-width: 820px) 96px, 30vw')}<span>${legenda(k)}</span>${k===0&&imgs.length>1?`<em>${imgs.length} fotos</em>`:''}</button>`).join('');
  const faixa=imgs.slice(1).map((_,j)=>{const k=j+1;return `<button type="button" class="gal-mini${k<5?' so-cel':''}" data-k="${k}" aria-label="Ampliar foto ${k+1}: ${legenda(k)}">${imgTag(item,k,'','132px')}</button>`;}).join('');
  return `<div class="gal${imgs.length===1?' single':''}" id="gal">${mosaico}</div>${faixa?`<div class="gal-faixa${imgs.length<=5?' so-cel':''}" role="group" aria-label="Mais fotos">${faixa}</div>`:''}`;
}
function detailsHTML(item) {
  const m2=v=>vazio(v)?null:v+' m²';
  const fields=[
    [item.dormitorios,'Dormitórios','dormitorios'],[item.suites,'Suítes','suites'],[item.banheiros,'Banheiros','banheiros'],
    [item.vagas,'Vagas','vagas'],[m2(item.areaTotal),'Área total','area'],[m2(item.areaUtil),'Área útil','area']
  ];
  const whats=String(item.anunciante?.whatsapp||'').replace(/\D/g,'');
  const zapLink=whats.length>=10?`https://wa.me/${whats}?text=${encodeURIComponent('Olá! Tenho interesse no imóvel '+(item.id||item.codigo)+' anunciado no Imoplace.')}`:'';
  const ref=esc(item.id||item.codigo);
  const enderecoPublico=String(item.localizacao?.endereco||local(item)||'').trim();
  const stats=fields.filter(([n])=>!vazio(n)).map(([n,label,i])=>`<div>${icone(ICONES[i])}<b>${esc(n)}</b><span>${label}</span></div>`).join('');
  const grupos=caracGrupo('No imóvel',item.caracteristicasImovel)+caracGrupo('No condomínio',item.caracteristicasCondominio);
  const mapa=enderecoPublico?'<div class="map"><iframe title="Mapa da localização do imóvel" src="https://www.google.com/maps?q='+encodeURIComponent(enderecoPublico+', Brasil')+'&amp;output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>':'';
  /* Valores: o preço já está no topo; linha sem valor não aparece, e o quadro some se não sobrar nenhuma. */
  const num=v=>typeof v==='number'&&Number.isFinite(v);
  const linhas=[];
  if(num(item.preco)&&item.areaTotal)linhas.push(['Preço por m²',brl(item.preco/item.areaTotal)]);
  if(num(item.condominio))linhas.push(['Condomínio',brl(item.condominio)]);
  if(num(item.iptuAnual))linhas.push(['IPTU anual',brl(item.iptuAnual)]);
  return `<a class="back" href="${esc(SITE_ROOT)}index.html#imoveis">← Voltar aos resultados</a>
  ${galleryHTML(item)}
  ${stats?`<div class="stats">${stats}</div>`:''}
  ${faixaHTML(item)}
  ${ImoplaceMidias.html(item)}
  <div class="dhead"><h1 class="dt">${esc(item.titulo)}</h1><div class="dact"><button type="button" class="btn btn-line share-mobile" id="share"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg><span>Compartilhar</span></button><button type="button" class="btn btn-line" id="save" aria-pressed="false">${icone(CORACAO,18,"")}<span>Salvar</span></button></div></div>
  <div class="imovel-layout">
   <div class="box imovel-sobre"><h3>Sobre o imóvel</h3><p style="white-space:pre-line">${esc(item.descricao||'Descrição não cadastrada.')}</p></div>
   ${linhas.length?`<div class="box imovel-valores"><h3>Valores</h3><dl class="vals">${linhas.map(([r,v])=>`<dt>${r}</dt><dd>${v}</dd>`).join('')}</dl></div>`:''}
   ${enderecoPublico?`<div class="box imovel-mapa"><h3>Localização</h3>${mapa}<div class="where">${esc(enderecoPublico)}</div></div>`:''}
   <div class="imovel-barra">${grupos?`<aside class="box carac" aria-label="Características"><h2>Características</h2>${grupos}</aside>`:''}<aside class="aside box"><div class="adv"><div class="av">I</div><div><b>${esc(item.anunciante?.nome||'Imoplace')}</b>${item.anunciante?.creci?`<span class="where">CRECI ${esc(item.anunciante.creci)}</span>`:''}</div></div>
   ${zapLink?'<div class="contact-note">Solicite mais informações diretamente ao anunciante.</div>':''}
   ${zapLink?`<a class="btn btn-accent" id="whatsapp" target="_blank" rel="noopener noreferrer" href="${zapLink}">Chamar no WhatsApp</a>`:'<button class="btn btn-accent" disabled>Contato indisponível</button>'}
   <div class="ref">Código do imóvel: ${ref}</div></aside><div class="box imoplace-lead" data-lead-property="${ref}" hidden></div></div>
  </div>
  ${zapLink?`<a class="zap-flutuante" href="${zapLink}" target="_blank" rel="noopener noreferrer" aria-label="Chamar no WhatsApp" title="Chamar no WhatsApp" hidden>${icone(ZAP_ICONE,28,'')}</a>`:''}
  <dialog class="viewer" id="photo-viewer" aria-label="Galeria de fotos">
    <div class="viewer-head"><b id="viewer-caption"></b><button class="btn btn-line" type="button" id="viewer-close">Fechar ✕</button></div>
    <div class="viewer-picture" id="viewer-picture"></div>
    <div class="viewer-foot"><button class="btn btn-line" type="button" id="viewer-prev">← Anterior</button><span id="viewer-count"></span><button class="btn btn-line" type="button" id="viewer-next">Próxima →</button></div>
    <div class="viewer-thumbs" id="viewer-thumbs" role="group" aria-label="Todas as fotos"></div>
  </dialog>
  <p id="announce" class="sr-only" role="status" aria-live="polite"></p>`;
}
function updateViewer(index) {
  const gallery=currentItem?.imagens||[];if(!gallery.length)return;
  selectedIndex=(index+gallery.length)%gallery.length;
  const img=gallery[selectedIndex];
  $('#viewer-picture').innerHTML=imgTag(currentItem,selectedIndex);
  $('#viewer-caption').textContent=img.legenda||`Foto ${selectedIndex+1}`;
  $('#viewer-count').textContent=`${selectedIndex+1} de ${gallery.length}`;
  const thumbs=$('#viewer-thumbs');
  if(thumbs&&!thumbs.children.length)thumbs.innerHTML=gallery.map((g,k)=>`<button type="button" class="viewer-thumb" data-k="${k}" aria-label="Foto ${k+1}: ${esc(g.legenda||'Foto '+(k+1))}">${imgTag(currentItem,k,'','88px')}</button>`).join('');
  $$('.viewer-thumb',thumbs||document).forEach(b=>b.setAttribute('aria-current',String(Number(b.dataset.k)===selectedIndex)));
  $(`.viewer-thumb[data-k="${selectedIndex}"]`)?.scrollIntoView({block:'nearest',inline:'nearest'});
}
/* WhatsApp flutuante: aparece quando o botão do cartão de contato sai da tela; some com o cartão à vista,
   com o visualizador de fotos aberto e enquanto se digita no formulário. Nunca os dois botões juntos. */
let atualizarZap=()=>{};
function ligarZapFlutuante(){
  const flutuante=$('.zap-flutuante',det),cartao=$('#whatsapp',det);
  if(!flutuante){atualizarZap=()=>{};return;}
  let cartaoVisivel=false;
  atualizarZap=()=>{flutuante.hidden=cartaoVisivel||!!det.dataset.digitando||!!$('#photo-viewer',det)?.open;};
  if(cartao&&'IntersectionObserver' in window)new IntersectionObserver(es=>{cartaoVisivel=es[0].isIntersecting;atualizarZap();}).observe(cartao);
  else atualizarZap();
  $('#photo-viewer',det)?.addEventListener('close',()=>atualizarZap());
}
det.addEventListener('focusin',e=>{if(e.target.closest('.imoplace-lead')){det.dataset.digitando='1';atualizarZap();}});
det.addEventListener('focusout',e=>{if(e.target.closest('.imoplace-lead')){delete det.dataset.digitando;atualizarZap();}});
det.addEventListener('click',async e=>{
  const mais=e.target.closest('.carac-mais');
  if(mais){
    const aberto=mais.closest('.carac-grupo').classList.toggle('aberto');
    mais.setAttribute('aria-expanded',String(aberto));
    mais.textContent=aberto?'Mostrar menos ↑':`Mostrar todos os ${mais.dataset.total} ↓`;
    return;
  }
  if(!currentItem)return;
  const photo=e.target.closest('.ph, .gal-mini, .viewer-thumb');
  if(photo&&photo.dataset.k!==undefined){
    updateViewer(Number(photo.dataset.k));
    const viewer=$('#photo-viewer');if(viewer&&!viewer.open){viewer.showModal();atualizarZap();}
  }
  if(e.target.closest('#viewer-close')) $('#photo-viewer')?.close();
  if(e.target.closest('#viewer-prev'))updateViewer(selectedIndex-1);
  if(e.target.closest('#viewer-next'))updateViewer(selectedIndex+1);
  if(e.target.closest('#share')) {
    try {if(navigator.share)await navigator.share({title:currentItem.titulo,url:location.href});
      else {await navigator.clipboard.writeText(location.href);$('#announce').textContent='Link copiado.';}}
    catch {$('#announce').textContent='Não foi possível compartilhar.';}
  }
  if(e.target.closest('#save')) {
    const favs=getFavs(),found=favs.includes(currentItem.codigo);
    setFavs(found?favs.filter(x=>x!==currentItem.codigo):[...favs,currentItem.codigo]);
    marcarSalvo(!found);
    $('#announce').textContent=found?'Removido dos favoritos.':'Salvo neste navegador.';
  }
});
function marcarSalvo(salvo){const b=$('#save');if(!b)return;b.setAttribute('aria-pressed',String(salvo));const t=b.querySelector('span');if(t)t.textContent=salvo?'Salvo':'Salvar';}
getCatalog().then(items=>{
  const item=items.find(x=>x.codigo===code);
  if(!item){det.innerHTML=`<a class="back" href="${SITE_ROOT}index.html#imoveis">← Voltar</a><div class="box"><h3>Imóvel não disponível</h3></div>`;return;}
  currentItem=item;
  document.title=`${item.titulo} | Imoplace`;
  det.innerHTML=detailsHTML(item);
  marcarSalvo(getFavs().includes(item.codigo));
}).catch(error=>{console.warn('Catálogo temporariamente indisponível. Exibindo HTML estático do build.',error);}).finally(()=>{window.ImoplaceLead?.mount(det);ligarZapFlutuante();});

/* Contagem anônima: uma chamada por carregamento; não identifica visitantes. */
(function(){
 if(window.imoplaceMonitorIniciado)return;window.imoplaceMonitorIniciado=true;
 const id=document.getElementById('monitor-imovel')?.dataset.imovel;
 if(!id||!/^[A-Za-z0-9_-]{1,80}$/.test(id))return;
 fetch(SITE_ROOT+'monitor-config.json',{cache:'no-store',credentials:'omit'})
 .then(r=>{if(!r.ok)throw Error('config');return r.json();})
 .then(cfg=>{if(!cfg.ativo||!/^https:\/\/script\.google\.com\/macros\/s\/[A-Za-z0-9_-]+\/exec$/.test(cfg.url))return;
 return fetch(cfg.url+'?imovel='+encodeURIComponent(id),{mode:'no-cors',credentials:'omit',cache:'no-store',keepalive:true});})
 .catch(()=>{});
})();
