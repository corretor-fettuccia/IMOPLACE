# ImoPlace — Manual de instalação

Este é o **único** roteiro de instalação. Siga as partes na ordem. Os demais documentos são referência:
`OPERACAO.md` (como funciona no dia a dia), `HOMOLOGACAO_PRODUCAO.md` (liberação), `MARCA_DAGUA.md`,
`RECONSTRUCAO_PROGRESSIVA.md` e `CRIAR_GOOGLE_CREDENTIALS.md` (detalhes da credencial do Drive).

## Visão geral

```text
Você ──► Painel (Apps Script PainelPrivado) ──► Planilha + Drive (fotos)
                                                     │
GitHub Actions (a cada 15 min) ──► Ponte (IntegracaoActions) ──► Escritor central (PainelPrivado, POST assinado)
            │            └──────► API Pública (feed dos publicados)
            └──► baixa fotos do Drive (conta de serviço, só leitura) ──► GitHub Pages (seu domínio)
```

| Peça | Onde | Para quê |
|---|---|---|
| `imoplace-API-PainelPrivado` | Apps Script | painel, planilha, fotos; também o **escritor central** que recebe o GitHub |
| `imoplace-API-Publica` | Apps Script | feed somente leitura dos imóveis publicados |
| `imoplace-API-IntegracaoActions` | Apps Script | ponte entre o GitHub e o escritor central; não lê a planilha |
| Conta de serviço Google | Google Cloud | o GitHub lê as fotos do Drive, só leitura |
| Repositório GitHub | GitHub | código do motor (`scripts/`), workflow e o site (`site/`) publicado no Pages |

Pacote: `GOOGLE.APPSCRIPT/` fica **só no seu computador**; o **conteúdo** de `GIT-PAGE/` vira a raiz do repositório.

## Pré-requisitos (uma vez)

- Computador com Linux (os scripts foram feitos no Fedora), `python3`, `git`, `node`/`npm`.
- `clasp`: `npm install -g @google/clasp`, depois `clasp login` com a conta Google que será a dona de tudo.
- Ative a **Google Apps Script API** em https://script.google.com/home/usersettings.
- Conta GitHub. Em plano gratuito, o GitHub Pages exige repositório **público** (dados privados nunca vão ao
  repositório; os logs públicos não mostram segredos se você seguir a parte C).
- Domínio (ex.: `imoplace.com.br`) com acesso ao DNS (ex.: Registro.br).
- Guarde a pasta `.instalacao-local/` que os scripts criam: ela tem o segredo e as URLs, e **nunca** vai ao Git.

---

## Parte A — Google Apps Script

### A1. Criar os três projetos e enviar o código
```bash
cd GOOGLE.APPSCRIPT
./instalar.sh
```
Para cada projeto o script pede: crie em https://script.google.com/home/projects/create, dê **exatamente** o nome
pedido, abra Configurações do projeto e copie o **ID do script** (não é URL nem ID de implantação). O script envia
o código (`clasp push`). Ao final ele chama `./continuar_configuracao.sh`, que guia os passos A2 a A5
(se parar, rode-o de novo: ele retoma).

### A2. Planilha, pastas e gatilhos
No editor do **PainelPrivado**, escolha a função `instalar` e clique em Executar; autorize Planilhas e Drive.
Ela cria (ou reaproveita) a planilha "ImoPlace — Banco de dados", as pastas `ImoPlace/Imoveis` no seu Drive, as
propriedades `PLANILHA_ID`, `PASTA_RAIZ_ID`, `PASTA_IMOVEIS_ID`, `ADMIN_EMAIL`, `PROXIMO_ID` e os gatilhos diários
(limpeza às 4h, reserva da sincronização às 6h). Pode rodar de novo sem perder dados.

### A3. Segredo da integração
O `continuar_configuracao.sh` gera o segredo em `GOOGLE.APPSCRIPT/.instalacao-local/SEGREDO_INTEGRACAO.txt`
(64 caracteres, só você lê). No PainelPrivado > Configurações do projeto > **Propriedades do script**, crie
`SEGREDO_INTEGRACAO` com esse valor. O mesmo valor vai no GitHub (parte C).

### A4. API Pública
No projeto **Publica**, Propriedades do script: `PLANILHA_ID` (o mesmo do PainelPrivado) e `SITE_URL`
(`https://imoplace.com.br`). Execute `testarFeed` no editor e autorize.

### A5. Implantações (Implantar > Nova implantação > Aplicativo da Web, sempre "Executar como: Eu")

| Projeto | Quem pode acessar | A URL `/exec` vira |
|---|---|---|
| Publica | Qualquer pessoa | `API_PUBLICA_URL` (GitHub) |
| PainelPrivado — painel | **Somente eu** | endereço do seu painel (guarde nos favoritos) |
| PainelPrivado — escritor (2ª implantação) | Qualquer pessoa | `ESCRITOR_URL` (GitHub) e `CENTRAL_WRITER_URL` (ponte) |
| IntegracaoActions — ponte | Qualquer pessoa | `API_INTEGRACAO_ACTIONS_URL` (GitHub) |

O escritor é público, mas só aceita chamadas assinadas com o segredo, e o painel recusa quem não é o `ADMIN_EMAIL`
(o passo A7 comprova). O script salva as URLs em `.instalacao-local/URLs_APPSCRIPT.txt`.

### A6. Ligar a ponte ao escritor
```bash
./configurar_integracao.sh
```
Ele guia a criação de `CENTRAL_WRITER_URL` (URL do **escritor**, não a da ponte) nas Propriedades do projeto
**IntegracaoActions**. Depois, no editor da ponte, execute `verificarConfiguracaoIntegracao`: precisa registrar
`[OK] CENTRAL_WRITER_URL configurada`.

### A7. Homologar o acesso anônimo (obrigatório)
```bash
python3 scripts/homologar_acesso.py
```
Tem de terminar em **APROVADO**. Se aparecer `CRÍTICO`, retire a implantação pública do PainelPrivado na hora.

### A8. Opcionais (Propriedades do PainelPrivado)
`MAX_POR_EXECUCAO` e `LOTE_RECONSTRUCAO` (padrão 20), `MARCA_DAGUA_*` (ver `MARCA_DAGUA.md`). Sem eles, valem os padrões.

---

## Parte B — Credencial do Drive para o GitHub

1. Em https://console.cloud.google.com/ crie um projeto, habilite a **Google Drive API**, crie uma
   **conta de serviço** e uma chave **JSON** (passo a passo em `CRIAR_GOOGLE_CREDENTIALS.md`).
2. No Drive, compartilhe a pasta **`ImoPlace/Imoveis`** (a de `PASTA_IMOVEIS_ID`) com o e-mail da conta de serviço,
   como **Leitor**.
3. Guarde o JSON fora do repositório; ele vai inteiro no Secret `GOOGLE_CREDENTIALS` (parte C).

---

## Parte C — GitHub

### C1. Repositório e primeiro envio
Crie o repositório (público) e envie **o conteúdo** de `GIT-PAGE/` para a raiz, incluindo arquivos ocultos
(`.github/`, `site/.nojekyll`). Na raiz devem ficar `.github/workflows/publicar.yml`, `imoplace.json`, `scripts/`,
`site/`. Antes do commit:
```bash
./verificar.sh
```
Opcional: `./instalar.sh` gera `.instalacao-local/GITHUB_CONFIGURACAO.txt` com a lista do passo C3 (não envie essa pasta).

### C2. Pages e domínio
Settings > Pages > Build and deployment > Source: **GitHub Actions** (nunca "Deploy from a branch").
Custom domain: o seu domínio; configure o DNS conforme a tela do GitHub e marque **Enforce HTTPS** quando liberar.
`site/CNAME` e `urlPublica` em `imoplace.json` devem ter o mesmo domínio.

### C3. Secrets e Variables (Settings > Secrets and variables > Actions)

| Aba | Nome | Valor |
|---|---|---|
| Variables | `API_PUBLICA_URL` | `/exec` da Publica |
| Variables | `SITE_URL` | `https://imoplace.com.br` |
| Secrets | `API_INTEGRACAO_ACTIONS_URL` | `/exec` da ponte |
| Secrets | `ESCRITOR_URL` | `/exec` do escritor (PainelPrivado, implantação pública) — **obrigatório** |
| Secrets | `SEGREDO_INTEGRACAO` | conteúdo de `.instalacao-local/SEGREDO_INTEGRACAO.txt` |
| Secrets | `GOOGLE_CREDENTIALS` | conteúdo inteiro do JSON da parte B |

Variables aparecem nos logs públicos; por isso as URLs não públicas vão em Secrets. Sem `ESCRITOR_URL` ou
`API_INTEGRACAO_ACTIONS_URL`, a execução para com `ERRO: Configure ESCRITOR_URL e API_INTEGRACAO_ACTIONS_URL`.

### C4. Token do GitHub para o painel
Necessário para o botão "Sincronizar agora" e para manter o agendamento ativo (o GitHub desliga workflows
agendados após 60 dias sem atividade; o gatilho diário das 6h reativa).
1. GitHub > Settings (da sua conta) > Developer settings > Personal access tokens > **Fine-grained tokens** > Generate.
2. Repository access: **Only select repositories** > este repositório.
3. Permissions > Repository permissions > **Actions: Read and write**. Nada mais.
4. Anote a data de expiração e renove antes dela.
5. No PainelPrivado, Propriedades do script: `GITHUB_REPO` = `dono/repositorio`, `GITHUB_TOKEN` = o token.

### C5. Primeira execução
Actions > **Publicar ImoPlace** > Run workflow > `main`, **forçar desmarcado**. Com a fila vazia, a execução fica
verde sem publicar nada; o passo "Homologar acesso anônimo" deve mostrar os `[OK]`.

---

## Parte D — Homologação e liberação

Siga `HOMOLOGACAO_PRODUCAO.md` com 1 a 3 imóveis de teste e `permitirIndexacao: false`. Com os blocos A, B e C
marcados, ligue `"permitirIndexacao": true` em `imoplace.json`, envie ao repositório e rode o workflow.

---

## Parte E — Atualizar para uma versão nova

1. Backup da planilha (Arquivo > Fazer uma cópia).
2. Leia `docs/ALTERACOES_<versão>.md`: ele diz quais implantações precisam de nova versão e se precisa `instalar()`.
3. Google: `cd GOOGLE.APPSCRIPT && ./atualizar.sh`. Se as notas pedirem, rode `instalar()` no PainelPrivado
   **antes** de criar as novas versões. Depois: Implantar > Gerenciar implantações > editar > **Nova versão**.
4. GitHub: substitua **somente** `.github/workflows/publicar.yml`, `scripts/`, `docs/` e os arquivos da raiz
   (`VERSAO`, `verificar.sh`, `instalar.sh`, `COMECE_AQUI.md`). **Nunca** substitua nem sincronize com "apagar
   extras" `site/catalogo.json` e `site/imoveis/`: são o que está publicado. Arquivos de `site/assets/` e
   `site/index.html` só se as notas pedirem. Rode `./verificar.sh`, faça commit e push.
5. Rode o workflow manualmente (forçar desmarcado) e confira o painel.

---

## Referência — todas as configurações

| Projeto (Propriedades do script) | Nome | Obrigatório | Origem / padrão |
|---|---|---|---|
| PainelPrivado | `PLANILHA_ID`, `PASTA_RAIZ_ID`, `PASTA_IMOVEIS_ID`, `ADMIN_EMAIL`, `PROXIMO_ID` | sim | `instalar()` |
| PainelPrivado | `SEGREDO_INTEGRACAO` | sim | A3 |
| PainelPrivado | `GITHUB_REPO`, `GITHUB_TOKEN` | sim em produção | C4 |
| PainelPrivado | `SITE_URL`, `GITHUB_WORKFLOW`, `GITHUB_BRANCH`, `MAX_FOTO_MB`, `MAX_FOTOS` | não | `instalar()` grava padrões |
| PainelPrivado | `MAX_POR_EXECUCAO`, `LOTE_RECONSTRUCAO`, `MARCA_DAGUA_*` | não | 20, 20, ver `MARCA_DAGUA.md` |
| Publica | `PLANILHA_ID`, `SITE_URL` | sim | A4 |
| Publica | `CACHE_SEGUNDOS` | não | 60 |
| IntegracaoActions | `CENTRAL_WRITER_URL` | sim | A6 |

GitHub: tabela do passo C3. `imoplace.json`: `urlPublica`, `permitirIndexacao`, `nome`, `ano`.

## Problemas frequentes

| Mensagem | Causa | O que fazer |
|---|---|---|
| `ERRO: Configure ESCRITOR_URL e API_INTEGRACAO_ACTIONS_URL` | Secret faltando | C3 |
| `CENTRAL_WRITER_URL ausente ou inválida` | ponte sem a URL do escritor | A6 |
| `Escritor central devolveu página em vez de JSON` | implantação do escritor não está como "Qualquer pessoa" | A5 |
| `Assinatura inválida` | `SEGREDO_INTEGRACAO` diferente no PainelPrivado e no GitHub | copie o mesmo arquivo nos dois (A3, C3) |
| `CRÍTICO: GET anônimo no escritor serviu o painel` | painel exposto | retire a implantação pública e refaça A5/A7 |
| `Drive recusou … (HTTP 403)` | pasta não compartilhada com a conta de serviço | B2 |
| `GOOGLE_ACCESS_TOKEN ausente` | Secret `GOOGLE_CREDENTIALS` faltando ou inválido | B, C3 |
| `Aba FILA sem as colunas …` | esquema antigo na planilha | rode `instalar()` no PainelPrivado |
| `PUBLICACAO BLOQUEADA: imóvel … ficaria fora do catálogo` | imóvel no ar perdeu dados ou fotos sem pedido de baixa | corrija os dados na planilha, restaure as fotos, use "Baixar" no painel, ou rode o workflow com **forçar** (reconstrução) |
| `foto(s) publicada(s) ausente(s)` | repositório perdeu fotos | rode o workflow com **forçar** (reconstrução em lotes) |
| `site com … MB: passa do limite de 1 GB` | limite do GitHub Pages | menos fotos ou outro armazenamento (`OPERACAO.md`) |
| `#ERROR!` numa célula da planilha | texto gravado antes da proteção contra fórmulas | corrija o texto pelo painel |
| Aba LOG com `reativar-workflow:erro` | token vencido ou sem permissão | C4 |
| `Outra gravação está em andamento` | painel e GitHub gravando ao mesmo tempo | tente de novo em segundos |
