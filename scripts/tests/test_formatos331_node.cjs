'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),os=require('node:os'),cp=require('node:child_process'),{pathToFileURL}=require('node:url');
(async()=>{
 const root=path.resolve(__dirname,'../..'),folder=path.join(root,'atualizacoes/core-3.3.1');
 const gs=fs.readFileSync(path.join(folder,'FormatoImagens331.gs'),'utf8');
 new vm.Script(gs);
 const p={};const api=new Function('PropertiesService','exigirAdmin_','sincronizarConfiguracaoOperacional_',gs+';return {install:instalarFormatoImagens331,normalize:normalizarFormatoImagem331_,detect:detectarFormatoImagem331_};')({getScriptProperties:()=>({getProperty:k=>p[k]??null,setProperty:(k,v)=>p[k]=v})},()=>true,()=>{});
 assert.equal(api.install().formato,'webp');assert.equal(p.FORMATO_PADRAO_IMAGENS,'webp');assert.equal(api.normalize('JPG'),'jpeg');assert.throws(()=>api.normalize('gif'));
 assert.equal(api.detect([137,80,78,71,13,10,26,10,0,0,0,0]),'png');assert.equal(api.detect([255,216,255,0,0,0,0,0,0,0,0,0]),'jpeg');assert.equal(api.detect([255,10,0,0,0,0,0,0,0,0,0,0]),'jxl');assert.equal(api.detect([82,73,70,70,0,0,0,0,87,69,66,80]),'webp');
 const html=fs.readFileSync(path.join(folder,'FormatoImagens331Js.html'),'utf8').replace(/^\s*<script>/,'').replace(/<\/script>\s*$/,'');
 new vm.Script(html);
 let selected='webp',wrong=false,marked=0;const calls=[];
 const original=async name=>{calls.push(name);return name==='obterFormatoPadraoImagens331'?selected:{ok:true};};
 const doc={querySelector:()=>null,createElement:()=>({width:0,height:0,getContext:()=>({drawImage(){},fillRect(){},getImageData:()=>({data:[],width:800,height:600})}),toBlob(fn,mime){fn({type:wrong?'image/png':mime});},toDataURL:()=>'data:image/webp;base64,AAAA'})};
 class Reader{readAsDataURL(blob){this.result='data:'+blob.type+';base64,AAAA';this.onload();}}
 const front=new Function('api','converter','codecJxl','aplicarMarcaDagua','document','createImageBitmap','FileReader','Blob',html+';return {converter,api};')(original,()=>{},async()=>({encodeLossless:async()=>new Uint8Array([255,10]).buffer}),()=>marked++,doc,async()=>({width:800,height:600,close(){}}),Reader,Blob);
 for(const f of ['webp','jpeg','png','jxl']){selected=f;const image=await front.converter({name:'foto.png'},{});assert.equal(image.formato,f);assert.equal(image.largura,800);}
 await front.api('enviarImagem','1001',{});assert(calls.includes('enviarImagemFormato331'));assert.equal(marked,4);
 selected='webp';wrong=true;await assert.rejects(front.converter({name:'x.png'},{}));
 const {prepararAtualizacao331}=await import(pathToFileURL(path.join(folder,'aplicar-core-3.3.1.mjs')));
 const fixture={'Painel.html':'<body>Olá</body>','ConfigOperacional.gs':'function x(){var dados = { SITE_URL: CONFIG.siteUrl, LOTE_MAXIMO: String(limite) };}','Instalador.gs':'function instalar(){\n  sincronizarConfiguracaoOperacional_();\n}','Codigo.gs':'ImoplaceCore.3.3.0','Imoveis.gs':"var x=(f.FORMATO === 'jxl' ? 'jxl' : 'webp);"};
 const prepared=prepararAtualizacao331(fixture);assert(prepared['Painel.html'].includes('FormatoImagens331Js'));assert(prepared['ConfigOperacional.gs'].includes('FORMATO_PADRAO_IMAGENS'));assert.deepEqual(prepararAtualizacao331(prepared),prepared);assert.throws(()=>prepararAtualizacao331({...fixture,'Instalador.gs':'não reconhecido'}));
 const offline=fs.readFileSync(path.join(folder,'ATUALIZAR-CORE-3.3.1.html'),'utf8');const script=offline.match(/<script>([\s\S]*)<\/script>/)[1];
 const ctx={Uint8Array,DataView,Blob,DecompressionStream,console,document:{querySelector:()=>({addEventListener(){}})}};vm.createContext(ctx);vm.runInContext(script,ctx);
 const archived=ctx.zipStore331({'Pacote/CORE/Painel.html':'Olá, marca d’água'});const content=await ctx.lerCoreZip331(archived);assert.equal(content['Painel.html'],'Olá, marca d’água');
 // Exercise the same DEFLATE method used by the original Python-built 3.3.0 ZIP.
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'imoplace-331-'));try{
  const zip=path.join(temp,'fixture.zip');cp.execFileSync('python',['-c',"import zipfile,sys\nwith zipfile.ZipFile(sys.argv[1],'w',zipfile.ZIP_DEFLATED) as z:z.writestr('Pacote/CORE/Painel.html','Conteúdo comprimido com acentuação')",zip]);
  const out=await ctx.lerCoreZip331(new Uint8Array(fs.readFileSync(zip)));assert.equal(out['Painel.html'],'Conteúdo comprimido com acentuação');
 }finally{fs.rmSync(temp,{recursive:true,force:true});}
 console.log('3.3.1: quatro formatos, WebP padrão, marca única, patch idempotente e ZIP/DEFLATE conferidos.');
})().catch(error=>{console.error(error);process.exitCode=1;});
