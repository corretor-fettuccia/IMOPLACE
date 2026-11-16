/* Worker dedicado a avisos; não intercepta nem armazena a navegação do portal. */
'use strict';
self.addEventListener('push',event=>{
 let data={};try{data=event.data?.json()||{};}catch{}
 let url=new URL('/noticias/',self.location.origin);try{const proposed=new URL(data.url,self.location.origin);if(proposed.origin===self.location.origin&&proposed.pathname.startsWith('/noticias/'))url=proposed;}catch{}
 event.waitUntil(self.registration.showNotification(String(data.title||'Novidades no Imoplace').slice(0,100),{body:String(data.body||'Uma nova atualização está disponível.').slice(0,200),icon:'/icon.png',badge:'/icon.png',tag:String(data.tag||'imoplace-noticias').slice(0,100),renotify:true,data:{url:url.href}}));
});
self.addEventListener('notificationclick',event=>{
 event.notification.close();const url=new URL(event.notification.data?.url||'/noticias/',self.location.origin);
 if(url.origin!==self.location.origin||!url.pathname.startsWith('/noticias/'))return;
 event.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(windows=>{const match=windows.find(x=>x.url===url.href);return match?match.focus():self.clients.openWindow(url.href);}));
});
