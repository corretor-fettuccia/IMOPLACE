# Alterações v2.3.2.20 (registro feito na 2.3.2.21; detalhes em GO_LIVE_2.3.2.20.md)

- `gerador.py`: falha fechada — imóvel já publicado não sai do catálogo sem baixa explícita (`PUBLICACAO BLOQUEADA`).
- `homologar_acesso.py` / `publicar.yml`: `--exigir-ambos` (ESCRITOR_URL e API_INTEGRACAO_ACTIONS_URL obrigatórios)
  e `--falha-rede-bloqueia`.
- Problema conhecido, corrigido na 2.3.2.21: a trava também foi aplicada a imóveis aguardando a fila, o que impedia a
  reconstrução de recuperar fotos perdidas com o catálogo intacto. Documentação ficou contraditória (ESCRITOR_URL
  "opcional", "falta de rede só avisa", "envie todo o GIT-PAGE").
