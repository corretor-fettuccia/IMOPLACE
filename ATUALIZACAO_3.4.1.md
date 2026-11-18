# Imoplace 3.4.1 — formulário de contato dos imóveis

Esta versão do publicador evolui o pacote 3.4.0. Usa o CORE Apps Script 3.4.0, o Monitor GS 1.0 e as implantações existentes de marketing, notícias, avisos e Meta CAPI.

## Páginas dos imóveis

O gerador em `scripts/paginas.py` inclui o formulário nas novas fichas. O renderizador do catálogo em `site/assets/js/imovel.js` mantém o mesmo cartão após atualizar a ficha no navegador. Se a consulta ao catálogo falhar, o formulário usa o ID presente no HTML estático. As 14 fichas desta versão já incluem a integração. A URL antiga do imóvel 1010 continua redirecionando.

No desktop, o cartão fica na coluna direita abaixo do cartão do WhatsApp. No celular, os dois cartões formam um bloco de largura total depois dos dados principais e antes da descrição.

## Form Sender e eventos

O módulo `site/assets/js/imovel-lead.js` usa o endpoint da exportação do ImobfyStudio. Nome, e-mail, telefone e mensagem seguem em FormData. As quatro respostas seguem em `msg`, `complementacaoRapida` e `qualificacao_1` a `qualificacao_4`. O ID da ficha segue em `codigoimovel` e no texto de `produto`, por exemplo `Imoplace - 1004`.

Após uma resposta de sucesso da API, o módulo dispara `generate_lead` nas integrações Google configuradas e `Lead` na integração Meta já configurada. Os eventos levam o identificador público do imóvel. Os dados de contato e a mensagem seguem apenas para o Form Sender.

## Publicação e homologação

O workflow existente **Publicar ImoPlace — CORE** publica as alterações enviadas à branch `main`. Esta versão não altera a planilha, o Apps Script nem o Worker. Para validar o recebimento real, preencha um lead identificado como teste na ficha do imóvel 1004 e confirme o registro do código e das quatro respostas no destino da API. Confira também a ficha em desktop e celular.
