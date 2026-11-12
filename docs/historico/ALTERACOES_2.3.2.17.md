# Alterações v2.3.2.17

Nova função: **marca d'água nas fotos**, aplicada no navegador na conversão para WebP. Guia: `docs/MARCA_DAGUA.md`.

- `PainelJs.html`: `aplicarMarcaDagua()` desenha o texto no canvas antes do `toBlob('image/webp')`; só na foto
  grande, nunca na miniatura. Vale para envio e substituição. Posições: 4 cantos, centro e mosaico.
- `Painel.html`: caixa "Aplicar marca d'água" (marcada por padrão) na aba Imagens, com o resumo da configuração.
- `Config.gs`: `CONFIG.marcaDagua` lê `MARCA_DAGUA_*` com padrão seguro (ativa, domínio do site, inferior direita,
  50%, 4%); valor inválido volta ao padrão. Enviada ao painel junto das opções do formulário.
- Sem mudança em planilha, feed, integração, motor Python, workflow ou site. Não precisa rodar `instalar()`.
- Testes: Apps Script 33 (+2: configuração e desenho). Conferido também em Chrome real: as 4 posições testadas
  geram `image/webp` válido.
