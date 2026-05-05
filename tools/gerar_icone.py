"""
Gera um ícone .ico para o SIGBEF a partir de um desenho programático.

Uso:
    python tools/gerar_icone.py

Cria assets/sigbef.ico com múltiplos tamanhos (16, 32, 48, 64, 128, 256).

Não exige Pillow se for chamado com --svg-only (gera apenas SVG).
"""
from pathlib import Path
import struct
import sys


PROJECT = Path(__file__).resolve().parent.parent
ASSETS = PROJECT / "assets"
ASSETS.mkdir(exist_ok=True)


SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#2E75B6"/>
      <stop offset="100%" stop-color="#1F4E79"/>
    </linearGradient>
  </defs>
  <rect width="256" height="256" rx="44" ry="44" fill="url(#g)"/>
  <!-- livro -->
  <g transform="translate(48,52)">
    <rect x="6" y="6" width="148" height="152" rx="6" ry="6" fill="#FFFFFF" opacity="0.18"/>
    <rect x="0" y="0" width="148" height="152" rx="6" ry="6" fill="#FFFFFF"/>
    <rect x="0" y="0" width="148" height="22" fill="#F2A900"/>
    <rect x="14" y="42" width="120" height="6" rx="3" fill="#1F4E79"/>
    <rect x="14" y="58" width="100" height="4" rx="2" fill="#9DB7CC"/>
    <rect x="14" y="72" width="110" height="4" rx="2" fill="#9DB7CC"/>
    <rect x="14" y="86" width="80"  height="4" rx="2" fill="#9DB7CC"/>
    <!-- código de barras -->
    <g transform="translate(14,108)">
      <rect width="3" height="34" fill="#1F4E79"/>
      <rect x="6"  width="2" height="34" fill="#1F4E79"/>
      <rect x="11" width="4" height="34" fill="#1F4E79"/>
      <rect x="18" width="2" height="34" fill="#1F4E79"/>
      <rect x="23" width="3" height="34" fill="#1F4E79"/>
      <rect x="29" width="5" height="34" fill="#1F4E79"/>
      <rect x="37" width="2" height="34" fill="#1F4E79"/>
      <rect x="42" width="4" height="34" fill="#1F4E79"/>
      <rect x="49" width="2" height="34" fill="#1F4E79"/>
      <rect x="54" width="3" height="34" fill="#1F4E79"/>
      <rect x="60" width="5" height="34" fill="#1F4E79"/>
      <rect x="68" width="2" height="34" fill="#1F4E79"/>
      <rect x="73" width="4" height="34" fill="#1F4E79"/>
      <rect x="80" width="2" height="34" fill="#1F4E79"/>
      <rect x="85" width="3" height="34" fill="#1F4E79"/>
      <rect x="91" width="2" height="34" fill="#1F4E79"/>
      <rect x="96" width="5" height="34" fill="#1F4E79"/>
      <rect x="104" width="3" height="34" fill="#1F4E79"/>
      <rect x="110" width="2" height="34" fill="#1F4E79"/>
      <rect x="115" width="4" height="34" fill="#1F4E79"/>
    </g>
  </g>
  <!-- texto SIGBEF (estilizado) -->
  <text x="128" y="232" text-anchor="middle"
        font-family="Segoe UI, Arial, sans-serif"
        font-weight="700" font-size="28" fill="#FFFFFF"
        letter-spacing="2">SIGBEF</text>
</svg>"""


def salvar_svg() -> Path:
    out = ASSETS / "sigbef.svg"
    out.write_text(SVG_TEMPLATE, encoding="utf-8")
    print(f"OK: {out}")
    return out


def converter_para_png_e_ico() -> None:
    """Tenta usar Pillow + cairosvg para converter o SVG em ICO."""
    try:
        from PIL import Image
    except ImportError:
        print("Pillow nao instalado. Pulando geracao do .ico.")
        print("Para gerar o icone .ico, instale: pip install pillow cairosvg")
        return

    try:
        import cairosvg
    except ImportError:
        # Fallback: cria icone PNG simples sem SVG
        _criar_icone_simples()
        return

    svg_path = ASSETS / "sigbef.svg"
    pngs = []
    for tamanho in (16, 32, 48, 64, 128, 256):
        png = ASSETS / f"sigbef_{tamanho}.png"
        cairosvg.svg2png(url=str(svg_path), write_to=str(png),
                          output_width=tamanho, output_height=tamanho)
        pngs.append(png)

    images = [Image.open(p) for p in pngs]
    ico = ASSETS / "sigbef.ico"
    images[0].save(ico, format="ICO",
                   sizes=[(p.size[0], p.size[1]) for p in images])
    print(f"OK: {ico}")
    for p in pngs:
        p.unlink()


def _criar_icone_simples():
    """Cria um ícone .ico simples com apenas Pillow (sem SVG)."""
    from PIL import Image, ImageDraw, ImageFont

    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    for s in sizes:
        img = Image.new("RGBA", s, (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Fundo arredondado
        margem = max(1, s[0] // 16)
        d.rounded_rectangle([margem, margem, s[0]-margem, s[1]-margem],
                              radius=s[0] // 6, fill=(31, 78, 121, 255))
        # Letra S
        try:
            font_size = int(s[0] * 0.55)
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        text = "S"
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((s[0]-tw)//2 - bbox[0], (s[1]-th)//2 - bbox[1]),
               text, fill=(255, 255, 255, 255), font=font)
        images.append(img)

    ico = ASSETS / "sigbef.ico"
    images[0].save(ico, format="ICO",
                   sizes=[s for s in sizes])
    print(f"OK (modo simples): {ico}")


def main():
    salvar_svg()
    if "--svg-only" in sys.argv:
        return
    try:
        converter_para_png_e_ico()
    except Exception as e:
        print(f"Aviso: nao foi possivel gerar .ico ({e}).")
        print("O build continua sem icone customizado.")


if __name__ == "__main__":
    main()
