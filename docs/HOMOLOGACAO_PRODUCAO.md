# ImoPlace — Roteiro de homologação para produção

Os testes do pacote rodam sem Google e sem GitHub. Este roteiro é o que falta: executar no ambiente real e
anotar o resultado. **Só libere produção com todos os itens marcados.** Use 1 a 3 imóveis de teste e
`permitirIndexacao: false` em `imoplace.json` até o fim.

Anote em cada item: data, quem executou e a evidência (print, ID do job, link do Actions).

## A. Acesso e segurança (bloqueante)

- [ ] `python3 GOOGLE.APPSCRIPT/scripts/homologar_acesso.py` → **APROVADO**.
- [ ] URL `/exec` do escritor aberta numa janela anônima → "Acesso negado", sem o painel.
- [ ] URL do painel restrito aberta com outra conta Google → sem acesso.
- [ ] Secret `ESCRITOR_URL` cadastrado no GitHub (e `API_INTEGRACAO_ACTIONS_URL` movida para Secrets); a execução seguinte mostra
      "[OK] GET anônimo no escritor não mostra o painel" no passo "Homologar acesso anônimo".
- [ ] O segredo `SEGREDO_INTEGRACAO` não aparece em nenhum log do Actions nem no repositório.

## B. Ciclo de um imóvel (bloqueante)

- [ ] Criar e publicar um imóvel com 3 fotos → aparece no site e o painel mostra "publicado/sincronizado".
- [ ] Fotos com marca d'água no padrão esperado; uma foto enviada com a caixa desmarcada sai sem marca.
- [ ] Descrição começando com "+ 3 quartos" e "- Sala ampla" aparece igual no site (sem `#ERROR!`).
- [ ] Editar só o preço → site atualizado e nenhuma foto baixada de novo (log "0 foto(s) baixada(s)").
- [ ] Substituir uma foto → versão nova no site; a antiga continua no Drive por 48h após a confirmação.
- [ ] Baixar o imóvel → some do site e do sitemap; o painel confirma.

## C. Falhas e recuperação (bloqueante)

- [ ] Cancelar o workflow **logo depois do passo "Commit de imagens e páginas"** (antes do deploy) → o painel não marca
      como publicado; a execução seguinte (até 15 min + 30 min de reserva) publica e confirma, sem duplicar nada.
- [ ] Em Actions, "Re-run all jobs" numa execução que já confirmou → nada é publicado ou confirmado em dobro.
- [ ] Remover o compartilhamento da pasta Imoveis com a conta de serviço e editar um imóvel → a execução falha com
      mensagem clara, **os outros imóveis continuam no ar**; reativar o compartilhamento → recupera sozinho.
- [ ] Apagar o título de um imóvel publicado direto na planilha → o imóvel **continua no site** e o log do Actions
      mostra o aviso "sumiu do feed sem pedido na fila"; restaurar o título.

- [ ] Num imóvel de teste publicado, apagar no repositório a pasta `site/imoveis/<codigo>/imagens/`, commit, e rodar
      o workflow com **forçar** → a reconstrução baixa as fotos de novo do Drive e o imóvel volta ao site.

## D. Volume (recomendado antes de muitos imóveis)

- [ ] Reconstrução completa com ~25 imóveis de teste: a campanha conclui, `CONFIRMADOS` bate com o total e
      nenhuma execução passa de 15 minutos. Anote o tempo médio por execução.
- [ ] Feed público (`API_PUBLICA_URL`) responde em menos de 10 s com o catálogo de teste.

## E. Liberação

- [ ] `permitirIndexacao: true` em `imoplace.json`, `SITE_URL` e `CNAME` no domínio definitivo.
- [ ] Settings > Pages mostra o domínio verificado e **Enforce HTTPS** marcado; o site abre com cadeado.
- [ ] Backup da planilha agendado (cópia semanal no Drive).
- [ ] `GITHUB_REPO` e `GITHUB_TOKEN` configurados no PainelPrivado; a aba LOG não mostra `reativar-workflow:erro`.
- [ ] Política de uso do GitHub Pages lida e aceita para este site (alternativa sem mudar código: Cloudflare Pages ou Netlify).
- [ ] Responsável definido para olhar falhas do Actions (o GitHub envia e-mail em falha de workflow).
