# Correções v2.3.2.14

Origem: relatório "Auditoria Ponytail — ImoPlace v2.3.2.13" (achados A1 a A6).

## A1 — Repetição de assinatura (alta)
- O cenário "duas tentativas no mesmo segundo" não ocorria na prática (o cliente espera 4s ou mais entre
  tentativas), mas agora é impossível por construção: `Integracao._novo_ts()` garante um carimbo de tempo sempre
  maior que o anterior, então cada tentativa tem assinatura própria e o cache anti-repetição nunca recusa uma
  tentativa legítima. Protocolo HMAC inalterado (sem mudança no Apps Script para isso).
- Junto com a idempotência por `jobId` da 2.3.2.13 (`pendencias` e `confirmar`), uma interrupção de rede é
  retomada pela própria repetição do cliente.

## A2 — Painel e escritor no mesmo projeto (alta)
- Mantido no mesmo projeto, de propósito: o `LockService` só vale dentro de um projeto e é o que impede painel e
  ACK de gravarem por cima um do outro.
- Novo `GOOGLE.APPSCRIPT/scripts/homologar_acesso.py`: testa as implantações **reais** como visitante anônimo
  (GET no escritor não pode mostrar o painel; POST sem assinatura no escritor e na ponte tem de ser recusado pelo
  HMAC; GET na ponte só aceita POST). Não envia segredo nem altera dados. Passo 8a do guia de instalação.

## A3 — Reconstrução sem paginação (média-alta)
- `forcar` agora só coloca na FILA os publicados que não estão nela e segue o fluxo normal: no máximo
  `MAX_POR_EXECUCAO` por execução, o agendamento drena o resto. Removido o caminho especial `_reconstruir`.
- A resposta de `pendencias` traz `aguardando` (IDs que seguem na fila). O motor não bloqueia a publicação por
  falta de fotos desses imóveis; eles entram no site na vez deles.
- Sem reserva no job, o workflow não segue (`tem=false`) e não abre execução vazia em EXECUCOES.

## A4 — Lote com linhas intermediárias (média)
- `gravarLinhas_` grava por blocos de linhas próximas (lacuna máxima de 10 linhas). Linhas 2, 4 e 5000 viram
  dois blocos (2–4 e 5000), não um intervalo de 4.999 linhas.

## A5 — Commit antes do deploy (média)
- Ordem mantida, de propósito, e documentada em `docs/OPERACAO.md`: repositório à frente do site se resolve sozinho
  na próxima execução; repositório atrás do site bloquearia o motor. O commit nunca vale como "publicado": só o
  ACK depois da conferência no domínio. Novo teste em `test_pages.py` impede inverter a ordem.

## A6 — Mensagem Variable × Secret (baixa)
- `integracao.py`: a mensagem manda configurar `API_INTEGRACAO_ACTIONS_URL` em **Variables**.

## Testes
- Python 26 (+3), Apps Script 26 (+3), instalador 5 (+3 do homologador). Os novos falham na 2.3.2.13.
