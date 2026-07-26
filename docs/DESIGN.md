# Guia de design do SIGBEF

Referência única de identidade visual do projeto — desktop, site e app
Android. Os valores aqui **espelham o código** (`sigbef/ui_tema.py`,
`site/tailwind.config.js` e
`sigbef-mobile/app/src/main/java/br/rn/cefe/sigbef/ui/theme/Color.kt`);
se mudar num, atualize os outros e este arquivo.

Kit de marca completo (logo em variações, fontes .woff2, guia navegável):
pasta `SIGBEF_kit_marca` gerada em 21/07/2026 (Downloads do Marcello) e
guia online em https://claude.ai/code/artifact/aaa64b2e-9861-4a23-9aeb-79d996bbd557

---

## 1. Cores

### Marca

| Papel | Nome | HEX | RGB | Uso |
|---|---|---|---|---|
| Primária | Navy | `#1F4E79` | 31, 78, 121 | Estrutura, títulos, cabeçalhos, sidebar |
| Secundária | Azul | `#2E75B6` | 46, 117, 182 | Links, botões, ícones, apoio |
| Destaque | Dourado | `#F2A900` | 242, 169, 0 | Faixa da marca, CTAs, realces — **com parcimônia** |

Regra de dominância: **navy domina (60–70%), azul apoia, dourado é a única
faísca**. Nunca usar dourado em blocos grandes.

No site, o CTA amarelo usa `yellow-400` (`#FACC15`) do Tailwind — mesma
família do dourado da marca.

### Base (neutros)

| Papel | HEX |
|---|---|
| Fundo | `#F5F7FA` |
| Fundo escuro (faixas) | `#E8ECF1` |
| Card / branco | `#FFFFFF` |
| Borda | `#D5DAE0` |
| Texto | `#1A1A1A` |
| Texto sobre cor | `#FFFFFF` |

### Estado (feedback — nunca decorativas)

| Papel | HEX |
|---|---|
| Sucesso | `#2E7D32` |
| Aviso | `#EF6C00` |
| Erro | `#C62828` |

### Contraste (lição aprendida na auditoria WCAG de 23/07/2026)

- Texto normal precisa de **4,5:1** contra o fundo (WCAG AA).
- `gray-400` do Tailwind **reprova** sobre branco (2,5:1) — usar `gray-500`
  no mínimo. No rodapé escuro, `gray-600` reprova — usar `gray-400`+.
- O desktop tem guarda automática: `ui_tema.primaria_clara_demais()` impede
  cor primária ilegível na personalização.

---

## 2. Tipografia

| Papel | Fonte | Pesos | Onde |
|---|---|---|---|
| Títulos | **Montserrat** | 700 / 800 | Site (headings), materiais de divulgação, slides |
| Corpo e interface | **Inter** | 400 / 600 | Materiais gráficos, kit de marca |
| Interface nativa | **Segoe UI** (system-ui) | — | App desktop e site (corpo) — zero dependência |

Ambas gratuitas (licença OFL): fonts.google.com/specimen/Montserrat e /Inter.
Arquivos `.woff2` no kit de marca.

Detalhes que usamos: `text-wrap: balance` em h1–h3; rótulos em caixa alta
com `tracking-widest`; números tabulares onde há colunas de dígitos.

---

## 3. Logo

- Arquivo fonte: `site/public/logo.png` (fundo transparente) e `favicon.svg`.
- **Sobre cor primária de qualquer paleta**: usar a variante "plaqueta"
  (logo sobre quadrado branco arredondado) — gerada em `tools/gerar_icones.js`
  (chaves `logoplaca_original_*` em `sigbef/icones_data.py`).
- Área de respiro: margem mínima equivalente à faixa dourada do símbolo.
- Tamanho mínimo em tela: 28 px (abaixo disso o código de barras vira ruído).
- Proibido: distorcer, recolorir, aplicar sombra/contorno extra.

---

## 4. Ícones

- Família única: **Font Awesome** (Solid; Brands só para WhatsApp/GitHub).
- Site: pacote `@fortawesome/react-fontawesome`.
- Desktop: PNGs base64 gerados em dev-time por `tools/gerar_icones.js`
  (react-icons + sharp) e embutidos em `sigbef/icones_data.py` — runtime
  continua 100% stdlib. Nunca editar `icones_data.py` à mão.
- Padrão visual: ícone dentro de contêiner arredondado (`rounded-lg`/círculo)
  com fundo claro da mesma família da cor do ícone.
- Paleta dos ícones: azul e dourado/âmbar da marca (não usar arco-íris de
  cores — lição da crítica de design de 23/07/2026). Verde/vermelho só para
  convenção universal (disponível / atraso).

---

## 5. Padrões de componentes (site)

1. **Cabeçalho de página interna**: faixa gradiente `from-#1F4E79 to-#2E75B6`
   + eyebrow em caixa alta azul-claro + `h1` branco + subtítulo `blue-100`.
2. **Alternância de fundo** entre seções: branco → `gray-50` → branco.
3. **Cards**: `rounded-2xl`, borda `gray-100`/`gray-200`, sombra leve.
   Card com hover só se for clicável (senão parece botão quebrado).
4. **Containers**: `max-w-4xl` a `max-w-6xl` centralizados.
5. **CTA primário**: amarelo com texto navy; secundário: contorno.
6. **Mockup do app no hero**: HTML/CSS puro (não imagem) — nítido em
   qualquer tela e mostra a versão atual via `versao.js`.

## 5.1. Padrões do app Android (Compose)

O app usa a **mesma assinatura visual do site**, adaptada ao celular.

- Tokens em `ui/theme/Color.kt`; `ui/components/Marca.kt` guarda o que é
  identidade (gradiente, pílula, rótulo de seção). **Nenhuma tela escreve
  `Color(0xFF…)` na mão** — se faltar um tom, ele nasce no tema, com nome.
- **Barra do topo** (`SigbefTopAppBar`): gradiente
  `SigbefNavy → SigbefBlue` fechado por faixa dourada de 4dp, com o título
  da tela e um subtítulo opcional. É o equivalente do cabeçalho de página
  interna do site (item 1 acima).
- A barra também carrega o botão de **atualizar** e o estado da conexão.
  Antes isso era um chip flutuando sobre o conteúdo.
- **Pílula de status** (`PilulaStatus`): totalmente arredondada, fundo
  lavado da cor de estado, com ícone e texto. Igual à do site
  ("✓ ok" / "atrasado"). Nunca depende só da cor — sempre tem texto.
- Fundos de pílula são cores **chapadas** (`SigbefSuccessFundo` etc.), não
  alpha: as mesmas pílulas aparecem sobre cartão branco e sobre o fundo
  cinza, e com alpha mudariam de tom conforme o lugar.
- Barra de status do sistema em ícones claros
  (`SystemBarStyle.dark`), porque o gradiente navy passa por baixo dela.

> **Cuidado ao gerar tema Material 3 automaticamente.** Os `*Container`
> do gerador (`D1E4FF`, `7CBAFF`, `001D35`, `004A7D`) são azuis parecidos
> com os nossos, mas de outra família — e como os componentes do Material
> os usam por padrão, aquela paleta reaparecia nas telas sem ninguém ter
> escolhido. Hoje eles derivam do navy e do azul de verdade.

## 6. Padrões do desktop (Tkinter)

- Estilos ttk centralizados em `sigbef/ui_tema.py` (`aplicar_tema`).
- `Card.TFrame` (com borda) vs `CardInner.TFrame` (sem borda) — nunca
  aninhar dois `Card.TFrame` (borda dupla).
- Cores derivadas da primária em runtime (`COR_PRIMARIA_SUAVE/ESCURA` via
  `_mesclar_branco`/`_ajustar_cor`) — nada de azul fixo em tela que precisa
  respeitar paleta personalizada.
- 5 paletas prontas: padrão, verde floresta, roxo universitário, vermelho
  acadêmico, marrom biblioteca — todas com primária escura validada.

---

## 7. Acessibilidade — checklist mínimo

- [ ] Contraste AA (4,5:1 texto; 3:1 componentes)
- [ ] Foco visível (`:focus-visible` com anel azul) em tudo que é interativo
- [ ] Skip link "Pular para o conteúdo"
- [ ] `alt` real em imagem informativa; `aria-hidden` em decorativa
- [ ] Botão só com ícone → `aria-label`
- [ ] Modal/lightbox: fecha com Esc, trava scroll, devolve foco
- [ ] Não transmitir informação só por cor/emoji (usar ícone + texto sr-only)
- [ ] Alvos de toque ≥ 44×44 px no mobile

---

## 8. Skills de design (Claude Code)

Quais skills invocar para cada tipo de trabalho neste projeto:

| Tarefa | Skill | Observação |
|---|---|---|
| Criar UI/página nova | `frontend-design` | Direção estética; evita cara de template |
| Elevar qualidade do site existente | `redesign-existing-projects` | Sem quebrar funcionalidade |
| Auditar UI contra boas práticas | `web-design-guidelines` | Estilo linter de UX (achou 12 itens em 23/07) |
| Auditoria WCAG formal | `design:accessibility-review` | Achou 11 itens em 23/07 |
| Crítica de hierarquia/consistência | `design:design-critique` | Achou o screenshot falso |
| Texto de interface | `design:ux-copy` + `copywriting` | |
| Humanizar texto PT-BR | `anthropic-skills:humanizador-tedson` | Padrão do projeto para todo texto público |
| Gráficos e dashboards | `dataviz` | Carregar ANTES de escrever código de gráfico |
| Print/mockup → código | `image-to-code` | |
| Identidade de marca | `brandkit` | Complementa este guia |
| Slides e materiais | `anthropic-skills:pptx` | Fluxogramas seguem §1–§4 deste guia |

Fluxo recomendado para trabalho visual novo:
`frontend-design` (criar) → `web-design-guidelines` + `design:accessibility-review`
(auditar) → `design:design-critique` (olhar de fora) → corrigir → deploy.

---

## 9. Assets prontos e geradores

| Asset | Onde |
|---|---|
| Logo + variações + fontes | Kit de marca (`SIGBEF_kit_marca/`) |
| Ícones do desktop | `tools/gerar_icones.js` → `sigbef/icones_data.py` |
| Captura real do painel | `site/public/screenshot-painel.png` (fonte em `capturas app/`, fora do git) |
| Fotos de eventos | `site/public/eventos/<evento>/` (originais fora do git) |
| Fluxogramas (percurso, produto) | gerados por script sharp/SVG — pedir regeneração quando mudar conteúdo |
