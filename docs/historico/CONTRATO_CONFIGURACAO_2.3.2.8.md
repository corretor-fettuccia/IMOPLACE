# ImoPlace v2.3.2.8 — Manual definitivo do GitHub Actions

## O problema corrigido

A execução falhava porque uma orientação anterior reutilizou `FEED_URL` e `INTEGRACAO_URL` no YAML, mas o verificador Python **rejeitava esses nomes**. Agora instalador, workflow, cliente Python, verificador e testes usam **o mesmo contrato**.

## 1. Configuração única (exatamente estes nomes)

No repositório `corretor-fettuccia/IMOPLACE`, abra **Settings → Secrets and variables → Actions**.

**Aba Variables** (não Secrets):

| Nome | Valor | Origem |
|---|---|---|
| `API_PUBLICA_URL` | `https://script.google.com/macros/s/.../exec` | implantação de `imoplace-API-Publica` |
| `API_INTEGRACAO_ACTIONS_URL` | `https://script.google.com/macros/s/.../exec` | implantação de `imoplace-API-IntegracaoActions` |
| `SITE_URL` | `https://imoplace.com.br` | domínio público |

**Aba Secrets** (não Variables):

| Nome | Valor | Origem |
|---|---|---|
| `SEGREDO_INTEGRACAO` | chave aleatória de 64 caracteres hexadecimais | mesmo valor da propriedade no Apps Script `imoplace-API-PainelPrivado` |
| `GOOGLE_CREDENTIALS` | JSON da conta de serviço Google com permissão de leitura no Drive | Google Cloud |

A chave `SEGREDO_INTEGRACAO` já foi exposta em conversa anterior. **Gere outra**, atualize nos dois sistemas e não a cole em mensagens.

### Nomes antigos — migração única

| Excluir após migração | Substituir por | Aba correta |
|---|---|---|
| `FEED_URL` | `API_PUBLICA_URL` | Variables |
| `INTEGRACAO_URL` | `API_INTEGRACAO_ACTIONS_URL` | Variables |
| `INTEGRACAO_SEGREDO` | `SEGREDO_INTEGRACAO` | Secrets |
| `CONFERIR_URL` | `SITE_URL` | Variables |

Os nomes antigos **não são lidos pelo motor**. O workflow novo também não faz remapeamento escondido.

## 2. Subir o código da atualização

Na raiz do repositório local (que corresponde ao conteúdo de `GIT-PAGE/`):

```bash
./verificar.sh
python3 -m unittest discover -s scripts/tests -t scripts
git add .github/workflows/publicar.yml scripts/ instalar.sh verificar.sh docs/ GUIA_INSTALACAO_GITHUB.md VERSAO
git commit -m 'ImoPlace v2.3.2.8: contrato Actions unificado'
git push origin main
```

Se houver arquivos `site/` modificados pela atualização, revise também o `git status` e inclua os arquivos apropriados.

## 3. Configurar o Pages (não selecionar root)

**Settings → Pages → Build and deployment → Source: GitHub Actions.**

A branch `main` contém código e `site/`. O workflow publica `estado/publicacao/` (cópia verificada de `site/`) e o conteúdo aparece diretamente em `/` no domínio. Não usar `Deploy from a branch → main → /(root)` ou `/docs`.

Configure `imoplace.com.br` em **Settings → Pages → Custom domain** e os registros DNS no Registro.br. No modo Actions, o arquivo CNAME não substitui essa configuração.

## 4. Testar

Em **Actions → Publicar ImoPlace v2.3.2.8 → Run workflow**, selecione `main` e execute.

O primeiro script `verificar_configuracao.py --workflow` distingue claramente falta de uma **Variable** de falta de um **Secret**. Se faltar `GOOGLE_CREDENTIALS`, ele para antes de tentar baixar fotos.

- Se passar na validação, `[1/8]` consulta a fila.
- Sem pendências, não há deploy novo (economia de tráfego).
- Com pendências, monta páginas em `site/imoveis/`, valida e publica o artefato.
- Confirma ao Apps Script somente após conferir publicação no Pages.

## 5. Configurações do Apps Script (não misturar)

- `imoplace-API-Publica`: `PLANILHA_ID`, `SITE_URL`, opcional `CACHE_SEGUNDOS`.
- `imoplace-API-PainelPrivado`: `PLANILHA_ID`, Drive, `SEGREDO_INTEGRACAO`, e configurações para o botão Sincronizar Agora.
- `imoplace-API-IntegracaoActions`: `CENTRAL_WRITER_URL` (URL da implantação POST assinada do PainelPrivado).

Não cadastrar os URLs do próprio `/exec` em cada projeto: `API_PUBLICA_URL` e `API_INTEGRACAO_ACTIONS_URL` são **Variables do GitHub Actions**.

## 6. Limites da validação

Os testes são locais, sem usar sua conta Google nem publicar em seu GitHub. A primeira execução real valida permissões do Pages, conta de serviço, comunicação HMAC e acesso ao Drive. Não coloque valores secretos em capturas de log ou mensagens.
