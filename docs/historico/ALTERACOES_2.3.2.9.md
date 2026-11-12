# Correções v2.3.2.9

- Verificador recebe `GOOGLE_CREDENTIALS_DISPONIVEL` derivado de `secrets.GOOGLE_CREDENTIALS != ''`; o JSON privado permanece apenas na ação de autenticação.
- Testes cruzados Apps Script requerem arquivos-fonte presentes; ausência no runner faz `skip`.
- `verificar.sh` valida presença de `imoplace.json` na raiz e roda a suíte sem rede.
- Guia único `COMECE_AQUI.md` e tutorial `CRIAR_GOOGLE_CREDENTIALS.md`.
- Interfaces e três projetos Apps Script preservados.
