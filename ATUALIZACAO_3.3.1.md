# ImoplaceCore 3.3.1 — formato padrão nas propriedades

## Propriedade

| Nome | Padrão | Valores aceitos |
| --- | --- | --- |
| FORMATO_PADRAO_IMAGENS | webp | webp, jxl, jpeg, png |

A escolha é feita no Apps Script. A imagem recebe a marca-d'água antes da codificação no formato escolhido. A preferência também é sincronizada com o publicador para ordenar os formatos do picture: com webp, WebP é oferecido antes de JXL.

As fotos existentes não são substituídas nem convertidas só porque você mudou a propriedade. O arquivo no Drive mantém seu formato original; a nova escolha vale para os próximos envios e substituições. A preferência de exibição pode mudar na publicação seguinte sem regravar a matriz.

## Gerar o CORE completo sem editar código

Este pacote é uma atualização sobre a versão 3.3.0. Ele inclui um atualizador local, não contém um banco de dados nem cópia das suas fotos.

1. Extraia este pacote e abra **ATUALIZAR-CORE-3.3.1.html** em um navegador atual.
2. Selecione o arquivo **ImoplaceCore.3.3.0-ATUALIZACAO.zip** que você já possui.
3. Clique em **Gerar CORE 3.3.1** e baixe o ZIP completo gerado.
4. Envie os arquivos de CORE ao mesmo projeto Apps Script, preservando as propriedades existentes.
5. Execute **instalar()**. A nova propriedade será criada com **webp** se ainda não existir.
6. Atualize a implantação privada para a nova versão. Se utiliza a implantação pública de avisos, atualize-a também.
7. Recarregue o painel e publique pelo Actions.

O atualizador processa os arquivos no seu navegador, sem upload, login nem chamadas externas. Preserva os demais arquivos do CORE e a configuração clasp existente. Para arquivos que não correspondam à estrutura conhecida da versão 3.3.0, interrompe a atualização.

### Alternativa pelo terminal

Na pasta deste atualizador:

~~~bash
node aplicar-core-3.3.1.mjs /caminho/para/CORE
~~~

O aplicador valida os arquivos antes de escrever, salva um backup em uma pasta irmã e acrescenta os complementos. Depois envie CORE normalmente e execute instalar(). O comando não envia código para o Google ou GitHub.

### Atualizar pelo editor, usando servidor concatenado

Se você já usa Servidor.gs.txt em um único arquivo Código.gs e prefere não usar clasp, use o gerador HTML para obter o CORE completo. Importe o conjunto completo de arquivos separados, removendo o servidor concatenado antigo para não duplicar as funções. Preserve a planilha e as propriedades.

Outra opção é adicionar FormatoImagens331.gs e FormatoImagens331Js.html ao projeto e aplicar as alterações abaixo ao servidor atual:

- Em Painel.html, acrescente `<?!= incluir_('FormatoImagens331Js') ?>` imediatamente antes de `</body>`.
- Na função sincronizarConfiguracaoOperacional_, acrescente ao objeto dados a chave FORMATO_PADRAO_IMAGENS: normalizarFormatoImagem331_(propriedade_('FORMATO_PADRAO_IMAGENS','webp')).
- Em Imoveis.gs, na clonagem, substitua a escolha limitada a jxl/webp por normalizarFormatoImagem331_(f.FORMATO || 'webp'), para preservar também JPEG/PNG ao clonar.
- Execute **instalarFormatoImagens331()** uma vez. Esse modo manual usa o inicializador próprio; o aplicador automático também inclui a chamada no instalador principal.

Não redefina o vínculo Cloud nem crie cliente OAuth para esta atualização.

## Alterar depois

Em Configurações do projeto → Propriedades do script, altere FORMATO_PADRAO_IMAGENS para webp, jxl, jpeg ou png. JPG também é aceito como alias de jpeg.

Recarregue o painel ou execute instalarFormatoImagens331() e publique pelo Actions. Não é necessário alterar flags do GitHub para escolher o formato padrão. As opções avançadas IMOPLACE_AVIF e IMOPLACE_JXL continuam sendo opções separadas do publicador.

## Compatibilidade

- WebP: padrão para novos arquivos. O painel usa WebP diretamente, sem carregar o codificador JXL.
- JPEG: transparência é composta sobre branco; o arquivo é salvo com MIME image/jpeg.
- PNG: preserva transparência e não utiliza compressão com perdas.
- JXL: usa o codificador sem perdas existente, depois da aplicação da marca.
- JPEG e WebP são formatos com perdas: nesta versão são codificados uma única vez no envio, diretamente dos pixels da imagem com a marca, sem cascata intermediária.
- Resolução, limite de tamanho e regras de marca-d'água existentes são mantidos. Esta atualização não recupera detalhes perdidos nos arquivos antigos.

No site, imagens JPEG/PNG/JXL recebidas são preservadas como matrizes. Há um WebP de compatibilidade para o contrato público atual e variantes derivadas diretamente da matriz. O SEO mantém fallback rastreável e JPEG de compartilhamento; escolher JXL não torna JXL obrigatório para buscadores ou redes sociais.

Se o navegador não conseguir gerar o MIME solicitado, o painel informa erro em vez de salvar PNG com extensão incorreta.

## Conteúdo e validação

FormatoImagens331.gs e FormatoImagens331Js.html são complementos do CORE 3.3.0; não substituem o servidor inteiro sozinhos. O ZIP completo do CORE é gerado pelo atualizador a partir do seu pacote anterior.

Foram verificadas nesta preparação a sintaxe JavaScript, a propriedade padrão, normalização de valores, quatro assinaturas, roteamento de upload, seleção dos quatro formatos com codificadores simulados, rejeição de MIME incompatível, ordem WebP/JPEG no picture, idempotência do aplicador e integridade/UTF-8 de um ZIP sem compressão. Isso não equivale a um teste real de navegador ou da sua implantação.

O workflow “Verificar formatos 3.3.1” executa no GitHub a compilação Python e os testes completos, incluindo JPEG/PNG reais, preservação de matriz e extração DEFLATE do gerador. Verifique sua conclusão antes de instalar. Ele não usa credenciais Google e não publica o site.

O Apps Script e suas propriedades ainda precisam ser atualizados por você; esta entrega não modifica diretamente sua conta.
