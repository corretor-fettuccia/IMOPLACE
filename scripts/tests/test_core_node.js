'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'../../..');
const dir=path.join(root,'CORE');
let code=fs.readdirSync(dir).filter(x=>x.endsWith('.gs')).map(x=>fs.readFileSync(path.join(dir,x),'utf8')).join('\n');
new vm.Script(code); // sintaxe dos arquivos do único projeto
assert(!code.includes('function doPost('),'não deve haver POST público');
const result=fs.readFileSync(path.join(dir,'Resultados.gs'),'utf8');
const im={ID:'1001',VERSAO:6,VERSAO_PUBLICADA:5,NO_SITE:'NAO',ESTADO_SYNC:'pendente'};
const fil={IMOVEL_ID:'1001',VERSAO:6,ESTADO:'pendente',_linha:2};
const fake={
  comTrava_:(fn)=>fn(),
  lerAba_:(name)=>name==='RESULTADOS' ? {linhas:[{IMOVEL_ID:'1001',VERSAO:6,STATUS:'PUBLICADO',CODIGO:'PUBLISHED_OK',IMAGENS_JSON:'[]',DATA:'2026-11-12'}]} : {linhas:[]},
  carregar_:()=>({imoveis:{linhas:[im]},fila:{linhas:[fil]},imagens:{linhas:[]}}),
  gravarLinha_:(name, ctx, obj)=>Object.assign(name==='IMOVEIS'?im:fil,obj),
  aba_:()=>({deleteRow:(row)=>{assert.equal(row,2);fake.deleted=true;}}),
  agoraIso_:()=> '2026-11-12',
  console,
};
vm.createContext(fake);vm.runInContext(result,fake);
assert.equal(fake.reconciliarResultados_(),1);
assert.equal(im.VERSAO_PUBLICADA,6);
assert.equal(im.NO_SITE,'SIM');
assert.equal(im.ULTIMO_CODIGO,'PUBLISHED_OK');
assert(fake.deleted);
// Evento antigo jamais confirma uma nova versão.
const im2={ID:'1001',VERSAO:7,VERSAO_PUBLICADA:6,NO_SITE:'SIM',ESTADO_SYNC:'pendente'};
const fil2={IMOVEL_ID:'1001',VERSAO:7,ESTADO:'pendente',_linha:2};
fake.carregar_=()=>({imoveis:{linhas:[im2]},fila:{linhas:[fil2]},imagens:{linhas:[]}});
fake.gravarLinha_=()=>{throw Error('Evento obsoleto não deveria gravar')};
assert.equal(fake.reconciliarResultados_(),0);
assert.equal(im2.VERSAO_PUBLICADA,6);
console.log('CORE: sintaxe válida, publicação individual e evento antigo rejeitado.');
// ---------- 3.1.1: aviso por e-mail ao operador quando as tentativas automáticas se esgotam ----------
function ambiente(eventos, props) {
  const fila={IMOVEL_ID:'1001',VERSAO:6,ESTADO:'pendente',_linha:2};
  const imov={ID:'1001',VERSAO:6,VERSAO_PUBLICADA:5,TITULO:'Casa Jardim',ESTADO_SYNC:'pendente'};
  const guardadas=Object.assign({ADMIN_EMAIL:'dono@exemplo.com'},props||{});
  const env={emails:[],logs:[],
    comTrava_:fn=>fn(), console,
    lerAba_:n=>n==='RESULTADOS'?{linhas:eventos}:{linhas:[]},
    carregar_:()=>({imoveis:{linhas:[imov]},fila:{linhas:[fila]},imagens:{linhas:[]}}),
    gravarLinha_:(n,c,o)=>Object.assign(n==='IMOVEIS'?imov:fila,o),
    aba_:()=>({deleteRow(){}}), anexarLinha_(){},
    agoraIso_:()=>new Date().toISOString(), textoCelula_:x=>String(x||''),
    registrarLog_:(u,a,i,r,d)=>env.logs.push(a+':'+r),
    PropertiesService:{getScriptProperties:()=>({getProperty:k=>guardadas[k]===undefined?null:guardadas[k],setProperty:(k,v)=>{guardadas[k]=v;}})},
    MailApp:{sendEmail:o=>{if(env.falharEnvio)throw Error('cota de e-mail');env.emails.push(o);}},
  };
  env.propriedade_=(k,p)=>{const v=guardadas[k];return v===undefined||String(v).trim()===''?(p===undefined?'':p):String(v).trim();};
  env.CONFIG={get adminEmail(){return env.propriedade_('ADMIN_EMAIL').toLowerCase();},githubRepo:'fettuccia/imoplace'};
  vm.createContext(env); vm.runInContext(result,env);
  return env;
}
const ha=min=>new Date(Date.now()-min*60000).toISOString();
const tentativa=(min,fim)=>[{IMOVEL_ID:'1001',VERSAO:6,STATUS:'PROCESSANDO',DATA:ha(min),GITHUB_RUN_ID:'111'+min},
  ...(fim?[{IMOVEL_ID:'1001',VERSAO:6,STATUS:fim,DATA:ha(min-2),MENSAGEM:'Drive recusou (HTTP 403)',GITHUB_RUN_ID:'111'+min}]:[])];
// 3 tentativas com erro: um e-mail ao ADMIN_EMAIL, com imóvel, erro e link da execução; nunca repetido.
let env=ambiente([...tentativa(200,'ERRO'),...tentativa(120,'ERRO'),...tentativa(40,'ERRO')]);
env.reconciliarResultados_();
assert.equal(env.emails.length,1);
assert.equal(env.emails[0].to,'dono@exemplo.com');
assert(/Casa Jardim/.test(env.emails[0].body) && /HTTP 403/.test(env.emails[0].body));
assert(/github\.com\/fettuccia\/imoplace\/actions\/runs\/11140/.test(env.emails[0].body),'link da última execução');
env.reconciliarResultados_(); env.reconciliarAgendado();
assert.equal(env.emails.length,1,'mesmo imóvel e versão: não repete o aviso');
// Só 2 tentativas: o GitHub ainda vai tentar sozinho, sem e-mail.
env=ambiente([...tentativa(200,'ERRO'),...tentativa(120,'ERRO')]); env.reconciliarResultados_();
assert.equal(env.emails.length,0);
// EMAIL_OPERADOR substitui o administrador e aceita vários endereços; inválidos são ignorados.
env=ambiente([...tentativa(200,'ERRO'),...tentativa(120,'ERRO'),...tentativa(40,'ERRO')],{EMAIL_OPERADOR:'op@exemplo.com, x, outro@exemplo.com.br'});
env.reconciliarResultados_();
assert.equal(env.emails[0].to,'op@exemplo.com,outro@exemplo.com.br');
// Execução que não respondeu (cancelada/expirada) 3 vezes também avisa; a que ainda pode estar rodando, não.
env=ambiente([...tentativa(200),...tentativa(120),...tentativa(10)]); env.reconciliarResultados_();
assert.equal(env.emails.length,0,'última execução há 10 min pode estar rodando');
env=ambiente([...tentativa(200),...tentativa(120),...tentativa(50)]); env.reconciliarResultados_();
assert.equal(env.emails.length,1);
assert(/não respondeu/.test(env.emails[0].body));
// Falha no envio não marca como avisado (tenta na próxima hora) e fica na aba LOG.
env=ambiente([...tentativa(200,'ERRO'),...tentativa(120,'ERRO'),...tentativa(40,'ERRO')]); env.falharEnvio=true;
env.reconciliarResultados_();
assert(env.logs.includes('aviso-email:erro'));
env.falharEnvio=false; env.reconciliarResultados_();
assert.equal(env.emails.length,1,'reenvia depois que o envio volta a funcionar');
// O núcleo e o GitHub usam o mesmo limite de tentativas; instalar() cria o gatilho; manifesto tem a permissão.
const py=fs.readFileSync(path.join(root,'GITHUB','scripts','core_google.py'),'utf8');
assert.equal(Number(/^MAX_TENTATIVAS = (\d+)/m.exec(py)[1]),Number(/var MAX_TENTATIVAS_ = (\d+)/.exec(result)[1]));
assert(fs.readFileSync(path.join(dir,'Instalador.gs'),'utf8').includes("newTrigger('reconciliarAgendado').timeBased().everyHours(1)"));
assert(JSON.parse(fs.readFileSync(path.join(dir,'appsscript.json'),'utf8')).oauthScopes.includes('https://www.googleapis.com/auth/script.send_mail'));
console.log('CORE: aviso por e-mail ao operador (3 tentativas, sem repetir, vários destinatários, reenvio após falha).');


// Confirmação do job antigo chega atrasada: não substitui PROCESSANDO do job atual.
const ev=(job, status, min)=>({IMOVEL_ID:'1001',VERSAO:6,JOB_ID:job,STATUS:status,DATA:ha(min),CODIGO:status==='PUBLICADO'?'PUBLISHED_OK':status});
env=ambiente([ev('gh-old','PROCESSANDO',55),ev('gh-new','PROCESSANDO',1),ev('gh-old','PUBLICADO',0)]);
assert.equal(env.reconciliarResultados_(),1);
assert.equal(env.carregar_().imoveis.linhas[0].VERSAO_PUBLICADA,5);
assert.equal(env.carregar_().imoveis.linhas[0].ESTADO_SYNC,'em_processamento');
assert.equal(env.carregar_().fila.linhas[0].JOB_ID,'gh-new');
// O job atual pode publicar normalmente.
env=ambiente([ev('gh-old','PROCESSANDO',55),ev('gh-new','PROCESSANDO',1),ev('gh-old','PUBLICADO',0),ev('gh-new','PUBLICADO',0)]);
assert.equal(env.reconciliarResultados_(),1);
assert.equal(env.carregar_().imoveis.linhas[0].VERSAO_PUBLICADA,6);
console.log('CORE: evento atrasado de outro JOB_ID ignorado, ACK atual aceito.');
