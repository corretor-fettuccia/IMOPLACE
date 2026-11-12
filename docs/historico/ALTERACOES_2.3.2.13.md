# Correções v2.3.2.13

Origem: revalidação do relatório "Auditoria Ponytail — ImoPlace v2.3.2.12".

## Código

- **Repetição de `pendencias` (achado 1):** se a resposta se perder na rede e o GitHub repetir com o mesmo `jobId`,
  o escritor central devolve a mesma reserva, sem gravar nem criar outra linha em EXECUCOES. Antes vinha lista
  vazia e os imóveis ficavam presos em `em_processamento` por 30 minutos. Job já encerrado é recusado.
- **Repetição de `confirmar`:** ACK repetido depois de resultado `desatualizado` ou `parcial` agora é idempotente
  (antes só `ok` era; os outros davam "execução encerrada" e derrubavam o workflow).
- **Limpeza de fotos (achado 2):** a carência de 48h conta a partir do mais recente entre o pedido de descarte e
  a última confirmação do imóvel (`IMOVEIS.PUBLICADO_EM`). Antes, um ACK 47h após a troca deixava só 1h.
- **Versões não reservadas (achado 3):** o feed público passa a trazer `versaoPublicada`. Imóvel fora da fila do
  job com alteração ainda não confirmada fica no site com a última versão confirmada; se nunca foi confirmado,
  só entra quando a fila processar (antes podia aparecer sem fotos). Feed sem o campo mantém o comportamento antigo.
- **Gravação em lote (achados 5 e 7):** `gravarLinhas_` e `anexarLinhas_` em `COMUM/Planilha.gs`. `pendencias_`,
  `confirmar_` e `falha_` gravam 2 chamadas por coluna alterada, não 2 por linha; as linhas de reconstrução
  forçada entram numa única gravação. Ex.: 30 imóveis × 40 fotos novas passavam de 2.400 chamadas ao Sheets.
- **Teste de acesso anônimo (achado 4):** `doGet()` do painel recusa visitante sem e-mail.
- Testes: +5 no Apps Script (23 no total), +1 em Python (23 no total). Todos os novos falham na 2.3.2.12.

## Documentação (achado 8)

- Um único guia Google: `GOOGLE.APPSCRIPT/GUIA_INSTALACAO.md` (removidas as cópias idênticas
  `GUIA_INTEGRACAO.md` e `GUIA_INSTALADOR_GUIADO.md`).
- Changelogs e contratos antigos em `docs/historico/`, com aviso de que não servem para instalar.

## Não alterado, por decisão

- **Achado 6 (janela entre validar e deploy):** é próprio de publicação assíncrona. O painel já separa versão
  atual (`VERSAO`) de publicada (`VERSAO_PUBLICADA`), o ACK recusa versão obsoleta e a próxima execução
  (até 15 min) publica a nova.
- **Cursor de reconstrução (parte do achado 5):** com a gravação em lote, a reserva fica barata e as fotos já
  presentes não são baixadas de novo (conferência por SHA-256). Só uma reconstrução com o repositório perdido e
  centenas de imóveis pode passar dos 30 min do workflow; nesse caso aumente `timeout-minutes`.
