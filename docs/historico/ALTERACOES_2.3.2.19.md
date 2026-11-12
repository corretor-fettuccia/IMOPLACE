# Alterações v2.3.2.19

Origem: segunda auditoria (ameaças, integridade, injeção, operação real) da v2.3.2.18.

1. **Texto virando fórmula ou data na planilha** (`COMUM/Planilha.gs`): `valorCelula_()` em toda escrita
   (`anexarLinha_`, `anexarLinhas_`, `gravarLinha_`, `gravarLinhas_`). Texto começando com `+ = - @`, ou que o Sheets
   leria como número ou data, recebe apóstrofo; colunas já formatadas como texto não mudam. Antes,
   "+ 3 quartos" era gravado como `#ERROR!` e publicado assim.
2. **Agendamento desligado após 60 dias sem atividade** (`Sincronizar.gs`): `reservaDiaria` reativa o workflow pela
   API do GitHub todo dia; "Sincronizar agora" também reativa antes de disparar. Falha vai para a aba LOG.
3. **Tamanho do GitHub Pages** (`validar.py`): mostra o tamanho do site, avisa acima de 800 MB e bloqueia acima de
   1 GB com mensagem clara.
4. **URLs nos logs públicos** (`publicar.yml`, `verificar_configuracao.py`): `API_INTEGRACAO_ACTIONS_URL` e
   `ESCRITOR_URL` aceitas como Secret (mascaradas), com Variable de reserva. Guias e assistente recomendam Secret.

Testes: Python 34 (+2), Apps Script 36 (+2). Docs: `OPERACAO.md`, `HOMOLOGACAO_PRODUCAO.md`.
