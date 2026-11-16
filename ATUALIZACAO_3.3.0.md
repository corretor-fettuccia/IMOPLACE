# ImoplaceCore 3.3.0 — notícias e avisos no navegador

Este pacote é uma atualização sobre a 3.2.2. A pasta CORE contém o servidor completo; GITHUB contém somente os arquivos alterados e deve ser aplicada por sobre o repositório existente, sem apagar os demais arquivos. Não é um backup do catálogo ou das fotos.

## Entrega

- Os WebP existentes não são reconvertidos, recompactados nem substituídos automaticamente. As URLs e os bytes das fotos legadas permanecem.
- Fotos novas enviadas pelo painel seguem a matriz JXL sem perdas da versão 3.2.2, com marca-d’água antes da codificação. Isso também vale para uma foto nova adicionada a um imóvel antigo; as fotos antigas dele permanecem WebP.
- Módulo Notícias no mesmo painel CORE: rascunhos, publicação, arquivamento, categorias, autor, capa por URL, resumo, texto, título SEO e descrição SEO.
- Blog público em /noticias/, matérias individuais, filtros por categoria, datas, leitura estimada, RSS e links para imóveis.
- HTML estático, canonical, Open Graph, Twitter Card, dados estruturados BlogPosting e sitemap com as matérias publicadas.
- Botão “Notifique-me em caso de atualizações”, por navegador, para todas as notícias ou uma matéria específica. Nenhuma permissão é solicitada automaticamente.
- Cancelamento em /noticias/avisos/; assinaturas expiradas são desativadas pelo publicador.

A publicação não cria notícias fictícias. O blog começa vazio até você cadastrar e publicar a primeira matéria.

## 1. Atualizar o CORE existente

Atualize os arquivos do mesmo Apps Script que já está configurado. Preserve propriedades, planilha e pastas. Execute **instalar()** para acrescentar as abas NOTICIAS, CONFIG_PUSH, PUSH_INSCRICOES e PUSH_ENTREGAS, sem apagar dados. Depois execute **verificarInstalacao()**.

O projeto de destino continua o ID informado: `1vrBc6O0n13mkl0diARfgSKgViaOJMbROG-7IJey43dbGjoJE5qW69z3o`.

Atualize a implantação administrativa existente em **Implantar → Gerenciar implantações → Editar → Nova versão**. Mantenha **Executar como: Eu** e **Acesso: Somente eu**. A URL administrativa atual permanece configurada no GitHub.

Para instalação manual, use IMPORTACAO_MANUAL/Servidor.gs.txt como conteúdo do arquivo Código.gs e os quatro HTML: Painel, PainelCss, PainelJs e NoticiasJs. Não use o arquivo concatenado junto com os .gs separados. O envio por clasp continua disponível em CORE/subir.sh.

## 2. Publicar notícias

Abra **Notícias e avisos → Nova matéria**. O texto aceita parágrafos, subtítulos com `##`, itens com `-` e destaque com `**texto**`. HTML digitado é tratado como texto, para impedir incorporação de código.

A capa usa URL HTTPS de imagem pública em formato compatível; não use JXL/SVG como capa de SEO. Preencha a descrição da capa. Defina o status como Publicado para aparecer no blog; Rascunho e Arquivado não aparecem.

O botão Salvar grava e solicita o workflow de publicação. Se a integração GitHub não estiver configurada, o painel informa que você precisa executá-lo manualmente. O cron existente também verifica as notícias. Uma notícia não depende de haver imóveis na fila.

Marque **Avisar inscritos após esta versão estar publicada no site** apenas nas versões que devem gerar aviso. Atualizações desse registro têm nova versão e podem notificar novamente. O envio só considera matérias publicadas depois da inscrição ou atualizadas após ela; não distribui automaticamente todo o histórico a um novo inscrito.

## 3. Ativar “Notifique-me” no navegador

Notificações precisam receber inscrições de visitantes. Para isso há uma **segunda implantação Web App do mesmo CORE**, dedicada às rotas públicas de inscrição e cancelamento. Não crie outro projeto e não mude a implantação administrativa para pública.

1. No mesmo Apps Script, faça **Implantar → Nova implantação → Aplicativo da Web**.
2. Descrição: **Imoplace — inscrições de avisos**.
3. Executar como: **Eu**; acesso: **Qualquer pessoa**, inclusive sem login. Se sua conta/organização não oferecer acesso anônimo, este cadastro público não funcionará com essa configuração.
4. Copie a URL /exec dessa segunda implantação.
5. Volte ao painel privado: **Notícias e avisos → Avisos no navegador**.
6. Cole a URL pública e clique em **Configurar avisos**. O navegador do administrador gera o par de chaves VAPID P-256. Não é necessário copiar chaves manualmente para o GitHub.
7. Execute **Actions → Publicar ImoPlace — CORE → Run workflow** para publicar o blog e a configuração pública de avisos.
8. Abra o blog no navegador que receberá os avisos. Clique no botão e permita as notificações. Faça uma publicação de teste com a opção de avisar marcada.

A segunda implantação tem POST limitado a inscrição e cancelamento de Web Push. As funções administrativas continuam exigindo o administrador; a rota normal do painel continua protegida. As inscrições e a chave privada ficam apenas nas abas privadas da planilha, acessíveis à conta de serviço já usada no Actions. Não compartilhe a planilha publicamente. O site recebe apenas a chave pública e a URL do cadastro.

Quando atualizar o CORE no futuro, atualize **as duas implantações** para a nova versão: a privada do painel e a pública dos avisos. Preserve as chaves existentes; regenerá-las invalida inscrições anteriores. O botão de configuração não substitui as chaves já cadastradas.

Não há nova propriedade de script obrigatória. A configuração dos avisos é feita pela interface e armazenada nas novas abas privadas. Os Secrets PLANILHA_ID e GOOGLE_CREDENTIALS do GitHub continuam os mesmos.

## 4. Como os avisos são enviados

O Actions compila as notícias e publica o site. Só depois consulta o catálogo público no domínio e confere ID/versão da matéria. Inscritos que acompanham a matéria ou todas as notícias recebem o aviso criptografado por Web Push/VAPID. O clique abre a matéria no próprio domínio.

Cada entrega é registrada por matéria, versão e inscrição. Respostas 404/410 desativam assinaturas expiradas. Há limite de 100 tentativas por execução; o cron existente continua o lote pendente. Falha no serviço de notificações não desfaz a publicação nem marca imóveis já confirmados como erro.

Não há serviço pago de newsletter nem envio de e-mail para visitantes. A entrega usa os serviços de push do próprio navegador. Conexão, permissão, configurações de bateria e políticas do navegador afetam a entrega; não há garantia de aviso instantâneo. Uma falha entre o aceite do provedor e o registro da entrega pode repetir a tentativa; as notificações usam uma tag por matéria.

No iPhone/iPad compatível, adicione o site à tela de início, abra por esse ícone e então permita os avisos. O pacote inclui manifest e ícones para esse uso. Navegadores sem suporte apresentam uma mensagem em vez de simular um cadastro concluído.

## 5. SEO e fotos legadas

WebP já publicado é um formato compatível com buscadores e permanece como estava. Não se cria um JXL dessas fotos nem se gera outro JPEG a partir delas nesta versão.

As fotos novas com matriz JXL continuam gerando formatos de exibição e compartilhamento diretamente dos pixels da matriz, como na 3.2.2. O site não exige que buscadores, redes sociais ou navegadores abram JXL.

As matérias têm SEO próprio, mas o módulo não promete aumento automático de posicionamento. É preciso publicar conteúdo original, útil e bem relacionado aos imóveis e regiões atendidas.

## Verificação

65 testes locais passaram, incluindo preservação de WebP, blog/SEO, exclusão de dados privados, versão pública antes do envio, escopo da inscrição, cancelamento, deduplicação, expiração e criptografia Web Push real com transporte simulado. Nenhum aviso foi enviado a visitantes durante os testes.

O teste ponta a ponta com sua conta Google, a segunda implantação pública e navegadores reais depende dos passos de ativação acima. A conferência visual em desktop/celular não foi concluída neste ambiente. O envio do Apps Script continua sendo feito por você; o pacote não altera as implantações remotas.
