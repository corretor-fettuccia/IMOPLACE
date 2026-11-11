# Árvore de projeto e motor 2.3

```text
imoplace-v2.3.1/
├── GIT-PAGE/                   ← conteúdo desta pasta vira a raiz do repositório
│   ├── .github/workflows/publicar.yml
│   ├── site/                   ← pasta pública (deploy de conteúdo desta pasta)
│   │   ├── index.html
│   │   ├── assets/
│   │   ├── anunciar/
│   │   ├── catalogo.json
│   │   └── imoveis/{slug}-{id}/
│   │       ├── index.html
│   │       └── imagens/*.webp
│   ├── scripts/                ← 8 etapas Python, helpers e testes
│   ├── docs/
│   ├── imoplace.json
│   └── .gitignore
└── GOOGLE.APPSCRIPT/
    ├── COMUM/
    ├── imoplace-API-Publica/
    ├── imoplace-API-PainelPrivado/
    └── imoplace-API-IntegracaoActions/
```

A pasta `site/` é copiada para o artefato de deploy e se torna a raiz do **site**, não do repositório. O uso dessa separação evita expor `scripts/`, `docs/`, segredos, relatórios e os arquivos Apps Script. Não apontar o GitHub Pages diretamente para a raiz do repositório.

## Etapas independentes

| Etapa | Script | Entrada | Saída |
|---|---|---|---|
| 1 | `sincronizar.py` | API HMAC | `estado/job.json` |
| 2 | `montar_catalogo.py` | feed público | `estado/catalogo-candidato.json`, `estado/feed-snapshot.json` |
| 3 | `montar_imoveis.py` | snapshot, fila, Drive | `site/catalogo.json`, `site/imoveis/`, relatório |
| 4 | `montar_extras.py` | catálogo final | sitemap, robots, Merchant, Meta |
| 5 | `validar.py` | site local | sucesso/erro |
| 6 | `montar_site.py` | site validado | `estado/publicacao/` |
| 7 | `conferir.py` | site publicado | valida online todas as páginas e fotos alteradas |
| 8 | `confirmar.py` | relatório e job | confirmação HMAC no Apps Script |

A etapa 7 ocorre após `actions/deploy-pages`. A confirmação só acontece após a publicação e a conferência. O workflow faz commit da pasta pública após publicação e antes do ACK.
