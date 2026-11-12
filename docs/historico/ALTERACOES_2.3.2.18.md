# Alterações v2.3.2.18 — Preparação para produção

## 1. Preservação de imóveis já publicados (risco corrigido)
Regra nova no motor (`gerador.py`): **imóvel só sai do site por pedido explícito na fila.**
- Sumiu do feed sem pedido (ex.: título apagado direto na planilha): antes, página e fotos eram apagadas; agora
  continua no ar com aviso no log do Actions.
- Download da versão nova falhou com o `catalogo.json` anterior perdido: antes, a pasta com as fotos publicadas
  era apagada; agora a versão no ar é remontada do feed (fotos da versão publicada).
- Alteração não confirmada com catálogo anterior perdido: idem.
- Imóvel na fila como publicado, mas fora do feed por dados incompletos: mantém a versão no ar.
- Testes: +3 em Python, cada um falha na 2.3.2.17.

## 2. Eficiência do feed e da reconstrução
- `lerAba_(nome, ignorar)` lê só as colunas necessárias, em faixas contíguas. O feed público, a integração
  (`pendencias`, `confirmar`, `falha`) e a limpeza deixam de ler `IMAGENS.MINIATURA`.
- Medido no Chrome: ~8.800 caracteres por miniatura. Com 300 imóveis × 20 fotos, cerca de 53 MB de texto a
  menos por leitura, a cada execução de 15 min durante a reconstrução.
- Teste: +1 no Apps Script (resultado idêntico, coluna não lida).

## 3. Segurança da implantação pública
- Homologador movido para `GIT-PAGE/scripts/homologar_acesso.py` (o atalho em `GOOGLE.APPSCRIPT/scripts/` continua).
- Novo passo no workflow, antes da fila: `homologar_acesso.py --ci`. Implantação desprotegida derruba a
  execução; falta de rede só gera aviso. Variable opcional `ESCRITOR_URL` inclui a verificação do painel.
- Novo `docs/HOMOLOGACAO_PRODUCAO.md`: roteiro de liberação (segurança, ciclo do imóvel, falhas, volume).
- Teste de ordem do workflow passa a exigir a homologação antes da sincronização.

Testes: Python 32, Apps Script 34, instalador 2.
