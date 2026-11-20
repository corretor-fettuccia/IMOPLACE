'use strict';
/* Botão Compartilhar das notícias: só aparece em celular/tablet (CSS .share-mobile, pointer:coarse)
   e abre o menu de compartilhar do próprio aparelho. Sem esse menu, copia o link. */
document.addEventListener('click',async e=>{
 const b=e.target.closest('[data-compartilhar]');if(!b)return;
 const url=new URL(b.dataset.compartilhar||location.href,location.href).href,title=b.dataset.titulo||document.title,texto=b.textContent;
 try{
  if(navigator.share){await navigator.share({title,url});return;}
  await navigator.clipboard.writeText(url);b.textContent='Link copiado';
 }catch(err){if(err&&err.name==='AbortError')return;b.textContent='Não foi possível compartilhar';}
 setTimeout(()=>{b.textContent=texto;},2500);
});
