#!/usr/bin/env node
/**
 * Aplicador local do CORE 3.3.1. Não acessa contas, tokens, APIs nem faz deploy.
 * Uso: node aplicar-core-3.3.1.mjs /caminho/CORE
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const PAYLOAD={
  "FormatoImagens331.gs": "/**\n * Imoplace CORE 3.3.1 — formato configurável. Complemento do CORE 3.3.0.\n * Propriedade: FORMATO_PADRAO_IMAGENS = webp | jpeg | png | jxl.\n */\nfunction normalizarFormatoImagem331_(valor) {\n  var formato=String(valor||'webp').trim().toLowerCase();\n  if(formato==='jpg')formato='jpeg';\n  if(['webp','jpeg','png','jxl'].indexOf(formato)<0)throw new Error('FORMATO_PADRAO_IMAGENS deve ser webp, jpeg, png ou jxl.');\n  return formato;\n}\nfunction instalarFormatoImagens331() {\n  exigirAdmin_();\n  var props=PropertiesService.getScriptProperties();\n  if(!props.getProperty('FORMATO_PADRAO_IMAGENS'))props.setProperty('FORMATO_PADRAO_IMAGENS','webp');\n  var formato=normalizarFormatoImagem331_(props.getProperty('FORMATO_PADRAO_IMAGENS'));\n  props.setProperty('FORMATO_PADRAO_IMAGENS',formato);\n  sincronizarConfiguracaoOperacional_();\n  return {ok:true,formato:formato};\n}\nfunction obterFormatoPadraoImagens331() {\n  exigirAdmin_();\n  return instalarFormatoImagens331().formato;\n}\nfunction detectarFormatoImagem331_(bytes) {\n  var b=bytes.slice(0,12).map(function(x){return x&255;});\n  if(b[0]===255&&b[1]===216&&b[2]===255)return 'jpeg';\n  if(b.slice(0,8).join(',')==='137,80,78,71,13,10,26,10')return 'png';\n  if(b[0]===255&&b[1]===10||b.join(',')==='0,0,0,12,74,88,76,32,13,10,135,10')return 'jxl';\n  var sig=String.fromCharCode.apply(null,b.slice(0,4))+String.fromCharCode.apply(null,b.slice(8,12));\n  if(sig==='RIFFWEBP')return 'webp';\n  throw new Error('Arquivo não reconhecido. Use WebP, JPEG, PNG ou JXL.');\n}\nfunction prepararArquivoFormato331_(arquivo,imagemId) {\n  if(!arquivo||typeof arquivo.base64!=='string')throw new Error('Arquivo ausente.');\n  var bytes=Utilities.base64Decode(arquivo.base64);\n  if(bytes.length<16)throw new Error('Arquivo vazio.');\n  if(bytes.length>CONFIG.maxFotoBytes)throw new Error('Imagem acima do limite de tamanho configurado.');\n  var formato=detectarFormatoImagem331_(bytes);\n  if(arquivo.formato&&normalizarFormatoImagem331_(arquivo.formato)!==formato)throw new Error('Conteúdo da imagem diferente do formato informado.');\n  var mini=String(arquivo.miniatura||'');\n  if(mini&&(!/^data:image\\/(webp|jpeg|png);base64,[A-Za-z0-9+/=]+$/.test(mini)||mini.length>40000))mini='';\n  return {blob:Utilities.newBlob(bytes,'image/'+formato,imagemId+'.'+formato),formato:formato,bytes:bytes.length,sha256:hexDeBytes_(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,bytes)),miniatura:mini,nome:texto_(arquivo.nome||'foto',80),largura:Math.max(0,Math.round(Number(arquivo.largura)||0)),altura:Math.max(0,Math.round(Number(arquivo.altura)||0))};\n}\nfunction enviarImagemFormato331(id,arquivo) {\n  var usuario=exigirAdmin_();\n  var resultado=comTrava_(function(){\n    var ctx=carregar_(),imovel=acharImovel_(ctx,id),ativas=imagensDoImovel_(ctx,id,false);\n    if(ativas.length>=CONFIG.maxFotos)throw new Error('Limite de fotos por imóvel atingido.');\n    var imagemId=novoIdImagem_(),p=prepararArquivoFormato331_(arquivo,imagemId),pasta=pastaDoImovel_(imovel),file=pasta.createFile(p.blob);\n    var ordem=ativas.reduce(function(m,i){return Math.max(m,Number(i.ORDEM)||0);},0)+1;\n    anexarLinha_('IMAGENS',ctx.imagens,{IMAGEM_ID:imagemId,IMOVEL_ID:imovel.ID,DRIVE_FILE_ID:file.getId(),NOME:p.nome,LEGENDA:texto_(arquivo.legenda,80),ALT:'',ORDEM:ordem,SHA256:p.sha256,BYTES:p.bytes,LARGURA:p.largura,ALTURA:p.altura,FORMATO:p.formato,MINIATURA:p.miniatura,VERSAO:1,VERSAO_PUBLICADA:0,OPERACAO:'incluir',ESTADO_SYNC:'pendente',ATUALIZADO_EM:agoraIso_()});\n    if(!imovel.IMAGEM_CAPA_ID)imovel.IMAGEM_CAPA_ID=imagemId;\n    marcarAlteracao_(ctx,imovel,'foto-incluir',usuario);gravarLinha_('IMOVEIS',ctx.imoveis,imovel);\n    return visaoPainel_(ctx,imovel);\n  });\n  solicitarPublicacaoAutomatica_(resultado);return resultado;\n}\nfunction substituirImagemFormato331(id,imagemId,arquivo) {\n  var usuario=exigirAdmin_();\n  var resultado=comTrava_(function(){\n    var ctx=carregar_(),imovel=acharImovel_(ctx,id),img=acharImagem_(ctx,id,imagemId);\n    if(img.OPERACAO==='excluir')throw new Error('Esta foto está marcada para exclusão.');\n    var p=prepararArquivoFormato331_(arquivo,String(img.IMAGEM_ID)),antigo=String(img.DRIVE_FILE_ID||''),file=pastaDoImovel_(imovel).createFile(p.blob);\n    img.DRIVE_FILE_ID=file.getId();img.SHA256=p.sha256;img.BYTES=p.bytes;img.FORMATO=p.formato;img.LARGURA=p.largura;img.ALTURA=p.altura;\n    if(p.miniatura)img.MINIATURA=p.miniatura;\n    img.NOME=p.nome;img.VERSAO=(Number(img.VERSAO)||0)+1;img.OPERACAO=Number(img.VERSAO_PUBLICADA)>0?'atualizar':'incluir';img.ESTADO_SYNC='pendente';img.ATUALIZADO_EM=agoraIso_();\n    gravarLinha_('IMAGENS',ctx.imagens,img);\n    if(antigo)registrarLimpeza_(antigo,String(imovel.ID),String(img.IMAGEM_ID),'substituicao',agoraIso_());\n    marcarAlteracao_(ctx,imovel,'foto-substituir',usuario);gravarLinha_('IMOVEIS',ctx.imoveis,imovel);\n    return visaoPainel_(ctx,imovel);\n  });\n  solicitarPublicacaoAutomatica_(resultado);return resultado;\n}\n",
  "FormatoImagens331Js.html": "<script>\n/* Imoplace 3.3.1: este complemento deve ser incluído após PainelJs. */\n(function(){\n  'use strict';\n  var apiAnterior331=api;\n  api=function(fn){\n    var args=Array.prototype.slice.call(arguments,1);\n    var route=fn==='enviarImagem'?'enviarImagemFormato331':fn==='substituirImagem'?'substituirImagemFormato331':fn;\n    return apiAnterior331.apply(null,[route].concat(args));\n  };\n  function mostrarFormato331(formato){\n    var label=document.querySelector('#zona-envio .meta');\n    if(label)label.textContent='Formato padrão: '+formato.toUpperCase()+'. A marca d\\u2019água é aplicada antes de salvar. Clique na estrela para escolher a capa.';\n  }\n  converter=async function(arquivo,marca){\n    var formato=await apiAnterior331('obterFormatoPadraoImagens331');\n    mostrarFormato331(formato);\n    var bmp;\n    try{bmp=await createImageBitmap(arquivo);}catch(e){throw new Error(arquivo.name+': o navegador não abriu a imagem. Envie o JPG/PNG original.');}\n    try{\n      if(bmp.width*bmp.height>50000000)throw new Error('Imagem acima de 50 megapixels.');\n      var canvas=document.createElement('canvas');canvas.width=bmp.width;canvas.height=bmp.height;\n      var g=canvas.getContext('2d',{willReadFrequently:true});\n      if(formato==='jpeg'){g.fillStyle='#ffffff';g.fillRect(0,0,canvas.width,canvas.height);}\n      g.drawImage(bmp,0,0);aplicarMarcaDagua(g,canvas.width,canvas.height,marca);\n      var blob;\n      if(formato==='jxl'){\n        var codec=await codecJxl();\n        blob=new Blob([await codec.encodeLossless(g.getImageData(0,0,canvas.width,canvas.height))],{type:'image/jxl'});\n      }else{\n        var mime='image/'+formato;\n        blob=await new Promise(function(ok,fail){\n          canvas.toBlob(function(result){if(!result||result.type!==mime)fail(new Error('Este navegador não gera '+formato+'. Selecione outro formato nas propriedades.'));else ok(result);},mime,0.92);\n        });\n      }\n      var scale=Math.min(1,240/Math.max(bmp.width,bmp.height)),mini=document.createElement('canvas');\n      mini.width=Math.max(1,Math.round(bmp.width*scale));mini.height=Math.max(1,Math.round(bmp.height*scale));mini.getContext('2d').drawImage(canvas,0,0,mini.width,mini.height);\n      var base64=await new Promise(function(ok,fail){var reader=new FileReader();reader.onload=function(){ok(String(reader.result).split(',')[1]);};reader.onerror=fail;reader.readAsDataURL(blob);});\n      return {nome:arquivo.name.replace(/\\.[^.]+$/,''),base64:base64,formato:formato,miniatura:mini.toDataURL('image/webp',0.65),largura:canvas.width,altura:canvas.height};\n    }finally{if(bmp.close)bmp.close();}\n  };\n  apiAnterior331('obterFormatoPadraoImagens331').then(mostrarFormato331).catch(function(e){if(typeof erro==='function')erro(e);});\n})();\n</script>\n"
};
function prepararAtualizacao331(arquivos) {
  const out={...arquivos};
  for(const nome of ['Painel.html','ConfigOperacional.gs','Instalador.gs','Codigo.gs','Imoveis.gs'])if(typeof out[nome]!=='string')throw new Error('Arquivo necessário ausente: '+nome);
  const include="<?!= incluir_('FormatoImagens331Js') ?>";
  if(!out['Painel.html'].includes(include)){
    if(!out['Painel.html'].includes('</body>'))throw new Error('Painel não reconhecido: nenhuma alteração aplicada.');
    out['Painel.html']=out['Painel.html'].replace('</body>',include+'\n</body>');
  }
  const old="var dados = { SITE_URL: CONFIG.siteUrl, LOTE_MAXIMO: String(limite) };";
  if(!out['ConfigOperacional.gs'].includes('FORMATO_PADRAO_IMAGENS')){
    if(!out['ConfigOperacional.gs'].includes(old))throw new Error('ConfigOperacional não corresponde ao CORE 3.3.0: nenhuma alteração aplicada.');
    out['ConfigOperacional.gs']=out['ConfigOperacional.gs'].replace(old,"var dados = { SITE_URL: CONFIG.siteUrl, LOTE_MAXIMO: String(limite), FORMATO_PADRAO_IMAGENS: normalizarFormatoImagem331_(propriedade_('FORMATO_PADRAO_IMAGENS','webp')) };");
  }
  if(!out['Instalador.gs'].includes('instalarFormatoImagens331();')){
    const marker='  sincronizarConfiguracaoOperacional_();';
    if(!out['Instalador.gs'].includes(marker))throw new Error('Instalador não reconhecido: nenhuma alteração aplicada.');
    out['Instalador.gs']=out['Instalador.gs'].replace(marker,marker+'\n  instalarFormatoImagens331();');
  }
  const cloneOld="f.FORMATO === 'jxl' ? 'jxl' : 'webp'";
  if(!out['Imoveis.gs'].includes("normalizarFormatoImagem331_(f.FORMATO")){
    if(!out['Imoveis.gs'].includes(cloneOld))throw new Error('Rotina de clonagem não reconhecida: nenhuma alteração aplicada.');
    out['Imoveis.gs']=out['Imoveis.gs'].replace(cloneOld,"normalizarFormatoImagem331_(f.FORMATO || 'webp')");
  }
  out['Codigo.gs']=out['Codigo.gs'].replace(/ImoplaceCore\.3\.3\.0/g,'ImoplaceCore.3.3.1');
  return out;
}
export {prepararAtualizacao331};
function aplicar(diretorio) {
  const root=path.resolve(diretorio);
  const nomes=['Painel.html','ConfigOperacional.gs','Instalador.gs','Codigo.gs','Imoveis.gs'];
  const originals=Object.fromEntries(nomes.map(nome=>[nome,fs.readFileSync(path.join(root,nome),'utf8')]));
  // Prepara tudo antes de escrever: uma versão inesperada não gera atualização parcial.
  const updated={...prepararAtualizacao331(originals),...PAYLOAD};
  const stamp=new Date().toISOString().replace(/[:.]/g,'-');
  const backup=path.join(path.dirname(root),path.basename(root)+'.backup-3.3.1-'+stamp);
  fs.mkdirSync(backup,{recursive:true});
  for(const [nome,content]of Object.entries(updated)){
    const target=path.join(root,nome);
    if(fs.existsSync(target))fs.copyFileSync(target,path.join(backup,nome));
    fs.writeFileSync(target,content,'utf8');
  }
  console.log('CORE local preparado para 3.3.1. Backup: '+backup);
  console.log('Envie os arquivos ao Apps Script, execute instalar() e atualize a implantação.');
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  if(!process.argv[2])throw new Error('Informe a pasta CORE existente: node aplicar-core-3.3.1.mjs /caminho/CORE');
  aplicar(process.argv[2]);
}
