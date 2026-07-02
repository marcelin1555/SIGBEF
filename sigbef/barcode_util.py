"""
SIGBEF — Geração e renderização de códigos de barras.

Gera identificadores únicos (EX.../US...) e renderiza códigos de barras
**Code 128 reais** (escaneáveis por qualquer leitor USB), em Python puro,
sem dependência externa. Renderiza tanto em canvas Tk (preview na tela)
quanto em SVG/HTML pronto para impressão (folha de etiquetas).
"""
from __future__ import annotations

import html
import random
import string
from datetime import datetime

PREFIXO_EXEMPLAR = "EX"
PREFIXO_USUARIO = "US"


def gerar_codigo_exemplar() -> str:
    """Gera um código de barras único para um exemplar de livro."""
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    sufixo = "".join(random.choices(string.digits, k=4))
    return f"{PREFIXO_EXEMPLAR}{timestamp}{sufixo}"


def gerar_codigo_usuario() -> str:
    """Gera um código de barras único para o cartão de um usuário."""
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    sufixo = "".join(random.choices(string.digits, k=4))
    return f"{PREFIXO_USUARIO}{timestamp}{sufixo}"


# ---------------------------------------------------------------------------
# Code 128 (Code Set B) — codificação real, escaneável
# ---------------------------------------------------------------------------
# Larguras de cada símbolo (valores 0..106). Cada dígito é a largura de um
# elemento, alternando barra/espaço começando por barra. Tabela padrão Code 128.
_CODE128 = [
    "212222", "222122", "222221", "121223", "121322", "131222", "122213",
    "122312", "132212", "221213", "221312", "231212", "112232", "122132",
    "122231", "113222", "123122", "123221", "223211", "221132", "221231",
    "213212", "223112", "312131", "311222", "321122", "321221", "312212",
    "322112", "322211", "212123", "212321", "232121", "111323", "131123",
    "131321", "112313", "132113", "132311", "211313", "231113", "231311",
    "112133", "112331", "132131", "113123", "113321", "133121", "313121",
    "211331", "231131", "213113", "213311", "213131", "311123", "311321",
    "331121", "312113", "312311", "332111", "314111", "221411", "431111",
    "111224", "111422", "121124", "121421", "141122", "141221", "112214",
    "112412", "122114", "122411", "142112", "142211", "241211", "221114",
    "413111", "241112", "134111", "111242", "121142", "121241", "114212",
    "124112", "124211", "411212", "421112", "421211", "212141", "214121",
    "412121", "111143", "111341", "131141", "114113", "114311", "411113",
    "411311", "113141", "114131", "311141", "411131", "211412", "211214",
    "211232", "2331112",
]
_START_B = 104
_STOP = 106


def _code128b_valores(texto: str) -> list[int]:
    """Sequência de valores Code 128B (start + dados + checksum + stop)."""
    valores = [_START_B]
    for ch in texto:
        o = ord(ch)
        valores.append(o - 32 if 32 <= o <= 126 else 0)  # fora da faixa -> espaço
    soma = valores[0]
    for i, v in enumerate(valores[1:], start=1):
        soma += v * i
    valores.append(soma % 103)
    valores.append(_STOP)
    return valores


def _code128b_barras(texto: str) -> list[tuple[int, bool]]:
    """Lista de (largura_em_modulos, é_barra) do código de barras inteiro."""
    barras: list[tuple[int, bool]] = []
    for v in _code128b_valores(texto):
        barra = True
        for d in _CODE128[v]:
            barras.append((int(d), barra))
            barra = not barra
    return barras


# ---------------------------------------------------------------------------
# Renderização em canvas Tk (preview na tela)
# ---------------------------------------------------------------------------
def desenhar_barras(canvas, codigo: str, x0: int = 10, y0: int = 10,
                    altura: int = 60, largura_unit: int = 2) -> int:
    """Desenha um código de barras Code 128 real em um canvas tkinter.

    `largura_unit` é a largura de um módulo em pixels. Retorna a largura
    total ocupada (px), já incluindo as zonas de silêncio.

    Não apaga desenhos anteriores: várias etiquetas convivem no mesmo
    canvas (quem quiser limpar chama canvas.delete("barcode") antes).
    """
    quiet = 10  # módulos de zona de silêncio de cada lado
    x = x0 + quiet * largura_unit
    for largura, eh_barra in _code128b_barras(codigo):
        w = largura * largura_unit
        if eh_barra:
            canvas.create_rectangle(x, y0, x + w, y0 + altura,
                                    fill="black", outline="", tags="barcode")
        x += w
    x += quiet * largura_unit
    largura_total = x - x0
    canvas.create_text(
        x0 + largura_total / 2, y0 + altura + 12,
        text=codigo, font=("Consolas", 10), tags="barcode")
    return largura_total


# ---------------------------------------------------------------------------
# Renderização em SVG / HTML (impressão de etiquetas)
# ---------------------------------------------------------------------------
def barcode_svg(codigo: str, altura_mm: float = 13.0, modulo_mm: float = 0.33,
                mostrar_texto: bool = True) -> str:
    """Retorna um <svg> com o código de barras Code 128 em milímetros."""
    quiet = 10
    barras = _code128b_barras(codigo)
    total_modulos = sum(w for w, _ in barras) + 2 * quiet
    largura_mm = round(total_modulos * modulo_mm, 3)
    texto_h = 4.5 if mostrar_texto else 0.0
    altura_total = round(altura_mm + texto_h, 3)

    rects = []
    x = quiet * modulo_mm
    for largura, eh_barra in barras:
        w = largura * modulo_mm
        if eh_barra:
            rects.append(
                f'<rect x="{round(x,3)}" y="0" width="{round(w,3)}" '
                f'height="{altura_mm}" fill="#000"/>')
        x += w
    texto = ""
    if mostrar_texto:
        texto = (f'<text x="{largura_mm/2}" y="{altura_mm + 3.4}" '
                 f'text-anchor="middle" font-family="monospace" '
                 f'font-size="3" fill="#000">{html.escape(codigo)}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{largura_mm}mm" height="{altura_total}mm" '
            f'viewBox="0 0 {largura_mm} {altura_total}">'
            f'{"".join(rects)}{texto}</svg>')


def _celula_etiqueta(titulo_e: str, ex: dict) -> str:
    """Uma etiqueta (título já escapado + código de barras + tombo)."""
    cod = ex.get("codigo_barras", "")
    tombo = html.escape(str(ex.get("numero_tombo") or ""))
    svg = barcode_svg(cod)
    return ('<div class="etiqueta">'
            f'<div class="et-titulo">{titulo_e}</div>'
            f'<div class="et-barra">{svg}</div>'
            f'<div class="et-tombo">Tombo: {tombo}</div>'
            '</div>')


def etiquetas_html(titulo: str, exemplares: list[dict]) -> str:
    """Monta uma página HTML pronta para impressão com uma etiqueta por
    exemplar (título, código de barras Code 128, tombo e código)."""
    titulo_e = html.escape(titulo or "")
    cels = [_celula_etiqueta(titulo_e, ex) for ex in exemplares]
    return _pagina_etiquetas(titulo_e, cels)


def etiquetas_lote_html(exemplares: list[dict],
                        titulo_pagina: str = "acervo") -> str:
    """Etiquetas de vários livros de uma vez — cada exemplar traz o
    próprio `titulo` no dict (impressão em massa do acervo)."""
    cels = [_celula_etiqueta(html.escape(str(ex.get("titulo") or "")), ex)
            for ex in exemplares]
    return _pagina_etiquetas(html.escape(titulo_pagina), cels)


def _pagina_etiquetas(titulo_e: str, cels: list[str]) -> str:
    """Página HTML completa de etiquetas, pronta para Ctrl+P."""
    return f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<title>Etiquetas — {titulo_e}</title>
<style>
  body {{ font-family: Segoe UI, Arial, sans-serif; margin: 12mm; color: #111; }}
  .topo {{ margin-bottom: 8mm; }}
  .topo h1 {{ font-size: 16px; margin: 0 0 4px; }}
  .dica {{ color: #555; font-size: 13px; }}
  button {{ font-size: 14px; padding: 8px 16px; cursor: pointer;
           background: #1F4E79; color: #fff; border: 0; border-radius: 6px; }}
  .folha {{ display: flex; flex-wrap: wrap; gap: 6mm; }}
  .etiqueta {{ border: 1px solid #bbb; border-radius: 4px; padding: 3mm 4mm;
              display: inline-block; page-break-inside: avoid; }}
  .et-titulo {{ font-size: 11px; font-weight: 600; max-width: 90mm;
               white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
               margin-bottom: 1.5mm; }}
  .et-tombo {{ font-size: 10px; color: #333; margin-top: 1mm; }}
  @media print {{
    body {{ margin: 8mm; }}
    .topo {{ display: none; }}
    .etiqueta {{ border-color: #ddd; }}
  }}
</style></head>
<body>
  <div class="topo">
    <h1>Etiquetas — {titulo_e}</h1>
    <p class="dica">{len(cels)} etiqueta(s). Use o botão abaixo (ou Ctrl+P)
    para imprimir, ou escolha "Salvar como PDF" na impressora.</p>
    <button onclick="window.print()">Imprimir / Salvar PDF</button>
  </div>
  <div class="folha">{"".join(cels)}</div>
</body></html>"""


def cartoes_html(usuarios: list[dict]) -> str:
    """Monta uma página HTML pronta para impressão com um cartão de
    biblioteca por usuário (nome, matrícula, perfil e código de barras),
    no tamanho padrão de crachá/cartão (85,6 × 54 mm)."""
    cels = []
    for u in usuarios:
        nome = html.escape(u.get("nome") or "")
        matricula = html.escape(str(u.get("matricula") or ""))
        perfil = html.escape((u.get("perfil") or "").title())
        turma = html.escape(u.get("turma") or "")
        detalhe = f"{perfil} · {turma}" if turma else perfil
        svg = barcode_svg(u.get("codigo_barras") or "", altura_mm=10.0,
                          modulo_mm=0.25)
        cels.append(
            '<div class="cartao">'
            '<div class="c-topo"><span class="c-marca">SIGBEF</span>'
            '<span class="c-sub">Biblioteca do CEFE</span></div>'
            f'<div class="c-nome">{nome}</div>'
            f'<div class="c-info">Matrícula {matricula} &nbsp;·&nbsp; {detalhe}</div>'
            f'<div class="c-barra">{svg}</div>'
            '</div>')
    return f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<title>Cartões de usuário — SIGBEF</title>
<style>
  body {{ font-family: Segoe UI, Arial, sans-serif; margin: 12mm; color: #111; }}
  .topo {{ margin-bottom: 8mm; }}
  .topo h1 {{ font-size: 16px; margin: 0 0 4px; }}
  .dica {{ color: #555; font-size: 13px; }}
  button {{ font-size: 14px; padding: 8px 16px; cursor: pointer;
           background: #1F4E79; color: #fff; border: 0; border-radius: 6px; }}
  .folha {{ display: flex; flex-wrap: wrap; gap: 6mm; }}
  .cartao {{ width: 85.6mm; height: 54mm; border: 1px solid #bbb;
            border-radius: 3mm; overflow: hidden; page-break-inside: avoid;
            display: flex; flex-direction: column; }}
  .c-topo {{ background: #1F4E79; color: #fff; padding: 2.5mm 4mm;
            border-bottom: 1mm solid #F2A900; display: flex;
            justify-content: space-between; align-items: baseline; }}
  .c-marca {{ font-size: 13px; font-weight: 700; letter-spacing: 0.5px; }}
  .c-sub {{ font-size: 9px; opacity: 0.85; }}
  .c-nome {{ font-size: 13px; font-weight: 600; padding: 2.5mm 4mm 0;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .c-info {{ font-size: 10px; color: #444; padding: 0.5mm 4mm 0; }}
  .c-barra {{ margin-top: auto; padding: 0 4mm 2.5mm; text-align: center; }}
  @media print {{
    body {{ margin: 8mm; }}
    .topo {{ display: none; }}
  }}
</style></head>
<body>
  <div class="topo">
    <h1>Cartões de usuário — SIGBEF</h1>
    <p class="dica">{len(usuarios)} cartão(ões). Use o botão abaixo (ou Ctrl+P)
    para imprimir, ou escolha "Salvar como PDF" na impressora.</p>
    <button onclick="window.print()">Imprimir / Salvar PDF</button>
  </div>
  <div class="folha">{"".join(cels)}</div>
</body></html>"""
