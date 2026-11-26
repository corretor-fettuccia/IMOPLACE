'use strict';
/* 4.4.0: exclusão definitiva (Drive + planilha), saída do vendido após 90 dias e campos novos no feed do CORE. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const dir=path.join(path.resolve(__dirname,'../../..'),'CORE');
const ler=n=>fs.readFileSync(path.join(dir,n),'utf8');
function contexto(imoveis,opcoes={}){
  const apagadas={},drive=[],logs=[],marcadas=[];
  const ctx={imoveis:{linhas:imoveis},imagens:{linhas:opcoes.imagens||[]},fila:{linhas:opcoes.fila||[]}};
  const c={console,Date,JSON,Math,encodeURIComponent,
    exigirAdmin_:()=>'admin@x',comTrava_:fn=>fn(),carregar_:()=>ctx,
    acharImovel_:(cx,id)=>{const r=cx.imoveis.linhas.find(l=>String(l.ID)===String(id));if(!r)throw Error('nao achou');return r;},
    noSite_:im=>String(im.NO_SITE).toUpperCase()==='SIM',textoCelula_:v=>String(v??'').trim(),agoraIso_:()=>'2026-11-26T12:00:00.000Z',
    lerAba_:n=>({linhas:n==='LIMPEZA'?(opcoes.limpeza||[]):[]}),gravarLinha_:()=>{},registrarLog_:(...a)=>logs.push(a),
    apagarLinhas_:(n,l)=>{apagadas[n]=(apagadas[n]||[]).concat(l);},
    marcarAlteracao_:(cx,im,motivo)=>{marcadas.push([im.ID,motivo]);im.ESTADO_SYNC='pendente';},
    visaoPainel_:(cx,im)=>({ID:im.ID,STATUS:im.STATUS,ESTADO_SYNC:im.ESTADO_SYNC}),solicitarPublicacaoAutomatica_:()=>{},
    ScriptApp:{getOAuthToken:()=>'tok'},
    UrlFetchApp:{fetch:(url,o)=>{drive.push([url,o.method]);const falha=opcoes.falhar&&url.includes(opcoes.falhar);
      return {getResponseCode:()=>falha?403:(url.includes('sumiu')?404:204),getContentText:()=>falha?'proibido':''};}}};
  vm.createContext(c);vm.runInContext(ler('Esquema.gs')+'\n'+ler('Exclusao.gs'),c);
  return {c,apagadas,drive,logs,marcadas,ctx};
}
// Confirmação errada não apaga nada.
let t=contexto([{ID:'1001',STATUS:'arquivado',NO_SITE:'NAO',_linha:2}]);
assert.throws(()=>t.c.excluirImovelDefinitivo('1001','1002',''),/digite exatamente o código/);
assert.equal(t.drive.length,0);
// Fora do site: apaga fotos, pasta e linhas na hora (sem lixeira: DELETE na API do Drive).
t=contexto([{ID:'1001',STATUS:'baixado',NO_SITE:'NAO',DRIVE_PASTA_ID:'pasta1',_linha:5}],
  {imagens:[{IMOVEL_ID:'1001',DRIVE_FILE_ID:'f1',BYTES:1048576,_linha:3},{IMOVEL_ID:'1001',DRIVE_FILE_ID:'sumiu',BYTES:0,_linha:4},{IMOVEL_ID:'9',DRIVE_FILE_ID:'outro',_linha:9}],
   fila:[{IMOVEL_ID:'1001',_linha:7}],limpeza:[{IMOVEL_ID:'1001',DRIVE_FILE_ID:'antigo',ESTADO:'aguardando',_linha:2}]});
let r=t.c.excluirImovelDefinitivo('1001','1001','');
assert.equal(r.pendente,false);assert.equal(r.resumo.fotos,2);assert.equal(r.resumo.arquivos,3);
assert.deepEqual(t.drive.map(d=>d[1]),['delete','delete','delete','delete']);
assert(t.drive.some(d=>d[0].includes('/files/pasta1?')));assert(!t.drive.some(d=>d[0].includes('outro')));
assert.deepEqual(t.apagadas,{IMAGENS:[3,4],LIMPEZA:[2],FILA:[7],IMOVEIS:[5]});
// Falha no Drive: nenhuma linha some (dá para tentar de novo).
t=contexto([{ID:'1001',STATUS:'baixado',NO_SITE:'NAO',_linha:5}],{imagens:[{IMOVEL_ID:'1001',DRIVE_FILE_ID:'f1',_linha:3}],falhar:'f1'});
assert.throws(()=>t.c.excluirImovelDefinitivo('1001','1001',''),/Nada foi apagado da planilha/);
assert.deepEqual(t.apagadas,{});
// No site: primeiro sai do site; a exclusão fica agendada até a confirmação.
const pub={ID:'1001',STATUS:'publicado',NO_SITE:'SIM',_linha:5};
t=contexto([pub]);r=t.c.excluirImovelDefinitivo('1001','1001','');
assert.equal(r.pendente,true);assert.equal(pub.STATUS,'arquivado');assert.equal(pub.EXCLUIR_PENDENTE,'SIM');
assert.deepEqual(t.marcadas,[['1001','despublicar']]);assert.equal(t.drive.length,0);
// Confirmação do site chegou (NO_SITE=NAO, sem fila): a reconciliação apaga.
pub.NO_SITE='NAO';assert.equal(t.c.processarExclusoesPendentes_(),1);assert.deepEqual(t.apagadas.IMOVEIS,[5]);
// Ainda com fila pendente: espera.
const pend={ID:'1002',STATUS:'arquivado',NO_SITE:'NAO',EXCLUIR_PENDENTE:'SIM',_linha:6};
t=contexto([pend],{fila:[{IMOVEL_ID:'1002',_linha:2}]});assert.equal(t.c.processarExclusoesPendentes_(),0);assert.deepEqual(t.apagadas,{});
// Vendido há mais de 90 dias sai do site; com 89 dias, fica.
const velho={ID:'1',STATUS:'publicado',DISPONIBILIDADE:'sold',VENDIDO_EM:new Date(Date.now()-91*864e5).toISOString()};
const novo={ID:'2',STATUS:'publicado',DISPONIBILIDADE:'sold',VENDIDO_EM:new Date(Date.now()-89*864e5).toISOString()};
const disp={ID:'3',STATUS:'publicado',DISPONIBILIDADE:'in_stock',VENDIDO_EM:''};
t=contexto([velho,novo,disp]);
assert.deepEqual(Array.from(t.c.retirarVendidosAntigos_()),['1']);assert.equal(velho.STATUS,'baixado');assert.equal(novo.STATUS,'publicado');
// Esquema: valores novos e campos públicos.
assert(t.c.ESQUEMA.disponibilidades.includes('sold'));assert.equal(t.c.ESQUEMA.diasVendidoNoSite,90);
['TARJA','TARJA_TEXTO','PRECO_ANTERIOR','VENDIDO_EM','EXCLUIR_PENDENTE'].forEach(c=>assert(t.c.ESQUEMA.abas.IMOVEIS.includes(c),c));
['TARJA','TARJA_TEXTO','PRECO_ANTERIOR'].forEach(c=>assert(t.c.ESQUEMA.editaveis.includes(c),c));
assert(!t.c.ESQUEMA.editaveis.includes('VENDIDO_EM'));
assert.equal(t.c.disponibilidade_({DISPONIBILIDADE:'xx'}),'in_stock');
// Salvar grava/zera a data do vendido; Resultados chama a exclusão pendente; painel tem o botão.
const imov=ler('Imoveis.gs');assert(imov.includes("if (disponibilidade_(imovel) === 'sold') { if (dispAntes !== 'sold'"));
assert(ler('Resultados.gs').includes('processarExclusoesPendentes_()'));
assert(ler('Sincronizar.gs').includes('retirarVendidosAntigos_()'));
assert(ler('Painel.html').includes('id="btn-excluir"'));
assert(ler('PainelJs.html').includes("api('excluirImovelDefinitivo'"));
console.log('CORE 4.4.0: exclusão definitiva, vendidos 90 dias e esquema aprovados.');
