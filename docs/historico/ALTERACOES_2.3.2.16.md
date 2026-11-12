# Correções v2.3.2.16

Origem: auditoria Ponytail da v2.3.2.15. A reconstrução progressiva da 2.3.2.15 foi mantida.

1. **Reconstrução travava com repositório perdido (regressão).** A resposta de `pendencias` só listava em
   `aguardando` o que estava na FILA; os imóveis que a campanha ainda ia percorrer não entravam, o motor exigia as
   fotos deles e a execução falhava sempre (o lote com erro ocupava a fila e o próximo nunca entrava). Agora
   `aguardando` inclui os publicados entre o cursor e o `ID_LIMITE` da campanha ativa, também na repetição do mesmo
   job. Filtro único `restantesReconstrucao_()` usado pelo lote e pelo aviso.
2. **Guia de atualização** (`docs/RECONSTRUCAO_PROGRESSIVA.md`, sem número de versão no nome): substituir só
   `publicar.yml` e `scripts/`; nunca `site/catalogo.json` nem `site/imoveis/`.
3. **Ordem obrigatória em destaque:** `instalar()` no PainelPrivado antes de qualquer nova versão de implantação.
4. **Contador `CONFIRMADOS`:** conta só imóveis autorizados e concluídos no ACK (linha da FILA encerrada e no site).
   ACK desatualizado não conta, e a confirmação posterior conta uma vez.
5. Removida `statusReconstrucao()`, sem uso (o painel usa `Sincronizar.gs`).
6. Versão: `VERSAO` da raiz corrigido, notas da 2.3.2.15 registradas em `docs/historico/`, rótulos atualizados.

Testes: Apps Script 31 (+2, ambos falham na 2.3.2.15), Python 26, instalador 5.
