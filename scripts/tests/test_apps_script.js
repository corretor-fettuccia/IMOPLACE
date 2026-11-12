// Testes do código Apps Script que roda fora do Google (regras puras + sintaxe de todos os arquivos).
// Rodar: node scripts/tests/test_apps_script.js
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const os = require('os');
const vm = require('vm');
const { RAIZ, carregarComum } = require('./apoio');

let ok = 0;
function teste(nome, fn) { fn(); ok++; console.log('ok -', nome); }

const c = carregarComum();

teste('slug sem acento, minúsculo e limitado', () => {
  assert.strictEqual(c.slugify_('Casa com 3 Dormitórios em São José!'), 'casa-com-3-dormitorios-em-sao-jose');
  assert.strictEqual(c.slugify_(''), 'imovel');
  assert.ok(c.slugify_('a'.repeat(200)).length <= 60);
});

teste('código e caminho públicos usam o ID fixo', () => {
  const im = { ID: '1001', TITULO: 'Apto Centro', CATEGORIA: 'venda', SLUG: '' };
  assert.strictEqual(c.codigoImovel_(im), 'apto-centro-1001');
  assert.strictEqual(c.caminhoImovel_(im), 'imoveis/apto-centro-1001/');
});

teste('nome de foto pública é versionado e não colide', () => {
  const n = c.nomeImagemPublica_({ NOME: 'Sala de Estar.JPG', IMAGEM_ID: 'iABCDEF0123' }, 3);
  assert.strictEqual(n, 'sala-de-estar-iabcdef0123.v3.webp');
  assert.match(n, /^[a-z0-9-]+-i[0-9a-f]{10}\.v\d+\.webp$/);
  assert.strictEqual(c.nomeImagemPublica_({ NOME: '', IMAGEM_ID: 'i0000000001' }, 1), 'foto-i0000000001.v1.webp');
});

teste('feed público nunca leva campos privados', () => {
  const linha = {};
  c.ESQUEMA.abas.IMOVEIS.forEach(k => { linha[k] = 'SEGREDO-' + k; });
  Object.assign(linha, { ID: '1001', CATEGORIA: 'venda', TITULO: 'Casa', DISPONIBILIDADE: 'in_stock' });
  const pub = JSON.stringify(c.serializarPublico_(linha, [], 'https://imoplace.com.br'));
  c.ESQUEMA.privados.forEach(k => assert.ok(!pub.includes('SEGREDO-' + k), 'vazou ' + k));
  ['proprietario', 'enderecoInterno', 'obsInterna', 'driveFileId', 'drivePastaId'].forEach(k => assert.ok(!pub.includes('"' + k + '"'), 'chave ' + k));
});

teste('foto destaque vem primeiro no feed', () => {
  const im = { ID: '7', CATEGORIA: 'venda', TITULO: 'X', IMAGEM_CAPA_ID: 'i0000000002' };
  const imgs = [{ IMAGEM_ID: 'i0000000001', ORDEM: 1, versao: 1 }, { IMAGEM_ID: 'i0000000002', ORDEM: 2, versao: 4 }];
  const pub = c.serializarPublico_(im, imgs, '');
  assert.strictEqual(pub.imagemCapaId, 'i0000000002');
  assert.ok(pub.imagens[0].arquivo.endsWith('-i0000000002.v4.webp'));
});

teste('números brasileiros e booleanos da planilha', () => {
  assert.strictEqual(c.numeroOuNulo_('1.234.567,89'), 1234567.89);
  assert.strictEqual(c.numeroOuNulo_('550000'), 550000);
  assert.strictEqual(c.numeroOuNulo_(''), null);
  assert.strictEqual(c.booleano_('SIM'), true);
  assert.strictEqual(c.booleano_('NAO'), false);
  assert.strictEqual(JSON.stringify(c.lista_('Piscina, piscina; Churrasqueira')), JSON.stringify(['Piscina', 'Churrasqueira']));
});

teste('publicar exige título, categoria, tipo, cidade e foto', () => {
  const erros = c.validarParaPublicar_({ TITULO: '', CATEGORIA: 'x', TIPO: '' }, []);
  assert.ok(erros.length >= 4);
  assert.strictEqual(c.validarParaPublicar_({ TITULO: 'Casa', CATEGORIA: 'venda', TIPO: 'Casa', CIDADE: 'Canoas', UF: 'RS' }, [{}]).length, 0);
});

teste('hex de bytes assinados e comparação segura', () => {
  assert.strictEqual(c.hexDeBytes_([-1, 0, 15, 127, -128]), 'ff000f7f80');
  assert.ok(c.iguaisSeguro_('abcd', 'abcd'));
  assert.ok(!c.iguaisSeguro_('abcd', 'abce'));
  assert.ok(!c.iguaisSeguro_('', ''));
});

teste('arquivos comuns idênticos nos três projetos', () => {
  for (const arq of fs.readdirSync(path.join(RAIZ, 'COMUM'))) {
    const base = fs.readFileSync(path.join(RAIZ, 'COMUM', arq), 'utf8');
    for (const p of ['imoplace-API-PainelPrivado', 'imoplace-API-Publica', 'imoplace-API-IntegracaoActions']) {
      assert.strictEqual(fs.readFileSync(path.join(RAIZ, p, arq), 'utf8'), base, `${p}/${arq} desatualizado: rode scripts/copiar_comum.py`);
    }
  }
});

teste('sintaxe de todos os .gs e scripts do painel', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gs-'));
  const verificar = (nome, codigo) => {
    const f = path.join(tmp, nome.replace(/[\\/]/g, '_') + '.js');
    fs.writeFileSync(f, codigo);
    execFileSync(process.execPath, ['--check', f], { stdio: 'pipe' });
  };
  for (const p of ['imoplace-API-PainelPrivado', 'imoplace-API-Publica', 'imoplace-API-IntegracaoActions']) {
    let tudo = '';
    for (const arq of fs.readdirSync(path.join(RAIZ, p))) {
      const txt = fs.readFileSync(path.join(RAIZ, p, arq), 'utf8');
      if (arq.endsWith('.gs')) { verificar(p + '/' + arq, txt); tudo += txt + '\n'; }
      if (arq.endsWith('.html')) {
        const m = txt.match(/<script>([\s\S]*?)<\/script>/);
        if (m) verificar(p + '/' + arq, m[1]);
      }
      if (arq === 'appsscript.json') JSON.parse(txt);
    }
    verificar(p + '_concatenado', tudo); // Apps Script junta todos os arquivos num escopo só
  }
});

teste('API pública não tem nenhuma função de escrita', () => {
  const feed = fs.readFileSync(path.join(RAIZ, 'imoplace-API-Publica', 'Feed.gs'), 'utf8');
  ['gravarLinha_(', 'anexarLinha_(', 'apagarLinhas_(', 'setValues', 'doPost', 'DriveApp'].forEach(t => assert.ok(!feed.includes(t), t));
  const escopo = JSON.parse(fs.readFileSync(path.join(RAIZ, 'imoplace-API-Publica', 'appsscript.json'), 'utf8')).oauthScopes;
  assert.deepStrictEqual(escopo, ['https://www.googleapis.com/auth/spreadsheets']);
  assert.ok(feed.includes('VERSAO_PUBLICADA'), 'o feed só deve listar imagens já confirmadas no site');
});

teste('painel exige administrador em toda função exposta', () => {
  for (const arq of ['Imoveis.gs', 'Imagens.gs', 'Sincronizar.gs', 'Codigo.gs']) {
    const txt = fs.readFileSync(path.join(RAIZ, 'imoplace-API-PainelPrivado', arq), 'utf8');
    const funcoes = [...txt.matchAll(/^function ([A-Za-z]\w*[^_\W])\s*\(/gm)].map(m => m[1]).filter(n => n !== 'reservaDiaria');
    for (const f of funcoes) {
      const corpo = txt.slice(txt.indexOf('function ' + f + '('));
      const primeira = corpo.slice(0, corpo.indexOf('\n}'));
      assert.ok(primeira.includes('exigirAdmin_()'), `${arq}:${f} sem exigirAdmin_`);
    }
  }
});


teste('ACK atrasado não confirma nem apaga fila atualizada pelo operador', () => {
  const rows = {
    IMOVEIS: [{_linha:2, ID:'1001',VERSAO:8,VERSAO_PUBLICADA:6,ESTADO_SYNC:'pendente'}],
    IMAGENS: [{_linha:2,IMOVEL_ID:'1001',IMAGEM_ID:'img1',VERSAO:2,VERSAO_PUBLICADA:1,DRIVE_FILE_ID:'novo'}],
    FILA: [{_linha:2,IMOVEL_ID:'1001',VERSAO:8,ESTADO:'pendente',JOB_ID:'gh-novo'}],
    EXECUCOES:[{_linha:2,JOB_ID:'gh-antigo',RESULTADO:'em_andamento',IMOVEIS:'1001'}]
  };
  const ctx=vm.createContext({console,
    comTrava_:f=>f(),
    lerAba_:key=>({cabecalho:[],linhas:rows[key]}),
    gravarLinha_:(key,tab,val)=>Object.assign(rows[key].find(x=>x._linha===val._linha),val),
    gravarLinhas_:(key,tab,l)=>l.forEach(o=>Object.assign(rows[key].find(x=>x._linha===o._linha),o)),
    apagarLinhas_:(key,ids)=>{rows[key]=rows[key].filter(x=>!ids.includes(x._linha));},
    agoraIso_:()=>new Date().toISOString(), registrarLog_:()=>{},
    registrarLimpeza_:()=>{}, DriveApp:{getFileById:()=>({setTrashed:()=>{throw Error('Lixeira inesperada');}})}
  });
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'imoplace-API-PainelPrivado','Integracao.gs'),'utf8'),ctx);
  const ack={imoveis:[{imovelId:'1001',versao:7,noSite:true}],imagens:[{imagemId:'img1',versao:1}]};
  const result=ctx.confirmar_('gh-antigo',ack);
  assert.strictEqual(result.confirmados.length,0);
  assert.strictEqual(rows.IMOVEIS[0].VERSAO_PUBLICADA,6);
  assert.strictEqual(rows.IMAGENS[0].VERSAO_PUBLICADA,1);
  assert.strictEqual(rows.FILA.length,1);
  assert.strictEqual(rows.FILA[0].JOB_ID,'gh-novo');
});

teste('integração C não escreve na planilha nem solicita escopos de Drive', () => {
  const codigo=fs.readFileSync(path.join(RAIZ,'imoplace-API-IntegracaoActions','Integracao.gs'),'utf8');
  const scopes=JSON.parse(fs.readFileSync(path.join(RAIZ,'imoplace-API-IntegracaoActions','appsscript.json'),'utf8')).oauthScopes;
  assert.deepStrictEqual(scopes,['https://www.googleapis.com/auth/script.external_request']);
  ['SpreadsheetApp','DriveApp','gravarLinha_','comTrava_'].forEach(t=>assert.ok(!codigo.includes(t),t));
});

teste('ponte C aceita CENTRAL_WRITER_URL com espaço colado e explica resposta HTML', () => {
  const codigo=fs.readFileSync(path.join(RAIZ,'imoplace-API-IntegracaoActions','Integracao.gs'),'utf8');
  const exec='https://script.google.com/macros/s/AKfy_abc-123/exec';
  const rodar=(prop,resposta)=>{
    const enviados=[];
    const sb={
      PropertiesService:{getScriptProperties:()=>({getProperty:()=>prop})},
      UrlFetchApp:{fetch:(u,o)=>{enviados.push(u);return {getResponseCode:()=>200,getContentText:()=>resposta};}},
      ContentService:{MimeType:{JSON:'json'},createTextOutput:t=>({setMimeType:()=>JSON.parse(t)})},
      console
    };
    vm.createContext(sb); vm.runInContext(codigo,sb);
    return {saida:sb.doPost({postData:{contents:'{"acao":"x"}'}}),enviados,diag:()=>sb.verificarConfiguracaoIntegracao()};
  };
  const r=rodar(exec+' \n','{"ok":true}');
  assert.deepStrictEqual(r.saida,{ok:true});
  assert.deepStrictEqual(r.enviados,[exec]);
  assert.strictEqual(r.diag(),true);
  const vazio=rodar('','{}');
  assert.match(vazio.saida.erro,/CENTRAL_WRITER_URL ausente/);
  assert.throws(vazio.diag);
  assert.match(rodar(exec,'<html>login</html>').saida.erro,/qualquer pessoa/);
});


teste('ACK do job correto confirma versão exata e encerra fila', () => {
  const rows={
    IMOVEIS:[{_linha:2,ID:'1001',VERSAO:4,VERSAO_PUBLICADA:3,NO_SITE:'SIM'}],
    IMAGENS:[{_linha:2,IMOVEL_ID:'1001',IMAGEM_ID:'img1',VERSAO:2,VERSAO_PUBLICADA:1,OPERACAO:'atualizar',DRIVE_FILE_ID:'novo'}],
    FILA:[{_linha:2,IMOVEL_ID:'1001',VERSAO:4,ESTADO:'em_processamento',JOB_ID:'gh-123'}],
    EXECUCOES:[{_linha:2,JOB_ID:'gh-123',RESULTADO:'em_andamento'}]
  };
  const ctx=vm.createContext({console,comTrava_:f=>f(),
    lerAba_:k=>({cabecalho:[],linhas:rows[k]}),
    gravarLinha_:(k,tab,obj)=>Object.assign(rows[k].find(x=>x._linha===obj._linha),obj),
    gravarLinhas_:(k,tab,l)=>l.forEach(o=>Object.assign(rows[k].find(x=>x._linha===o._linha),o)),
    apagarLinhas_:(k,ids)=>{rows[k]=rows[k].filter(x=>!ids.includes(x._linha));},
    agoraIso_:()=>new Date().toISOString(),registrarLog_:()=>{},registrarLimpeza_:()=>{throw Error('Não deveria limpar')}
  });
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'imoplace-API-PainelPrivado','Integracao.gs'),'utf8'),ctx);
  const out=ctx.confirmar_('gh-123',{imoveis:[{imovelId:'1001',versao:4,noSite:true}],imagens:[{imagemId:'img1',versao:2}]});
  assert.strictEqual(out.confirmados.join(','),'1001v4');
  assert.strictEqual(rows.IMOVEIS[0].VERSAO_PUBLICADA,4);
  assert.strictEqual(rows.IMAGENS[0].VERSAO_PUBLICADA,2);
  assert.strictEqual(rows.FILA.length,0);
  assert.strictEqual(rows.EXECUCOES[0].RESULTADO,'ok');
  assert.strictEqual(ctx.confirmar_('gh-123',{imoveis:[],imagens:[]}).idempotente,true);
});

teste('falha tardia não retoma nem marca com erro trabalho de novo job', () => {
  const rows={
    IMOVEIS:[{_linha:2,ID:'1001',ESTADO_SYNC:'em_processamento'}],
    IMAGENS:[],FILA:[{_linha:2,IMOVEL_ID:'1001',JOB_ID:'gh-200',ESTADO:'em_processamento'}],
    EXECUCOES:[{_linha:2,JOB_ID:'gh-100',RESULTADO:'em_andamento'}]
  };
  const ctx=vm.createContext({console,comTrava_:f=>f(),
    lerAba_:k=>({cabecalho:[],linhas:rows[k]}),
    gravarLinha_:(k,tab,obj)=>Object.assign(rows[k].find(x=>x._linha===obj._linha),obj),
    gravarLinhas_:(k,tab,l)=>l.forEach(o=>Object.assign(rows[k].find(x=>x._linha===o._linha),o)),
    agoraIso_:()=>new Date().toISOString(),registrarLog_:()=>{}
  });
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'imoplace-API-PainelPrivado','Integracao.gs'),'utf8'),ctx);
  const out=ctx.falha_('gh-100',{erro:'falha antiga',imoveis:[{imovelId:'1001',erro:'antigo'}]});
  assert.strictEqual(out.afetados.length,0);
  assert.strictEqual(rows.FILA[0].ESTADO,'em_processamento');
  assert.strictEqual(rows.IMOVEIS[0].ESTADO_SYNC,'em_processamento');
});

teste('limpeza respeita carência de 48h, pendências e versão publicada', () => {
  const ago = (hours) => new Date(Date.now()-hours*3600000).toISOString();
  const lim={_linha:2,DRIVE_FILE_ID:'antigo',IMOVEL_ID:'1001',IMAGEM_ID:'img1',MOTIVO:'substituicao',SOLICITADO_EM:ago(60),ESTADO:'aguardando'};
  const rows={LIMPEZA:[lim],IMAGENS:[{_linha:2,IMOVEL_ID:'1001',IMAGEM_ID:'img1',DRIVE_FILE_ID:'novo',VERSAO:2,VERSAO_PUBLICADA:2}],FILA:[{IMOVEL_ID:'1001',ESTADO:'pendente'}],IMOVEIS:[]};
  let descartes=0;
  const ctx=vm.createContext({console,comTrava_:f=>f(),
    lerAba_:key=>({cabecalho:[],linhas:rows[key]}),
    gravarLinha_:(key,tab,obj)=>Object.assign(rows[key].find(x=>x._linha===obj._linha),obj),
    gravarLinhas_:(key,tab,l)=>l.forEach(o=>Object.assign(rows[key].find(x=>x._linha===o._linha),o)),
    agoraIso_:()=>new Date().toISOString(),textoCelula_:x=>String(x),
    DriveApp:{getFileById:()=>({setTrashed:()=>{descartes++;}})}
  });
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'imoplace-API-PainelPrivado','Limpeza.gs'),'utf8'),ctx);
  assert.strictEqual(ctx.limparArquivosAntigos().descartados,0); // pendência
  rows.FILA=[];
  lim.SOLICITADO_EM=ago(2);
  assert.strictEqual(ctx.limparArquivosAntigos().descartados,0); // carência
  lim.SOLICITADO_EM=ago(60);
  rows.IMAGENS[0].VERSAO_PUBLICADA=1;
  assert.strictEqual(ctx.limparArquivosAntigos().descartados,0); // versão não confirmada
  rows.IMAGENS[0].VERSAO_PUBLICADA=2;
  assert.strictEqual(ctx.limparArquivosAntigos().descartados,1);
  assert.strictEqual(descartes,1);
  assert.strictEqual(lim.ESTADO,'descartado');
});

// ---------- v2.3.2.13 ----------
function escritor(rows, extra) {
  if (!rows.RECONSTRUCOES) rows.RECONSTRUCOES = [];
  const ctx=vm.createContext(Object.assign({console,comTrava_:f=>f(),
    lerAba_:k=>({cabecalho:[],linhas:rows[k]}),
    gravarLinha_:(k,t,o)=>Object.assign(rows[k].find(x=>x._linha===o._linha),o),
    gravarLinhas_:(k,t,l)=>l.forEach(o=>Object.assign(rows[k].find(x=>x._linha===o._linha),o)),
    anexarLinha_:(k,t,o)=>{o._linha=rows[k].length+2;rows[k].push(o);return o;},
    anexarLinhas_:(k,t,l)=>l.forEach(o=>{o._linha=rows[k].length+2;rows[k].push(o);}),
    apagarLinhas_:(k,ids)=>{rows[k]=rows[k].filter(x=>!ids.includes(x._linha));},
    propriedade_:(k,p)=>p, textoCelula_:x=>String(x||''), agoraIso_:()=>new Date().toISOString(),
    registrarLog_:()=>{}, registrarLimpeza_:()=>{}
  },extra||{}));
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Esquema.gs'),'utf8'),ctx);
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'imoplace-API-PainelPrivado','Integracao.gs'),'utf8'),ctx);
  return ctx;
}

teste('pendencias repetida com o mesmo jobId devolve a mesma reserva sem gravar de novo', () => {
  const rows={
    IMOVEIS:[{_linha:2,ID:'1001',VERSAO:3,STATUS:'publicado',CATEGORIA:'venda',TITULO:'Casa'}],
    IMAGENS:[{_linha:2,IMOVEL_ID:'1001',IMAGEM_ID:'i0000000001',DRIVE_FILE_ID:'drv',VERSAO:1,ESTADO_SYNC:'pendente'}],
    FILA:[{_linha:2,IMOVEL_ID:'1001',VERSAO:3,ESTADO:'pendente',JOB_ID:'',SOLICITADO_EM:'2026-01-01'}],
    EXECUCOES:[]
  };
  const ctx=escritor(rows);
  const a=ctx.pendencias_('gh-9-1',{forcar:false});
  assert.strictEqual(JSON.stringify(a.pendencias.map(p=>p.imovelId)),'["1001"]');
  assert.strictEqual(rows.FILA[0].ESTADO,'em_processamento');
  assert.strictEqual(rows.EXECUCOES.length,1);
  // Resposta perdida na rede: o GitHub repete. Antes vinha lista vazia e o imóvel ficava preso 30 min.
  rows.FILA.push({_linha:3,IMOVEL_ID:'2002',VERSAO:1,ESTADO:'pendente',JOB_ID:'',SOLICITADO_EM:'2026-01-02'});
  const b=ctx.pendencias_('gh-9-1',{forcar:false});
  assert.strictEqual(b.repetida,true);
  assert.strictEqual(JSON.stringify(b.pendencias),JSON.stringify(a.pendencias));
  assert.strictEqual(rows.EXECUCOES.length,1,'não duplica a execução');
  assert.strictEqual(rows.FILA[1].ESTADO,'pendente','repetição não reserva trabalho novo');
  rows.EXECUCOES[0].RESULTADO='ok';
  assert.throws(()=>ctx.pendencias_('gh-9-1',{}),/encerrado/);
});

teste('ACK repetido depois de resultado desatualizado ou parcial é idempotente', () => {
  for (const r of ['desatualizado','parcial']) {
    const rows={IMOVEIS:[],IMAGENS:[],FILA:[],EXECUCOES:[{_linha:2,JOB_ID:'gh-5',RESULTADO:r}]};
    assert.strictEqual(escritor(rows).confirmar_('gh-5',{imoveis:[],imagens:[]}).idempotente,true);
    assert.strictEqual(rows.EXECUCOES[0].RESULTADO,r);
  }
});

teste('gravarLinhas_ grava só as colunas pedidas, em lote', () => {
  const grade=[[1,'a','x'],[2,'b','y'],[3,'c','z']]; // linhas 2..4
  let chamadas=0;
  const sh={getRange:(l,c,n,w)=>({getValues:()=>{chamadas++;return grade.slice(l-2,l-2+n).map(r=>r.slice(c-1,c-1+w));},
    setValues:v=>{chamadas++;v.forEach((r,i)=>r.forEach((x,j)=>{grade[l-2+i][c-1+j]=x;}));}})};
  const ctx=vm.createContext({console,SpreadsheetApp:{openById:()=>({getSheetByName:()=>sh})},
    PropertiesService:{getScriptProperties:()=>({getProperty:()=>'id'})}});
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Esquema.gs'),'utf8'),ctx);
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Planilha.gs'),'utf8'),ctx);
  ctx.gravarLinhas_('X',{cabecalho:['ID','ESTADO','OUTRA']},[{_linha:2,ESTADO:'ok'},{_linha:4,ESTADO:null}]);
  assert.deepStrictEqual(grade,[[1,'ok','x'],[2,'b','y'],[3,'','z']]);
  assert.strictEqual(chamadas,2,'uma leitura e uma gravação por coluna, não por linha');
});

teste('limpeza conta 48h a partir da última confirmação do imóvel', () => {
  const ago=h=>new Date(Date.now()-h*3600000).toISOString();
  const lim={_linha:2,DRIVE_FILE_ID:'antigo',IMOVEL_ID:'1001',IMAGEM_ID:'img1',MOTIVO:'substituicao',SOLICITADO_EM:ago(49),ESTADO:'aguardando'};
  const rows={LIMPEZA:[lim],FILA:[],IMAGENS:[{_linha:2,IMOVEL_ID:'1001',IMAGEM_ID:'img1',DRIVE_FILE_ID:'novo',VERSAO:2,VERSAO_PUBLICADA:2}],
    IMOVEIS:[{_linha:2,ID:'1001',PUBLICADO_EM:ago(1)}]};
  let descartes=0;
  const ctx=vm.createContext({console,comTrava_:f=>f(),lerAba_:k=>({cabecalho:[],linhas:rows[k]}),
    gravarLinha_:(k,t,o)=>Object.assign(rows[k].find(x=>x._linha===o._linha),o),
    agoraIso_:()=>new Date().toISOString(),textoCelula_:x=>String(x||''),
    DriveApp:{getFileById:()=>({setTrashed:()=>{descartes++;}})}});
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'imoplace-API-PainelPrivado','Limpeza.gs'),'utf8'),ctx);
  // Troca há 49h, mas ACK há 1h: antes descartava 1h depois do ACK.
  assert.strictEqual(ctx.limparArquivosAntigos().descartados,0);
  rows.IMOVEIS[0].PUBLICADO_EM=ago(49);
  assert.strictEqual(ctx.limparArquivosAntigos().descartados,1);
  assert.strictEqual(descartes,1);
});

teste('painel recusa visitante anônimo na implantação pública', () => {
  const ctx=vm.createContext({console,
    Session:{getActiveUser:()=>({getEmail:()=>''})},
    PropertiesService:{getScriptProperties:()=>({getProperty:k=>k==='ADMIN_EMAIL'?'dono@exemplo.com':null})},
    HtmlService:{createTemplateFromFile:()=>{throw Error('HTML do painel servido a anônimo');}}});
  for (const f of ['Planilha.gs','Config.gs','Codigo.gs'])
    vm.runInContext(fs.readFileSync(path.join(RAIZ,f==='Planilha.gs'?'COMUM':'imoplace-API-PainelPrivado',f),'utf8'),ctx);
  assert.throws(()=>ctx.doGet(),/Acesso negado/);
});

// ---------- v2.3.2.14 ----------
teste('reconstrução cria tarefa persistente e não enfileira tudo de uma vez', () => {
  const pub=id=>({_linha:Number(id)-998,ID:id,VERSAO:2,VERSAO_PUBLICADA:2,STATUS:'publicado',CATEGORIA:'venda',TITULO:'Casa '+id});
  const rows={IMOVEIS:Array.from({length:55},(_,i)=>pub(String(1000+i))),IMAGENS:[],FILA:[],EXECUCOES:[]};
  const ctx=escritor(rows,{propriedade_:(k,p)=>k==='MAX_POR_EXECUCAO'?'20':p});
  const r=ctx.pendencias_('gh-rec-1',{forcar:true});
  assert.strictEqual(r.pendencias.length,20);
  assert.strictEqual(rows.FILA.length,20,'no máximo 20 na fila');
  assert.strictEqual(rows.RECONSTRUCOES.length,1);
  assert.strictEqual(rows.RECONSTRUCOES[0].ULTIMO_ID,'1019');
  assert.strictEqual(rows.RECONSTRUCOES[0].STATUS,'em_andamento');
  // Em simulação: o primeiro job foi confirmado e teve suas linhas removidas.
  rows.EXECUCOES[0].RESULTADO='ok'; rows.FILA=[];
  const r2=ctx.pendencias_('gh-rec-2',{forcar:false});
  assert.strictEqual(r2.pendencias.length,20);
  assert.strictEqual(rows.RECONSTRUCOES.length,1,'não cria nova campanha');
  assert.strictEqual(rows.RECONSTRUCOES[0].ULTIMO_ID,'1039');
  rows.EXECUCOES[1].RESULTADO='ok'; rows.FILA=[];
  const r3=ctx.pendencias_('gh-rec-3',{forcar:false});
  assert.strictEqual(r3.pendencias.length,15);
  assert.strictEqual(rows.RECONSTRUCOES[0].ULTIMO_ID,'1054');
  rows.EXECUCOES[2].RESULTADO='ok'; rows.FILA=[];
  const r4=ctx.pendencias_('gh-rec-4',{forcar:false});
  assert.strictEqual(r4.pendencias.length,0);
  assert.strictEqual(rows.RECONSTRUCOES[0].STATUS,'concluida');
});

teste('reconstrução respeita prioridade da fila normal e não avança cursor se lotada', () => {
  const pub=id=>({_linha:Number(id)-998,ID:id,VERSAO:2,STATUS:'publicado',CATEGORIA:'venda',TITULO:'Casa'});
  const rows={IMOVEIS:[pub('1000'),pub('1001'),pub('1002')],IMAGENS:[],
    FILA:[{_linha:2,IMOVEL_ID:'1002',VERSAO:2,ESTADO:'pendente',JOB_ID:'',SOLICITADO_EM:'2026-01-01'}],EXECUCOES:[]};
  const ctx=escritor(rows,{propriedade_:(k,p)=>k==='MAX_POR_EXECUCAO'?'1':p});
  const r=ctx.pendencias_('gh-prioridade-1',{forcar:true});
  assert.deepStrictEqual(Array.from(r.pendencias,p=>p.imovelId),['1002']);
  assert.strictEqual(rows.RECONSTRUCOES[0].ULTIMO_ID,'','não avança com fila ocupada');
  assert.strictEqual(rows.FILA.length,1);
  rows.FILA=[];rows.EXECUCOES[0].RESULTADO='ok';
  const r2=ctx.pendencias_('gh-prioridade-2',{forcar:false});
  assert.strictEqual(r2.pendencias[0].imovelId,'1000');
  assert.strictEqual(rows.RECONSTRUCOES[0].ULTIMO_ID,'1000');
});

teste('falha não remove lote de reconstrução e o job seguinte o recupera', () => {
  const rows={IMOVEIS:[{_linha:2,ID:'1001',VERSAO:3,STATUS:'publicado',CATEGORIA:'venda',TITULO:'Casa'}],
    IMAGENS:[],FILA:[],EXECUCOES:[]};
  const ctx=escritor(rows);
  ctx.pendencias_('gh-falha-1',{forcar:true});
  const recId=rows.RECONSTRUCOES[0].ID;
  ctx.falha_('gh-falha-1',{erro:'rede indisponível'});
  assert.strictEqual(rows.FILA.length,1);
  assert.strictEqual(rows.FILA[0].RECONSTRUCAO_ID,recId);
  assert.strictEqual(rows.RECONSTRUCOES[0].STATUS,'em_andamento');
  const r=ctx.pendencias_('gh-falha-2',{forcar:false});
  assert.strictEqual(r.pendencias.length,1);
  assert.strictEqual(rows.FILA.length,1,'sem duplicar o imóvel que falhou');
});

teste('ACK incrementa progresso uma vez e conclui a reconstrução após drenar fila', () => {
  const rows={IMOVEIS:[{_linha:2,ID:'1001',VERSAO:3,VERSAO_PUBLICADA:2,STATUS:'publicado',CATEGORIA:'venda',TITULO:'Casa'}],
    IMAGENS:[],FILA:[],EXECUCOES:[]};
  const ctx=escritor(rows);
  ctx.pendencias_('gh-confirma-1',{forcar:true});
  assert.strictEqual(rows.RECONSTRUCOES[0].STATUS,'em_andamento');
  const a=ctx.confirmar_('gh-confirma-1',{imoveis:[{imovelId:'1001',versao:3,noSite:true}],imagens:[]});
  assert.strictEqual(a.confirmados.length,1);
  assert.strictEqual(rows.RECONSTRUCOES[0].CONFIRMADOS,1);
  assert.strictEqual(rows.FILA.length,0);
  assert.strictEqual(rows.RECONSTRUCOES[0].STATUS,'concluida');
  assert.strictEqual(ctx.confirmar_('gh-confirma-1',{imoveis:[{imovelId:'1001',versao:3,noSite:true}],imagens:[]}).idempotente,true);
  assert.strictEqual(rows.RECONSTRUCOES[0].CONFIRMADOS,1,'ACK repetido não conta duas vezes');
});

teste('reconstrução sem nada a reservar não abre execução vazia', () => {
  const rows={IMOVEIS:[],IMAGENS:[],FILA:[],EXECUCOES:[]};
  const r=escritor(rows).pendencias_('gh-vazio',{forcar:true});
  assert.strictEqual(r.pendencias.length,0);
  assert.strictEqual(rows.EXECUCOES.length,0);
});

teste('gravarLinhas_ separa linhas distantes em blocos e não regrava o meio', () => {
  const lidas=[];
  const grade={};
  const sh={getRange:(l,c,n)=>({getValues:()=>{lidas.push([l,n]);return Array.from({length:n},(_,i)=>[grade[l+i]||'']);},
    setValues:v=>v.forEach((r,i)=>{grade[l+i]=r[0];})})};
  const ctx=vm.createContext({console,SpreadsheetApp:{openById:()=>({getSheetByName:()=>sh})},
    PropertiesService:{getScriptProperties:()=>({getProperty:()=>'id'})}});
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Esquema.gs'),'utf8'),ctx);
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Planilha.gs'),'utf8'),ctx);
  ctx.gravarLinhas_('X',{cabecalho:['ESTADO']},[{_linha:5000,ESTADO:'c'},{_linha:2,ESTADO:'a'},{_linha:4,ESTADO:'b'}]);
  assert.strictEqual(JSON.stringify(lidas),'[[2,3],[5000,1]]','dois blocos: 2..4 e 5000');
  assert.strictEqual(grade[2]+grade[4]+grade[5000],'abc');
});

// ---------- v2.3.2.16 ----------
teste('reconstrução avisa o motor de tudo que ainda vai percorrer (repositório perdido não trava)', () => {
  const pub=id=>({_linha:Number(id)-998,ID:id,VERSAO:2,VERSAO_PUBLICADA:2,STATUS:'publicado',CATEGORIA:'venda',TITULO:'Casa '+id});
  const rows={IMOVEIS:['1000','1001','1002'].map(pub),IMAGENS:[],FILA:[],EXECUCOES:[]};
  const ctx=escritor(rows,{propriedade_:(k,p)=>['MAX_POR_EXECUCAO','LOTE_RECONSTRUCAO'].includes(k)?'1':p});
  const r=ctx.pendencias_('gh-perdido-1',{forcar:true});
  assert.strictEqual(JSON.stringify(r.pendencias.map(p=>p.imovelId)),'["1000"]');
  assert.strictEqual(JSON.stringify(Array.from(r.aguardando).sort()),'["1001","1002"]','fora do lote, mas ainda na campanha');
  // Repetição do mesmo job também avisa.
  assert.strictEqual(JSON.stringify(Array.from(ctx.pendencias_('gh-perdido-1',{}).aguardando).sort()),'["1001","1002"]');
  // Campanha concluída: nada a aguardar.
  rows.RECONSTRUCOES[0].STATUS='concluida'; rows.EXECUCOES[0].RESULTADO='ok'; rows.FILA=[];
  assert.strictEqual(ctx.pendencias_('gh-perdido-2',{}).aguardando.length,0);
});

teste('ACK desatualizado não conta progresso; a confirmação real conta uma vez', () => {
  const rows={IMOVEIS:[{_linha:2,ID:'1001',VERSAO:3,VERSAO_PUBLICADA:2,STATUS:'publicado',CATEGORIA:'venda',TITULO:'Casa'}],
    IMAGENS:[],FILA:[],EXECUCOES:[]};
  const ctx=escritor(rows);
  ctx.pendencias_('gh-velho',{forcar:true});
  rows.IMOVEIS[0].VERSAO=4; // operador editou durante o job
  ctx.confirmar_('gh-velho',{imoveis:[{imovelId:'1001',versao:3,noSite:true}],imagens:[]});
  assert.strictEqual(Number(rows.RECONSTRUCOES[0].CONFIRMADOS)||0,0);
  // Linha volta a ser pega quando a reserva vence (30 min), já com a versão nova.
  rows.FILA[0].VERSAO=4; rows.FILA[0].ATUALIZADO_EM='2000-01-01T00:00:00Z';
  ctx.pendencias_('gh-novo',{});
  ctx.confirmar_('gh-novo',{imoveis:[{imovelId:'1001',versao:4,noSite:true}],imagens:[]});
  assert.strictEqual(rows.RECONSTRUCOES[0].CONFIRMADOS,1);
  assert.strictEqual(rows.RECONSTRUCOES[0].STATUS,'concluida');
});

// ---------- v2.3.2.17: marca d'água ----------
teste("marca d'água: padrão seguro e valores inválidos voltam ao padrão", () => {
  const rodar=props=>{
    const ctx=vm.createContext({console,PropertiesService:{getScriptProperties:()=>({getProperty:k=>props[k]===undefined?null:props[k]})}});
    vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Esquema.gs'),'utf8'),ctx);
    for (const f of ['Planilha.gs']) vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM',f),'utf8'),ctx);
    vm.runInContext(fs.readFileSync(path.join(RAIZ,'imoplace-API-PainelPrivado','Config.gs'),'utf8'),ctx);
    return JSON.parse(JSON.stringify(ctx.CONFIG.marcaDagua));
  };
  assert.deepStrictEqual(rodar({SITE_URL:'https://imoplace.com.br'}),
    {ativa:true,texto:'imoplace.com.br',posicao:'inferior-direita',opacidade:0.5,tamanho:4});
  assert.deepStrictEqual(rodar({MARCA_DAGUA_POSICAO:'meio',MARCA_DAGUA_OPACIDADE:'7',MARCA_DAGUA_TAMANHO:'abc'}),
    {ativa:true,texto:'imoplace.com.br',posicao:'inferior-direita',opacidade:0.5,tamanho:4});
  const pers=rodar({MARCA_DAGUA_TEXTO:'Fettuccia Imóveis',MARCA_DAGUA_POSICAO:'Mosaico',MARCA_DAGUA_OPACIDADE:'0,3',MARCA_DAGUA_TAMANHO:'6'});
  assert.strictEqual(pers.texto,'Fettuccia Imóveis'); assert.strictEqual(pers.posicao,'mosaico');
  assert.strictEqual(pers.opacidade,0.3); assert.strictEqual(pers.tamanho,6);
  assert.strictEqual(rodar({MARCA_DAGUA_ATIVA:'nao'}).ativa,false);
});

teste("marca d'água: desenha na posição certa, com contorno, e só na foto grande", () => {
  const html=fs.readFileSync(path.join(RAIZ,'imoplace-API-PainelPrivado','PainelJs.html'),'utf8');
  const bloco=html.slice(html.indexOf('/* marca-dagua:inicio'),html.indexOf('/* marca-dagua:fim */'));
  const ctx=vm.createContext({Math}); vm.runInContext(bloco,ctx);
  const falso=()=>{const g={escritas:[],save(){},restore(){},translate(){},rotate(){},measureText:t=>({width:t.length*10}),
    strokeText(t,x,y){g.contornos=(g.contornos||0)+1;},fillText(t,x,y){g.escritas.push([x,y,g.textAlign,g.textBaseline]);}};return g;};
  const cfg=p=>({ativa:true,texto:'imoplace.com.br',posicao:p,opacidade:0.5,tamanho:4});
  let g=falso(); assert.strictEqual(ctx.aplicarMarcaDagua(g,1920,1080,cfg('inferior-direita')),true);
  const fonte=Math.round(1080*0.04), m=Math.round(fonte*0.8);
  assert.strictEqual(JSON.stringify(g.escritas),JSON.stringify([[1920-m,1080-m,'right','bottom']]));
  assert.strictEqual(g.globalAlpha,0.5); assert.strictEqual(g.contornos,1); assert.match(g.font,new RegExp(fonte+'px'));
  g=falso(); ctx.aplicarMarcaDagua(g,1000,800,cfg('superior-esquerda'));
  assert.strictEqual(JSON.stringify(g.escritas[0].slice(2)),'["left","top"]');
  g=falso(); ctx.aplicarMarcaDagua(g,1000,800,cfg('centro'));
  assert.strictEqual(JSON.stringify(g.escritas[0]),'[500,400,"center","middle"]');
  g=falso(); ctx.aplicarMarcaDagua(g,1920,1080,cfg('mosaico'));
  assert.ok(g.escritas.length>=6,'mosaico cobre a foto: '+g.escritas.length);
  g=falso(); ctx.aplicarMarcaDagua(g,200,150,cfg('inferior-direita'));
  assert.match(g.font,/ 12px/,'fonte mínima legível em foto pequena');
  assert.strictEqual(ctx.aplicarMarcaDagua(falso(),100,100,null),false);
  assert.strictEqual(ctx.aplicarMarcaDagua(falso(),100,100,Object.assign(cfg('centro'),{ativa:false})),false);
  assert.ok(html.includes('desenhar(LADO_MINI, 0.55, null)'),'miniatura do painel sem marca');
  assert.ok(html.includes("converter(lista[i], marcaDoEnvio())") && html.includes("converter(f, marcaDoEnvio())"),'envio e substituição aplicam');
});

// ---------- v2.3.2.18 ----------
teste('feed e integração leem IMAGENS sem a coluna MINIATURA, com o mesmo resultado no resto', () => {
  const cab=['IMAGEM_ID','IMOVEL_ID','DRIVE_FILE_ID','NOME','LEGENDA','ALT','ORDEM','SHA256','BYTES','LARGURA','ALTURA','MINIATURA','VERSAO','VERSAO_PUBLICADA','OPERACAO','ESTADO_SYNC','ATUALIZADO_EM'];
  const grade=[cab];
  for (let i=0;i<300;i++) grade.push(cab.map(c=>i===150?'':c==='MINIATURA'?'data:image/webp;base64,'+'A'.repeat(12000):c+i));
  let celulasLidas=0, leuMiniatura=false;
  const sh={getLastColumn:()=>cab.length,getLastRow:()=>grade.length,
    getRange:(l,c,n,w)=>({getValues:()=>{celulasLidas+=n*w; if(l>1&&c<=12&&c+w-1>=12) leuMiniatura=true;
      return grade.slice(l-1,l-1+n).map(r=>r.slice(c-1,c-1+w));}})};
  const ctx=vm.createContext({console,SpreadsheetApp:{openById:()=>({getSheetByName:()=>sh})},
    PropertiesService:{getScriptProperties:()=>({getProperty:()=>'id'})}});
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Esquema.gs'),'utf8'),ctx);
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Planilha.gs'),'utf8'),ctx);
  const tudo=ctx.lerAba_('IMAGENS'); assert.ok(leuMiniatura);
  leuMiniatura=false; celulasLidas=0;
  const enxuto=ctx.lerAba_('IMAGENS',['MINIATURA']);
  assert.strictEqual(leuMiniatura,false,'MINIATURA não pode ser lida');
  assert.strictEqual(enxuto.linhas.length,299,'linha vazia continua ignorada');
  const semMini=tudo.linhas.map(o=>{const c=Object.assign({},o);delete c.MINIATURA;return c;});
  assert.strictEqual(JSON.stringify(enxuto.linhas),JSON.stringify(semMini));
  for (const [arq,trecho] of [['imoplace-API-Publica/Feed.gs',"lerAba_('IMAGENS', ['MINIATURA'])"],
    ['imoplace-API-PainelPrivado/Integracao.gs',"imagens: lerAba_('IMAGENS', ['MINIATURA'])"],
    ['imoplace-API-PainelPrivado/Limpeza.gs',"lerAba_('IMAGENS', ['MINIATURA'])"]])
    assert.ok(fs.readFileSync(path.join(RAIZ,arq),'utf8').includes(trecho),arq);
});

// ---------- v2.3.2.19 ----------
teste('texto que o Sheets interpretaria é gravado como texto (sem #ERROR! nem data)', () => {
  const ctx=vm.createContext({console});
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Esquema.gs'),'utf8'),ctx);
  vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Planilha.gs'),'utf8'),ctx);
  const v=(c,x)=>ctx.valorCelula_(c,x);
  for (const [entrada,esperado] of [['+ 3 quartos',"'+ 3 quartos"],['- Sala ampla',"'- Sala ampla"],['=vista mar',"'=vista mar"],
      ['@imoplace',"'@imoplace"],['10/12',"'10/12"],['2/3',"'2/3"],['90000-000',"'90000-000"],['R$ 1.500,00',"'R$ 1.500,00"],
      ['TRUE',"'TRUE"],['Casa com 3 quartos','Casa com 3 quartos'],['SIM','SIM'],['publicado','publicado'],['',''],
      ['2026-11-12T10:00:00.000Z','2026-11-12T10:00:00.000Z']])
    assert.strictEqual(v('DESCRICAO',entrada),esperado,entrada);
  assert.strictEqual(v('ATUALIZADO_EM','10/12'),'10/12','coluna já formatada como texto não recebe apóstrofo');
  assert.strictEqual(v('WHATSAPP','5551999999999'),'5551999999999');
  assert.strictEqual(v('PRECO',550000),550000,'número continua número');
  assert.strictEqual(v('DESCRICAO',null),'');
  // Todas as escritas passam pela proteção: anexar, gravar linha e gravar em lote.
  const plan=fs.readFileSync(path.join(RAIZ,'COMUM','Planilha.gs'),'utf8');
  assert.ok(plan.includes('return valorCelula_(c, obj[c]);'),'linhaParaValores_ (anexar e gravar linha)');
  assert.ok(plan.includes('v[o._linha - ini][0] = valorCelula_(c, o[c]);'),'gravarLinhas_');
});

teste('gatilho diário reativa o workflow do GitHub (agendamento desligado após 60 dias)', () => {
  const rodar=(props,codigoEnable,fila)=>{
    const chamadas=[], logs=[];
    const ctx=vm.createContext({console:{warn(){},log(){},error(){}},
      PropertiesService:{getScriptProperties:()=>({getProperty:k=>props[k]===undefined?null:props[k],setProperty(){}})},
      UrlFetchApp:{fetch:(u,o)=>{chamadas.push(o.method.toUpperCase()+' '+u.replace('https://api.github.com/repos/',''));
        return {getResponseCode:()=>u.endsWith('/enable')?codigoEnable:204};}},
      carregar_:()=>({fila:{linhas:fila||[]}}),registrarLog_:(u,a,i,r,d)=>logs.push(a+':'+r),
      textoCelula_:x=>String(x||''),agoraIso_:()=>new Date().toISOString(),exigirAdmin_:()=>'dono'});
    vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Esquema.gs'),'utf8'),ctx);
    vm.runInContext(fs.readFileSync(path.join(RAIZ,'COMUM','Planilha.gs'),'utf8'),ctx);
    for (const f of ['Config.gs','Sincronizar.gs']) vm.runInContext(fs.readFileSync(path.join(RAIZ,'imoplace-API-PainelPrivado',f),'utf8'),ctx);
    ctx.registrarLog_=(u,a,i,r,d)=>logs.push(a+':'+r); // Planilha.gs redefine; simulação vale depois de carregar
    return {ctx,chamadas,logs};
  };
  const gh={GITHUB_REPO:'fettuccia/imoplace',GITHUB_TOKEN:'tok'};
  let r=rodar(gh,204); r.ctx.reservaDiaria();
  assert.strictEqual(JSON.stringify(r.chamadas),'["PUT fettuccia/imoplace/actions/workflows/publicar.yml/enable"]','fila vazia: só reativa');
  r=rodar(gh,403); r.ctx.reservaDiaria();
  assert.strictEqual(JSON.stringify(r.logs),'["reativar-workflow:erro"]','falha fica registrada, gatilho não quebra');
  r=rodar({},204); r.ctx.reservaDiaria();
  assert.strictEqual(r.chamadas.length,0,'sem token configurado não chama o GitHub');
  r=rodar(gh,204,[{SOLICITADO_EM:'2000-01-01T00:00:00Z'}]); r.ctx.reservaDiaria();
  assert.strictEqual(JSON.stringify(r.chamadas),'["PUT fettuccia/imoplace/actions/workflows/publicar.yml/enable","PUT fettuccia/imoplace/actions/workflows/publicar.yml/enable","POST fettuccia/imoplace/actions/workflows/publicar.yml/dispatches"]',
    'fila parada: reativa e dispara');
});
console.log(`\n${ok} testes do Apps Script passaram.`);
