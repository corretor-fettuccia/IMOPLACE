# Correções v2.3.2.12

- `imoplace-API-IntegracaoActions/Integracao.gs`: `doPost()` e `verificarConfiguracaoIntegracao()` usam a mesma
  função `urlEscritorCentral_()` (apaga espaços do início e do fim e usa a mesma regra de validação). Antes, uma
  URL com espaço ou quebra de linha no fim passava no diagnóstico e falhava no GitHub.
- Mesma ponte: quando o escritor central devolve HTML (página de login), o erro passa a dizer que a implantação
  POST do PainelPrivado precisa de "Quem pode acessar: qualquer pessoa", em vez de `Unexpected token '<'`.
- `scripts/tests/test_apps_script.js`: novo teste da ponte (URL com espaço, URL ausente, resposta HTML).
- `GOOGLE.APPSCRIPT/scripts/test_assistente.py`: testes alinhados ao assistente atual (6 perguntas; segredos do
  GitHub ficam em `GIT-PAGE/scripts/assistente_git.py`).
- Rótulos de versão unificados em 2.3.2.12 (`VERSAO`, guias, `publicar.yml`).
- Nenhuma mudança em planilha, contrato do feed, motor Python ou vitrine.
