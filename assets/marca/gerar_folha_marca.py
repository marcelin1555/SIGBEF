# -*- coding: utf-8 -*-
"""Folha de uso da marca SIGBEF.

Um kit sem folha de uso e uma pasta de arquivos: a primeira pessoa que
precisar aplicar a marca vai esticar, recolorir ou apertar contra a
borda. Esta folha responde as perguntas que aparecem na hora --- qual
versao usar, qual cor, quanto respiro, tamanho minimo.

As cores sao lidas de `sigbef/ui_tema.py`. Se a paleta do sistema mudar,
esta folha muda junto.

Uso:
    python assets/marca/gerar_folha_marca.py
"""
import pathlib
import re
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = pathlib.Path(__file__).resolve().parent.parent.parent
KIT = RAIZ / "assets" / "marca"
PNG = KIT / "png"

tema = (RAIZ / "sigbef" / "ui_tema.py").read_text(encoding="utf-8")
m = re.search(r'"padrao":.*?"primaria": "(#\w{6})".*?"secundaria": "(#\w{6})"'
              r'.*?"destaque": "(#\w{6})".*?"fundo": "(#\w{6})"', tema, re.S)
if not m:
    sys.exit("nao consegui ler a paleta de sigbef/ui_tema.py")
HEX = dict(zip(("primaria", "secundaria", "destaque", "fundo"), m.groups()))


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


NAVY, AZUL, OURO, FUNDO = (rgb(HEX[k]) for k in
                           ("primaria", "secundaria", "destaque", "fundo"))
BRANCO, TEXTO, CINZA = (255, 255, 255), (0x1A, 0x1A, 0x1A), (0x6B, 0x77, 0x84)
BORDA, VERMELHO = (0xD8, 0xE0, 0xE8), (0xC6, 0x28, 0x28)

L, A = 2000, 3990           # alto o bastante para a folha inteira
img = Image.new("RGB", (L, A), BRANCO)
d = ImageDraw.Draw(img)
F = {"n": "C:/Windows/Fonts/segoeui.ttf",
     "b": "C:/Windows/Fonts/segoeuib.ttf",
     "i": "C:/Windows/Fonts/segoeuii.ttf",
     # Semibold de verdade, o peso que o sistema usa nos titulos
     "sb": "C:/Windows/Fonts/seguisb.ttf",
     # Times, para a amostra ser escrita na propria letra que nomeia
     "t": "C:/Windows/Fonts/times.ttf",
     "tb": "C:/Windows/Fonts/timesbd.ttf"}
estouros = []


def fonte(t, tipo="n"):
    return ImageFont.truetype(F[tipo], t)


def txt(x, y, s, tam=30, cor=TEXTO, tipo="n", centro=False, limite=None):
    f = fonte(tam, tipo)
    w = d.textlength(s, font=f)
    if limite and w > limite:
        estouros.append("'%s' (%.0fpx, cabe %d)" % (s[:40], w, limite))
    # Guarda vertical: a primeira versao desta folha teve a secao 5
    # cortada no rodape porque so a largura era conferida.
    if y + tam + 6 > A:
        estouros.append("'%s' passa da altura da folha (y=%d, folha=%d)"
                        % (s[:40], y + tam, A))
    d.text((x - w / 2 if centro else x, y), s, font=f, fill=cor)
    return w


def secao(y, n, titulo):
    d.rectangle([120, y, 132, y + 44], fill=OURO)
    txt(160, y - 2, "%s  %s" % (n, titulo), 34, NAVY, "b")
    return y + 78


def colar(caminho, x, y, larg, fundo=None):
    im = Image.open(caminho).convert("RGBA")
    alt = round(larg * im.height / im.width)
    im = im.resize((larg, alt), Image.LANCZOS)
    base = Image.new("RGBA", (larg, alt), (fundo or BRANCO) + (255,))
    base.alpha_composite(im)
    img.paste(base.convert("RGB"), (x, y))
    return alt


# ------------------------------------------------------------ cabecalho
d.rectangle([0, 0, L, 300], fill=NAVY)
colar(PNG / "sigbef-icone-negativo-256.png", 120, 66, 168, NAVY)
txt(330, 96, "SIGBEF", 76, BRANCO, "b")
txt(332, 190, "Manual de uso da marca", 30, (0xBF, 0xD4, 0xE8))
txt(L - 120 - d.textlength("versão 1", fonte(26)), 200, "versão 1", 26,
    (0xBF, 0xD4, 0xE8))

y = 400

# ------------------------------------------------------- 1. as versões
y = secao(y, "1", "As quatro versões, e quando usar cada uma")
itens = [
    ("sigbef-icone-colorido-512.png", BRANCO, "Colorida",
     "Uso padrão. Tela, site, slide,\nimpressão colorida."),
    ("sigbef-icone-monocromatico-512.png", BRANCO, "Uma cor",
     "Carimbo, serigrafia, bordado.\nGradiente não sobrevive a isso."),
    ("sigbef-icone-negativo-512.png", NAVY, "Negativa",
     "Sobre fundo escuro ou foto.\nNunca a colorida sobre escuro."),
    ("sigbef-icone-preto-512.png", BRANCO, "Preta",
     "Fotocópia, fax, documento\nem preto e branco."),
]
for i, (arq, bg, nome, uso) in enumerate(itens):
    x = 120 + i * 450
    d.rounded_rectangle([x, y, x + 400, y + 470], 16, outline=BORDA, width=3)
    colar(PNG / arq, x + 100, y + 40, 200, bg)
    txt(x + 200, y + 270, nome, 32, NAVY, "b", centro=True)
    for j, linha in enumerate(uso.split("\n")):
        txt(x + 200, y + 330 + j * 38, linha, 24, CINZA, centro=True)
y += 560

# ------------------------------------------------------ 2. horizontal
y = secao(y, "2", "Versão horizontal, para cabeçalho e crachá")
alt = colar(PNG / "sigbef-horizontal-1600.png", 120, y, 1000)
txt(1180, y + 20, "Completa", 28, NAVY, "b")
txt(1180, y + 66, "Quando há largura sobrando:", 24, CINZA)
txt(1180, y + 104, "papel timbrado, banner, site.", 24, CINZA)
y += alt + 40
alt = colar(PNG / "sigbef-horizontal-compacto-1600.png", 120, y, 700)
txt(1180, y + 20, "Compacta", 28, NAVY, "b")
txt(1180, y + 66, "Espaço apertado: crachá,", 24, CINZA)
txt(1180, y + 104, "fita, rodapé, assinatura.", 24, CINZA)
y += alt + 90

# ------------------------------------------------------------ 3. cores
y = secao(y, "3", "Cores")
cores = [("Azul institucional", HEX["primaria"], NAVY,
          "Cor principal. Texto, cabeçalho, marca."),
         ("Azul claro", HEX["secundaria"], AZUL,
          "Apoio, links, estados de destaque."),
         ("Âmbar", HEX["destaque"], OURO,
          "Só para chamar atenção. Nunca em bloco grande."),
         ("Fundo", HEX["fundo"], FUNDO,
          "Fundo das telas. Quase branco, de propósito.")]
for i, (nome, hx, cor, uso) in enumerate(cores):
    x = 120 + i * 450
    d.rounded_rectangle([x, y, x + 400, y + 150], 14, fill=cor,
                        outline=BORDA, width=2)
    txt(x, y + 168, nome, 27, TEXTO, "b")
    txt(x, y + 208, hx.upper(), 26, NAVY, "b")
    r, g, b = cor
    txt(x, y + 246, "RGB %d, %d, %d" % (r, g, b), 22, CINZA)
    for j, linha in enumerate(uso.split(". ")):
        if linha:
            txt(x, y + 288 + j * 32, linha.strip(". ") + ".", 21, CINZA,
                limite=400)
y += 400

# ----------------------------------------------------------- 4. fontes
y = secao(y, "4", "Fontes")

AMOSTRA = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
           "abcdefghijklmnopqrstuvwxyz",
           "0123456789  ÁÉÍÓÚ ÃÕ Ç  , . ; : ! ?")

# --- Segoe UI ---
d.rounded_rectangle([120, y, 940, y + 470], 14, outline=BORDA, width=3)
txt(160, y + 26, "Segoe UI", 52, NAVY, "sb")
txt(160, y + 96, "interface, marca, site e apresentações", 22, CINZA)
for i, linha in enumerate(AMOSTRA):
    txt(160, y + 148 + i * 42, linha, 26, TEXTO, limite=760)
txt(160, y + 296, "Regular", 27, TEXTO)
txt(360, y + 300, "corpo de texto", 21, CINZA)
txt(160, y + 340, "Semibold", 27, TEXTO, "sb")
txt(360, y + 344, "título, rótulo e destaque", 21, CINZA)
txt(160, y + 400, "Fonte do Windows: em Linux e macOS o sistema "
    "substitui pela equivalente.", 20, CINZA, limite=760)

# --- Times New Roman, escrito em Times ---
d.rounded_rectangle([1000, y, 1780, y + 470], 14, outline=BORDA, width=3)
txt(1040, y + 26, "Times New Roman", 46, NAVY, "tb")
txt(1040, y + 96, "somente no relatório de pesquisa", 22, CINZA)
for i, linha in enumerate(AMOSTRA):
    txt(1040, y + 148 + i * 42, linha, 26, TEXTO, "t", limite=720)
txt(1040, y + 300, "Não é escolha de marca: a ABNT exige", 23, TEXTO,
    limite=720)
txt(1040, y + 338, "fonte serifada no trabalho acadêmico.", 23, TEXTO,
    limite=720)
txt(1040, y + 396, "Não troque por Segoe UI ali.", 23, TEXTO, "b",
    limite=720)

y += 510
d.rounded_rectangle([120, y, L - 120, y + 108], 12, fill=(0xF5, 0xF8, 0xFC),
                    outline=BORDA, width=2)
txt(160, y + 20, "A pilha que o código usa, e que deve ser repetida em "
    "qualquer aplicação nova:", 22, CINZA, limite=1600)
txt(160, y + 58, 'system-ui, "Segoe UI", Roboto, sans-serif', 27, NAVY, "b")
y += 168

# --------------------------------------------- 5. respiro e tamanho
y = secao(y, "5", "Espaço de respiro e tamanho mínimo")
cx = 120
lado = 300
d.rectangle([cx - 2, y - 2, cx + lado + 2, y + lado + 2], outline=BORDA,
            width=3)
respiro = lado // 4
d.rectangle([cx + respiro, y + respiro, cx + lado - respiro,
             y + lado - respiro], outline=OURO, width=3)
colar(PNG / "sigbef-icone-colorido-256.png", cx + respiro, y + respiro,
      lado - 2 * respiro)
txt(cx + lado + 50, y + 20,
    "Deixe em volta da marca, livre de qualquer", 25, TEXTO)
txt(cx + lado + 50, y + 58,
    "elemento, uma faixa igual a 1/4 da altura dela.", 25, TEXTO)
txt(cx + lado + 50, y + 116, "Tamanho mínimo", 27, NAVY, "b")
for i, (t, lg) in enumerate((("impressa", "15 mm"), ("em tela", "48 px"))):
    txt(cx + lado + 50, y + 162 + i * 38, "%-10s %s" % (t, lg), 25, CINZA)
colar(PNG / "sigbef-icone-colorido-256.png", cx + lado + 640, y + 150, 48)
txt(cx + lado + 700, y + 158, "← 48 px, o menor aceitável", 22, CINZA)
y += lado + 90

# ------------------------------------------------------------ 5. nao
y = secao(y, "6", "O que não fazer")
nao = ["Não esticar nem achatar: mudar a proporção deforma o livro.",
       "Não trocar as cores por outras fora da paleta acima.",
       "Não aplicar a versão colorida sobre fundo escuro ou foto —"
       " existe a negativa para isso.",
       "Não redesenhar, adicionar sombra, contorno ou brilho.",
       "Não usar abaixo do tamanho mínimo: o código de barras vira borrão."]
for i, item in enumerate(nao):
    yy = y + i * 46
    d.line([132, yy + 16, 152, yy + 32], fill=VERMELHO, width=4)
    d.line([152, yy + 16, 132, yy + 32], fill=VERMELHO, width=4)
    txt(176, yy + 6, item, 25, TEXTO, limite=L - 300)
y += len(nao) * 46 + 40

d.line([120, y, L - 120, y], fill=BORDA, width=2)
txt(120, y + 24,
    "Arquivos em assets/marca — SVG para qualquer tamanho, PNG em 256, "
    "512 e 1024 px (ícone) e 800, 1600 e 3200 px (horizontal).",
    22, CINZA, limite=L - 240)
txt(120, y + 60,
    "As cores são lidas de sigbef/ui_tema.py, onde o próprio sistema as "
    "declara: esta folha e o software não podem divergir.",
    22, CINZA, limite=L - 240)

SAIDA = KIT / "SIGBEF_Manual_da_Marca.png"
img.save(SAIDA)
if estouros:
    print("TEXTO ESTOURANDO:")
    for e in estouros:
        print("  X " + e)
    raise SystemExit(1)
print("gerado:", SAIDA, "%dx%d" % (L, A))
