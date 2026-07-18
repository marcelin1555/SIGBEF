"""Ícones da interface (Font Awesome embutido, sem dependência externa).

Os PNGs vivem em `icones_data.py` como base64, gerados em tempo de
desenvolvimento por tools/gerar_icones.js. Aqui só existe stdlib:
tk.PhotoImage lê PNG nativamente no Tk 8.6 (mínimo suportado pelo app).

As cores são fixas de propósito, pra não brigar com paletas
personalizadas: "branco" pra sidebar/cabeçalho (fundo primário),
"cinza" neutro pros cards, e "verde"/"vermelho" apenas nos cards de
convenção universal (disponível / atraso).
"""
from __future__ import annotations

import tkinter as tk

from .icones_data import ICONES

# Cache: PhotoImage some da tela se for coletada pelo GC — guardar a
# referência aqui é obrigatório, não otimização.
_cache: dict[str, tk.PhotoImage] = {}


def icone(nome: str, cor: str = "branco", tamanho: int = 16) -> tk.PhotoImage:
    """PhotoImage do ícone pedido (ex.: icone("livro", "cinza", 20)).

    Requer um Tk root já criado. Levanta KeyError se a combinação não
    foi gerada — a lista canônica está em tools/gerar_icones.js.
    """
    chave = f"{nome}_{cor}_{tamanho}"
    if chave not in _cache:
        _cache[chave] = tk.PhotoImage(data=ICONES[chave])
    return _cache[chave]


def limpar_cache() -> None:
    """Descarta as imagens (usado ao trocar de root em testes)."""
    _cache.clear()
