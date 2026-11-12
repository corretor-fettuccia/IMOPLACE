# Alterações v2.3.2.21 — Liberação (go-live)

## Código
- `gerador.py`: a trava "PUBLICACAO BLOQUEADA" (2.3.2.20) deixa de valer para imóvel que já está na fila ou na
  campanha de reconstrução. Ele sai do site só até a vez dele. Corrige a reconstrução, que travava quando o
  repositório perdia fotos com o `catalogo.json` intacto. As outras 4 travas da 2.3.2.20 continuam.
- `IntegracaoActions/Integracao.gs`: mensagem de erro aponta para o manual (só texto; nova versão opcional).

## Instaladores
- `continuar_configuracao.sh`: gera o `SEGREDO_INTEGRACAO` (64 caracteres, `chmod 600`, reaproveitado nas
  repetições, nunca mostrado na tela) e orienta onde colocá-lo. Antes nenhum passo gerava o segredo.
- `assistente_git.py`: lista de configuração atual (ESCRITOR_URL obrigatório; URLs privadas em Secrets).
- Removido `GOOGLE.APPSCRIPT/scripts/assistente.py` (e teste): nenhum script o chamava e suas listas estavam antigas.
- Rótulos de versão antigos removidos dos instaladores.

## Documentação
- Novo **`docs/MANUAL_INSTALACAO.md`**: único roteiro, do zero à produção (Google, credencial do Drive, GitHub,
  token do painel, homologação, atualização), tabela de todas as configurações e problemas frequentes com as
  mensagens exatas do sistema. Pela primeira vez documenta como gerar o segredo e criar o `GITHUB_TOKEN`.
- `COMECE_AQUI.md`, `GUIA_INSTALACAO_GITHUB.md`, `GOOGLE.APPSCRIPT/GUIA_INSTALACAO.md` e `LEIA-ME.md` viraram
  apontamentos curtos (eles se contradiziam). `GO_LIVE_2.3.2.20.md` foi para `docs/historico/`.
- `OPERACAO.md`, `RECONSTRUCAO_PROGRESSIVA.md`, `ESTRUTURA.md` e `HOMOLOGACAO_PRODUCAO.md` alinhados ao código atual.
- Novo teste `test_documentacao.py`: arquivos citados existem, toda configuração do workflow está no manual,
  nenhuma orientação antiga contradiz o código, versões e notas batem.

## Atualizar a partir da 2.3.2.20
1. GitHub: substitua `.github/workflows/publicar.yml`, `scripts/`, `docs/`, `COMECE_AQUI.md`,
   `GUIA_INSTALACAO_GITHUB.md`, `VERSAO`, `instalar.sh` e `verificar.sh`. Nunca `site/catalogo.json` nem `site/imoveis/`.
2. Apps Script: nada obrigatório. Se quiser a mensagem nova da ponte, `./atualizar.sh` e nova versão da IntegracaoActions.
3. Confira `ESCRITOR_URL` e `API_INTEGRACAO_ACTIONS_URL` em Secrets e `GITHUB_REPO`/`GITHUB_TOKEN` no PainelPrivado.

Testes: Python 42 (+5: reconstrução com catálogo intacto e documentação), Apps Script 36.
