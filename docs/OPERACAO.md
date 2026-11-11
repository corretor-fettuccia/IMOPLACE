# Operação e implantação do ImoPlace 2.3.1

## 1. Implantar os três projetos Apps Script

Os três projetos (`imoplace-API-Publica`, `imoplace-API-PainelPrivado`, `imoplace-API-IntegracaoActions`) são **implantações separadas**. Configurar o mesmo ID da planilha e as propriedades apropriadas a cada projeto. Implantar a API pública como Web App que permita consulta pública; manter a interface privada restrita ao administrador. A integração exige segredo HMAC configurado nas propriedades e valida timestamp e assinatura. Não compartilhar esse segredo com a API pública.

Os arquivos `COMUM/` são as fontes canônicas: execute `python GIT-PAGE/scripts/copiar_comum.py` antes de subir por `clasp`. Defina `.clasp.json` de cada projeto somente na máquina do administrador e **não o publique**.

## 2. Preparar Drive e GitHub

A conta de serviço representada pelo secret `GOOGLE_CREDENTIALS` precisa ter acesso **de leitura** às pastas das imagens no Drive; ela não deve ter permissão de editar o repositório Google. Configure no GitHub Actions:

| Tipo | Nome | Valor |
|---|---|---|
| Secret | `GOOGLE_CREDENTIALS` | JSON da conta de serviço com permissão no Drive |
| Secret | `INTEGRACAO_URL` | URL `/exec` da API de integração |
| Secret | `INTEGRACAO_SEGREDO` | segredo HMAC, idêntico ao da API de integração |
| Variable | `FEED_URL` | URL `/exec` da API pública |
| Variable | `CONFERIR_URL` | URL pública do site, preferencialmente domínio definitivo |

Abra Settings → Pages → Build and deployment → **GitHub Actions**. Habilite o workflow e a permissão de escrita do `GITHUB_TOKEN` para commits, conforme a política do repositório. Confirme o DNS e `site/CNAME`; se não houver domínio próprio, remova CNAME e ajuste `imoplace.json` para o endereço base real.

## 3. Publicação

Workflow `publicar.yml`: cron de 15 minutos e execução manual. Quando a API indicar fila vazia, pula as etapas 2-8. Quando houver pendências, lê feed completo, gera catálogo e páginas, verifica SHA-256 de WebP, gera sitemap/robots/feeds, valida, cria pacote público, faz deploy, verifica publicação, faz commit da árvore pública e confirma versões. Se qualquer etapa falhar, não confirma os imóveis como publicados; a fila é liberada para nova tentativa.

> Atenção: o GitHub Actions não fornece garantia transacional entre publicação no Pages e resposta ao Apps Script. Em falhas de rede após deploy, o estado da API fica pendente e uma próxima execução reconcilia a versão. Alterações simultâneas devem ser protegidas pelo controle de versão na API.

## 4. Testes e inspeção

```bash
cd GIT-PAGE
python -m unittest discover -s scripts/tests -t scripts

# Testes JS opcionais somente no ambiente de desenvolvimento: node scripts/tests/test_apps_script.js
python scripts/validar.py
```

Para testar o motor completo offline, os testes usam dados simulados, sem credenciais. Para integração real, executar o workflow em repositório de homologação com as três APIs implantadas. Não utilizar tokens reais nos logs.

## 5. Endereçamento

Cada anúncio publicado fica em `/imoveis/{slug}-{id}/` independentemente da categoria. O motor mantém redirecionamentos HTML de URLs antigas para títulos alterados e migra URLs legadas `/imovel/{categoria}/{slug}-{id}/` quando elas estiverem presentes no Git. GitHub Pages não oferece redirecionamento HTTP 301 nativo; HTML meta refresh é a alternativa estática usada neste pacote.

## 6. Observações de segurança

- Links para Drive, `driveFileId`, SHA-256 privado, dados do proprietário e registros internos jamais entram em `catalogo.json`.
- Foto anterior do Drive fica preservada após substituição. Definir política de retenção posterior, somente após confirmação e prazo seguro.
- `permitirIndexacao=false` de fábrica, para impedir indexação acidental durante instalação.
- Os feeds Google Merchant e Meta são **arquivos tecnicamente gerados**, não garantem aprovação dessas plataformas para imóveis e não publicam automaticamente anúncios no Marketplace.

Consulte `GOOGLE.APPSCRIPT/GUIA_INSTALACAO.md` no pacote de distribuição para o fluxo `clasp` e os três Web Apps.
