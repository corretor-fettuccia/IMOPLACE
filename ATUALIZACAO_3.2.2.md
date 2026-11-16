# ImoplaceCore 3.2.2 — matriz JXL e SEO compatível

## O que mudou

Novas fotos recebem marca d’água nos pixels, no navegador, e são codificadas diretamente em **JXL sem perdas**, sem JPEG/WebP intermediário e sem redução automática de resolução. O Drive guarda essa matriz. O publicador decodifica a matriz e gera cada formato diretamente dos mesmos pixels: JPEG/PNG, WebP, JXL responsivo e AVIF opcional.

A marca continua respeitando a configuração existente e a caixa de ativação do painel; você pode desmarcá-la para plantas e documentos. A miniatura é uma prévia WebP com a marca já aplicada, não a matriz usada para conversões.

## SEO e compartilhamento

| Uso | Formato utilizado |
| --- | --- |
| img src e fallback rastreável | JPEG para fotos; PNG quando há transparência; WebP legado se a foto ainda não tem variantes |
| picture/srcset | JXL, AVIF quando ativado, WebP e fallback compatível |
| Open Graph e Twitter Card | JPEG próprio em 1200 × 630, sem cortar a fotografia ou sua marca |
| Dados estruturados | URLs de JPEG/PNG; WebP para fotos legadas sem variantes |
| Sitemap de imagens | URLs de formatos compatíveis, sem depender de JXL |
| Feeds comerciais existentes | URLs das imagens compatíveis, sem JXL como imagem obrigatória |

Isso mantém alternativas para buscadores, redes sociais e navegadores. Não significa garantia de indexação, rich results ou aceitação por todos os serviços; os formatos são oferecidos com fallback, URLs estáveis, texto alternativo e HTML estático.

## Instalação sobre a 3.2.1 existente

O GitHub deve receber a atualização do publicador e os arquivos de `site/assets/vendor/jxl-1.3.0/` **antes de usar o painel novo para enviar fotos**. Esses arquivos incluem o codificador WASM, hospedado no próprio site, sem CDN de terceiros.

1. No GitHub, execute **Actions → Publicar ImoPlace — CORE → Run workflow** para publicar também os arquivos do codificador. Se houver erro, não ative o envio novo até corrigir a publicação.
2. Atualize os arquivos do mesmo projeto Apps Script onde a 3.2.1 já funciona. O `.clasp.json` aponta para o ID informado: `1vrBc6O0n13mkl0diARfgSKgViaOJMbROG-7IJey43dbGjoJE5qW69z3o`.
3. Preserve todas as propriedades existentes. **Não existe nova propriedade obrigatória.**
4. Execute **instalar()** no projeto já configurado. Ele acrescenta a coluna **FORMATO** ao fim de IMAGENS e mantém o banco existente. Execute **verificarInstalacao()** depois.
5. Atualize a implantação Web App existente em **Implantar → Gerenciar implantações → Editar → Nova versão**. Mantenha executar como você e acesso somente você. Ao editar a implantação existente, a URL /exec pode ser mantida; se criar outra, atualize os atalhos do GitHub.
6. Envie uma foto de teste, confira a marca e o arquivo `.jxl` no Drive, publique o imóvel e verifique a ficha.

Se estiver instalando em um projeto vazio, primeiro copie as propriedades e execute **migrarInstalacaoExistente()**, como na migração anterior. Não rode instalar() sem os IDs atuais se quiser reaproveitar o banco.

### Envio por clasp

Na pasta CORE:

```bash
bash subir.sh
```

Ou use IMPORTACAO_MANUAL/Servidor.gs.txt como conteúdo do arquivo Código.gs e copie os três HTML. Não importe simultaneamente o texto concatenado e os .gs individuais.

## Fotos e limites

Fotos WebP já existentes continuam funcionando e preservam as URLs publicadas. Elas não recuperam qualidade por serem recodificadas. Para obter uma matriz nova com a qualidade disponível no arquivo de origem, substitua a foto enviando novamente o original.

Cada imagem aceita até 50 megapixels. O limite de tamanho já configurado em MAX_FOTO_MB é respeitado, com teto de 20 MB por arquivo. Uma matriz sem perdas pode ser maior que o WebP anterior: se sua propriedade atual for 8, ela continuará em 8; você pode ajustar MAX_FOTO_MB para até 20. Não há redução silenciosa de qualidade ou resolução para caber no limite.

A preservação é dos pixels **depois** da decodificação e marca no canvas sRGB de 8 bits. Não se promete preservar o arquivo original, metadados de câmera, RAW, HDR ou toda a profundidade de uma imagem de 16 bits. Para fotos comuns, evita a cadeia de recompressões com perdas.

A foto de entrada precisa ser aberta pelo navegador. JPG/PNG usuais funcionam; se ele não abrir um arquivo JXL/HEIC, use o original em um formato que esse navegador consiga abrir. O encoder gera JXL mesmo que o navegador não consiga exibir JXL.

O Drive mantém a matriz e o site/repositório conserva uma cópia marcada dessa matriz para builds reproduzíveis. As versões públicas compatíveis são derivadas dela. A credencial do Actions permanece com Drive somente leitura.

## Opções existentes

IMOPLACE_AVIF=1 ativa AVIF, quando disponível. Fotos nativas JXL recebem variantes JXL diretamente da matriz, sem depender de IMOPLACE_JXL; essa variável serve para gerar JXL adicional também a partir de fotos legadas, sem recuperar seus detalhes perdidos. IMOPLACE_IMAGENS_ADAPTATIVAS=0 desativa as variantes na exibição após novo build, preservando o fallback WebP público.

## Verificação e limites de teste

Foram testados o codificador WASM utilizado pelo painel e um decodificador libjxl independente, com igualdade exata dos pixels RGBA, incluindo transparência e uma marca desenhada. Também há teste integrado de Drive simulado → matriz → formatos → HTML/SEO → preservação da matriz na publicação seguinte.

A conferência visual no painel real, no celular e em redes sociais continua necessária após a instalação. O pacote não altera remotamente o Apps Script. O codificador no navegador pode consumir memória e tempo em fotografias grandes.
