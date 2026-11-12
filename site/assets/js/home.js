/* Lista e filtros sobre catalogo.json. Executa no navegador e funciona com servidor HTTP local. */
'use strict';
const form=$('.search'), grid=$('#grid'), resultCount=$('.list-head span'), more=$('.more button');
const advanced=$('#rf'), toggle=$('#tg'), counter=$('#cnt'), sorter=$('.list-head select');
const tabs=$$('.tabs button');
const PAGE_SIZE=6;
let entries=[], filtered=[], shown=PAGE_SIZE, tab='comprar';
const selected = group => $('.chip[aria-pressed="true"]',group)?.textContent.trim() || null;
const selectedMany = group => $$('.chip[aria-pressed="true"]',group).map(c=>c.textContent.trim());
const groupByTitle = title => $$('.grp',advanced).find(g=>clean($('h3',g)?.textContent)===clean(title));
const amount = value => {
  const input=String(value || '').trim();
  if (!input) return null;
  const cleaned=input.replace(/[^\d.,]/g,'').replace(/\./g,'').replace(',','.');
  const n=Number(cleaned);return Number.isFinite(n)?n:null;
};
const minChoice = group => Number.parseInt(selected(group),10) || 0;
function updateCount() {
  const activeChips=$$('.chip[aria-pressed="true"]',advanced).length;
  const activeRanges=$$('input',advanced).filter(el=>el.value.trim()).length;
  counter.textContent=(activeChips+activeRanges)||'';
}
function setTab(which) {
  tab=which;
  tabs.forEach(btn=>btn.setAttribute('aria-selected',String(btn.dataset.tab===which)));
  apply();
}
function matches(item) {
  if (tab==='lancamento' && item.categoria!=='lancamento') return false;
  const search=clean($('#q').value.trim());
  if (search && !clean([item.titulo,item.tipo,item.descricao,local(item)].join(' ')).includes(search)) return false;
  if ($('#t').value!=='Todos' && item.tipo!==$('#t').value) return false;
  if ($('#p').value && $('#p').value!=='Sem limite' && Number(item.preco)>Number($('#p').value)) return false;
  if ($('#a').value && $('#a').value!=='Qualquer' && Number(item.areaTotal)<Number($('#a').value)) return false;
  if (Number(item.dormitorios||0)<minChoice(groupByTitle('Dormitórios'))) return false;
  if (Number(item.banheiros||0)<minChoice(groupByTitle('Banheiros'))) return false;
  if (Number(item.vagas||0)<minChoice(groupByTitle('Vagas de garagem'))) return false;
  const condition=selected(groupByTitle('Condição'));
  if (condition && clean(item.condicao)!==clean(condition)) return false;
  const money=$$('input',groupByTitle('Faixa de preço (R$)')).map(e=>amount(e.value));
  const area=$$('input',groupByTitle('Área (m²)')).map(e=>amount(e.value));
  if (money[0]!==null && Number(item.preco)<money[0]) return false;
  if (money[1]!==null && Number(item.preco)>money[1]) return false;
  if (area[0]!==null && Number(item.areaTotal)<area[0]) return false;
  if (area[1]!==null && Number(item.areaTotal)>area[1]) return false;
  const conditions=selectedMany(groupByTitle('Condições de compra'));
  if (conditions.includes('Aceita financiamento') && !item.financiamento) return false;
  if (conditions.includes('Aceita permuta') && !item.permuta) return false;
  if (conditions.includes('Documentação em dia') && !item.documentacaoEmDia) return false;
  const wanted=selectedMany(groupByTitle('Comodidades'));
  if (!wanted.every(x=>(item.comodidades||[]).some(y=>clean(x)===clean(y)))) return false;
  return true;
}
function order(items) {
  const order=sorter.value;
  if (order==='Menor preço') items.sort((a,b)=>(a.preco||0)-(b.preco||0));
  else if (order==='Maior preço') items.sort((a,b)=>(b.preco||0)-(a.preco||0));
  else if (order==='Mais recentes') items.sort((a,b)=>String(b.atualizadoEm).localeCompare(String(a.atualizadoEm)));
  else items.sort((a,b)=>Number(b.destaque)-Number(a.destaque));
  return items;
}
function render() {
  grid.innerHTML=filtered.length ? filtered.slice(0,shown).map(cardHTML).join('') : '<p class="empty-state">Nenhum imóvel corresponde aos filtros. Experimente reduzir os critérios.</p>';
  bindCards(grid);
  resultCount.textContent=`${filtered.length} ${filtered.length===1?'encontrado':'encontrados'}`;
  $('.more').hidden=shown>=filtered.length;
}
function apply() {filtered=order(entries.filter(matches));shown=PAGE_SIZE;render();updateCount();}
form.addEventListener('submit',e=>{e.preventDefault();apply();$('#imoveis').scrollIntoView({behavior:'smooth',block:'start'});});
$('#q').addEventListener('input',apply);
['t','p','a'].forEach(id=>$('#'+id).addEventListener('change',apply));
sorter.addEventListener('change',apply);
more.addEventListener('click',()=>{shown+=PAGE_SIZE;render();});
toggle.addEventListener('click',()=>{const on=advanced.classList.toggle('open');toggle.setAttribute('aria-expanded',String(on));});
advanced.addEventListener('click',e=>{
  const chip=e.target.closest('.chip');if(!chip) return;
  const on=chip.getAttribute('aria-pressed')!=='true';
  if (chip.parentElement.hasAttribute('data-one')) $$('.chip',chip.parentElement).forEach(c=>c.setAttribute('aria-pressed','false'));
  chip.setAttribute('aria-pressed',String(on));apply();
});
$$('input',advanced).forEach(input=>input.addEventListener('input',apply));
$('#clr').addEventListener('click',()=>{$$('.chip',advanced).forEach(c=>c.setAttribute('aria-pressed','false'));$$('input',advanced).forEach(e=>e.value='');apply();});
tabs.forEach(btn=>btn.addEventListener('click',()=>setTab(btn.dataset.tab)));
$('#nav-lancamentos')?.addEventListener('click',()=>{});
const params=new URLSearchParams(location.search);
if (params.get('categoria')==='lancamento') tab='lancamento';
tabs.forEach(btn=>btn.setAttribute('aria-selected',String(btn.dataset.tab===tab)));
grid.innerHTML='<p class="empty-state">Carregando imóveis...</p>';
getCatalog().then(items=>{entries=items;apply();}).catch(error=>{
  console.error('Falha no catálogo',error);
  grid.innerHTML='<p class="empty-state">Não foi possível carregar o catálogo. Abra o projeto pelo servidor HTTP local, não diretamente pelo arquivo.</p>';
  resultCount.textContent='Catálogo indisponível';
  $('.more').hidden=true;
});
