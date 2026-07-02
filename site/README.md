# SIGBEF — Site oficial

Site de apresentação do SIGBEF, sistema gratuito de gestão de biblioteca escolar. Construído com React + Vite + Tailwind CSS e hospedado na Vercel.

**URL de produção:** https://sigbef.vercel.app/

---

## Stack

| Tecnologia | Versão | Função |
|---|---|---|
| React | 19 | UI |
| Vite | 8 | Bundler / dev server |
| Tailwind CSS | 3 | Estilização |
| React Router | 7 (BrowserRouter) | Navegação multi-página |
| Font Awesome | 6 | Ícones SVG (inclusive brands, para o WhatsApp) |

---

## Páginas

| Rota | Conteúdo |
|---|---|
| `/` | Landing: hero, problema, funcionalidades, prova, instalação, planos |
| `/funcionalidades` | Funcionalidades completas por perfil + tabela comparativa |
| `/download` | Requisitos de sistema, passo a passo, FAQ de instalação |
| `/planos` | Pricing Open Core + FAQ de preços |
| `/equipe` | Equipe + linha do tempo do projeto |
| `/novidades` | Changelog público, versão por versão (curado a partir de `docs/CHANGELOG.md`) |

BrowserRouter é usado para URLs limpas (sem `#`). O rewrite de SPA que faz
qualquer rota carregar `index.html` (necessário para refresh/link direto
funcionar) está configurado em `vercel.json`.

---

## Rodar localmente

```bash
cd site
npm install
npm run dev
# Acesse http://localhost:5173/
```

## Build de produção

```bash
npm run build
# Saída em site/dist/
```

## Deploy na Vercel

```bash
npm install -g vercel   # se ainda não tiver a CLI
vercel                  # primeiro deploy (preview) e configuração do projeto
vercel --prod           # publica em produção
```

O `vercel.json` na raiz do site já cuida do rewrite de SPA — não precisa
configurar nada a mais no painel da Vercel.

---

## Estrutura

```
site/
├── public/
│   ├── logo.png               # Logo do SIGBEF
│   ├── favicon.svg
│   └── icons.svg
├── src/
│   ├── components/            # Componentes reutilizáveis
│   │   ├── Nav.jsx            # Navegação com NavLink ativo
│   │   ├── Hero.jsx           # Hero 2 colunas com mockup CSS
│   │   ├── Problema.jsx       # Seção de dores
│   │   ├── Prova.jsx          # Prova social + métricas
│   │   ├── Funcionalidades.jsx
│   │   ├── Comparativo.jsx
│   │   ├── Planos.jsx
│   │   ├── Equipe.jsx
│   │   ├── ODS.jsx
│   │   ├── BotaoWhatsApp.jsx  # Botão flutuante de contato
│   │   └── Footer.jsx
│   ├── pages/                 # Páginas completas (1 por rota)
│   │   ├── Home.jsx
│   │   ├── FuncionalidadesPage.jsx
│   │   ├── DownloadPage.jsx
│   │   ├── PlanosPage.jsx
│   │   ├── EquipePage.jsx
│   │   └── NovidadesPage.jsx  # Changelog público
│   ├── App.jsx                # Rotas + ScrollToTop + BotaoWhatsApp
│   ├── main.jsx                # Entrada (BrowserRouter)
│   └── index.css              # Tailwind directives
├── index.html
├── vercel.json                # rewrite de SPA para a Vercel
├── vite.config.js             # base: '/'
└── tailwind.config.js         # cores: primary #2E75B6, dark #1F4E79
```

---

## Paleta de cores

| Nome | Hex | Uso |
|---|---|---|
| `primary` | `#2E75B6` | Botões, links, destaques |
| `dark` | `#1F4E79` | Fundo hero, headers, nav |
| Amarelo | `#FBBF24` | CTAs principais |
| WhatsApp | `#25D366` | Botão de contato flutuante |

---

Licença MIT — parte do projeto SIGBEF.
