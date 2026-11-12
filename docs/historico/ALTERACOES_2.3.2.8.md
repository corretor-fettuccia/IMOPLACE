# ImoPlace v2.3.2.8 — Correção de configuração GitHub Actions

- `API_PUBLICA_URL`, `API_INTEGRACAO_ACTIONS_URL` e `SITE_URL` são **Repository Variables**.
- `SEGREDO_INTEGRACAO` e `GOOGLE_CREDENTIALS` são **Repository Secrets**.
- `publicar.yml`, `scripts/integracao.py`, `scripts/verificar_configuracao.py`, `scripts/assistente_git.py` e a documentação usam os mesmos nomes.
- O verificador informa a aba correta e rejeita a configuração incompleta antes do acesso à API.
- Regressões testadas em `scripts/tests/test_configuracao_github.py`.
- Removido de uso o contrato histórico 2.3.2.6; manual definitivo em `../GUIA_INSTALACAO_GITHUB.md`.
- Google Apps Script e layout não foram alterados.

**Limitação:** sem credenciais reais, não foi executado deploy no Pages nem comunicação com o Drive.
