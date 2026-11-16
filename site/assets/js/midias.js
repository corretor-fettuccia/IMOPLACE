/* Mídias só carregam terceiros após ação do visitante. */
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
 function picture(f,item,k,cls=''){
  const d=f.adaptativas||{},formats=d.formatos||{},fallback=formats.jpg||formats.png||[];
  const path=x=>esc(assetURL(x)),sizes='(max-width: 768px) 100vw, 60vw';
  const set=rows=>rows.map(x=>path(x.arquivo)+' '+Number(x.largura)+'w').join(', ');
  return '<picture>'+['jxl','avif','webp'].filter(x=>formats[x]?.length).map(x=>`<source type="image/${x}" srcset="${set(formats[x])}" sizes="${sizes}">`).join('')+
   `<img class="${esc(cls)}" src="${path(fallback.length?fallback.at(-1).arquivo:f.arquivo||'')}" ${fallback.length?`srcset="${set(fallback)}" sizes="${sizes}"`:''} width="${Number(d.largura)||960}" height="${Number(d.altura)||600}" alt="${esc(f.alt||item.titulo)}" loading="${k===0?'eager':'lazy'}" ${k===0?'fetchpriority="high"':''} decoding="async"></picture>`;
 }
 function html(item){
  const medias=collection(item.midias),links=collection(item.links_externos);
  return '<div id="multimidia">'+(medias.length?'<section class="box" aria-label="Vídeos e tours"><h2>Vídeos e tours</h2>'+medias.map(x=>{
   const target=embed(x.url);return `<article class="midia-card"><h3>${esc(x.titulo)}</h3><p>${esc(x.descricao||'')}</p>${target?`<button type="button" class="btn btn-line" data-embed="${esc(target)}">Carregar player</button>`:x.tipo==='panorama_360'?`<button type="button" class="btn btn-line" data-panorama="${esc(x.url)}">Explorar em 360°</button>`:''} <a href="${esc(safe(x.url))}" target="_blank" rel="noopener noreferrer">Abrir em nova aba ↗</a><div data-player></div></article>`;
  }).join('')+'</section>':'')+(links.length?`<button class="btn btn-line" type="button" data-open-links>Mais links ↗</button><dialog id="external-links" aria-labelledby="links-title"><h2 id="links-title">Acessos externos</h2><button type="button" class="btn btn-line" data-close-links>Fechar ✕</button>${links.map(x=>`<p><a href="${esc(safe(x.url))}" target="_blank" rel="noopener noreferrer">${esc(x.titulo)} ↗</a><br>${esc(x.descricao||'')}</p>`).join('')}</dialog>`:'')+'</div>';
 }
 let opener;
 document.addEventListener('click',async e=>{
  if(e.target.closest('[data-open-links]')){opener=e.target.closest('button');document.querySelector('#external-links')?.showModal();}
  if(e.target.closest('[data-close-links]'))document.querySelector('#external-links')?.close();
  const b=e.target.closest('[data-embed], [data-panorama]');if(!b)return;
  const player=b.closest('article').querySelector('[data-player]');player.replaceChildren();
  if(b.dataset.embed){
   const url=embed(b.dataset.embed);if(!url)return;
   const iframe=document.createElement('iframe');iframe.src=url;iframe.title=b.closest('article').querySelector('h3').textContent;
   iframe.setAttribute('sandbox','allow-scripts allow-same-origin allow-presentation');iframe.allow='fullscreen; accelerometer; gyroscope; picture-in-picture';iframe.allowFullscreen=true;iframe.referrerPolicy='no-referrer';player.append(iframe);
  }else{
   try{await panorama(player,safe(b.dataset.panorama));}catch{player.textContent='Não foi possível carregar o panorama. Use o link para abrir a imagem.';}
  }
 });
 document.addEventListener('close',e=>{if(e.target.id==='external-links')opener?.focus();},true);
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
 return {html,picture,embed};
})();
