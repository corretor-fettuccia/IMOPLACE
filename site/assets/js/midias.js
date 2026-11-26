/* Mídias renderizam direto na página (iframe com loading=lazy, vídeo nativo, panorama ao chegar na tela). */
'use strict';
const ImoplaceMidias=(()=>{
 const safe=value=>{try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password?u.href:'';}catch{return '';}};
 const collection=items=>(Array.isArray(items)?items:[]).filter(x=>x&&x.visivel!==false&&safe(x.url)).sort((a,b)=>(Number(a.ordem)||0)-(Number(b.ordem)||0));
 function embed(value){
  const raw=safe(value);if(!raw)return '';const u=new URL(raw),host=u.hostname;let id='';
  if(['youtube.com','www.youtube.com','m.youtube.com','youtu.be','www.youtube-nocookie.com'].includes(host)){
   id=host==='youtu.be'?u.pathname.slice(1):(u.pathname==='/watch'?u.searchParams.get('v'):u.pathname.split('/').pop());
   if(/^[\w-]{11}$/.test(id||''))return 'https://www.youtube-nocookie.com/embed/'+id;
  }
  if(['vimeo.com','www.vimeo.com','player.vimeo.com'].includes(host)&&/^\d+$/.test(u.pathname.split('/').pop()))return 'https://player.vimeo.com/video/'+u.pathname.split('/').pop();
  if(host==='my.matterport.com'&&u.pathname==='/show/'&&/^[a-zA-Z0-9]+$/.test(u.searchParams.get('m')||''))return 'https://my.matterport.com/show/?m='+u.searchParams.get('m');
  return '';
 }
 function picture(f,item,k,cls='',sizes='(max-width: 768px) 100vw, 60vw'){
  const d=f.adaptativas||{},formats=d.formatos||{},fallback=formats.jpg||formats.png||[];
  const path=x=>esc(assetURL(x));
  const set=rows=>rows.map(x=>path(x.arquivo)+' '+Number(x.largura)+'w').join(', ');
  const preferred=(d.preferido||'webp').toLowerCase();
  const order=[preferred==='jpeg'?'jpg':preferred,'webp','avif','jxl'].filter((x,i,a)=>a.indexOf(x)===i);
  return '<picture>'+order.filter(x=>formats[x]?.length).map(x=>`<source type="image/${x==='jpg'?'jpeg':x}" srcset="${set(formats[x])}" sizes="${sizes}">`).join('')+
   `<img class="${esc(cls)}" src="${path(fallback.length?fallback.at(-1).arquivo:f.arquivo||'')}" ${fallback.length?`srcset="${set(fallback)}" sizes="${sizes}"`:''} width="${Number(d.largura)||960}" height="${Number(d.altura)||600}" alt="${esc(f.alt||item.titulo)}" loading="${k===0?'eager':'lazy'}" ${k===0?'fetchpriority="high"':''} decoding="async"></picture>`;
 }
 const EXT_VIDEO=/\.(mp4|webm|ogv|ogg|mov|m4v)$/i,EXT_IMAGEM=/\.(jpe?g|png|webp|avif)$/i;
 const PRESETS=['16/9','4/3','1/1','9/16','2/1','21/9','3/4'];
 const SANDBOX='allow-scripts allow-same-origin allow-presentation allow-popups allow-popups-to-escape-sandbox allow-forms';
 const ALLOW='autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture; web-share; accelerometer; gyroscope; xr-spatial-tracking';
 const prop=v=>{const m=String(v||'').match(/^\s*(\d{1,4})\s*[\/:x×]\s*(\d{1,4})\s*$/);return m&&+m[1]&&+m[2]?(+m[1])+'/'+(+m[2]):'';};
 const proprio=url=>{const h=new URL(url).hostname.toLowerCase(),own=['imoplace.com.br',(typeof location!=='undefined'&&location.hostname)||''].filter(Boolean);return own.some(d=>h===d||h.endsWith('.'+d));};
 function alvo(x){
  const url=safe(x.url);if(!url)return['link','',''];
  const path=new URL(url).pathname,p=prop(x.proporcao),oficial=embed(url);
  if(oficial)return['iframe',oficial,p||'16/9'];
  if(EXT_VIDEO.test(path))return['video',url,p||'16/9'];
  if(EXT_IMAGEM.test(path))return x.tipo==='panorama_360'?['panorama',url,'2/1']:['imagem',url,p];
  if(proprio(url))return['link',url,''];
  return['iframe',url,p||(x.tipo==='panorama_360'?'2/1':'16/9')];
 }
 const pixels=p=>{if(!p||PRESETS.includes(p))return null;const[w,h]=p.split('/').map(Number);return w>=80&&w<=1400&&h>=50&&h<=2000?[w,h]:null;};
 const estilo=p=>p?'aspect-ratio:'+p:'';
 function player(x){
  const[modo,src,p]=alvo(x),st=esc(estilo(p)),t=esc(x.titulo);
  if(modo==='iframe'){const px=pixels(p);return `<div class="midia-quadro" style="${st}"${px?` data-escala="${px[0]}"`:''}><iframe src="${esc(src)}" title="${t}"${px?` style="width:${px[0]}px;height:${px[1]}px"`:''} loading="lazy" allow="${ALLOW}" allowfullscreen sandbox="${SANDBOX}" referrerpolicy="strict-origin-when-cross-origin"></iframe></div>`;}
  if(modo==='video')return `<div class="midia-quadro" style="${st}"><video src="${esc(src)}" controls playsinline preload="metadata"${safe(x.capa)?` poster="${esc(safe(x.capa))}"`:''}>Seu navegador não reproduz este vídeo.</video></div>`;
  if(modo==='panorama')return `<div class="midia-quadro midia-panorama" style="${st}" data-panorama="${esc(src)}"></div>`;
  if(modo==='imagem')return `<div class="midia-imagem"><img src="${esc(src)}" alt="${t}" loading="lazy" decoding="async"></div>`;
  return '';
 }
 function carrossel(cards){
  if(cards.length<2)return cards.join('');
  return `<div class="midia-carrossel" data-carrossel><div class="mc-trilho" tabindex="0" aria-label="Mídias do imóvel, use as setas para navegar">${cards.join('')}</div><button type="button" class="mc-nav mc-prev" data-mc="-1" aria-label="Mídia anterior">‹</button><button type="button" class="mc-nav mc-next" data-mc="1" aria-label="Próxima mídia">›</button><div class="mc-contador" aria-live="polite"><span data-mc-atual>1</span> / ${cards.length}</div></div>`;
 }
 function html(item){
  const medias=collection(item.midias),links=collection(item.links_externos);
  const cards=medias.map(x=>`<article class="midia-card"><h3>${esc(x.titulo)}</h3>${x.descricao?`<p>${esc(x.descricao)}</p>`:''}${player(x)}<a class="midia-abrir" href="${esc(safe(x.url))}" target="_blank" rel="noopener noreferrer">Abrir em nova aba ↗</a></article>`);
  return '<div id="multimidia" class="imovel-midias">'+(cards.length?'<section class="box" aria-label="Vídeos e tours"><h3>Vídeos e tours</h3>'+carrossel(cards)+'</section>':'')+(links.length?`<button class="btn btn-line" type="button" data-open-links>Mais links ↗</button><dialog id="external-links" aria-labelledby="links-title"><h2 id="links-title">Acessos externos</h2><button type="button" class="btn btn-line" data-close-links>Fechar ✕</button>${links.map(x=>`<p><a href="${esc(safe(x.url))}" target="_blank" rel="noopener noreferrer">${esc(x.titulo)} ↗</a><br>${esc(x.descricao||'')}</p>`).join('')}</dialog>`:'')+'</div>';
 }
 /* Carrossel: setas ‹ › andam um item (com volta ao início), contador e pausa do vídeo que sai da tela. */
 const mcAtual=tr=>Math.round(tr.scrollLeft/Math.max(1,tr.clientWidth));
 function mcAtualizar(tr){
  const box=tr.closest('[data-carrossel]'),i=mcAtual(tr),out=box.querySelector('[data-mc-atual]');
  if(out&&out.textContent!==String(i+1))out.textContent=i+1;
  [...tr.children].forEach((card,k)=>{if(k!==i)card.querySelectorAll('video').forEach(v=>{if(!v.paused)v.pause();});});
 }
 let opener;
 document.addEventListener('click',e=>{
  const nav=e.target.closest('[data-mc]');
  if(nav){const tr=nav.closest('[data-carrossel]').querySelector('.mc-trilho'),n=tr.children.length,i=(mcAtual(tr)+Number(nav.dataset.mc)+n)%n;tr.scrollTo({left:i*tr.clientWidth,behavior:'smooth'});}
  if(e.target.closest('[data-open-links]')){opener=e.target.closest('button');document.querySelector('#external-links')?.showModal();}
  if(e.target.closest('[data-close-links]'))document.querySelector('#external-links')?.close();
 });
 let mcTimer;
 document.addEventListener('scroll',e=>{const tr=e.target;if(!tr.classList?.contains('mc-trilho'))return;clearTimeout(mcTimer);mcTimer=setTimeout(()=>mcAtualizar(tr),80);},true);
 document.addEventListener('keydown',e=>{const tr=e.target;if(!tr.classList?.contains('mc-trilho')||!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();tr.closest('[data-carrossel]').querySelector(e.key==='ArrowLeft'?'.mc-prev':'.mc-next').click();});
 document.addEventListener('close',e=>{if(e.target.id==='external-links')opener?.focus();},true);
 /* Panoramas de imagem 2:1 montam sozinhos quando chegam perto da tela. */
 /* Iframe com tamanho em px (do código colado): renderiza nesse tamanho e estica por escala até a largura do quadro. */
 const escalar=box=>{const f=box.querySelector('iframe'),w=Number(box.dataset.escala);if(f&&w&&box.clientWidth)f.style.transform='scale('+(box.clientWidth/w)+')';};
 const ro=typeof ResizeObserver!=='undefined'?new ResizeObserver(es=>es.forEach(e=>escalar(e.target))):null;
 function iniciar(root=document){
  root.querySelectorAll('[data-escala]').forEach(box=>{escalar(box);ro?.observe(box);});
  const boxes=[...root.querySelectorAll('[data-panorama]:not([data-pronto])')];if(!boxes.length)return;
  const montar=box=>{box.dataset.pronto='1';panorama(box,safe(box.dataset.panorama)).catch(()=>{box.textContent='Não foi possível carregar o panorama. Use o link para abrir a imagem.';});};
  if(typeof IntersectionObserver==='undefined'){boxes.forEach(montar);return;}
  const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){io.unobserve(e.target);montar(e.target);}}),{rootMargin:'300px'});
  boxes.forEach(b=>io.observe(b));
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>iniciar());else if(document.querySelectorAll)iniciar();
 async function panorama(box,url){
  const img=new Image();img.crossOrigin='anonymous';img.src=url;await img.decode();
  if(Math.abs(img.width/img.height-2)>.1)throw Error('Use imagem equiretangular 2:1');
  const canvas=document.createElement('canvas');canvas.width=960;canvas.height=480;canvas.tabIndex=0;canvas.setAttribute('aria-label','Panorama 360 graus. Arraste ou use as setas para olhar ao redor.');
  const gl=canvas.getContext('webgl');if(!gl||img.width>gl.getParameter(gl.MAX_TEXTURE_SIZE))throw Error('WebGL indisponível');
  const shader=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('Shader');return s;};
  const p=gl.createProgram();gl.attachShader(p,shader(gl.VERTEX_SHADER,'attribute vec2 a;varying vec2 v;void main(){v=a;gl_Position=vec4(a,0.,1.);}'));
  gl.attachShader(p,shader(gl.FRAGMENT_SHADER,'precision mediump float;varying vec2 v;uniform sampler2D tex;uniform float yaw;uniform float pitch;void main(){vec3 d=normalize(vec3(v.x*2.,v.y,1.));float y=d.y*cos(pitch)+d.z*sin(pitch);float z=-d.y*sin(pitch)+d.z*cos(pitch);float x=d.x*cos(yaw)+z*sin(yaw);z=-d.x*sin(yaw)+z*cos(yaw);gl_FragColor=texture2D(tex,vec2(atan(x,z)/6.2831853+0.5,0.5-asin(clamp(y,-1.,1.))/3.1415926));}'));
  gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error('Program');gl.useProgram(p);
  const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
  const loc=gl.getAttribLocation(p,'a');gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);
  gl.bindTexture(gl.TEXTURE_2D,gl.createTexture());gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGB,gl.RGB,gl.UNSIGNED_BYTE,img);
  let yaw=0,pitch=0,last=null;const draw=()=>{gl.uniform1f(gl.getUniformLocation(p,'yaw'),yaw);gl.uniform1f(gl.getUniformLocation(p,'pitch'),pitch);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);};
  canvas.onpointerdown=e=>{last=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);};
  canvas.onpointerup=canvas.onpointercancel=()=>last=null;
  canvas.onpointermove=e=>{if(!last)return;yaw-=(e.clientX-last[0])*.006;pitch=Math.max(-1.4,Math.min(1.4,pitch+(e.clientY-last[1])*.006));last=[e.clientX,e.clientY];draw();};
  canvas.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();yaw+=(e.key==='ArrowRight'?.1:e.key==='ArrowLeft'?-.1:0);pitch=Math.max(-1.4,Math.min(1.4,pitch+(e.key==='ArrowUp'?.1:e.key==='ArrowDown'?-.1:0)));draw();};
  box.append(canvas);draw();
 }
 return {html,picture,embed,alvo,player,iniciar,pixels};
})();
