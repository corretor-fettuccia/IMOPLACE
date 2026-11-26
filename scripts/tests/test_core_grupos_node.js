'use strict';
/* 4.5.0: grupos de imóveis (sem limite por imóvel) no CORE — cadastro, vínculo e campos públicos. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const dir=path.join(path.resolve(__dirname,'../../..'),'CORE');
const ler=n=>fs.readFileSync(path.join(dir,n),'utf8');
function contexto(grupos,imoveis){
  const logs=[],marcadas=[],gravadas=[],apagadas=[],disparos=[];
  const ctx={imoveis:{linhas:imoveis},imagens:{linhas:[]},fila:{linhas:[]}};
  const c={console,Date,JSON,Math,String,
    exigirAdmin_:()=>'admin@x',comTrava_:fn=>fn(),carregar_:()=>ctx,
    noSite_:im=>String(im.NO_SITE).toUpperCase()==='SIM',agoraIso_:()=>'2026-11-26T12:00:00.000Z',
    lerAba_:n=>n==='GRUPOS'?{cabecalho:[],linhas:grupos}:{linhas:imoveis},
    anexarLinha_:(n,d,o)=>{o._linha=d.linhas.length+2;d.linhas.push(o);return o;},
    gravarLinha_:(n,d,o)=>gravadas.push([n,o.ID]),apagarLinhas_:(n,l)=>apagadas.push([n,l]),
    registrarLog_:(...a)=>logs.push(a),
    marcarAlteracao_:(cx,im,motivo)=>{marcadas.push([im.ID,motivo]);im.ESTADO_SYNC='pendente';},
    solicitarPublicacaoAutomatica_:r=>disparos.push(r)};
  vm.createContext(c);vm.runInContext(ler('Esquema.gs')+'\n'+ler('Midias.gs')+'\n'+ler('Grupos.gs'),c);
  return {c,logs,marcadas,gravadas,apagadas,disparos};
}
// Esquema: aba nova, colunas no fim de IMOVEIS, editáveis e saída pública.
let t=contexto([],[]);const E=t.c.ESQUEMA;
assert.deepEqual(Array.from(E.abas.GRUPOS),['ID','NOME','TIPO','TITULO_SECAO','CRIADO_EM','ATUALIZADO_EM']);
assert.deepEqual(Array.from(E.abas.IMOVEIS.slice(-2)),['GRUPOS_IDS','UNIDADE_NOME']);
['GRUPOS_IDS','UNIDADE_NOME'].forEach(c=>{assert(E.editaveis.includes(c),c);assert(E.texto.IMOVEIS.includes(c),c);});
const pub=t.c.serializarPublico_({ID:'7',CATEGORIA:'venda',TITULO:'Lote',GRUPOS_IDS:'G2, G5;G2 ,',UNIDADE_NOME:'Lote 12'},[],'');
assert.deepEqual(Array.from(pub.grupoIds),['G2','G5']);
assert(E.tiposGrupo.includes('Cidade')&&E.tiposGrupo.includes('Condomínio fechado'));assert.equal(pub.unidade,'Lote 12');
// Cadastro: ID sequencial G1, G2…; nome obrigatório; tipo fora da lista vira Loteamento; nome repetido recusado.
const grupos=[];t=contexto(grupos,[]);
let g=t.c.salvarGrupo('',{NOME:'Reserva das Palmeiras',TIPO:'xx'});
assert.equal(g.ID,'G1');assert.equal(g.TIPO,'Condomínio');
assert.equal(t.c.salvarGrupo('',{NOME:'Edifício Monet',TIPO:'Condomínio'}).ID,'G2');
assert.throws(()=>t.c.salvarGrupo('',{NOME:'  '}),/Informe o nome/);
assert.throws(()=>t.c.salvarGrupo('',{NOME:'reserva das palmeíras'}),/Já existe/);
assert.equal(t.c.proximoIdGrupo_([{ID:'G9'},{ID:'G3'}]),'G10');
// Editar nome: só os imóveis do grupo que estão no site entram na fila, e a publicação é disparada.
const imoveis=[{ID:'1',GRUPOS_IDS:'G2, G1',STATUS:'publicado',NO_SITE:'SIM',_linha:2},{ID:'2',GRUPOS_IDS:'G1',STATUS:'rascunho',NO_SITE:'NAO',_linha:3},
  {ID:'3',GRUPOS_IDS:'G2',STATUS:'publicado',NO_SITE:'SIM',_linha:4}];
t=contexto(grupos,imoveis);
let r=t.c.salvarGrupo('G1',{NOME:'Reserva das Palmeiras II',TIPO:'Loteamento'});
assert.equal(r.FILA,1);assert.deepEqual(t.marcadas,[['1','grupo']]);assert.equal(t.disparos.length,1);
r=t.c.salvarGrupo('G1',{NOME:'Reserva das Palmeiras II',TIPO:'Loteamento'});   // nada mudou
assert.equal(r.FILA,0);assert.equal(t.marcadas.length,1);
// Lista para o formulário (ordem alfabética) e para a tela de grupos (contagens).
assert.deepEqual(t.c.gruposParaFormulario_().map(x=>x.ID),['G2','G1']);
const lista=t.c.listarGrupos();const g1=lista.find(x=>x.ID==='G1');
assert.equal(g1.IMOVEIS,2);assert.equal(g1.NO_SITE,1);assert.equal(lista.find(x=>x.ID==='G2').IMOVEIS,2);   // imóvel 1 está nos dois
assert(t.c.grupoExiste_('G2'));assert(!t.c.grupoExiste_('G7'));
// Excluir: recusa com imóveis vinculados; grupo vazio sai da planilha.
assert.throws(()=>t.c.excluirGrupo('G1'),/ainda tem 2 imóvel/);
grupos.push({ID:'G3',NOME:'Vazio',_linha:9});
assert.equal(t.c.excluirGrupo('G3').ok,true);assert.deepEqual(t.apagadas,[['GRUPOS',[9]]]);
// Salvar imóvel recusa grupo inexistente; clonar mantém o grupo e limpa o nome da unidade.
const imov=ler('Imoveis.gs');
assert(imov.includes("idsGrupos_(novo.GRUPOS_IDS).forEach(function (g) { if (!grupoExiste_(g))"));
assert(imov.includes("if (c === 'GRUPOS_IDS') { saida[c] = idsGrupos_(v).join(', '); return; }"));
assert(imov.includes("clone.UNIDADE_NOME = '';"));
assert(imov.includes('grupos: gruposParaFormulario_()'));
// Aba GRUPOS criada sozinha (sem instalar).
const planilha=ler('Planilha.gs');
assert(planilha.includes("if (!sh && nome === 'GRUPOS')"));
assert(planilha.includes("(nome === 'IMOVEIS' || nome === 'GRUPOS')"));
// Painel: seletor de grupo no imóvel e tela "Grupos".
const pj=ler('PainelJs.html');
assert(pj.includes("['GRUPOS_IDS','Grupos (marque quantos quiser)','grupos',{largo:1}]"));
assert(pj.includes("else if (tipo === 'grupos') dados[chave]"));
assert(pj.includes("api('salvarGrupo'")&&pj.includes("api('excluirGrupo'")&&pj.includes("api('listarGrupos')"));
assert(ler('Painel.html').includes('id="btn-grupos"'));
// Mídias e links externos no painel: lista recolhível (uma linha por item; formulário abre ao clicar).
assert(pj.includes('<div class="campo largo midia-colecao" data-colecao="${chave}">'));
assert(pj.includes('<details class="midia-linha"')&&pj.includes('function atualizarResumoMidia(row)'));
['function colecaoHTML(','function lerColecao(','extrairIframePainel(e.target.value)',"querySelector('[data-campo-capa]')"].forEach(x=>assert(pj.includes(x),x));
assert(ler('PainelCss.html').includes('.ml-lista{counter-reset:ml;'));
console.log('CORE 4.5.0: grupos de imóveis e lista de mídias aprovados.');
