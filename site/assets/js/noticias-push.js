/* Inscrição voluntária: nenhuma permissão é pedida sem clique. */
(()=>{'use strict';
const script=document.currentScript;
const root=new URL('../../',script.src);let configuration;
const status=(button,message)=>{const box=button.closest('.news-optin')||button.parentElement;const el=box.querySelector('.push-status');if(el)el.textContent=message;};
const bytes=s=>Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')+'='.repeat((4-s.length%4)%4)),c=>c.charCodeAt(0));
async function config(){return configuration??=(fetch(new URL('noticias/push-config.json',root),{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json();}));}
function registerOnServer(url,action,subscription,scope){
 return new Promise((resolve,reject)=>{
  const nonce=Array.from(crypto.getRandomValues(new Uint8Array(24)),x=>x.toString(16).padStart(2,'0')).join('');
  const frame=document.createElement('iframe');frame.hidden=true;frame.name='imoplace-'+nonce;frame.title='Registrar escolha de avisos';
  const form=document.createElement('form');form.action=url;form.method='POST';form.target=frame.name;form.hidden=true;
  for(const [name,value] of Object.entries({acao:action,nonce,dados:JSON.stringify({subscription:subscription.toJSON(),scope})})){const el=document.createElement('input');el.name=name;el.value=value;form.append(el);}
  let timer;const clean=()=>{clearTimeout(timer);window.removeEventListener('message',received);form.remove();frame.remove();};
  const received=e=>{
   const allowed=e.origin==='https://script.google.com'||/^https:\/\/[a-z0-9-]+\.googleusercontent\.com$/.test(e.origin);
   if(!allowed||!e.data?.imoplacePush||e.data.nonce!==nonce)return;
   clean();e.data.result?.ok?resolve():reject(Error('Não foi possível registrar. Tente novamente.'));
  };
  window.addEventListener('message',received);document.body.append(frame,form);timer=setTimeout(()=>{clean();reject(Error('Não foi possível confirmar o cadastro. Tente novamente.'));},25000);form.submit();
 });
}
const buttons=[...document.querySelectorAll('[data-push-scope]')];buttons.forEach(b=>b.disabled=true);
config().then(cfg=>{for(const b of buttons){b.disabled=!cfg.ativo;if(!cfg.ativo)status(b,'Avisos indisponíveis no momento.');}}).catch(()=>buttons.forEach(b=>status(b,'Avisos indisponíveis no momento.')));
for(const button of buttons)button.addEventListener('click',async()=>{
 if(!('serviceWorker'in navigator)||!('PushManager'in window)||!('Notification'in window)){status(button,'Este navegador não oferece avisos aqui. No iPhone, adicione o site à tela de início e abra por ela.');return;}
 // requestPermission é invocado diretamente pelo clique, antes de qualquer espera de rede.
 const permission=Notification.permission==='default'?Notification.requestPermission():Promise.resolve(Notification.permission);
 button.disabled=true;let newlyCreated=false,subscription;
 try{
  if(await permission!=='granted'){status(button,'Avisos não ativados. Você pode revisar a permissão nas configurações do navegador.');return;}
  const cfg=await config();if(!cfg.ativo)throw Error('Avisos indisponíveis no momento.');
  const reg=await navigator.serviceWorker.register(new URL('imoplace-push-sw.js',root),{scope:root.pathname});await navigator.serviceWorker.ready;
  subscription=await reg.pushManager.getSubscription();
  if(!subscription){subscription=await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:bytes(cfg.publicKey)});newlyCreated=true;}
  await registerOnServer(cfg.url,'push-inscrever',subscription,button.dataset.pushScope||'*');
  status(button,'Pronto! Você receberá os próximos avisos neste navegador.');button.textContent='Avisos ativados ✓';
 }catch(e){if(newlyCreated&&subscription)await subscription.unsubscribe().catch(()=>{});status(button,e.message||'Não foi possível ativar os avisos.');}
 finally{button.disabled=false;}
});
for(const button of document.querySelectorAll('[data-push-cancelar]'))button.addEventListener('click',async()=>{
 button.disabled=true;
 try{
  if(!('serviceWorker'in navigator)){status(button,'Não há avisos ativos neste navegador.');return;}
  const reg=await navigator.serviceWorker.getRegistration(root.href);const sub=await reg?.pushManager.getSubscription();
  if(sub){try{const cfg=await config();if(cfg.ativo)await registerOnServer(cfg.url,'push-remover',sub,'*');}finally{await sub.unsubscribe();}}
  status(button,'Avisos cancelados neste navegador.');
 }catch{status(button,'Revise também a permissão de notificações nas configurações do navegador.');}finally{button.disabled=false;}
});
})();
