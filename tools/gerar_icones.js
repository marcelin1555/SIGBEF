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
  FaExclamationTriangle, FaPlus, FaCheck, FaUndoAlt, FaClock,
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
  mais: FaPlus, confirmar: FaCheck, desfazer: FaUndoAlt,
  relogio: FaClock,
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
  // Botões de ação (texto branco) e avisos
  ["mais", "branco", 14], ["confirmar", "branco", 14],
  ["desfazer", "branco", 14], ["relogio", "branco", 16],
  // Tela final do assistente de primeira execução
  ["check", "verde", 28],
  // Menu principal do kiosk: 3 cards grandes coloridos
  ["barcode", "branco", 40], ["desfazer", "branco", 40],
  ["leitor", "branco", 40],
];

async function main() {
  const linhas = [];

  // Logo institucional (a mesma do site). "original" = cores próprias
  // da marca (fundo transparente), usada como ícone de janela.
  for (const tam of [32, 36, 64]) {
    const logo = await sharp("site/public/logo.png")
      .resize(tam, tam, { fit: "contain",
                          background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png().toBuffer();
    linhas.push(`    "logo_original_${tam}": "${logo.toString("base64")}",`);
  }

  // Variante "placa": logo sobre uma plaqueta branca arredondada, pra
  // assentar com contraste sobre a cor primária de QUALQUER paleta
  // (azul sobre azul ou azul sobre marrom ficavam "soltos").
  for (const tam of [28, 36, 48, 56]) {
    const raio = Math.round(tam * 0.22);
    const placa = Buffer.from(
      `<svg width="${tam}" height="${tam}">` +
      `<rect width="${tam}" height="${tam}" rx="${raio}" ry="${raio}" ` +
      `fill="#FFFFFF"/></svg>`);
    const miolo = Math.round(tam * 0.82);
    const logoMenor = await sharp("site/public/logo.png")
      .resize(miolo, miolo, { fit: "contain",
                              background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png().toBuffer();
    const off = Math.round((tam - miolo) / 2);
    const png = await sharp(placa)
      .composite([{ input: logoMenor, left: off, top: off }])
      .png().toBuffer();
    linhas.push(`    "logoplaca_original_${tam}": "${png.toString("base64")}",`);
  }

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
