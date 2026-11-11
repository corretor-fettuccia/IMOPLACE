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
function cardHTML(item) {
  const pics = (item.imagens || []).slice(0,5);
  const first = pics.length ? pics : [{arquivo:'',alt:'Imagem indisponível',legenda:'Sem imagem'}];
  const slides = first.map((img,j) => `<div class="sl${j===0?' on':''}"><img src="${esc(assetURL(img.arquivo))}" alt="${esc(img.alt || item.titulo)}" loading="lazy" width="640" height="400"></div>`).join('');
  return `<article class="card" data-codigo="${esc(item.codigo)}">
  <div class="thumb">
    ${item.tag?`<span class="tag">${esc(item.tag)}</span>`:''}
    <button class="fav" type="button" aria-pressed="false" aria-label="Salvar ${esc(item.titulo)}" title="Favorito neste navegador"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7-4.6-9.3-9.2C1.3 8.6 3.2 5 6.6 5c2 0 3.6 1.1 5.4 3 1.8-1.9 3.4-3 5.4-3 3.4 0 5.3 3.6 3.9 6.8C19 16.4 12 21 12 21z"/></svg></button>
    ${slides}<span class="plb"></span><div class="dots" aria-hidden="true">${first.map((_,j)=>`<i${j===0?' class="on"':''}></i>`).join('')}</div>
  </div>
  <div class="body"><div class="price">${brl(item.preco)}</div>
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
