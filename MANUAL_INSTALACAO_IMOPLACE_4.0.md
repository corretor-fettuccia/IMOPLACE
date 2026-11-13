# ImoPlace 4.0 — Manual completo de instalação, restauração e operação

**Edição:** ImoPlace 4.0 · **Fonte:** repositório GitHub `corretor-fettuccia/IMOPLACE` (branch `main` na geração do backup).

> **Escopo do ZIP:** este backup é o código completo do repositório GitHub (publicador Python, workflow, site estático, páginas e fotografias versionadas). **Não inclui** o código-fonte privado do Google Apps Script CORE, a planilha Google Sheets com seus dados, fotos particulares que existam somente no Drive, segredos do GitHub, contas de serviço, DNS ou histórico de execuções. Esses itens exigem backup separado. Não confunda um ZIP do repositório com um desastre-recovery integral do ambiente.

## 1. Arquitetura e estrutura

- `site/`: conteúdo público publicado no domínio, como `index.html`, `catalogo.json`, páginas `imoveis/<slug>/index.html`, imagens públicas, `404.html`, formulário e assets.
- `scripts/`: motor Python do publicador, contrato de feed, montagem de imóveis, importação de imagens do Drive, validação, indexação, verificações e testes.
- `.github/workflows/publicar.yml`: pipeline GitHub Actions, programado a cada 15 minutos e executável manualmente.
- `imoplace.json`: configuração pública básica (nome, domínio, indexação); `CONFIGURACOES` da planilha é a fonte operacional de SITE_URL e LOTE_MAXIMO.
- Google Apps Script CORE: **serviço administrativo privado e separado** deste repositório. Opera sobre a planilha Google Sheets; a integração Actions ↔ Sheets é via OAuth da conta de serviço. Não há necessidade de endpoint Apps Script público para o pipeline atual.

## 2. Requisitos de instalação

1. Conta GitHub com permissão para criar repositório, Secrets/Variables, Actions e GitHub Pages.
2. Projeto Google Cloud com **Google Sheets API** e **Google Drive API** habilitadas.
3. Conta de serviço do Google Cloud (JSON privado), com acesso adequado à planilha e leitura das imagens no Drive.
4. Planilha inicializada pelo CORE, com ao menos as abas `CONFIGURACOES`, `IMOVEIS`, `IMAGENS`, `FILA` e `RESULTADOS`. Estrutura/cabeçalhos devem corresponder à versão do CORE.
5. Fonte e implantação do **Apps Script CORE**, salvaguardadas separadamente.
6. Domínio opcional, por exemplo `imoplace.com.br`, com DNS apontando corretamente para GitHub Pages.
7. Para auditoria local: Python 3.12 ou compatível, Git; Node.js é opcional para verificar JS.

**Segurança:** nunca coloque `GOOGLE_CREDENTIALS`, tokens, arquivo JSON da conta de serviço, número de telefone privado, IDs internos do Drive ou a planilha integral dentro da pasta `site/` ou do GitHub público.

## 3. Restaurar o código no GitHub

1. Baixe o ZIP **fixado em commit** indicado junto à entrega. Guarde também o SHA completo e uma cópia offline.
2. Extraia o ZIP e abra a pasta extraída no terminal.
3. Crie um repositório GitHub vazio, ou prepare uma branch de recuperação em um repositório existente. Evite sobrescrever `main` em produção sem backup.
4. Exemplo para importar em um repositório novo:
   ```bash
   cd IMOPLACE-<commit>
   git init
   git add .
   git commit -m "restore: ImoPlace 4.0"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
   git push -u origin main
   ```
5. Em **Settings → Pages → Build and deployment**, use **Source: GitHub Actions**.
6. Ative o GitHub Actions para o repositório.

**Atenção:** se você restaurar no mesmo repositório e os imóveis mudaram desde o backup, a publicação pode substituir páginas e dados públicos mais recentes. Faça primeiro uma branch e confira o `site/catalogo.json`.

## 4. Restaurar CORE e banco de dados (separadamente)

1. Abra o **Apps Script** do projeto CORE original, ou crie um projeto a partir do seu backup privado de arquivos `.gs`, `.html` e `appsscript.json`. **Esses arquivos não estão neste ZIP do GitHub.**
2. Restaure a planilha Google Sheets com abas e cabeçalhos compatíveis; não recrie uma tabela vazia sobre o banco de produção.
3. Confirme `CONFIGURACOES` com cabeçalhos **CHAVE | VALOR** e linhas:
   - `SITE_URL` = `https://imoplace.com.br` (ou seu domínio final, em HTTPS, sem subcaminho)
   - `LOTE_MAXIMO` = inteiro entre **1 e 100**
4. Confirme que o CORE registra edições/publicações em `FILA`, armazena cadastros em `IMOVEIS`, metadados de fotos em `IMAGENS` e resultados/ACK em `RESULTADOS`.
5. Confirme que os IDs dos arquivos de foto no Drive continuam acessíveis pela conta de serviço. **Não reutilize fotos privadas a partir de uma cópia pública sem autorização.**
6. Mantenha o CORE administrativo com acesso restrito; não configure o Apps Script para permitir operações administrativas anônimas.

## 5. Secrets e Variables no GitHub

Em **Settings → Secrets and variables → Actions**, configure:

| Nome | Tipo | Para quê |
|---|---|---|
| `GOOGLE_CREDENTIALS` | **Repository Secret** | JSON integral e privado da conta de serviço Google; consumido pelo `google-github-actions/auth@v2` |
| `PLANILHA_ID` | **Repository Secret** (recomendado) ou Variable | ID da planilha Google Sheets restaurada |
| `GITHUB_TOKEN` | **Automático** | Token nativo do Actions, não crie nem salve um token pessoal para o pipeline atual |

O workflow requer permissões de job `contents: write`, `pages: write` e `id-token: write`. A autenticação Google solicita scopes `https://www.googleapis.com/auth/spreadsheets` e `https://www.googleapis.com/auth/drive.readonly`. Conceda à conta de serviço apenas os acessos necessários.

Os dados `GOOGLE_ACCESS_TOKEN`, `SITE_URL`, `LOTE_MAXIMO` e `IMOPLACE_CONFIG` são definidos durante a execução: **não é necessário gravá-los manualmente como secrets**.

## 6. Testes antes da primeira publicação

Abra a raiz do projeto:

```bash
python3 -m unittest discover -s scripts/tests -t scripts
python3 scripts/verificar_publicacao.py --estrutura
python3 scripts/validar.py
```

Se houver erros, investigue antes de publicar; não remova verificações para fazer o deploy passar. Testes sem rede não dependem de credenciais do Google.

Para verificar o site estático localmente, sem publicar:

```bash
cd site
python3 -m http.server 8000
```

Acesse `http://localhost:8000/`. O site deve ser testado em HTTP, e não com `file://`, pois o catálogo é carregado com `fetch`. A execução local **não reproduz** as permissões nem os serviços da nuvem.

## 7. Publicar em produção

1. Confira a configuração do domínio, Google APIs e Secrets.
2. Abra **Actions → Publicar ImoPlace — CORE → Run workflow → branch main → Run workflow**.
3. O workflow configura integração, executa testes e consulta a `FILA`.
4. Com fila pendente: reserva itens, monta catálogo, baixa fotos, gera páginas e feeds, valida, faz commit de páginas geradas, publica no GitHub Pages, confere no domínio e registra feedback na planilha.
5. Sem fila, em execução manual: valida e publica o `site/` existente sem confirmar nova versão de imóvel. Útil para ajustes de HTML, CSS, JavaScript, favicon ou 404.
6. A publicação programada ocorre a cada **15 minutos** conforme o cron, mas a programação não garante horário exato.
7. O artefato do Pages usa o nome `github-pages-attempt-<n>`, permitindo repetir uma execução sem confundir dois artefatos de tentativas distintas.

**Não use Re-run jobs em um commit antigo para esperar correções recentes:** um rerun utiliza o commit da execução original. Para instalar uma atualização, inicie um **novo Run workflow na branch main**.

## 8. Verificação pós-instalação

- `https://imoplace.com.br/` ou `/index.html`: home carregando catálogo e cards.
- `https://imoplace.com.br/catalogo.json`: JSON válido, com `total` consistente com `imoveis`.
- `https://imoplace.com.br/icon.png`: favicon compartilhado.
- `https://imoplace.com.br/404-teste-inexistente`: página 404 personalizada, status 404.
- `https://imoplace.com.br/anunciar/`: formulário público.
- `/imoveis/<codigo>/`: página individual, galeria, compartilhar/salvar e mapa Google.
- **Home:** seleção de 10, 20, 50 ou 100 anúncios por página, 10 por padrão, navegação Anterior/Próximo e números das páginas.
- Verifique `robots.txt`, `sitemap.xml`, `merchant-produtos.xml` e `meta-produtos.xml` se presentes e correspondentes às regras do site.
- Verifique na planilha `RESULTADOS` e `VERSAO_PUBLICADA` somente depois do deploy com fila.

**Nota:** com menos de 10 imóveis publicados, a página exibirá apenas os imóveis existentes. As opções de paginação não criam imóveis adicionais.

## 9. Solução de problemas

| Sintoma | Diagnóstico recomendado |
|---|---|
| Home sem imóveis | Confirme `catalogo.json`, status `publicado`, rede e erros de JavaScript. A chamada `tabs.forEach` exige `const tabs=$$('.tabs button')` no `home.js`. |
| Mudança CSS não aparece | Execute novo `Run workflow` na branch correta; verifique deployment e limpe cache do navegador. |
| Erro `Multiple artifacts named github-pages` | Use a versão do workflow com nomes por tentativa. Um rerun antigo pode continuar com o YAML anterior. |
| Erro Google Sheets | Confirme `PLANILHA_ID`, JSON da conta de serviço, permissões na planilha, APIs habilitadas e cabeçalhos. |
| Falha ao baixar fotos | Confirme permissão de Drive, `DRIVE_FILE_ID` e processamento WebP; consulte logs. |
| Página 404 padrão do GitHub | Confirme que `site/404.html` foi incluído no último deploy e que Pages usa GitHub Actions. |
| Botão direito, seleção ou atalhos continuam disponíveis | `site/assets/js/protecao.js` impõe somente restrições de interface; não é mecanismo confiável de segurança. |
| Google Maps vazio | Verifique endereço público disponível, rede e políticas do navegador para iframes externos. |
| Página de imóvel desapareceu | Confira catálogo, versão, status, fila e redirects; não restaure snapshots antigos sobre o site sem verificar. |

## 10. Checklist de backup completo (recuperação de desastre)

Salve em local privado e redundante, **fora do repositório público**:

- [ ] ZIP imutável do GitHub + SHA do commit.
- [ ] Código-fonte e versões da implantação **Apps Script CORE**.
- [ ] Cópia privada da planilha Sheets completa, abas e configurações.
- [ ] Fotografias originais/Drive e respectivos IDs ou mapeamento seguro.
- [ ] JSON da conta de serviço, armazenado de forma criptografada em gerenciador de segredos.
- [ ] Registro dos Secrets e Variables necessários (sem colocá-los no ZIP público).
- [ ] DNS, domínio e ajustes GitHub Pages.
- [ ] Procedimento e teste de restauração em ambiente separado.
- [ ] Registro das versões atuais de cada imóvel e da última publicação concluída.

## 11. Limites desta versão

O nome **ImoPlace 4.0** identifica o **marco de backup/documentação**, não significa mudança automática do contrato CORE, da estrutura da planilha nem migração de dados. Não invente interfaces, campos ou permissões além dos que existem no código.

**Repositório-fonte:** https://github.com/corretor-fettuccia/IMOPLACE
