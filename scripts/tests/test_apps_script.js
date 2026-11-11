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
  const rows={LIMPEZA:[lim],IMAGENS:[{_linha:2,IMOVEL_ID:'1001',IMAGEM_ID:'img1',DRIVE_FILE_ID:'novo',VERSAO:2,VERSAO_PUBLICADA:2}],FILA:[{IMOVEL_ID:'1001',ESTADO:'pendente'}]};
  let descartes=0;
  const ctx=vm.createContext({console,comTrava_:f=>f(),
    lerAba_:key=>({cabecalho:[],linhas:rows[key]}),
    gravarLinha_:(key,tab,obj)=>Object.assign(rows[key].find(x=>x._linha===obj._linha),obj),
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
console.log(`\n${ok} testes do Apps Script passaram.`);
