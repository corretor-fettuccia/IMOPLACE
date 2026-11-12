# ImoPlace — Marca d'água nas fotos (desde 2.3.2.17)

## Como funciona

A marca é desenhada **no navegador**, no mesmo canvas em que o painel já redimensiona a foto (lado maior 1920 px)
e gera o WebP. O servidor, o Drive, o motor Python e o site recebem a foto já marcada: nada mudou neles.

- Vale para **envio** e **substituição** de fotos. Fotos já enviadas não mudam; para marcá-las, use "substituir".
- A miniatura do painel (240 px) não leva marca.
- Na aba Imagens aparece a caixa **"Aplicar marca d'água"**, marcada por padrão. Desmarque para plantas,
  documentos ou fotos que não devem ser marcadas; a escolha vale para os próximos envios enquanto o painel estiver aberto.
- **A marca fica gravada na foto.** O Drive guarda só a versão marcada (o painel já não guardava o original em
  tamanho cheio). Para trocar o texto depois, é preciso reenviar a foto a partir do arquivo original.

## Configuração padrão (não precisa configurar nada)

| Propriedade (projeto `imoplace-API-PainelPrivado`) | Padrão | Valores |
|---|---|---|
| `MARCA_DAGUA_ATIVA` | `SIM` | `SIM` ou `NAO` (desliga e esconde a caixa) |
| `MARCA_DAGUA_TEXTO` | domínio de `SITE_URL` (`imoplace.com.br`) | até 60 caracteres |
| `MARCA_DAGUA_POSICAO` | `inferior-direita` | `inferior-esquerda`, `superior-direita`, `superior-esquerda`, `centro`, `mosaico` |
| `MARCA_DAGUA_OPACIDADE` | `0.5` | 0.1 a 0.9 (aceita vírgula) |
| `MARCA_DAGUA_TAMANHO` | `4` | altura do texto em % do lado menor da foto, 2 a 15 (mínimo 12 px) |

Valor inválido volta ao padrão, sem travar o envio. Mudou uma propriedade? Recarregue o painel.

Texto branco com contorno escuro: fica legível em céu claro e em áreas escuras. `mosaico` repete o texto na
diagonal pela foto inteira, mais difícil de recortar, porém mais visível e com arquivo maior (cerca de 4 vezes no teste).

## Limite conhecido

Só texto. Uma marca com o **logo** em imagem exige guardar o logo no projeto (o navegador não pode desenhar uma
imagem de outro domínio no canvas e depois gerar o WebP); fica como evolução se for necessário.
