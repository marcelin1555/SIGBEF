"""
SIGBEF — Gráficos desenhados à mão em Canvas do Tkinter.

Sem matplotlib, sem Pillow, sem nada novo: o projeto roda com a
biblioteca padrão do Python e essa regra vale aqui como valeu para o
código de barras (`barcode_util`) e para o QR code (`qr_util`). Um
gráfico de barras é retângulo e texto — não justifica arrastar 30 MB de
dependência para dentro do instalador de uma escola.

As cores saem de `ui_tema` **na hora de desenhar**, nunca no import: a
escola pode ter paleta personalizada, e `aplicar_tema()` recalcula os
tons derivados quando ela troca.
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Sequence

from . import ui_tema as tema

# Espaço para os rótulos ao redor da área de plotagem.
_MARGEM_ESQ = 46
_MARGEM_DIR = 12
_MARGEM_TOPO = 14
_MARGEM_BASE = 34

_FONTE_ROTULO = ("Segoe UI", 8)
_FONTE_VALOR = ("Segoe UI Semibold", 8)


def _texto_legivel(canvas: tk.Canvas, x: int, y: int, texto: str,
                   largura_max: int, **kw) -> None:
    """Escreve encurtando com reticências quando não couber.

    Nome de turma e de categoria variam muito de tamanho; sem isto, um
    rótulo comprido invade o gráfico do lado.
    """
    fonte = kw.pop("font", _FONTE_ROTULO)
    item = canvas.create_text(x, y, text=texto, font=fonte, **kw)
    while texto and canvas.bbox(item)[2] - canvas.bbox(item)[0] > largura_max:
        texto = texto[:-1]
        canvas.itemconfigure(item, text=texto.rstrip() + "…")


class GraficoBarras(tk.Canvas):
    """Barras horizontais com rótulo à esquerda e valor à direita.

    Horizontal, e não vertical, porque os rótulos daqui são palavras
    ("3º ano B", "Literatura Brasileira") — na vertical elas teriam que
    ser giradas ou abreviadas, e ninguém lê gráfico de cabeça virada.
    """

    def __init__(self, parent, altura_barra: int = 26, espaco: int = 8,
                 largura_rotulo: int = 120, **kw):
        super().__init__(parent, highlightthickness=0,
                         bg=kw.pop("bg", tema.COR_CARD), **kw)
        self._altura_barra = altura_barra
        self._espaco = espaco
        self._largura_rotulo = largura_rotulo
        self._dados: list[tuple[str, float, str]] = []
        self.bind("<Configure>", lambda e: self._desenhar())

    def mostrar(self, dados: Sequence[tuple[str, float]],
                cor: Optional[str] = None) -> None:
        """@param dados pares (rótulo, valor), já na ordem de exibição."""
        self._dados = [(str(r), float(v), cor or tema.COR_PRIMARIA)
                       for r, v in dados]
        altura = (len(self._dados) * (self._altura_barra + self._espaco)
                  + self._espaco)
        self.configure(height=max(altura, 40))
        self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        largura = self.winfo_width()
        if largura <= 1:
            return  # ainda não foi disposto na tela

        if not self._dados:
            self.create_text(largura // 2, 20, text="Sem dados ainda.",
                             fill=tema.COR_TEXTO, font=_FONTE_ROTULO)
            return

        maior = max((v for _, v, _ in self._dados), default=0) or 1
        x0 = self._largura_rotulo + 8
        espaco_valor = 44
        largura_util = max(largura - x0 - espaco_valor, 10)
        y = self._espaco

        for rotulo, valor, cor in self._dados:
            meio = y + self._altura_barra / 2
            _texto_legivel(self, self._largura_rotulo, meio, rotulo,
                           self._largura_rotulo - 4, anchor="e",
                           fill=tema.COR_TEXTO)

            comprimento = max(int(largura_util * valor / maior), 2)
            self.create_rectangle(x0, y, x0 + comprimento,
                                  y + self._altura_barra,
                                  fill=cor, outline="")
            self.create_text(x0 + comprimento + 6, meio,
                             text=f"{valor:g}", anchor="w",
                             font=_FONTE_VALOR, fill=tema.COR_TEXTO)
            y += self._altura_barra + self._espaco


class GraficoLinha(tk.Canvas):
    """Série temporal com pontos, eixo de base e rótulos alternados.

    Usada para o movimento mês a mês. Mês com zero é desenhado como
    zero, não pulado: o vale conta a história (férias, greve) que a
    linha reta esconderia.
    """

    def __init__(self, parent, altura: int = 170, **kw):
        super().__init__(parent, height=altura, highlightthickness=0,
                         bg=kw.pop("bg", tema.COR_CARD), **kw)
        self._dados: list[tuple[str, float]] = []
        self.bind("<Configure>", lambda e: self._desenhar())

    def mostrar(self, dados: Sequence[tuple[str, float]]) -> None:
        self._dados = [(str(r), float(v)) for r, v in dados]
        self._desenhar()

    def _desenhar(self) -> None:
        self.delete("all")
        largura, altura = self.winfo_width(), self.winfo_height()
        if largura <= 1 or altura <= 1:
            return

        if not self._dados:
            self.create_text(largura // 2, altura // 2,
                             text="Sem movimento no período.",
                             fill=tema.COR_TEXTO, font=_FONTE_ROTULO)
            return

        area_l = largura - _MARGEM_ESQ - _MARGEM_DIR
        area_a = altura - _MARGEM_TOPO - _MARGEM_BASE
        if area_l <= 0 or area_a <= 0:
            return

        maior = max((v for _, v in self._dados), default=0) or 1
        # Teto "redondo" para o eixo não terminar num número quebrado.
        teto = max(1, int(maior * 1.15) + 1)

        # Três linhas de grade e seus valores
        for fracao in (0, 0.5, 1):
            y = _MARGEM_TOPO + area_a * (1 - fracao)
            self.create_line(_MARGEM_ESQ, y, _MARGEM_ESQ + area_l, y,
                             fill=tema.COR_BORDA)
            self.create_text(_MARGEM_ESQ - 6, y, anchor="e",
                             text=f"{int(teto * fracao)}",
                             font=_FONTE_ROTULO, fill=tema.COR_TEXTO)

        n = len(self._dados)
        passo = area_l / max(n - 1, 1)
        pontos: list[tuple[float, float]] = []
        for i, (_, valor) in enumerate(self._dados):
            x = _MARGEM_ESQ + (passo * i if n > 1 else area_l / 2)
            y = _MARGEM_TOPO + area_a * (1 - valor / teto)
            pontos.append((x, y))

        if len(pontos) > 1:
            achatado = [c for p in pontos for c in p]
            self.create_line(*achatado, fill=tema.COR_PRIMARIA, width=2,
                             smooth=False)

        # Rótulos alternados quando são muitos, para não empilhar texto.
        pular = 2 if n > 8 else 1
        for i, ((x, y), (rotulo, valor)) in enumerate(zip(pontos, self._dados)):
            self.create_oval(x - 3, y - 3, x + 3, y + 3,
                             fill=tema.COR_PRIMARIA, outline=tema.COR_CARD)
            if i % pular == 0 or i == n - 1:
                self.create_text(x, altura - _MARGEM_BASE + 12,
                                 text=_mes_curto(rotulo),
                                 font=_FONTE_ROTULO, fill=tema.COR_TEXTO)
            if valor:
                self.create_text(x, y - 10, text=f"{valor:g}",
                                 font=_FONTE_VALOR, fill=tema.COR_PRIMARIA)


_MESES = ("jan", "fev", "mar", "abr", "mai", "jun",
          "jul", "ago", "set", "out", "nov", "dez")


def _mes_curto(aaaa_mm: str) -> str:
    """'2026-07' vira 'jul' — e 'jul/26' quando o ano vira."""
    try:
        ano, mes = aaaa_mm.split("-")
        nome = _MESES[int(mes) - 1]
        return nome if mes != "01" else f"{nome}/{ano[2:]}"
    except (ValueError, IndexError):
        return aaaa_mm


class CartaoNumero(tk.Frame):
    """Número grande com rótulo embaixo, para o topo do painel."""

    def __init__(self, parent, titulo: str, valor: str = "—",
                 detalhe: str = "", cor: Optional[str] = None, **kw):
        super().__init__(parent, bg=tema.COR_CARD,
                         highlightbackground=tema.COR_BORDA,
                         highlightthickness=1, **kw)
        self._lbl_valor = tk.Label(
            self, text=valor, bg=tema.COR_CARD,
            fg=cor or tema.COR_PRIMARIA, font=("Segoe UI Semibold", 22))
        self._lbl_valor.pack(anchor="w", padx=14, pady=(12, 0))
        tk.Label(self, text=titulo, bg=tema.COR_CARD, fg=tema.COR_TEXTO,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=14)
        self._lbl_detalhe = tk.Label(
            self, text=detalhe, bg=tema.COR_CARD, fg=tema.COR_TEXTO,
            font=("Segoe UI", 8))
        self._lbl_detalhe.pack(anchor="w", padx=14, pady=(0, 12))

    def atualizar(self, valor: str, detalhe: str = "",
                  cor: Optional[str] = None) -> None:
        self._lbl_valor.configure(text=valor)
        if cor:
            self._lbl_valor.configure(fg=cor)
        self._lbl_detalhe.configure(text=detalhe)
