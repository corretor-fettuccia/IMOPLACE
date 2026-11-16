'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const context={document:{addEventListener:()=>{}},esc:v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),assetURL:x=>'../../'+x,URL,console};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.resolve(__dirname,'../../site/assets/js/midias.js'),'utf8'),context);
const result=vm.runInContext(`({
 safe:ImoplaceMidias.embed('https://www.youtube-nocookie.com/embed/abcdefghijk'),
 bad:ImoplaceMidias.embed('https://youtube.com.evil.org/watch?v=abcdefghijk'),
 html:ImoplaceMidias.html({midias:[{url:'https://youtu.be/abcdefghijk',titulo:'<script>x</script>'}],links_externos:[{url:'javascript:alert(1)',titulo:'Bad'},{url:'https://example.org',titulo:'Proposta'}]}),
 picture:ImoplaceMidias.picture({arquivo:'foto.webp',adaptativas:{formatos:{jpg:[{arquivo:'foto.jpg',largura:480}],webp:[{arquivo:'foto.webp',largura:480}]}}},{titulo:'Casa'},0)
})`,context);
assert.equal(result.safe,'https://www.youtube-nocookie.com/embed/abcdefghijk');assert.equal(result.bad,'');assert(!result.html.includes('<iframe'));assert(!result.html.includes('<script>'));assert(!result.html.includes('javascript:'));assert(result.html.includes('data-open-links'));assert(result.picture.includes('srcset='));assert(result.picture.includes('fetchpriority="high"'));console.log('Mídias JS: validação, player sob demanda e picture aprovados.');
