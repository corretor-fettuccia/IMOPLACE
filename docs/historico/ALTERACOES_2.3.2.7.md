# ImoPlace 2.3.2.7 — Publicação na raiz do domínio via GitHub Actions

## Problema evitado

Em **Settings → Pages**, selecionar `Deploy from a branch → main → /(root)` faz o Pages servir a raiz do **repositório** e não a pasta `site/`. A opção `/site` não aparece nesse modo. O projeto utiliza o modo correto **GitHub Actions**, que publica um artefato distinto.

## Contrato técnico

- No GitHub, `main` contém `.github/workflows`, `scripts/`, `docs/`, `imoplace.json` e `site/`.
- O gerador produz `site/catalogo.json` e `site/imoveis/{slug}-{id}/index.html`.
- `montar_site.py` copia os arquivos públicos de `site/` para `estado/publicacao/` e cria o marcador de publicação.
- `actions/upload-pages-artifact@v4` envia `./estado/publicacao` **como raiz do site**, sem um diretório intermediário.
- `actions/deploy-pages@v4` implanta o artefato. `conferir.py` valida a URL pública antes da confirmação no Apps Script.
- O repositório recebe o commit de `site/` antes do deploy; o diretório `estado/` não é enviado ao Git.

## Proteções adicionadas

- Script `scripts/verificar_publicacao.py` com `--estrutura` e `--artefato`.
- O workflow executa a verificação de estrutura no início e do artefato imediatamente após a etapa 6.
- Testes `scripts/tests/test_pages.py` evitam regressões como `site/site/index.html` e marcador de publicação divergente.
- `GIT-PAGE/verificar.sh` inclui o teste do Pages; o instalador GitHub passa a explicar explicitamente qual Source selecionar.
- Manual principal reescrito com exemplo de caminhos e URL pública.

## O que não mudou

Não houve mudanças no visual do site, cadastro, fotos, contratos das APIs ou nomes de secrets/variables. A configuração do Pages é uma operação na interface do GitHub: um script local **não pode garantir** que a Source remota esteja selecionada corretamente sem acesso à conta. Confira-a manualmente.

## Primeira execução

A rotina de publicação só avança se existir fila de pendências no Apps Script. Cadastre e publique um imóvel de teste, depois execute `Actions → Publicar ImoPlace → Run workflow`. A execução com fila vazia **não publica o site inicial**.
