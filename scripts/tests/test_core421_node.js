'use strict';
// Regressões do CORE 4.2.1. Só roda no pacote completo (CORE/ ao lado de GITHUB/).
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const dir=path.resolve(__dirname,'../../../CORE');
const ler=n=>fs.readFileSync(path.join(dir,n),'utf8');

// 1. Preço digitado com ponto de milhar.
const esq={};vm.createContext(esq);vm.runInContext(ler('Esquema.gs'),esq);
const casos={'450.000':450000,'1.250.000':1250000,'1.234,56':1234.56,'R$ 350.000,00':350000,'450000':450000,'12.5':12.5,'72.35':72.35,'':null};
for(const [v,esperado] of Object.entries(casos))assert.strictEqual(esq.numeroOuNulo_(v),esperado,'numeroOuNulo_('+JSON.stringify(v)+')');
// Latitude/longitude: ponto é sempre decimal.
assert.strictEqual(esq.numeroOuNulo_('-30.051',true),-30.051);assert.strictEqual(esq.numeroOuNulo_('-51.230',true),-51.23);
assert(/numeroOuNulo_\(v, c === 'LAT' \|\| c === 'LNG'\)/.test(ler('Imoveis.gs')),'LAT/LNG sem ponto decimal');

// 2. instalar() só é livre na primeira vez.
const cfg={props:{},email:'dono@exemplo.com'};
const c={PropertiesService:{getScriptProperties:()=>({getProperty:k=>cfg.props[k]??null})},Session:{getActiveUser:()=>({getEmail:()=>cfg.email})},String,Number,Math,isFinite};
vm.createContext(c);vm.runInContext(ler('Planilha.gs')+'\n'+ler('Config.gs'),c);
c.exigirAdminOuPrimeiraInstalacao_();                       // sem ADMIN_EMAIL: liberado
cfg.props.ADMIN_EMAIL='dono@exemplo.com';c.exigirAdminOuPrimeiraInstalacao_();
cfg.email='outro@exemplo.com';assert.throws(()=>c.exigirAdminOuPrimeiraInstalacao_(),/Acesso negado/);
for(const [arq,fn] of [['Instalador.gs','instalar'],['Instalador.gs','verificarInstalacao'],['Migracao.gs','migrarInstalacaoExistente']]){
  const corpo=ler(arq).split('function '+fn+'(')[1].slice(0,200);
  assert(/exigirAdmin(OuPrimeiraInstalacao)?_\(\)/.test(corpo),fn+' sem verificação de administrador');
}
// MAX_FOTO_MB inválido não desliga o limite.
cfg.props.MAX_FOTO_MB='abc';assert.strictEqual(c.CONFIG.maxFotoBytes,20*1024*1024);
cfg.props.MAX_FOTO_MB='8';assert.strictEqual(c.CONFIG.maxFotoBytes,8*1024*1024);

// 3. Reconciliação não lê miniaturas; gravarLinha_ preserva a coluna não lida.
assert(/carregar_\(true\)/.test(ler('Resultados.gs')));
const pl={ESQUEMA:{texto:{}}};vm.createContext(pl);vm.runInContext(ler('Planilha.gs'),pl);
assert.deepStrictEqual(Array.from(pl.linhaParaValores_(['IMAGEM_ID','MINIATURA','VERSAO'],{IMAGEM_ID:'i1',VERSAO:3},['i1','data:image/webp;base64,AAAA',2])),['i1','data:image/webp;base64,AAAA',3]);

// 4. Uma única atualização automática no painel.
assert.strictEqual((ler('PainelJs.html').match(/setInterval\(/g)||[]).length,1,'polling duplicado no painel');

// 5. Trocar de módulo pergunta antes de esconder edição não salva.
assert(ler('Painel.html').includes('podeSair()'));assert(ler('AdministracaoJs.html').includes('podeSair()'));

// 6. Disparo grava a configuração operacional sob trava.
assert(/comTrava_\(sincronizarConfiguracaoOperacional_\)/.test(ler('Sincronizar.gs')));

// 7. Monitor lê só ID e STATUS.
const mon=fs.readFileSync(path.resolve(dir,'../MONITOR/Monitor.gs'),'utf8');
assert(!mon.includes('getDataRange'),'Monitor voltou a ler a aba inteira');
console.log('CORE 4.2.1: milhar, guarda de instalação, limite de foto, miniaturas, polling, módulos, trava e Monitor conferidos.');
