# ImoPlace — Reconstrução progressiva (desde 2.3.2.15)

## Objetivo

A opção **Reconstrução de todos os imóveis** cria uma única campanha persistente na planilha. Em vez de enfileirar todos os imóveis na primeira chamada, o Apps Script envia pequenos lotes ao motor Python. A fila normal tem prioridade, e o GitHub Actions continua a executar a cada 15 minutos.

## Contrato

- `MAX_POR_EXECUCAO`: quantidade máxima de imóveis reservados em cada execução do Actions; inteiro de 1 a 100, recomendado **20**.
- `LOTE_RECONSTRUCAO`: quantidade máxima acrescentada pela reconstrução por chamada; inteiro de 1 a 100, limitado também por `MAX_POR_EXECUCAO`, recomendado **20**.
- Essas duas propriedades são configuradas **exclusivamente** no projeto **`imoplace-API-PainelPrivado`**, em **Configurações do projeto → Propriedades do script**.
- `RECONSTRUCOES`: nova aba persistente de campanhas. O instalador `instalar()` no painel privado cria a aba sem apagar dados existentes e acrescenta `RECONSTRUCAO_ID` à aba `FILA`.
- Não há Secrets nem Variables novos no GitHub; o workflow continua utilizando a integração já existente.

## Como usar

1. Vindo da 2.3.2.14 ou anterior: rode `instalar()` no PainelPrivado (cria a aba `RECONSTRUCOES` e a coluna
   `FILA.RECONSTRUCAO_ID`) antes de qualquer nova versão de implantação. Atualização completa: `MANUAL_INSTALACAO.md`, parte E.
2. Rode o workflow **uma vez** com "Reconstrução de todos os imóveis" marcada. As execuções agendadas seguintes
   continuam a mesma campanha; deixe desmarcado.
3. Acompanhe na área de sincronização do painel (verificados, enfileirados, confirmados). A aba `RECONSTRUCOES`
   passa a `concluida` ao terminar.

## Comportamento e falhas

- No início é gravado `ID_LIMITE`, que delimita o conjunto de IDs existente. Novos imóveis posteriores ao limite entram pela fila incremental normal.
- `ULTIMO_ID` identifica o último ID inspecionado; a posição da linha da planilha não é utilizada como cursor.
- Se um imóvel já está na fila normal, ele não é duplicado. A edição de um imóvel em processamento continua submetida às verificações de versão já existentes.
- Se uma publicação falhar, a linha permanece em `FILA` e é retomada pela próxima execução. O cursor não volta ao início.
- Se não houver capacidade na fila, a campanha aguarda sem avançar o cursor.
- A reconstrução somente passa a `concluida` quando o cursor alcançou o limite inicial e não restam linhas `RECONSTRUCAO_ID` da campanha.
- `CONFIRMADOS` representa confirmações da campanha; `INSPECIONADOS` representa o avanço do cursor. Esses valores podem ser diferentes quando há alterações normais simultâneas.
- Não há re-download de fotos com SHA-256 válido já reutilizável; o motor existente mantém a lógica incremental.
- Repositório que perdeu fotos (com o `catalogo.json` intacto ou não): a resposta de `pendencias` lista em `aguardando` todos os imóveis que a campanha ainda vai percorrer. O motor publica o lote da vez; os demais saem do site só até a vez deles, sem travar a execução (correções 2.3.2.16 e 2.3.2.21).
- `CONFIRMADOS` conta só imóveis autorizados e concluídos no ACK; ACK desatualizado não conta (correção 2.3.2.16).

## Limitações e homologação

Testes locais comprovam a lógica de fila, lotes, continuidade, falha e ACK idempotente, **não** as cotas reais do Apps Script nem o tempo de processamento por imóvel. Recomenda-se homologar com 25 imóveis de teste e monitorar o consumo de Drive/Sheets. O limite 20 é conservador, mas ajustável.

O conjunto de IDs da campanha é delimitado pelo maior ID na abertura, e os valores das versões são lidos quando cada lote é preparado. A rotina não cria um snapshot imutável de todas as versões. Se o catálogo tiver IDs não monotônicos ou reaproveitados, uma estratégia de snapshot dedicado será necessária antes de usar reconstruções maciças.
