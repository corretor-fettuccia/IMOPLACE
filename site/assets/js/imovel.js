/* Detalhes: HTML estático inicial gerado pelo build, atualizado dinamicamente do catalogo.json. */
'use strict';
const det=$('#det');
const code=document.documentElement.dataset.codigo;
let selectedIndex=0;
let currentItem=null;
const list = items => (items||[]).length ? (items||[]).map(x=>`<li>${esc(x)}</li>`).join('') : '<li>Não informado</li>';
const value = n => n===null || n===undefined || n==='' ? 'Não informado' : esc(n);
function imgTag(item,index,cls='') {
  const image=item.imagens?.[index];
  return `<img class="${cls}" src="${esc(assetURL(image?.arquivo||''))}" alt="${esc(image?.alt || item.titulo)}" loading="${index===0?'eager':'lazy'}" width="960" height="600">`;
}
function galleryHTML(item,idx=0) {
  const imgs=item.imagens||[];
  if (!imgs.length) return `<div class="gal single"><div class="ph main">${imgTag(item,0)}<span>Imagem indisponível</span></div></div>`;
  const order=[idx,...imgs.map((_,k)=>k).filter(k=>k!==idx)].slice(0,5);
  return `<div class="gal${order.length===1?' single':''}" id="gal">${order.map((k,j)=>
    `<button type="button" class="ph${j===0?' main':''}" data-k="${k}" aria-label="${j===0?'Ampliar:':'Ver foto:'} ${esc(imgs[k].legenda||'Imagem '+(k+1))}">${imgTag(item,k)}<span>${esc(imgs[k].legenda || 'Imagem '+(k+1))}</span>${j===4 && imgs.length>5 ? `<em>+${imgs.length-5} fotos</em>`:''}</button>`).join('')}</div>`;
}
function detailsHTML(item) {
  const pictures=item.imagens||[];
  const fields=[
    [item.dormitorios,'Dormitórios'],[item.suites,'Suítes'],[item.banheiros,'Banheiros'],
    [item.vagas,'Vagas'],[item.areaTotal == null? null:item.areaTotal+' m²','Área total'],
    [item.areaUtil == null? null:item.areaUtil+' m²','Área útil']
  ];
  const whats=String(item.anunciante?.whatsapp||'').replace(/\D/g,'');
  const ref=esc(item.id||item.codigo);
  return `<a class="back" href="${esc(SITE_ROOT)}index.html#imoveis">← Voltar aos resultados</a>
  ${galleryHTML(item,selectedIndex)}
  <div class="dhead"><div><h1 class="dt">${esc(item.titulo)}</h1><div class="where">${esc(item.tipo)} · ${esc(local(item))}</div></div>
   <div class="dr"><div class="price big">${brl(item.preco)}</div><div class="dact"><button type="button" class="btn btn-line" id="share">Compartilhar</button><button type="button" class="btn btn-line" id="save">Salvar</button></div></div></div>
  <div class="dgrid"><div>
   <div class="stats">${fields.map(([n,label])=>`<div><b>${value(n)}</b><span>${label}</span></div>`).join('')}</div>
   <div class="box"><h3>Sobre o imóvel</h3><p style="white-space:pre-line">${esc(item.descricao||'Descrição não cadastrada.')}</p></div>
   <div class="box"><h3>Características</h3><div class="cols">
     <div><h4>No imóvel</h4><ul class="feat">${list(item.caracteristicasImovel)}</ul></div>
     <div><h4>No condomínio</h4><ul class="feat">${list(item.caracteristicasCondominio)}</ul></div></div></div>
   <div class="box"><h3>Valores</h3><dl class="vals"><dt>Preço</dt><dd>${brl(item.preco)}</dd><dt>Condomínio</dt><dd>${brl(item.condominio)}</dd><dt>IPTU anual</dt><dd>${brl(item.iptuAnual)}</dd></dl></div>
   <div class="box"><h3>Localização</h3><div class="map" aria-hidden="true"><i></i></div><div class="where">${esc(item.localizacao?.endereco||local(item))}</div></div>
  </div>
  <aside class="aside box"><div class="adv"><div class="av">I</div><div><b>${esc(item.anunciante?.nome||'Imoplace')}</b>${item.anunciante?.creci?`<span class="where">CRECI ${esc(item.anunciante.creci)}</span>`:''}</div></div>
   <div class="contact-note">${whats?'Solicite mais informações diretamente ao anunciante.':'Contato não informado para este anúncio.'}</div>
   ${whats?`<a class="btn btn-accent" id="whatsapp" target="_blank" rel="noopener noreferrer" href="https://wa.me/${whats}?text=${encodeURIComponent('Olá! Tenho interesse no imóvel '+(item.id||item.codigo)+' anunciado no Imoplace.')}">Chamar no WhatsApp</a>`:'<button class="btn btn-accent" disabled>Contato indisponível</button>'}
   <div class="ref">Código do imóvel: ${ref}</div></aside></div>
  <dialog class="viewer" id="photo-viewer" aria-label="Galeria de fotos">
    <div class="viewer-head"><b id="viewer-caption"></b><button class="btn btn-line" type="button" id="viewer-close">Fechar ✕</button></div>
    <div class="viewer-picture" id="viewer-picture"></div>
    <div class="viewer-foot"><button class="btn btn-line" type="button" id="viewer-prev">← Anterior</button><span id="viewer-count"></span><button class="btn btn-line" type="button" id="viewer-next">Próxima →</button></div>
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
}
det.addEventListener('click',async e=>{
  if(!currentItem)return;
  const photo=e.target.closest('.ph');
  if(photo){
    const k=Number(photo.dataset.k);
    if(photo.classList.contains('main')){updateViewer(k);$('#photo-viewer').showModal();}
    else {selectedIndex=k;$('#gal').outerHTML=galleryHTML(currentItem,k);}
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
    $('#save').textContent=found?'Salvar':'Salvo ✓';
    $('#announce').textContent=found?'Removido dos favoritos.':'Salvo neste navegador.';
  }
});
getCatalog().then(items=>{
  const item=items.find(x=>x.codigo===code);
  if(!item){det.innerHTML=`<a class="back" href="${SITE_ROOT}index.html#imoveis">← Voltar</a><div class="box"><h3>Imóvel não disponível</h3></div>`;return;}
  currentItem=item;
  document.title=`${item.titulo} | Imoplace`;
  det.innerHTML=detailsHTML(item);
  $('#save').textContent=getFavs().includes(item.codigo)?'Salvo ✓':'Salvar';
}).catch(error=>{console.warn('Catálogo temporariamente indisponível. Exibindo HTML estático do build.',error);});
