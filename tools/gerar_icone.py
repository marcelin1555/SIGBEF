"""
Gera o ícone .ico do SIGBEF (usado no executável e no instalador) a
partir do logo oficial em assets/sigbef_logo.png.

Uso:
    python tools/gerar_icone.py

Cria assets/sigbef.ico com múltiplos tamanhos (16, 32, 48, 64, 128, 256),
todos derivados do mesmo logo usado no site (site/public/logo.png é uma
cópia idêntica). Requer Pillow (pip install pillow).

Se o logo PNG não existir, cai para uma geração a partir do SVG
programático (requer também cairosvg) e, na ausência de qualquer um
dos dois, para um ícone mínimo com a letra "S" — apenas para o build
não falhar por completo.
"""
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parent.parent
ASSETS = PROJECT / "assets"
ASSETS.mkdir(exist_ok=True)

LOGO_PNG = ASSETS / "sigbef_logo.png"
ICO_OUT = ASSETS / "sigbef.ico"
TAMANHOS = (16, 32, 48, 64, 128, 256)


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


def _salvar_ico_multi_resolucao(imagem_base, destino: Path) -> None:
    """Salva um .ico com todos os TAMANHOS a partir de uma imagem
    quadrada de alta resolução.

    Importante: o PIL só consegue gerar tamanhos MENORES do que a
    imagem base (ele reduz, não aumenta). Por isso a imagem passada
    aqui precisa ser a MAIOR disponível — usar uma imagem pequena
    como base produz um .ico com um único frame borrado/cortado
    (foi exatamente o bug que gerou o ícone antigo, só com "S" 16x16).
    """
    imagem_base = imagem_base.convert("RGBA")
    imagem_base.save(
        destino, format="ICO",
        sizes=[(t, t) for t in TAMANHOS if t <= imagem_base.size[0]],
    )


def gerar_a_partir_do_logo() -> bool:
    """Gera o .ico a partir do logo oficial (assets/sigbef_logo.png),
    o mesmo usado no site. Caminho preferido: não depende de cairosvg."""
    if not LOGO_PNG.exists():
        return False
    try:
        from PIL import Image
    except ImportError:
        print("Pillow não instalado. Rode: pip install pillow")
        return False

    with Image.open(LOGO_PNG) as logo:
        _salvar_ico_multi_resolucao(logo, ICO_OUT)
        tamanho = logo.size
    print(f"OK: {ICO_OUT} (a partir de {LOGO_PNG.name}, "
          f"{tamanho[0]}x{tamanho[1]})")
    return True


def gerar_a_partir_do_svg() -> bool:
    """Fallback: renderiza o SVG programático via cairosvg em 256px
    (a maior resolução) e deriva os demais tamanhos a partir dela."""
    try:
        from PIL import Image
        import cairosvg
    except ImportError:
        return False

    svg_path = ASSETS / "sigbef.svg"
    svg_path.write_text(SVG_TEMPLATE, encoding="utf-8")

    import io
    png_bytes = cairosvg.svg2png(url=str(svg_path), output_width=256,
                                  output_height=256)
    with Image.open(io.BytesIO(png_bytes)) as img:
        _salvar_ico_multi_resolucao(img, ICO_OUT)
    print(f"OK: {ICO_OUT} (a partir do SVG via cairosvg)")
    return True


def gerar_icone_minimo() -> None:
    """Último recurso: ícone só com a letra 'S', usado apenas para o
    build não falhar quando nenhuma das opções acima está disponível."""
    from PIL import Image, ImageDraw, ImageFont

    tamanho_base = max(TAMANHOS)  # gera na maior resolução, reduz depois
    img = Image.new("RGBA", (tamanho_base, tamanho_base), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    margem = tamanho_base // 16
    d.rounded_rectangle(
        [margem, margem, tamanho_base - margem, tamanho_base - margem],
        radius=tamanho_base // 6, fill=(31, 78, 121, 255))
    try:
        font = ImageFont.truetype("arial.ttf", int(tamanho_base * 0.55))
    except OSError:
        font = ImageFont.load_default()
    texto = "S"
    bbox = d.textbbox((0, 0), texto, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((tamanho_base - tw) // 2 - bbox[0],
             (tamanho_base - th) // 2 - bbox[1]),
           texto, fill=(255, 255, 255, 255), font=font)

    _salvar_ico_multi_resolucao(img, ICO_OUT)
    print(f"OK (modo mínimo, apenas 'S'): {ICO_OUT}")
    print("Aviso: este não é o ícone oficial do SIGBEF. Restaure "
          "assets/sigbef_logo.png e rode este script de novo.")


def main():
    if "--svg-only" in sys.argv:
        (ASSETS / "sigbef.svg").write_text(SVG_TEMPLATE, encoding="utf-8")
        print(f"OK: {ASSETS / 'sigbef.svg'}")
        return

    if gerar_a_partir_do_logo():
        return
    print(f"Aviso: {LOGO_PNG.name} não encontrado, tentando gerar do SVG...")
    if gerar_a_partir_do_svg():
        return
    print("Aviso: cairosvg/Pillow indisponíveis para a rota SVG.")
    try:
        gerar_icone_minimo()
    except Exception as e:
        print(f"Aviso: não foi possível gerar nenhum ícone ({e}).")
        print("O build continuará sem ícone customizado.")


if __name__ == "__main__":
    main()
