# -*- coding: utf-8 -*-
"""Monta o kit de marca do SIGBEF.

O que o projeto ja tinha: o icone colorido, a versao horizontal e a
compacta. O que faltava, e que um kit precisa ter para servir de
verdade:

  - versao de UMA COR, para carimbo, bordado, serigrafia e fax de
    licitacao -- gradiente nao sobrevive a nada disso;
  - versao NEGATIVA, para aplicar sobre fundo escuro;
  - a folha de uso, com as cores em hex, o espaco de respiro e o
    tamanho minimo.

As cores nao sao escolha deste arquivo: sao lidas de
`sigbef/ui_tema.py`, onde o sistema de verdade as declara. Se a paleta
mudar la, o kit acusa a diferenca em vez de mentir.

Uso:
    python assets/marca/gerar_kit_marca.py
"""
import pathlib
import re
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent.parent
ASSETS = RAIZ / "assets"
KIT = ASSETS / "marca"
SVGS = KIT / "svg"
PNGS = KIT / "png"
for d in (SVGS, PNGS):
    d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------ paleta, da fonte real
tema = (RAIZ / "sigbef" / "ui_tema.py").read_text(encoding="utf-8")
m = re.search(r'"padrao":.*?"primaria": "(#\w{6})".*?"secundaria": "(#\w{6})"'
              r'.*?"destaque": "(#\w{6})".*?"fundo": "(#\w{6})"', tema, re.S)
if not m:
    sys.exit("nao consegui ler a paleta de sigbef/ui_tema.py")
PRIM, SEC, DEST, FUNDO = m.groups()
print("paleta lida do sistema: %s %s %s %s" % (PRIM, SEC, DEST, FUNDO))

ORIG = (ASSETS / "sigbef.svg").read_text(encoding="utf-8")


def variante(nome, trocas, descricao):
    """Grava um SVG derivado do icone original."""
    s = ORIG
    for de, para in trocas:
        s = s.replace(de, para)
    s = s.replace("<svg ", "<!-- SIGBEF: %s -->\n<svg " % descricao, 1)
    (SVGS / (nome + ".svg")).write_text(s, encoding="utf-8")
    return nome


# 1. Uma cor (navy solido sobre transparente): carimbo, serigrafia
variante(
    "sigbef-icone-monocromatico",
    [('fill="url(#g)"', 'fill="%s"' % PRIM),
     ('fill="#FFFFFF" opacity="0.18"', 'fill="none"'),
     ('fill="#F2A900"', 'fill="%s"' % PRIM),
     # As linhas finas do miolo eram cinza-azulado. Em branco elas
     # sumiam dentro do livro branco; na cor da marca, aparecem.
     ('fill="#9DB7CC"', 'fill="%s"' % PRIM)],
    "uma cor, para carimbo e serigrafia")

# 2. Negativo: sobre fundo escuro.
#
# Nao basta pintar tudo de branco -- a primeira tentativa virou um
# quadrado branco vazio, porque o miolo do livro tambem era branco e
# engoliu as linhas e o codigo de barras. Aqui o livro fica VAZADO, so
# com contorno, e o detalhe branco aparece contra o fundo escuro de quem
# aplica a marca.
variante(
    "sigbef-icone-negativo",
    [('fill="url(#g)"', 'fill="none"'),
     ('fill="#FFFFFF" opacity="0.18"', 'fill="none"'),
     ('rx="6" ry="6" fill="#FFFFFF"',
      'rx="6" ry="6" fill="none" stroke="#FFFFFF" stroke-width="7"'),
     ('fill="#F2A900"', 'fill="#FFFFFF"'),
     ('fill="#1F4E79"', 'fill="#FFFFFF"'),
     ('fill="#9DB7CC"', 'fill="#FFFFFF"')],
    "negativo vazado, para fundo escuro")

# 3. Preto puro: documento em preto e branco, fax, fotocopia
variante(
    "sigbef-icone-preto",
    [('fill="url(#g)"', 'fill="#000000"'),
     ('fill="#FFFFFF" opacity="0.18"', 'fill="none"'),
     ('fill="#F2A900"', 'fill="#000000"'),
     ('fill="#1F4E79"', 'fill="#000000"'),
     ('fill="#9DB7CC"', 'fill="#FFFFFF"')],
    "preto puro, para fotocopia")

# --------------------------------------- copia os originais para o kit
for origem, destino in (
        ("sigbef.svg", "sigbef-icone-colorido.svg"),
        ("sigbef_logo_horizontal.svg", "sigbef-horizontal.svg"),
        ("sigbef_logo_horizontal_compacto.svg", "sigbef-horizontal-compacto.svg")):
    (SVGS / destino).write_text(
        (ASSETS / origem).read_text(encoding="utf-8"), encoding="utf-8")

print("SVGs no kit:", len(list(SVGS.glob("*.svg"))))

# ------------------------------------------------------ PNG em tamanhos
NODE = "C:/Users/uemas/node_modules"
tarefas = []
for svg in sorted(SVGS.glob("*.svg")):
    larguras = (256, 512, 1024) if "icone" in svg.name else (800, 1600, 3200)
    for w in larguras:
        tarefas.append((svg.name, w))

script = """
const sharp = require('sharp');
const t = %s;
(async () => {
  for (const [nome, w] of t) {
    const base = nome.replace('.svg','');
    await sharp('%s/' + nome, {density: 400})
      .resize({width: w})
      .png()
      .toFile('%s/' + base + '-' + w + '.png');
  }
  console.log('PNGs gerados: ' + t.length);
})();
""" % (str([[n, w] for n, w in tarefas]).replace("'", '"'),
       SVGS.as_posix(), PNGS.as_posix())

r = subprocess.run(["node", "-e", script],
                   env={**__import__("os").environ, "NODE_PATH": NODE},
                   capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip()[:300])
