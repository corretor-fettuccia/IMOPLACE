# Operação e implantação do ImoPlace

## 1. Instalação e configuração

Tudo em `MANUAL_INSTALACAO.md` (partes A a C, tabela de configurações e problemas frequentes). Este documento
descreve o funcionamento.

## 3. Publicação

Workflow `publicar.yml`: cron de 15 minutos e execução manual. Quando a API indicar fila vazia, pula as etapas 2-8. Quando houver pendências, lê feed completo, gera catálogo e páginas, verifica SHA-256 de WebP, gera sitemap/robots/feeds, valida, cria pacote público, faz commit da árvore pública, faz deploy, verifica publicação e confirma versões. Se qualquer etapa falhar, não confirma os imóveis como publicados; a fila é liberada para nova tentativa.

**Preservação do que está publicado.** Um imóvel só sai do site por pedido explícito na fila (Baixar, Arquivar ou Rascunho no painel). Se ele some do feed sem pedido (ex.: título apagado direto na planilha), se o download da versão nova falha ou se há alteração ainda não confirmada, o site mantém a versão que já estava no ar (remontada do feed se o `catalogo.json` anterior se perdeu), com aviso no log. Se nem isso for possível porque faltam as fotos da versão no ar, a execução **para** com `PUBLICACAO BLOQUEADA` e nada é publicado: o site continua como estava até você corrigir os dados, restaurar as fotos, usar "Baixar" ou rodar a reconstrução. Única exceção: imóvel que já está na fila ou na campanha de reconstrução sai do site temporariamente e volta na vez dele, quando as fotos são baixadas de novo do Drive.

**Vigilância da implantação pública.** Toda execução roda `scripts/homologar_acesso.py` antes de tocar na fila: chamadas sem assinatura têm de ser recusadas pela ponte e pelo escritor, e o painel não pode aparecer para anônimos. `ESCRITOR_URL` e `API_INTEGRACAO_ACTIONS_URL` são obrigatórios. Implantação desprotegida, Secret faltando ou falta de rede param a execução antes de reservar a fila (nada se perde; a execução seguinte, 15 minutos depois, tenta de novo).

**Agendamento sempre ativo (desde 2.3.2.19).** Em repositório público, o GitHub desliga workflows agendados após 60 dias sem atividade, e aqui só publicar gera commit. O gatilho diário `reservaDiaria` do PainelPrivado reativa o workflow todo dia pela API do GitHub. Exige `GITHUB_REPO` e `GITHUB_TOKEN` (fine-grained, "Actions: Read and write" só neste repositório) nas propriedades do PainelPrivado. Falha fica na aba LOG (`reativar-workflow`).

**Texto gravado como texto (desde 2.3.2.19).** Toda escrita na planilha passa por `valorCelula_()`: texto que o Sheets transformaria em fórmula (`+`, `=`, `-`, `@` no início), número ou data (`10/12`, `90000-000`) recebe um apóstrofo invisível. Dados gravados antes da 2.3.2.19 com esse problema aparecem como `#ERROR!` na planilha: corrija-os pelo painel.

**Tamanho do site.** O GitHub Pages publica no máximo 1 GB. O validador mostra o tamanho a cada execução, avisa acima de 800 MB e bloqueia acima de 1 GB com mensagem clara. Com ~250 KB por foto, o teto é de cerca de 4.000 fotos. Perto disso: menos fotos por imóvel, ou levar as imagens para outro armazenamento (mudança de arquitetura, planejar com antecedência). O histórico do Git também cresce a cada foto substituída; o limite recomendado do repositório é 1 GB.

**Ordem commit → deploy → conferência → ACK (proposital).** O commit de `site/` acontece antes do deploy. Se o deploy falhar, o repositório fica à frente do site por alguns minutos; nada é confirmado no painel, a fila volta e a próxima execução republica o mesmo conteúdo (as fotos já estão no repositório, não são baixadas de novo). O contrário (commit depois do deploy) é perigoso: se o push falhasse, o site teria fotos que o repositório não tem, e o motor bloquearia as execuções seguintes. **A presença do commit nunca significa publicado**: só o ACK, enviado depois de conferir `publicacao.json` e `catalogo.json` no domínio, marca a versão como publicada. Um teste (`test_pages.py`) impede que essa ordem seja trocada.

**Reconstrução (workflow com "forçar").** Abre uma campanha na aba RECONSTRUCOES e cada execução põe na fila só um lote (`LOTE_RECONSTRUCAO`, limitado por `MAX_POR_EXECUCAO`, padrão 20); alterações normais passam na frente. O agendamento de 15 minutos drena o resto: 300 imóveis levam cerca de 4 horas com lote 20. Fotos que já estão no repositório não são baixadas de novo. Detalhes em `RECONSTRUCAO_PROGRESSIVA.md`.

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

Fluxo `clasp` e os três Web Apps: `MANUAL_INSTALACAO.md`, parte A.
