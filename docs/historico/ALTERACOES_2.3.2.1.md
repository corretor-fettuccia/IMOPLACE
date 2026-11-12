# ImoPlace 2.3.2.1 — Instalação guiada

Atualização conservadora sobre 2.3.2: sem alterações no visual público, no painel e no motor da sincronização.

- `GOOGLE.APPSCRIPT/instalar.sh`: assistente interativo e opção `--preparar`.
- `enviar_projetos.sh`: preserva envio existente por `clasp`.
- `atualizar.sh`: aponta para envio sem recriação.
- `scripts/assistente.py`: coleta validada de parâmetros, gerador de segredo de 256 bits, arquivos por API, variáveis GitHub e checklist.
- `.instalacao-local/`: arquivos com permissões restritas, ignorados pelo Git.
- Token GitHub deliberadamente NÃO é solicitado no terminal: preencher manualmente nas Script Properties do B.
- O instalador NÃO altera Script Properties nem implanta Web Apps automaticamente; siga o GUIA_INSTALADOR_GUIADO.md.

Homologação de implantação real ainda necessária; testes executados apenas em ambiente local.
