/* Imoplace 3.4.0 — integrações e eventos de atenção. */
(function(){
'use strict';
const c=window.imoplaceMarketing||{},fb=c.facebook||{};
window.dataLayer=window.dataLayer||[];
window.gtag=window.gtag||function(){window.dataLayer.push(arguments);};
const load=src=>{const s=document.createElement('script');s.async=true;s.src=src;document.head.append(s);};
if(c.gtm?.ativo&&/^GTM-[A-Z0-9]+$/.test(c.gtm.id)){window.dataLayer.push({'gtm.start':Date.now(),event:'gtm.js'});load('https://www.googletagmanager.com/gtm.js?id='+c.gtm.id);}
const tags=[c.analytics,c.conversao].filter(x=>x?.ativo&&x.id);
if(tags.length){load('https://www.googletagmanager.com/gtag/js?id='+tags[0].id);gtag('js',new Date());tags.forEach(x=>gtag('config',x.id));}
function id(){return window.crypto?.randomUUID?.()||Date.now()+'-'+Math.random().toString(36).slice(2);}
function cookie(n){return document.cookie.split('; ').find(x=>x.startsWith(n+'='))?.slice(n.length+1)||undefined;}
function capi(name,eventID,custom){if(!fb.ativo||!['api','ambos'].includes(fb.modo)||!fb.capiUrl)return;try{const capiUrl=new URL(fb.capiUrl);if(capiUrl.protocol!=='https:')return;fetch(capiUrl.href,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event_name:name,event_id:eventID,event_source_url:location.origin+location.pathname,custom_data:custom,fbp:cookie('_fbp'),fbc:cookie('_fbc')}),keepalive:true}).catch(()=>{});}catch(e){console.warn('Endpoint Meta inválido');}}
function meta(name,custom={}){if(!fb.ativo)return;const eventID=id();if(['classica','ambos'].includes(fb.modo)&&window.fbq)window.fbq('track',name,custom,{eventID});capi(name,eventID,custom);}
function snippet(html){const t=document.createElement('template');t.innerHTML=html;for(const n of [...t.content.childNodes]){if(n.nodeName==='SCRIPT'){const s=document.createElement('script');for(const a of n.attributes)s.setAttribute(a.name,a.value);s.textContent=n.textContent;document.head.append(s);}else document.body.append(n);}}
if(fb.ativo&&['classica','ambos'].includes(fb.modo)){
 if(fb.codigo?.trim()){
  // Deduplica o PageView padrão do snippet Meta com o evento do servidor.
  const eventID=id();let matched=false;
  const code=fb.codigo.replace(/fbq\(\s*(['"])track\1\s*,\s*(['"])PageView\2\s*\)/g,()=>{matched=true;return "fbq('track','PageView',{}, {eventID:"+JSON.stringify(eventID)+"})";});
  snippet(code);if(matched)capi('PageView',eventID,{});else if(fb.modo==='ambos')console.warn('Snippet Meta personalizado: envie PageView com ImoplaceTracking.meta para deduplicar.');
 }else if(/^\d{5,25}$/.test(fb.id||'')){
  if(!window.fbq){const q=window.fbq=function(){q.callMethod?q.callMethod.apply(q,arguments):q.queue.push(arguments);};q.push=q;q.loaded=true;q.version='2.0';q.queue=[];window._fbq=q;load('https://connect.facebook.net/en_US/fbevents.js');}
  window.fbq('init',fb.id);meta('PageView');
 }
}else if(fb.ativo&&fb.modo==='api')meta('PageView');
if(c.conversao?.ativo&&c.conversao.snippets)snippet(c.conversao.snippets);
const property=document.documentElement.dataset.codigo||document.getElementById('monitor-imovel')?.dataset.imovel||'';
function track(name,detail={}){const data={...detail,imovel_id:property};window.dataLayer.push({event:name,...data});if(c.analytics?.ativo)gtag('event',name,data);}
window.ImoplaceTracking={track,meta,conversion:(sendTo)=>{if(c.conversao?.ativo)gtag('event','conversion',{send_to:sendTo});}};
if(property){track('view_property');meta('ViewContent',{content_ids:[property],content_type:'product'});}
document.addEventListener('click',e=>{const a=e.target.closest('a');if(a){let u;try{u=new URL(a.href);}catch{return;}if(/(^|\.)(wa.me|whatsapp.com)$/.test(u.hostname)){track('contact_whatsapp');meta('Contact',{content_ids:property?[property]:[]});}else if(u.protocol==='tel:'){track('contact_phone');meta('Contact');}else if(u.pathname.startsWith('/imoveis/'))track('select_property',{destino:u.pathname});}const img=e.target.closest('img');if(img&&property)track('open_property_photo',{foto:img.getAttribute('alt')||img.getAttribute('src')?.split('/').pop()||''});});
let levels=new Set();function scroll(){const max=document.documentElement.scrollHeight-innerHeight;if(max<=0)return;const percent=Math.round(scrollY/max*100);for(const p of [25,50,75,90])if(percent>=p&&!levels.has(p)){levels.add(p);track('scroll_depth',{percentual:p});}}
addEventListener('scroll',scroll,{passive:true});
let visible=0,last=Date.now(),sent=new Set();setInterval(()=>{const now=Date.now();if(document.visibilityState==='visible')visible+=Math.min(now-last,1500);last=now;for(const sec of [30,60,120])if(visible>=sec*1000&&!sent.has(sec)){sent.add(sec);track('attention_time',{segundos:sec});}},1000);
})();
