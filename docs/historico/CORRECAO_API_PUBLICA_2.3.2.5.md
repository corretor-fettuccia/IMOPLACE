# Correção da API pública — ImoPlace 2.3.2.5

## Erro corrigido

`Exception: As permissões especificadas não são suficientes para chamar SpreadsheetApp.openById`

A causa era o escopo `spreadsheets.readonly` declarado em `imoplace-API-Publica/appsscript.json`. Para o método `SpreadsheetApp.openById`, o projeto exige `https://www.googleapis.com/auth/spreadsheets`. Isso **não adiciona funções de escrita** ao feed público; o projeto deve continuar com código e acesso rigorosamente limitados à leitura.

## Instalação / atualização (Fedora)

1. Abra `GOOGLE.APPSCRIPT/` no terminal.
2. Rode `./atualizar.sh` para enviar a API corrigida ao mesmo Script ID.
3. No editor do projeto **imoplace-API-Publica**, confirme `PLANILHA_ID` (o mesmo do painel), `SITE_URL` e `CACHE_SEGUNDOS` (opcional, padrão 60).
4. Execute `testarFeed` uma vez; conclua a autorização solicitada pelo Google.
5. Em **Implantar → Gerenciar implantações → Editar**, selecione **Nova versão** e implante.
6. Abra a URL `/exec` e verifique `ok:true` e `total`. O JSON é um snapshot dos imóveis publicados.

## Imagens não listadas no feed

O campo `imagens` é montado apenas com registros de `IMAGENS` cuja `VERSAO_PUBLICADA > 0`. Fotos cadastradas mas ainda não sincronizadas para o GitHub Pages permanecem fora do feed (comportamento intencional). Os arquivos novos chegam ao Actions pela API de integração. **Não altere `VERSAO_PUBLICADA` manualmente**: a confirmação deve ocorrer após a publicação efetiva.

## Limitação de segurança

O escopo OAuth de planilhas é amplo porque `SpreadsheetApp.openById` não oferece permissão de leitura mais restrita neste fluxo. Mantenha a API pública sem funções mutáveis e com projeto separado do painel.
