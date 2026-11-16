/**
 * Imoplace CORE 3.3.1 — formato configurável. Complemento do CORE 3.3.0.
 * Propriedade: FORMATO_PADRAO_IMAGENS = webp | jpeg | png | jxl.
 */
function normalizarFormatoImagem331_(valor) {
  var formato=String(valor||'webp').trim().toLowerCase();
  if(formato==='jpg')formato='jpeg';
  if(['webp','jpeg','png','jxl'].indexOf(formato)<0)throw new Error('FORMATO_PADRAO_IMAGENS deve ser webp, jpeg, png ou jxl.');
  return formato;
}
function instalarFormatoImagens331() {
  exigirAdmin_();
  var props=PropertiesService.getScriptProperties();
  if(!props.getProperty('FORMATO_PADRAO_IMAGENS'))props.setProperty('FORMATO_PADRAO_IMAGENS','webp');
  var formato=normalizarFormatoImagem331_(props.getProperty('FORMATO_PADRAO_IMAGENS'));
  props.setProperty('FORMATO_PADRAO_IMAGENS',formato);
  sincronizarConfiguracaoOperacional_();
  return {ok:true,formato:formato};
}
function obterFormatoPadraoImagens331() {
  exigirAdmin_();
  return instalarFormatoImagens331().formato;
}
function detectarFormatoImagem331_(bytes) {
  var b=bytes.slice(0,12).map(function(x){return x&255;});
  if(b[0]===255&&b[1]===216&&b[2]===255)return 'jpeg';
  if(b.slice(0,8).join(',')==='137,80,78,71,13,10,26,10')return 'png';
  if(b[0]===255&&b[1]===10||b.join(',')==='0,0,0,12,74,88,76,32,13,10,135,10')return 'jxl';
  var sig=String.fromCharCode.apply(null,b.slice(0,4))+String.fromCharCode.apply(null,b.slice(8,12));
  if(sig==='RIFFWEBP')return 'webp';
  throw new Error('Arquivo não reconhecido. Use WebP, JPEG, PNG ou JXL.');
}
function prepararArquivoFormato331_(arquivo,imagemId) {
  if(!arquivo||typeof arquivo.base64!=='string')throw new Error('Arquivo ausente.');
  var bytes=Utilities.base64Decode(arquivo.base64);
  if(bytes.length<16)throw new Error('Arquivo vazio.');
  if(bytes.length>CONFIG.maxFotoBytes)throw new Error('Imagem acima do limite de tamanho configurado.');
  var formato=detectarFormatoImagem331_(bytes);
  if(arquivo.formato&&normalizarFormatoImagem331_(arquivo.formato)!==formato)throw new Error('Conteúdo da imagem diferente do formato informado.');
  var mini=String(arquivo.miniatura||'');
  if(mini&&(!/^data:image\/(webp|jpeg|png);base64,[A-Za-z0-9+/=]+$/.test(mini)||mini.length>40000))mini='';
  return {blob:Utilities.newBlob(bytes,'image/'+formato,imagemId+'.'+formato),formato:formato,bytes:bytes.length,sha256:hexDeBytes_(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,bytes)),miniatura:mini,nome:texto_(arquivo.nome||'foto',80),largura:Math.max(0,Math.round(Number(arquivo.largura)||0)),altura:Math.max(0,Math.round(Number(arquivo.altura)||0))};
}
function enviarImagemFormato331(id,arquivo) {
  var usuario=exigirAdmin_();
  var resultado=comTrava_(function(){
    var ctx=carregar_(),imovel=acharImovel_(ctx,id),ativas=imagensDoImovel_(ctx,id,false);
    if(ativas.length>=CONFIG.maxFotos)throw new Error('Limite de fotos por imóvel atingido.');
    var imagemId=novoIdImagem_(),p=prepararArquivoFormato331_(arquivo,imagemId),pasta=pastaDoImovel_(imovel),file=pasta.createFile(p.blob);
    var ordem=ativas.reduce(function(m,i){return Math.max(m,Number(i.ORDEM)||0);},0)+1;
    anexarLinha_('IMAGENS',ctx.imagens,{IMAGEM_ID:imagemId,IMOVEL_ID:imovel.ID,DRIVE_FILE_ID:file.getId(),NOME:p.nome,LEGENDA:texto_(arquivo.legenda,80),ALT:'',ORDEM:ordem,SHA256:p.sha256,BYTES:p.bytes,LARGURA:p.largura,ALTURA:p.altura,FORMATO:p.formato,MINIATURA:p.miniatura,VERSAO:1,VERSAO_PUBLICADA:0,OPERACAO:'incluir',ESTADO_SYNC:'pendente',ATUALIZADO_EM:agoraIso_()});
    if(!imovel.IMAGEM_CAPA_ID)imovel.IMAGEM_CAPA_ID=imagemId;
    marcarAlteracao_(ctx,imovel,'foto-incluir',usuario);gravarLinha_('IMOVEIS',ctx.imoveis,imovel);
    return visaoPainel_(ctx,imovel);
  });
  solicitarPublicacaoAutomatica_(resultado);return resultado;
}
function substituirImagemFormato331(id,imagemId,arquivo) {
  var usuario=exigirAdmin_();
  var resultado=comTrava_(function(){
    var ctx=carregar_(),imovel=acharImovel_(ctx,id),img=acharImagem_(ctx,id,imagemId);
    if(img.OPERACAO==='excluir')throw new Error('Esta foto está marcada para exclusão.');
    var p=prepararArquivoFormato331_(arquivo,String(img.IMAGEM_ID)),antigo=String(img.DRIVE_FILE_ID||''),file=pastaDoImovel_(imovel).createFile(p.blob);
    img.DRIVE_FILE_ID=file.getId();img.SHA256=p.sha256;img.BYTES=p.bytes;img.FORMATO=p.formato;img.LARGURA=p.largura;img.ALTURA=p.altura;
    if(p.miniatura)img.MINIATURA=p.miniatura;
    img.NOME=p.nome;img.VERSAO=(Number(img.VERSAO)||0)+1;img.OPERACAO=Number(img.VERSAO_PUBLICADA)>0?'atualizar':'incluir';img.ESTADO_SYNC='pendente';img.ATUALIZADO_EM=agoraIso_();
    gravarLinha_('IMAGENS',ctx.imagens,img);
    if(antigo)registrarLimpeza_(antigo,String(imovel.ID),String(img.IMAGEM_ID),'substituicao',agoraIso_());
    marcarAlteracao_(ctx,imovel,'foto-substituir',usuario);gravarLinha_('IMOVEIS',ctx.imoveis,imovel);
    return visaoPainel_(ctx,imovel);
  });
  solicitarPublicacaoAutomatica_(resultado);return resultado;
}
