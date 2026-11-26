/* Imoplace: ferramentas de catálogo, URLs e cartões. Nenhum dado fixo de imóveis no JS. */
'use strict';
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
const SITE_ROOT = document.documentElement.dataset.root || './';
const brl = number => Number.isFinite(Number(number)) && number !== null && number !== ''
  ? Number(number).toLocaleString('pt-BR', {style:'currency', currency:'BRL', maximumFractionDigits:0})
  : 'Sob consulta';
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const clean = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const local = imóvel => [imóvel?.localizacao?.bairro,imóvel?.localizacao?.cidade,imóvel?.localizacao?.uf].filter(Boolean).join(', ');
function assetURL(path) {
  if (typeof path !== 'string' || !/^imoveis\/[\w./-]+\.(svg|webp|avif|png|jpe?g)$/i.test(path) || path.includes('..') || path.includes('\\')) {
    return SITE_ROOT + 'assets/img/sem-imagem.svg';
  }
  return SITE_ROOT + path;
}
function detailURL(item) {
  return SITE_ROOT + 'imoveis/' + encodeURIComponent(item.codigo) + '/';
}
let catalogPromise;
function getCatalog() {
  if (!catalogPromise) {
    catalogPromise = fetch(new URL(SITE_ROOT + 'catalogo.json', document.baseURI), {cache:'no-store'})
      .then(res => {if (!res.ok) throw Error(`HTTP ${res.status}`); return res.json();})
      .then(data => {
        if (!data || !Array.isArray(data.imoveis)) throw Error('Formato inválido do catálogo');
        return data.imoveis.filter(item => item.status === 'publicado' && /^[a-z0-9-]+$/.test(item.codigo) && ['venda','lancamento'].includes(item.categoria));
      });
  }
  return catalogPromise;
}
/* Disponibilidade e tarja (igual a paginas.selo): vendido e indisponível têm prioridade. */
const TARJAS={black_friday:'BLACK FRIDAY',oportunidade:'OPORTUNIDADE',baixou_preco:'BAIXOU O PREÇO',lancamento:'LANÇAMENTO'};
function disponibilidade(item){const v=item.disponibilidade||item.feeds?.disponibilidade||'in_stock';return ['in_stock','out_of_stock','sold'].includes(v)?v:'in_stock';}
function selo(item){
  const d=disponibilidade(item);
  if(d==='sold')return['vendido','VENDIDO'];
  if(d==='out_of_stock')return['indisponivel','INDISPONÍVEL'];
  const t=String(item.tarja||'');if(TARJAS[t])return[t,TARJAS[t]];
  const tx=String(item.tarjaTexto||'').trim().toUpperCase().slice(0,20);
  return t==='personalizada'&&tx?['personalizada',tx]:null;
}
function tarjaHTML(item){const s=selo(item);return s?`<span class="tarja tarja--${s[0]}">${esc(s[1])}</span>`:'';}
function estadoClasse(item){return {sold:'estado-vendido',out_of_stock:'estado-indisponivel'}[disponibilidade(item)]||'';}
function precoHTML(item,cls='price'){
  if(disponibilidade(item)==='sold')return`<b class="${cls} price-vendido">Vendido</b>`;
  const a=item.precoAnterior,p=item.preco;
  return (typeof a==='number'&&typeof p==='number'&&a>p?`<s class="price-old">${brl(a)}</s>`:'')+`<b class="${cls}">${brl(p)}</b>`;
}
/* Grupos do imóvel (sem limite) e uma tabela por grupo logo depois do mapa. Igual a paginas.unidades_html. */
const UN_VISIVEIS=8;
function gruposDo(item){const vistos=new Set();return (Array.isArray(item?.grupos)?item.grupos:[]).filter(g=>{const id=String(g?.id??'').trim();if(!id||vistos.has(id)||!String(g.nome??'').trim())return false;vistos.add(id);return true;});}
function unidadesGrupo(item,items,gid){
  const lista=(Array.isArray(items)?items:[]).filter(e=>gruposDo(e).some(g=>String(g.id)===gid));
  if(!lista.some(e=>e.codigo===item.codigo))lista.push(item);
  if(lista.length<2)return[];
  const num=v=>typeof v==='number'&&Number.isFinite(v);
  return lista.sort((a,b)=>(num(a.preco)?0:1)-(num(b.preco)?0:1)||(num(a.preco)?a.preco:0)-(num(b.preco)?b.preco:0)||Number(a.id||0)-Number(b.id||0));
}
function tabelaGrupo(item,g,lista){
  const gid=String(g.id),titulo=g.titulo||g.nome;
  const tem=v=>v!==null&&v!==undefined&&v!=='';
  const cel=v=>tem(v)?esc(v):'—';
  const areaDe=e=>e.areaUtil!==null&&e.areaUtil!==undefined?e.areaUtil:e.areaTotal;
  /* Coluna que nenhuma unidade preenche não aparece (ex.: loteamento sem dormitórios e vagas). */
  const cols=[['Área',areaDe],['Dorm.',e=>e.dormitorios],['Vagas',e=>e.vagas]].filter(([,f])=>lista.some(e=>tem(f(e)))).map(([c])=>c);
  const linhas=lista.map((e,k)=>{
    const atual=e.codigo===item.codigo,d=disponibilidade(e);
    const cls='un-linha'+(atual?' un-atual':'')+({sold:' un-vendida',out_of_stock:' un-indisponivel'}[d]||'')+(k>=UN_VISIVEIS&&!atual?' un-extra':'');
    const area=areaDe(e),s={sold:'Vendido',out_of_stock:'Indisponível'}[d];
    const valor=s?`<span class="un-selo">${s}</span>`:esc(brl(e.preco));
    const acao=atual?'<span class="un-aqui"><i aria-hidden="true"></i><span class="un-longo">Você está aqui</span><span class="un-curto">Aqui</span></span>':`<a href="${esc(detailURL(e))}" aria-label="Ver anúncio: ${esc(e.unidade||e.titulo||e.tipo||'Imóvel')}"><span class="un-longo">Ver anúncio →</span><span class="un-curto">Ver →</span></a>`;
    return `<tr class="${cls}"${atual?' aria-current="page"':''}><th scope="row"><span class="un-nome">${esc(e.unidade||e.titulo||e.tipo||'Imóvel')}</span><span class="un-tipo">${esc(e.tipo||'Imóvel')}</span></th>`
      +`<td class="un-valor">${valor}</td>`
      +(cols.includes('Área')?`<td>${cel(tem(area)?area+' m²':null)}</td>`:'')
      +(cols.includes('Dorm.')?`<td>${cel(e.dormitorios)}</td>`:'')
      +(cols.includes('Vagas')?`<td class="un-vagas">${cel(e.vagas)}</td>`:'')
      +`<td class="un-acao">${acao}</td></tr>`;
  }).join('');
  const mais=lista.length>UN_VISIVEIS?`<button type="button" class="un-mais" data-total="${lista.length}" aria-expanded="false">Mostrar todos os ${lista.length} ↓</button>`:'';
  const sub=[g.tipo||'',`${lista.length} imóveis`].filter(Boolean).join(' · ');
  return `<section class="box imovel-unidades" aria-labelledby="un-${esc(gid)}"><h3 id="un-${esc(gid)}">${esc(titulo)}</h3>`
    +`<p class="un-sub">${esc(sub)}</p>`
    +'<div class="un-tabela-wrap"><table class="un-tabela"><thead><tr><th scope="col"><span class="un-nome">Imóvel</span><span class="un-tipo">Tipo</span></th><th scope="col">Valor</th>'
    +cols.map(c=>`<th scope="col"${c==='Vagas'?' class="un-vagas"':''}>${c}</th>`).join('')+'<th scope="col"><span class="sr-only">Anúncio</span></th></tr></thead>'
    +`<tbody>${linhas}</tbody></table></div>${mais}</section>`;
}
function unidadesHTML(item,items){
  const tabelas=gruposDo(item).map(g=>{const l=unidadesGrupo(item,items,String(g.id));return l.length?tabelaGrupo(item,g,l):'';}).join('');
  return tabelas?`<div class="imovel-unidades-lista">${tabelas}</div>`:'';
}
function cardHTML(item) {
  const pics = (item.imagens || []).slice(0,5);
  const first = pics.length ? pics : [{arquivo:'',alt:'Imagem indisponível',legenda:'Sem imagem'}];
  const slides = first.map((img,j) => `<div class="sl${j===0?' on':''}">${typeof ImoplaceMidias!=='undefined'?ImoplaceMidias.picture(img,item,1):`<img src="${esc(assetURL(img.arquivo))}" alt="${esc(img.alt||item.titulo)}" loading="lazy" width="640" height="400">`}</div>`).join('');
  return `<article class="card ${estadoClasse(item)}" data-codigo="${esc(item.codigo)}">
  <div class="thumb">
    ${item.tag?`<span class="tag">${esc(item.tag)}</span>`:''}${tarjaHTML(item)}
    <button class="fav" type="button" aria-pressed="false" aria-label="Salvar ${esc(item.titulo)}" title="Favorito neste navegador"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7-4.6-9.3-9.2C1.3 8.6 3.2 5 6.6 5c2 0 3.6 1.1 5.4 3 1.8-1.9 3.4-3 5.4-3 3.4 0 5.3 3.6 3.9 6.8C19 16.4 12 21 12 21z"/></svg></button>
    ${slides}<span class="plb"></span><div class="dots" aria-hidden="true">${first.map((_,j)=>`<i${j===0?' class="on"':''}></i>`).join('')}</div>
  </div>
  <div class="body"><div class="price">${precoHTML(item,'price-v')}</div>
    <a class="title" href="${esc(detailURL(item))}">${esc(item.tipo)} · ${esc(item.titulo)}</a>
    <div class="where">${esc(local(item))}</div>
    <div class="specs"><span><b>${esc(item.dormitorios ?? '—')}</b> dorm.</span><span><b>${esc(item.banheiros ?? '—')}</b> banh.</span><span><b>${esc(item.vagas ?? '—')}</b> vagas</span><span><b>${esc(item.areaTotal ?? '—')}</b> m²</span></div>
  </div></article>`;
}
const REDUCED_MOTION = matchMedia('(prefers-reduced-motion: reduce)');
const FAV_KEY = 'imoplace-favoritos';
function getFavs() { try {return JSON.parse(localStorage.getItem(FAV_KEY) || '[]');} catch {return [];} }
function setFavs(items) { try {localStorage.setItem(FAV_KEY, JSON.stringify(items));} catch {} }
function bindCards(root) {
  $$('.card',root).forEach(card => {
    const fav = $('.fav',card), code=card.dataset.codigo;
    fav.setAttribute('aria-pressed',String(getFavs().includes(code)));
    fav.addEventListener('click', e => {
      e.preventDefault();
      const list = getFavs();
      const active = !list.includes(code);
      setFavs(active ? [...list,code] : list.filter(value=>value!==code));
      fav.setAttribute('aria-pressed',String(active));
    });
    const slides = $$('.sl',card), dots=$$('.dots i',card), label=$('.plb',card);
    let current=0, timer=0;
    const show = k => {
      current=k;
      slides.forEach((s,j)=>s.classList.toggle('on',j===k));
      dots.forEach((d,j)=>d.classList.toggle('on',j===k));
      label.textContent=k ? `Imagem ${k+1} de ${slides.length}` : '';
    };
    const begin = () => {
      if (REDUCED_MOTION.matches || timer || slides.length<2) return;
      show(1); timer=setInterval(()=>show((current+1)%slides.length),1500);
    };
    const end = () => {clearInterval(timer); timer=0;show(0);};
    card.addEventListener('mouseenter',begin);
    card.addEventListener('mouseleave',end);
    card.addEventListener('focusin',begin);
    card.addEventListener('focusout',e=>{if(!card.contains(e.relatedTarget))end();});
  });
}
