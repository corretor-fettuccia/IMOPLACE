# ImoPlace v2.3.2.20 — Correção de bloqueio à produção

## Mudanças específicas

- `GIT-PAGE/scripts/gerador.py`: impedida a publicação de catálogo que retire um imóvel já publicado por falhas de dados ou fotografias **sem baixa explícita**. A falha interrompe o workflow antes de gerar o artefato e antes de executar limpeza.
- `GIT-PAGE/scripts/tests/test_publicacao.py`: novos testes cobrindo perda de foto + feed ausente, foto ausente durante reconstrução e baixa legítima.
- `GIT-PAGE/scripts/homologar_acesso.py` e `.github/workflows/publicar.yml`: antes de sincronizar, exigem `ESCRITOR_URL` **e** `API_INTEGRACAO_ACTIONS_URL`, e recusam publicar quando uma checagem de acesso anônimo não conseguir ser executada por falha de rede.

## Instalação e liberação real

1. Faça backup local da planilha, conteúdo do Drive e repositório por sua conta.
2. Envie **somente o conteúdo de `GIT-PAGE/`** à raiz do repositório GitHub da vitrine, mantendo as configurações existentes.
3. Nos GitHub Actions Secrets, configure `ESCRITOR_URL` com o `/exec` da implantação POST de `imoplace-API-PainelPrivado` e `API_INTEGRACAO_ACTIONS_URL` com o `/exec` de `imoplace-API-IntegracaoActions`. Este último também aceita a Variable existente, mas o Secret é preferível. Não troque as duas URLs entre si.
4. Confirme as demais variáveis/secrets anteriores: `API_PUBLICA_URL`, `SEGREDO_INTEGRACAO`, `GOOGLE_CREDENTIALS`, `SITE_URL`.
5. No Google Apps Script, verifique que a implantação POST do PainelPrivado **não exibe a interface administrativa para anônimos** e que POST sem HMAC é recusado. O workflow agora faz uma verificação automatizada, mas é recomendável acompanhar a primeira execução manualmente.
6. Em GitHub > Settings > Pages, use Source = **GitHub Actions**. Confirme domínio personalizado e certificado HTTPS.
7. Rode o workflow `Publicar ImoPlace v2.3.2.20` manualmente, `forcar=false`. Acompanhe todos os passos até `Conferir site publicado` e `Confirmar publicação ao painel`.
8. Teste um imóvel publicado, uma edição de preço, troca de foto e baixa explícita. Confirme URL, imagem e catálogo públicos. Só depois habilite `permitirIndexacao` no `imoplace.json` se desejar rastreamento dos mecanismos de busca.

## Limitações

- Testes locais **não substituem** a homologação real das implantações Apps Script e do Pages.
- Se um imóvel já publicado perder fotografias **antes** de sair do feed, o job pode falhar e deverá ser recuperado (restaurando os arquivos ou executando reconstrução apropriada). **Isso é intencional**: evita retiradas silenciosas.
- A janela entre commit e confirmação do deploy ainda existe. Se o deploy falhar, o job não confirma o ACK, e a próxima execução deve retomar a fila. Acompanhe eventual divergência entre commit e conteúdo publicado.
- Reconstrução e fila permanecem na arquitetura anterior. A otimização do payload de `aguardando` é futura, não é bloqueio de liberação para catálogo pequeno.
