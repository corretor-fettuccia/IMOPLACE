# Correções v2.3.2.15 (registro feito na 2.3.2.16)

- Reconstrução completa vira campanha persistente na nova aba `RECONSTRUCOES` (cursor `ULTIMO_ID`, `ID_LIMITE`,
  contadores). Cada execução acrescenta um lote (`LOTE_RECONSTRUCAO`) à FILA; alterações normais têm prioridade.
- Nova coluna `FILA.RECONSTRUCAO_ID`; exige rodar `instalar()` no PainelPrivado antes do código novo.
- `MAX_POR_EXECUCAO` validado (inteiro 1–100) e padrão alterado de **30 para 20**.
- Painel mostra o progresso da campanha na área de sincronização.
- Guia: `docs/RECONSTRUCAO_PROGRESSIVA.md`.
- Problemas conhecidos, corrigidos na 2.3.2.16: reconstrução travava com repositório perdido; contador
  `CONFIRMADOS` somava ACK desatualizado; guia mandava substituir todo `GIT-PAGE/` (incluindo `site/`).
