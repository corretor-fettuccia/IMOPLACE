# ImoplaceCore 3.2.1

Atualização compatível com o contrato imoplace-v1, com mídias em seção fixa, links externos em modal e fotos responsivas. Os oito anúncios e as fotos de origem foram preservados.

O administrador está migrando o Apps Script em separado. Os atalhos /adm mantêm a URL anterior até existir a nova implantação. Depois da implantação privada, execute:

```bash
python scripts/configurar_admin.py 'https://script.google.com/macros/s/ID_DA_IMPLANTACAO/exec'
```

Envie as alterações dos dois atalhos ao GitHub. O ID da implantação não é o ID do projeto.

O CORE novo acrescenta MIDIAS_JSON e LINKS_EXTERNOS_JSON às colunas BE e BF de IMOVEIS. Mantenha PLANILHA_ID e GOOGLE_CREDENTIALS atuais no Actions se a planilha e a conta de serviço forem as mesmas. O cliente OAuth Web antigo não é usado pelo publicador.

O workflow instala Pillow e gera JPEG/PNG e WebP no próximo build do catálogo. AVIF e JXL são opcionais via Variables IMOPLACE_AVIF=1 e IMOPLACE_JXL=1. O padrão de ambos é 0. IMOPLACE_IMAGENS_ADAPTATIVAS=0 permite voltar às fotos de origem no próximo build.

As novas mídias ficam visíveis após salvar e publicar o imóvel. Players externos carregam após clique. Outros provedores não autorizados para iframe aparecem como links. Panoramas exigem imagem equiretangular 2:1 por HTTPS com CORS. Fotos de origem permanecem WebP do fluxo existente.

Validação local: 51 testes passaram. A autorização do novo Apps Script e a conferência visual da implantação ainda dependem da instalação na conta administradora. JXL não foi codificado no ambiente local; a opção fica desligada por padrão.
