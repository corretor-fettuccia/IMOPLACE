# Árvore do projeto e etapas do motor

```text
imoplace-v<versão>/
├── LEIA-ME.md, VERSAO
├── GIT-PAGE/                   ← o CONTEÚDO desta pasta vira a raiz do repositório GitHub
│   ├── .github/workflows/publicar.yml
│   ├── COMECE_AQUI.md, VERSAO, imoplace.json, instalar.sh, verificar.sh, .gitignore
│   ├── site/                   ← pasta pública (vira a raiz do domínio no deploy)
│   │   ├── index.html, anunciar/, assets/, CNAME, robots.txt, .nojekyll
│   │   ├── catalogo.json       ← estado publicado: nunca substituir ao atualizar
│   │   └── imoveis/{slug}-{id}/   ← estado publicado: nunca substituir ao atualizar
│   │       ├── index.html
│   │       └── imagens/*.webp
│   ├── scripts/                ← etapas Python, homologador, helpers e testes
│   └── docs/                   ← MANUAL_INSTALACAO.md, OPERACAO.md, HOMOLOGACAO_PRODUCAO.md, ... e historico/
└── GOOGLE.APPSCRIPT/           ← fica só no seu computador
    ├── instalar.sh, continuar_configuracao.sh, configurar_integracao.sh, atualizar.sh, verificar.sh
    ├── scripts/                ← configurar_integracao.py, homologar_acesso.py (atalho), copiar_comum.py
    ├── COMUM/                  ← Esquema.gs e Planilha.gs (copiados para os três projetos)
    ├── imoplace-API-Publica/
    ├── imoplace-API-PainelPrivado/
    └── imoplace-API-IntegracaoActions/
```

A pasta `site/` é copiada para o artefato de deploy e se torna a raiz do **site**, não do repositório. O uso dessa separação evita expor `scripts/`, `docs/`, segredos, relatórios e os arquivos Apps Script. Não apontar o GitHub Pages diretamente para a raiz do repositório.

## Etapas independentes

| Etapa | Script | Entrada | Saída |
|---|---|---|---|
| 0 | `homologar_acesso.py` | URLs da ponte e do escritor | para tudo se o acesso anônimo não estiver bloqueado |
| 1 | `sincronizar.py` | API HMAC | `estado/job.json` |
| 2 | `montar_catalogo.py` | feed público | `estado/catalogo-candidato.json`, `estado/feed-snapshot.json` |
| 3 | `montar_imoveis.py` | snapshot, fila, Drive | `site/catalogo.json`, `site/imoveis/`, relatório |
| 4 | `montar_extras.py` | catálogo final | sitemap, robots, Merchant, Meta |
| 5 | `validar.py` | site local | sucesso/erro |
| 6 | `montar_site.py` | site validado | `estado/publicacao/` |
| 7 | `conferir.py` | site publicado | valida online todas as páginas e fotos alteradas |
| 8 | `confirmar.py` | relatório e job | confirmação HMAC no Apps Script |

A etapa 7 ocorre após `actions/deploy-pages`. A confirmação só acontece após a publicação e a conferência. O workflow faz commit da pasta pública **antes do deploy** e só depois do deploy/conferência envia o ACK.

**Fonte obrigatória em Settings → Pages:** GitHub Actions, não `main → /(root)` nem `main → /docs`. O conteúdo do artefato `estado/publicacao/` é a raiz `/` do domínio.
