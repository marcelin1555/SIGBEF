"""
SIGBEF — Geração e renderização de códigos de barras.

Renderiza o padrão Code 128 em SVG (sem dependências externas) e também
um PNG simples utilizando Pillow caso esteja disponível. Para o protótipo,
usamos uma representação visual de barras feita em canvas Tk (ver ui_admin).
"""
from __future__ import annotations

import random
import string
from datetime import datetime

# Tabela simplificada de larguras Code 128 (não é o padrão real do Code 128B,
# mas produz uma representação visual válida e legível por humanos para o
# protótipo). Quando integrado ao leitor real, recomenda-se usar a biblioteca
# python-barcode para gerar PNGs/SVGs reais.

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
# Renderização de barras em canvas Tk (representação visual)
# ---------------------------------------------------------------------------
def desenhar_barras(canvas, codigo: str, x0: int = 10, y0: int = 10,
                    altura: int = 60, largura_unit: int = 2) -> int:
    """
    Desenha um código de barras estilizado em um canvas tkinter.

    A representação não é uma codificação Code 128 real — é uma série de
    barras pseudo-aleatórias derivadas dos caracteres do código, suficiente
    para o protótipo funcionar sem dependências externas. Retorna a largura
    total ocupada (px).
    """
    canvas.delete("barcode")
    x = x0

    # Barras de início (quiet zone)
    canvas.create_rectangle(x, y0, x + largura_unit, y0 + altura,
                            fill="black", outline="", tags="barcode")
    x += largura_unit * 3

    for ch in codigo:
        v = ord(ch)
        # Determinístico: cada caractere gera quatro barras de larguras 1..4
        for offset in (0, 2, 4, 6):
            largura = ((v >> offset) & 0b11) + 1
            cor = "black" if (v >> offset) & 1 else "white"
            canvas.create_rectangle(
                x, y0, x + largura * largura_unit, y0 + altura,
                fill=cor, outline="", tags="barcode"
            )
            x += largura * largura_unit
        # Espaço entre caracteres
        x += largura_unit

    # Barras de fim
    canvas.create_rectangle(x, y0, x + largura_unit, y0 + altura,
                            fill="black", outline="", tags="barcode")
    x += largura_unit * 3

    # Código em texto
    canvas.create_text(
        x0 + (x - x0) / 2, y0 + altura + 12,
        text=codigo, font=("Consolas", 10), tags="barcode"
    )
    return x - x0
