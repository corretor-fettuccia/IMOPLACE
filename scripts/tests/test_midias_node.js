'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const context={document:{addEventListener:()=>{},readyState:'complete',querySelectorAll:()=>[]},esc:v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),assetURL:x=>'../../'+x,URL,console};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.resolve(__dirname,'../../site/assets/js/midias.js'),'utf8'),context);
const result=vm.runInContext(`({
 safe:ImoplaceMidias.embed('https://www.youtube-nocookie.com/embed/abcdefghijk'),
 bad:ImoplaceMidias.embed('https://youtube.com.evil.org/watch?v=abcdefghijk'),
 html:ImoplaceMidias.html({midias:[{url:'https://youtu.be/abcdefghijk',titulo:'<script>x</script>'}],links_externos:[{url:'javascript:alert(1)',titulo:'Bad'},{url:'https://example.org',titulo:'Proposta'}]}),
 fb:ImoplaceMidias.html({midias:[{tipo:'iframe',url:'https://www.facebook.com/plugins/post.php?href=x',titulo:'Post',proporcao:'500/463'}]}),
 video:ImoplaceMidias.html({midias:[{tipo:'video',url:'https://cdn.example.org/a.webm',titulo:'V'}]}),
 proprio:ImoplaceMidias.alvo({tipo:'iframe',url:'https://imoplace.com.br/adm/'})[0],
 picture:ImoplaceMidias.picture({arquivo:'foto.webp',adaptativas:{formatos:{jpg:[{arquivo:'foto.jpg',largura:480}],webp:[{arquivo:'foto.webp',largura:480}]}}},{titulo:'Casa'},0)
})`,context);
assert.equal(result.safe,'https://www.youtube-nocookie.com/embed/abcdefghijk');assert.equal(result.bad,'');assert(result.html.includes('<iframe src="https://www.youtube-nocookie.com/embed/abcdefghijk"'));assert(!result.html.includes('Carregar player'));assert(result.fb.includes('aspect-ratio:500/463;max-width:500px'));assert(result.fb.includes('loading="lazy"'));assert(result.video.includes('<video src="https://cdn.example.org/a.webm" controls'));assert.equal(result.proprio,'link');assert(!result.html.includes('<script>'));assert(!result.html.includes('javascript:'));assert(result.html.includes('data-open-links'));assert(result.picture.includes('srcset='));assert(result.picture.includes('fetchpriority="high"'));console.log('Mídias JS: validação, renderização automática e picture aprovados.');
