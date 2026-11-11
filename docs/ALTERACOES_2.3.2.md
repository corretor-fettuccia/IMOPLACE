# ImoPlace 2.3.2 — Confiabilidade

## Migração obrigatória (não colocar em produção antes)

1. Faça cópia da planilha e dos IDs das implantações; mantenha backup v2.3.1.
2. Atualize imoplace-API-PainelPrivado via `atualizar.sh`; execute `instalar()` para criar a aba `LIMPEZA` e o gatilho diário.
3. Em imoplace-API-PainelPrivado configure `SEGREDO_INTEGRACAO` igual ao secret `INTEGRACAO_SEGREDO` do GitHub (mínimo 32 caracteres).
4. No **mesmo projeto B**, crie **duas implantações** Web App: (a) painel restrito ao administrador; (b) endpoint de integração executado como proprietário, acesso **Qualquer pessoa**, exclusivamente para POST HMAC. `doGet` do painel verifica administrador e não deve retornar HTML para anônimos. Verifique essa restrição com um navegador anônimo antes de liberar a URL.
5. Em imoplace-API-IntegracaoActions configure `CENTRAL_WRITER_URL` para o endpoint B público; atualize C. C não tem acesso de escrita nem requer `PLANILHA_ID` nesta versão. O GitHub continua usando a URL /exec de C e o secret antigo.
6. Atualize imoplace-API-Publica para incluir `versao` na projeção pública. Configure `PLANILHA_ID` e `SITE_URL`.
7. Publique GitHub e teste um imóvel em homologação: criar → publicar → substituir foto durante execução → confirmar → limpar após 48h.

## Garantias e limites

- Um único projeto B com `LockService.getScriptLock` faz todas as mutações do painel e do Actions.
- ACK exige mesmo job, reserva ativa e versão igual à atual (do imóvel e da foto); confirmações antigas não limpam a fila nova.
- Feed informa `versao` e o motor cancela quando o snapshot está fora de sincronia com a reserva.
- Arquivos antigos do Drive ficam em `LIMPEZA` para descarte após pelo menos 48h, sem pendências; 20 por execução do gatilho diário.
- O commit do site precede o deploy; se `git push` falhar, o Pages não é publicado e não há ACK.
- O catálogo só é marcado como no ar depois do teste HTTP contra o site público.
- Ainda existe uma pequena janela de concorrência entre o último check de reserva e o deploy; nessa situação ACK rejeita o job antigo, mantendo pendência para recuperação.
- A API B pública precisa de teste real de permissões e HMAC com a conta Google antes de ser considerada apta a produção.
- Nenhum componente servidor Node.js faz parte desta arquitetura; `clasp` existente é usado apenas para manutenção.

## Casos de teste acrescentados

- ACK antigo não limpa a fila de um job novo;
- ACK válido confirma exatamente a versão reservada;
- erro tardio de execução antiga não altera o estado do novo job;
- feed com versão alterada durante a sincronização é recusado;
- `publicacao.json` contém job ID e hash exato do catálogo publicado;
- API C não tem escopos do Google Sheets nem do Drive.

## Sequência do GitHub Actions

1. Consulta a fila assinada;
2. Consulta o feed e confere versões;
3. Baixa imagens WebP necessárias, por SHA;
4. Gera extras;
5. Valida;
6. Gera artefato e identificador da execução;
7. Valida reserva na API, faz commit, publica e confere o marker e o catálogo HTTP;
8. Confirma no escritor central somente a versão exata publicada.

## Recuperação

- Falha antes do deploy: sem ACK; o job marca erro apenas nas reservas que ainda possui.
- Commit realizado, deploy falhou: repositório já contém build, mas painel continua pendente;
  nova execução faz deploy/ACK. Não marcar manualmente como publicado.
- Operador altera imóvel durante o workflow: o ACK antigo é recusado e a nova fila permanece pendente;
  o site converge em execução posterior.
- Drive indisponível: bloqueia publicação; fotos antigas são preservadas.
- Limpeza diária: só descarta versões antigas após no mínimo 48h e nenhuma pendência correspondente.

## Limitação residual importante

Não há transação distribuída ACID entre Google Sheets, GitHub e GitHub Pages.
Uma alteração imediatamente após a validação de reserva ainda pode fazer com que o site exiba
brevemente a versão anterior; a confirmação tardia é recusada e a fila permanece para nova
publicação. Os testes locais **não substituem** testes reais de autenticação dos Web Apps,
permissões de acesso anônimo ao POST assinado, tempo de deploy e cotas de Apps Script.
