# SIGBEF — Site oficial

Site de apresentação do SIGBEF, sistema gratuito de gestão de biblioteca escolar. Construído com React + Vite + Tailwind CSS e hospedado no GitHub Pages.

**URL de produção:** https://marcelin1555.github.io/SIGBEF/

---

## Stack

| Tecnologia | Versão | Função |
|---|---|---|
| React | 19 | UI |
| Vite | 8 | Bundler / dev server |
| Tailwind CSS | 3 | Estilização |
| React Router | 7 (HashRouter) | Navegação multi-página |
| Font Awesome | 6 | Ícones SVG |

---

## Páginas

| Rota | Conteúdo |
|---|---|
| `/` | Landing: hero, problema, funcionalidades, prova, instalação, planos |
| `/#/funcionalidades` | Funcionalidades completas por perfil + tabela comparativa |
| `/#/download` | Requisitos de sistema, passo a passo, FAQ de instalação |
| `/#/planos` | Pricing Open Core + FAQ de preços |
| `/#/equipe` | Equipe + linha do tempo do projeto |

HashRouter foi escolhido para compatibilidade nativa com GitHub Pages sem configuração de servidor.

---

## Rodar localmente

```bash
cd site
npm install
npm run dev
# Acesse http://localhost:5173/SIGBEF/
```

## Build de produção

```bash
npm run build
# Saída em site/dist/
```

## Deploy no GitHub Pages

```bash
npm run build
# Copie o conteúdo de dist/ para o branch gh-pages
# Ou use o pacote gh-pages:
npm install -D gh-pages
npx gh-pages -d dist
```

---

## Estrutura

```
site/
├── public/
│   └── logo.png              # Logo do SIGBEF
├── src/
│   ├── components/           # Componentes reutilizáveis
│   │   ├── Nav.jsx           # Navegação com NavLink ativo
│   │   ├── Hero.jsx          # Hero 2 colunas com mockup CSS
│   │   ├── Problema.jsx      # Seção de dores
│   │   ├── Prova.jsx         # Prova social + métricas
│   │   ├── Funcionalidades.jsx
│   │   ├── ComoInstalar.jsx
│   │   ├── Comparativo.jsx
│   │   ├── Planos.jsx
│   │   ├── Equipe.jsx
│   │   ├── ODS.jsx
│   │   └── Footer.jsx
│   ├── pages/                # Páginas completas (1 por rota)
│   │   ├── Home.jsx
│   │   ├── FuncionalidadesPage.jsx
│   │   ├── DownloadPage.jsx
│   │   ├── PlanosPage.jsx
│   │   └── EquipePage.jsx
│   ├── App.jsx               # Rotas + ScrollToTop
│   ├── main.jsx              # Entrada (HashRouter)
│   └── index.css             # Tailwind directives
├── index.html
├── vite.config.js            # base: '/SIGBEF/'
└── tailwind.config.js        # cores: primary #2E75B6, dark #1F4E79
```

---

## Paleta de cores

| Nome | Hex | Uso |
|---|---|---|
| `primary` | `#2E75B6` | Botões, links, destaques |
| `dark` | `#1F4E79` | Fundo hero, headers, nav |
| Amarelo | `#FBBF24` | CTAs principais |

---

Licença MIT — parte do projeto SIGBEF.
