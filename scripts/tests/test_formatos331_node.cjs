'use strict';
// Formatos 3.3.1 integrados ao CORE (antes em atualizacoes/core-3.3.1, retirado no commit 987f389).
// Só roda no pacote completo (CORE/ ao lado de GITHUB/); no repositório o teste Python é pulado.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const core=path.resolve(__dirname,'../../../CORE');
 const gs=fs.readFileSync(path.join(core,'FormatoImagens331.gs'),'utf8');
 const p={};let sincronizou=0;
 const api=new Function('PropertiesService','exigirAdmin_','sincronizarConfiguracaoOperacional_','propriedade_',gs+';return {install:instalarFormatoImagens331,get:obterFormatoPadraoImagens331,normalize:normalizarFormatoImagem331_,detect:detectarFormatoImagem331_};')(
  {getScriptProperties:()=>({getProperty:k=>p[k]??null,setProperty:(k,v)=>p[k]=v})},()=>true,()=>sincronizou++,(k,d)=>p[k]??d);
 assert.equal(api.install().formato,'webp');assert.equal(p.FORMATO_PADRAO_IMAGENS,'webp');
 assert.equal(api.normalize('JPG'),'jpeg');assert.throws(()=>api.normalize('gif'));
 assert.equal(api.detect([137,80,78,71,13,10,26,10,0,0,0,0]),'png');assert.equal(api.detect([255,216,255,0,0,0,0,0,0,0,0,0]),'jpeg');
 assert.equal(api.detect([255,10,0,0,0,0,0,0,0,0,0,0]),'jxl');assert.equal(api.detect([82,73,70,70,0,0,0,0,87,69,66,80]),'webp');
 // 4.2.1: a leitura do formato (chamada a cada foto) não grava nada.
 const antes=sincronizou;p.FORMATO_PADRAO_IMAGENS='jpg';assert.equal(api.get(),'jpeg');assert.equal(sincronizou,antes);assert.equal(p.FORMATO_PADRAO_IMAGENS,'jpg');
 const html=fs.readFileSync(path.join(core,'FormatoImagens331Js.html'),'utf8').replace(/^\s*<script>/,'').replace(/<\/script>\s*$/,'');
 let selected='webp',wrong=false,marked=0;
 const fakeApi=async name=>name==='obterFormatoPadraoImagens331'?selected:{ok:true};
 const doc={querySelector:()=>null,createElement:()=>({width:0,height:0,getContext:()=>({drawImage(){},fillRect(){},getImageData:()=>({data:[],width:800,height:600})}),toBlob(fn,mime){fn({type:wrong?'image/png':mime});},toDataURL:()=>'data:image/webp;base64,AAAA'})};
 class Reader{readAsDataURL(blob){this.result='data:'+blob.type+';base64,AAAA';this.onload();}}
 const front=new Function('api','converter','codecJxl','aplicarMarcaDagua','document','createImageBitmap','FileReader','Blob',html+';return {converter};')(
  fakeApi,()=>{},async()=>({encodeLossless:async()=>new Uint8Array([255,10]).buffer}),()=>marked++,doc,async()=>({width:800,height:600,close(){}}),Reader,Blob);
 for(const f of ['webp','jpeg','png','jxl']){selected=f;const image=await front.converter({name:'foto.png'},{});assert.equal(image.formato,f);assert.equal(image.largura,800);}
 assert.equal(marked,4);
 selected='webp';wrong=true;await assert.rejects(front.converter({name:'x.png'},{}));
 // O painel chama as funções reais do servidor, sem redirecionamento.
 const painel=fs.readFileSync(path.join(core,'PainelJs.html'),'utf8');
 assert(painel.includes("api('enviarImagemFormato331'")&&painel.includes("api('substituirImagemFormato331'"));
 console.log('Formatos: quatro formatos, WebP padrão, leitura sem gravação e envio direto conferidos.');
})().catch(error=>{console.error(error);process.exitCode=1;});
