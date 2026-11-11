// Carrega os arquivos comuns do Apps Script num contexto Node isolado (sem planilha, Drive ou rede).
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const RAIZ = path.resolve(__dirname, '..', '..', '..', 'GOOGLE.APPSCRIPT');

function carregarComum() {
  const ctx = vm.createContext({ console });
  for (const nome of ['Esquema.gs']) {
    vm.runInContext(fs.readFileSync(path.join(RAIZ, 'COMUM', nome), 'utf8'), ctx, { filename: nome });
  }
  return ctx;
}

module.exports = { RAIZ, carregarComum };

// Uso por linha de comando (testes Python): node apoio.js serializar < linha.json
if (require.main === module) {
  const ctx = carregarComum();
  const entrada = JSON.parse(fs.readFileSync(0, 'utf8'));
  const cmd = process.argv[2];
  let saida;
  if (cmd === 'serializar') saida = ctx.serializarPublico_(entrada.imovel, entrada.imagens, entrada.siteUrl);
  else if (cmd === 'assinar') saida = { mensagem: ctx.mensagemAssinada_(entrada.acao, entrada.ts, entrada.jobId, entrada.payload) };
  else if (cmd === 'nome') saida = { nome: ctx.nomeImagemPublica_(entrada.img, entrada.versao) };
  else { console.error('comando desconhecido'); process.exit(2); }
  process.stdout.write(JSON.stringify(saida));
}
