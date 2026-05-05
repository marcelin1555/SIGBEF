"""
SIGBEF — Tema visual e helpers de UI compartilhados.

Define paleta de cores, fontes padrão, estilos ttk e funções utilitárias
para mensagens.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# Paleta institucional ---------------------------------------------------------
COR_PRIMARIA = "#1F4E79"     # azul escuro
COR_SECUNDARIA = "#2E75B6"   # azul médio
COR_DESTAQUE = "#F2A900"      # amarelo dourado
COR_SUCESSO = "#2E7D32"
COR_ERRO = "#C62828"
COR_AVISO = "#EF6C00"
COR_FUNDO = "#F5F7FA"
COR_FUNDO_ESCURO = "#E8ECF1"
COR_TEXTO = "#1A1A1A"
COR_TEXTO_CLARO = "#FFFFFF"
COR_CARD = "#FFFFFF"
COR_BORDA = "#D5DAE0"

# Fontes ----------------------------------------------------------------------
FONTE_BASE = ("Segoe UI", 10)
FONTE_TITULO = ("Segoe UI Semibold", 22)
FONTE_SUBTITULO = ("Segoe UI Semibold", 14)
FONTE_BOTAO = ("Segoe UI Semibold", 10)
FONTE_BOTAO_GRANDE = ("Segoe UI Semibold", 14)
FONTE_DISPLAY = ("Segoe UI Semibold", 32)
FONTE_MONO = ("Consolas", 10)


def aplicar_tema(root: tk.Misc) -> ttk.Style:
    """Configura o ttk.Style com a paleta institucional."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=COR_FUNDO)

    style.configure(".", font=FONTE_BASE,
                    background=COR_FUNDO, foreground=COR_TEXTO)
    style.configure("TFrame", background=COR_FUNDO)
    style.configure("Card.TFrame", background=COR_CARD, relief="flat")
    style.configure("Sidebar.TFrame", background=COR_PRIMARIA)
    style.configure("Header.TFrame", background=COR_PRIMARIA)

    style.configure("TLabel", background=COR_FUNDO, foreground=COR_TEXTO)
    style.configure("Card.TLabel", background=COR_CARD, foreground=COR_TEXTO)
    style.configure("Titulo.TLabel", font=FONTE_TITULO, foreground=COR_PRIMARIA,
                    background=COR_FUNDO)
    style.configure("Subtitulo.TLabel", font=FONTE_SUBTITULO,
                    foreground=COR_PRIMARIA, background=COR_FUNDO)
    style.configure("Header.TLabel", font=FONTE_SUBTITULO,
                    background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO)
    style.configure("HeaderSmall.TLabel",
                    background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO)
    style.configure("Display.TLabel", font=FONTE_DISPLAY,
                    foreground=COR_PRIMARIA, background=COR_CARD)
    style.configure("Hint.TLabel", foreground="#6B7280", background=COR_FUNDO)
    style.configure("CardHint.TLabel", foreground="#6B7280", background=COR_CARD)
    style.configure("Sucesso.TLabel", foreground=COR_SUCESSO, background=COR_FUNDO)
    style.configure("Erro.TLabel", foreground=COR_ERRO, background=COR_FUNDO)
    style.configure("Aviso.TLabel", foreground=COR_AVISO, background=COR_FUNDO)

    style.configure("TEntry", fieldbackground="white", padding=6)
    style.configure("TCombobox", fieldbackground="white", padding=4)
    style.configure("TSpinbox", fieldbackground="white", padding=4)

    style.configure("TButton", font=FONTE_BOTAO, padding=(14, 8),
                    background=COR_SECUNDARIA, foreground=COR_TEXTO_CLARO,
                    borderwidth=0)
    style.map("TButton",
              background=[("active", COR_PRIMARIA), ("disabled", "#9DB1C8")])

    style.configure("Primario.TButton", font=FONTE_BOTAO_GRANDE,
                    background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO,
                    padding=(18, 10))
    style.map("Primario.TButton",
              background=[("active", "#13365B"), ("disabled", "#9DB1C8")])

    style.configure("Sucesso.TButton", background=COR_SUCESSO,
                    foreground=COR_TEXTO_CLARO)
    style.map("Sucesso.TButton",
              background=[("active", "#1B5E20"), ("disabled", "#9DB1C8")])

    style.configure("Perigo.TButton", background=COR_ERRO,
                    foreground=COR_TEXTO_CLARO)
    style.map("Perigo.TButton",
              background=[("active", "#8E1F1F"), ("disabled", "#D9A0A0")])

    style.configure("Aviso.TButton", background=COR_AVISO,
                    foreground=COR_TEXTO_CLARO)
    style.map("Aviso.TButton",
              background=[("active", "#B85400"), ("disabled", "#E0B79A")])

    style.configure("Sidebar.TButton", font=FONTE_BOTAO_GRANDE,
                    background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO,
                    padding=(20, 14), borderwidth=0, anchor="w")
    style.map("Sidebar.TButton",
              background=[("active", COR_SECUNDARIA),
                          ("selected", COR_SECUNDARIA)])

    # Treeview
    style.configure("Treeview",
                    background="white", fieldbackground="white",
                    foreground=COR_TEXTO, rowheight=28, borderwidth=0,
                    font=("Segoe UI", 10))
    style.configure("Treeview.Heading",
                    background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO,
                    font=("Segoe UI Semibold", 10), padding=8)
    style.map("Treeview.Heading",
              background=[("active", COR_SECUNDARIA)])
    style.map("Treeview",
              background=[("selected", COR_SECUNDARIA)],
              foreground=[("selected", COR_TEXTO_CLARO)])

    # Notebook (abas)
    style.configure("TNotebook", background=COR_FUNDO, borderwidth=0)
    style.configure("TNotebook.Tab",
                    padding=(18, 10), font=("Segoe UI Semibold", 10),
                    background=COR_FUNDO_ESCURO)
    style.map("TNotebook.Tab",
              background=[("selected", COR_CARD)],
              foreground=[("selected", COR_PRIMARIA)])

    return style


def caixa_card(parent, padx=20, pady=20) -> ttk.Frame:
    """Cria um Frame estilizado como 'card' (com fundo branco)."""
    frame = ttk.Frame(parent, style="Card.TFrame", padding=(padx, pady))
    return frame


def linha_separadora(parent, cor=COR_BORDA):
    f = tk.Frame(parent, height=1, bg=cor)
    f.pack(fill="x", pady=8)
    return f


def centralizar_janela(janela: tk.Tk | tk.Toplevel, largura: int, altura: int):
    janela.update_idletasks()
    sw = janela.winfo_screenwidth()
    sh = janela.winfo_screenheight()
    x = (sw - largura) // 2
    y = (sh - altura) // 3
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
