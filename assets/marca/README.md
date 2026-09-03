# Kit de marca do SIGBEF

Tudo que é preciso para aplicar a marca sem deformá-la. Comece pelo
**`SIGBEF_Manual_da_Marca.png`** — ele responde as perguntas que aparecem
na hora de usar: qual versão, qual cor, quanto respiro, tamanho mínimo.

## O que tem aqui

```
marca/
├── SIGBEF_Manual_da_Marca.png    a folha de uso, para consultar
├── svg/                          vetor: escala para qualquer tamanho
└── png/                          bitmap: 3 tamanhos de cada versão
```

## As seis peças

| Arquivo | Quando usar |
|---|---|
| `sigbef-icone-colorido` | Padrão. Tela, site, slide, impressão colorida |
| `sigbef-icone-monocromatico` | Carimbo, serigrafia, bordado — gradiente não sobrevive |
| `sigbef-icone-negativo` | Sobre fundo escuro ou foto |
| `sigbef-icone-preto` | Fotocópia, fax, documento em preto e branco |
| `sigbef-horizontal` | Cabeçalho, papel timbrado, banner |
| `sigbef-horizontal-compacto` | Crachá, fita, rodapé, assinatura de e-mail |

**Prefira sempre o SVG.** Ele escala de um favicon a um banner de dois
metros sem perder nitidez. Use PNG só onde o SVG não for aceito.

## Cores

| | Hex | Uso |
|---|---|---|
| Azul institucional | `#1F4E79` | Cor principal |
| Azul claro | `#2E75B6` | Apoio, links |
| Âmbar | `#F2A900` | Destaque, nunca em bloco grande |
| Fundo | `#F5F7FA` | Fundo das telas |

Estas cores **não são declaradas aqui**. Elas são lidas de
`sigbef/ui_tema.py`, onde o próprio sistema as define. Se alguém mudar a
paleta lá, os geradores deste kit passam a produzir a nova — a folha e o
software não podem divergir.

## Fontes

**Segoe UI** na interface, na marca, no site e nas apresentações.
Regular no corpo, Semibold em título e destaque. É fonte do Windows: em
Linux e macOS o sistema substitui, e por isso o código sempre declara a
pilha `system-ui, "Segoe UI", Roboto, sans-serif`.

**Times New Roman** só no relatório de pesquisa. Isso não é escolha de
marca: a ABNT exige fonte serifada no trabalho acadêmico.

## Regenerar

```bash
python assets/marca/gerar_kit_marca.py      # variantes e PNGs
python assets/marca/gerar_folha_marca.py    # a folha de uso
```

Os dois geradores falham de propósito se algum texto estourar a caixa ou
a altura da folha — foi assim que a seção "O que não fazer" foi flagrada
cortada no rodapé antes de virar entrega.
