/*
 * SIGBEF — Gerador dos ícones da interface (tempo de desenvolvimento).
 *
 * Renderiza ícones Font Awesome (react-icons) em PNGs minúsculos e grava
 * tudo como base64 em sigbef/icones_data.py. O aplicativo continua 100%
 * biblioteca padrão: em runtime só existe tk.PhotoImage(data=base64).
 *
 * Uso:  node tools/gerar_icones.js   (na raiz do repo)
 * Requer os módulos globais já usados pelo gerador de PPTX:
 * react-icons, react-dom, sharp.
 */
const NPM = "C:/Users/uemas/AppData/Roaming/npm/node_modules/";
const React = require(NPM + "react");
const ReactDOMServer = require(NPM + "react-dom/server");
const sharp = require(NPM + "sharp");
const fs = require("fs");
const {
  FaHome, FaBook, FaUsers, FaExchangeAlt, FaChartBar, FaCog, FaSearch,
  FaBookReader, FaSignOutAlt, FaBarcode, FaCheckCircle,
  FaExclamationTriangle,
} = require(NPM + "react-icons/fa");

// Paleta fixa (à prova de paleta personalizada do usuário):
// branco pra sidebar/cabeçalho, cinza neutro pros cards, verde/vermelho
// só nos cards de convenção universal (disponível / atraso).
const CORES = {
  branco: "#FFFFFF",
  cinza: "#6B7280",
  verde: "#2E7D32",
  vermelho: "#C62828",
};

const COMPONENTES = {
  home: FaHome, livro: FaBook, usuarios: FaUsers, troca: FaExchangeAlt,
  grafico: FaChartBar, engrenagem: FaCog, busca: FaSearch,
  leitor: FaBookReader, sair: FaSignOutAlt, barcode: FaBarcode,
  check: FaCheckCircle, alerta: FaExclamationTriangle,
};

// (nome, cor, tamanho em px) — só o que a UI realmente usa
const SPEC = [
  // Sidebar + botão Sair (fundo COR_PRIMARIA, texto branco)
  ["home", "branco", 16], ["livro", "branco", 16], ["usuarios", "branco", 16],
  ["troca", "branco", 16], ["grafico", "branco", 16],
  ["engrenagem", "branco", 16], ["busca", "branco", 16],
  ["leitor", "branco", 16], ["sair", "branco", 16],
  // Cards do painel inicial (fundo branco do card)
  ["livro", "cinza", 20], ["barcode", "cinza", 20], ["check", "verde", 20],
  ["troca", "cinza", 20], ["alerta", "vermelho", 20],
  ["usuarios", "cinza", 20],
];

async function main() {
  const linhas = [];
  for (const [nome, cor, tam] of SPEC) {
    const svg = ReactDOMServer.renderToStaticMarkup(
      React.createElement(COMPONENTES[nome],
        { color: CORES[cor], size: String(tam) }));
    const png = await sharp(Buffer.from(svg), { density: 300 })
      .resize(tam, tam, { fit: "contain",
                          background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png().toBuffer();
    linhas.push(`    "${nome}_${cor}_${tam}": "${png.toString("base64")}",`);
  }
  const py = [
    '"""Dados dos ícones da interface (PNG em base64).',
    "",
    "Arquivo GERADO por tools/gerar_icones.js — não edite à mão.",
    "Em runtime, sigbef/icones.py carrega tudo com tk.PhotoImage(data=...),",
    'que é biblioteca padrão (Tk 8.6 lê PNG nativamente)."""',
    "",
    "ICONES = {",
    ...linhas,
    "}",
    "",
  ].join("\n");
  fs.writeFileSync("sigbef/icones_data.py", py);
  console.log(`OK: sigbef/icones_data.py (${SPEC.length} icones)`);
}

main().catch((e) => { console.error(e); process.exit(1); });
