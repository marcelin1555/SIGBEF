"""
SIGBEF — Tema visual e helpers de UI compartilhados.

Paleta de cores, fontes, estilos ttk e utilitarios. As cores marcadas
com * podem ser personalizadas em Configuracoes -> Aparencia (salvas no
banco, recarregadas no boot).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# Paleta institucional padrao -------------------------------------------------
COR_PRIMARIA = "#1F4E79"
COR_SECUNDARIA = "#2E75B6"
COR_DESTAQUE = "#F2A900"
COR_FUNDO = "#F5F7FA"
COR_SUCESSO = "#2E7D32"
COR_ERRO = "#C62828"
COR_AVISO = "#EF6C00"
COR_FUNDO_ESCURO = "#E8ECF1"
COR_TEXTO = "#1A1A1A"
COR_TEXTO_CLARO = "#FFFFFF"
COR_CARD = "#FFFFFF"
COR_BORDA = "#D5DAE0"

FONTE_BASE = ("Segoe UI", 10)
FONTE_TITULO = ("Segoe UI Semibold", 22)
FONTE_SUBTITULO = ("Segoe UI Semibold", 14)
FONTE_BOTAO = ("Segoe UI Semibold", 10)
FONTE_BOTAO_GRANDE = ("Segoe UI Semibold", 14)
FONTE_DISPLAY = ("Segoe UI Semibold", 32)
FONTE_MONO = ("Consolas", 10)


PRESETS = {
    "padrao": {"nome": "Padrão", "descricao": "Azul institucional padrão",
               "primaria": "#1F4E79", "secundaria": "#2E75B6",
               "destaque": "#F2A900", "fundo": "#F5F7FA"},
    "verde_floresta": {"nome": "Verde Floresta", "descricao": "Verde escolar sereno",
                       "primaria": "#1B5E20", "secundaria": "#43A047",
                       "destaque": "#FBC02D", "fundo": "#F1F8E9"},
    "roxo_universitario": {"nome": "Roxo Universitario", "descricao": "Tom academico classico",
                            "primaria": "#4527A0", "secundaria": "#7E57C2",
                            "destaque": "#FFD740", "fundo": "#F3E5F5"},
    "vermelho_academico": {"nome": "Vermelho Academico", "descricao": "Bordo institucional",
                            "primaria": "#8E1F1F", "secundaria": "#C62828",
                            "destaque": "#FFB300", "fundo": "#FFF5F5"},
    "marrom_biblioteca": {"nome": "Marrom Biblioteca", "descricao": "Tom classico de bibliotecas",
                           "primaria": "#4E342E", "secundaria": "#795548",
                           "destaque": "#FFA000", "fundo": "#FAF6F2"},
}


def carregar_personalizacao():
    global COR_PRIMARIA, COR_SECUNDARIA, COR_DESTAQUE, COR_FUNDO
    try:
        from .database import get_config
    except Exception:
        return
    try:
        COR_PRIMARIA = get_config("tema.cor_primaria", COR_PRIMARIA) or COR_PRIMARIA
        COR_SECUNDARIA = get_config("tema.cor_secundaria", COR_SECUNDARIA) or COR_SECUNDARIA
        COR_DESTAQUE = get_config("tema.cor_destaque", COR_DESTAQUE) or COR_DESTAQUE
        COR_FUNDO = get_config("tema.cor_fundo", COR_FUNDO) or COR_FUNDO
    except Exception:
        pass


def aplicar_preset(chave_preset):
    preset = PRESETS.get(chave_preset)
    if not preset:
        return False
    from .database import set_config
    set_config("tema.cor_primaria", preset["primaria"])
    set_config("tema.cor_secundaria", preset["secundaria"])
    set_config("tema.cor_destaque", preset["destaque"])
    set_config("tema.cor_fundo", preset["fundo"])
    return True


def salvar_cores(primaria, secundaria, destaque, fundo):
    from .database import set_config
    set_config("tema.cor_primaria", primaria)
    set_config("tema.cor_secundaria", secundaria)
    set_config("tema.cor_destaque", destaque)
    set_config("tema.cor_fundo", fundo)


def restaurar_padrao():
    aplicar_preset("padrao")


def _ajustar_cor(cor_hex: str, fator: float) -> str:
    """Clareia (fator > 1) ou escurece (fator < 1) uma cor #RRGGBB.

    Usado para derivar estados hover/pressionado de qualquer paleta,
    inclusive as personalizadas — sem cores fixas que só combinam
    com o azul padrão.
    """
    cor_hex = cor_hex.lstrip("#")
    try:
        r, g, b = (int(cor_hex[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return f"#{cor_hex}"
    r, g, b = (max(0, min(255, round(c * fator))) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def aplicar_tema(root):
    carregar_personalizacao()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=COR_FUNDO)

    # Estados derivados da paleta ativa (funciona com qualquer preset)
    hover_prim = _ajustar_cor(COR_PRIMARIA, 0.80)
    press_prim = _ajustar_cor(COR_PRIMARIA, 0.65)
    hover_sec = _ajustar_cor(COR_SECUNDARIA, 0.85)
    press_sec = _ajustar_cor(COR_SECUNDARIA, 0.70)

    style.configure(".", font=FONTE_BASE, background=COR_FUNDO, foreground=COR_TEXTO)
    style.configure("TFrame", background=COR_FUNDO)
    style.configure("Card.TFrame", background=COR_CARD, relief="solid",
                    borderwidth=1, bordercolor=COR_BORDA)
    # Frame interno de um card: mesmo fundo, sem borda propria (evita
    # o efeito "card dentro de card" com bordas duplicadas)
    style.configure("CardInner.TFrame", background=COR_CARD)
    style.configure("Sidebar.TFrame", background=COR_PRIMARIA)
    style.configure("Header.TFrame", background=COR_PRIMARIA)

    style.configure("TLabel", background=COR_FUNDO, foreground=COR_TEXTO)
    style.configure("Card.TLabel", background=COR_CARD, foreground=COR_TEXTO)
    style.configure("Titulo.TLabel", font=FONTE_TITULO, foreground=COR_PRIMARIA, background=COR_FUNDO)
    style.configure("Subtitulo.TLabel", font=FONTE_SUBTITULO, foreground=COR_PRIMARIA, background=COR_FUNDO)
    style.configure("Header.TLabel", font=FONTE_SUBTITULO, background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO)
    style.configure("HeaderSmall.TLabel", background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO)
    style.configure("Display.TLabel", font=FONTE_DISPLAY, foreground=COR_PRIMARIA, background=COR_CARD)
    style.configure("Hint.TLabel", foreground="#6B7280", background=COR_FUNDO)
    style.configure("CardHint.TLabel", foreground="#6B7280", background=COR_CARD)
    style.configure("Sucesso.TLabel", foreground=COR_SUCESSO, background=COR_FUNDO)
    style.configure("Erro.TLabel", foreground=COR_ERRO, background=COR_FUNDO)
    style.configure("Aviso.TLabel", foreground=COR_AVISO, background=COR_FUNDO)

    # Campos: borda sutil que ganha a cor do tema ao receber foco
    style.configure("TEntry", fieldbackground="white", padding=6,
                    bordercolor=COR_BORDA, lightcolor="white", darkcolor="white")
    style.map("TEntry",
              bordercolor=[("focus", COR_SECUNDARIA)],
              lightcolor=[("focus", COR_SECUNDARIA)],
              darkcolor=[("focus", COR_SECUNDARIA)])
    style.configure("TCombobox", fieldbackground="white", padding=4,
                    bordercolor=COR_BORDA, arrowcolor=COR_PRIMARIA)
    style.map("TCombobox", bordercolor=[("focus", COR_SECUNDARIA)])
    style.configure("TSpinbox", fieldbackground="white", padding=4,
                    bordercolor=COR_BORDA, arrowcolor=COR_PRIMARIA)
    style.map("TSpinbox", bordercolor=[("focus", COR_SECUNDARIA)])

    style.configure("TButton", font=FONTE_BOTAO, padding=(14, 8),
                    background=COR_SECUNDARIA, foreground=COR_TEXTO_CLARO, borderwidth=0)
    style.map("TButton", background=[("pressed", press_sec), ("active", hover_sec),
                                      ("disabled", "#9DB1C8")])

    style.configure("Primario.TButton", font=FONTE_BOTAO_GRANDE,
                    background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO, padding=(18, 10))
    style.map("Primario.TButton", background=[("pressed", press_prim), ("active", hover_prim),
                                               ("disabled", "#9DB1C8")])

    style.configure("Sucesso.TButton", background=COR_SUCESSO, foreground=COR_TEXTO_CLARO)
    style.map("Sucesso.TButton", background=[("active", "#1B5E20"), ("disabled", "#9DB1C8")])

    style.configure("Perigo.TButton", background=COR_ERRO, foreground=COR_TEXTO_CLARO)
    style.map("Perigo.TButton", background=[("active", "#8E1F1F"), ("disabled", "#D9A0A0")])

    style.configure("Aviso.TButton", background=COR_AVISO, foreground=COR_TEXTO_CLARO)
    style.map("Aviso.TButton", background=[("active", "#B85400"), ("disabled", "#E0B79A")])

    style.configure("Sidebar.TButton", font=FONTE_BOTAO_GRANDE,
                    background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO,
                    padding=(20, 14), borderwidth=0, anchor="w",
                    focuscolor=COR_PRIMARIA)  # some com a borda pontilhada de foco
    style.map("Sidebar.TButton",
              background=[("active", COR_SECUNDARIA), ("selected", COR_SECUNDARIA)],
              focuscolor=[("selected", COR_SECUNDARIA)])

    # Checkbuttons/radios sem "flash" cinza no hover
    style.configure("TCheckbutton", background=COR_FUNDO)
    style.map("TCheckbutton", background=[("active", COR_FUNDO)])
    style.configure("TRadiobutton", background=COR_FUNDO)
    style.map("TRadiobutton", background=[("active", COR_FUNDO)])

    style.configure("Treeview", background="white", fieldbackground="white",
                    foreground=COR_TEXTO, rowheight=30, borderwidth=0, font=("Segoe UI", 10))
    style.configure("Treeview.Heading", background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO,
                    font=("Segoe UI Semibold", 10), padding=(8, 7), relief="flat")
    style.map("Treeview.Heading",
              background=[("pressed", press_prim), ("active", COR_SECUNDARIA)])
    style.map("Treeview", background=[("selected", COR_SECUNDARIA)],
              foreground=[("selected", COR_TEXTO_CLARO)])

    # Scrollbars discretas, na paleta do tema
    style.configure("TScrollbar", background=COR_FUNDO_ESCURO, troughcolor=COR_FUNDO,
                    bordercolor=COR_FUNDO, arrowcolor=COR_PRIMARIA, borderwidth=0)
    style.map("TScrollbar", background=[("active", COR_BORDA)])

    style.configure("TNotebook", background=COR_FUNDO, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(18, 10),
                    font=("Segoe UI Semibold", 10), background=COR_FUNDO_ESCURO)
    style.map("TNotebook.Tab", background=[("selected", COR_CARD)],
              foreground=[("selected", COR_PRIMARIA)])

    style.configure("TLabelframe", background=COR_FUNDO, bordercolor=COR_BORDA)
    style.configure("TLabelframe.Label", background=COR_FUNDO,
                    foreground=COR_PRIMARIA, font=("Segoe UI Semibold", 10))

    # Cursor de mão nos botões (ttk e tk)
    for classe in ("TButton", "Button"):
        root.bind_class(classe, "<Enter>",
                        lambda e: e.widget.configure(cursor="hand2"), add="+")

    return style


def aplicar_zebra(tree, cor: str | None = None) -> None:
    """Aplica fundo alternado (zebra) nas linhas de uma Treeview populada.

    Chame ao final de cada recarga da tabela. Linhas que já têm tags
    semânticas (ex.: 'atrasado') são preservadas sem zebra, para não
    disputar a cor de fundo.
    """
    tree.tag_configure("zebra", background=cor or COR_FUNDO)
    for i, item in enumerate(tree.get_children()):
        atuais = tree.item(item, "tags")
        if isinstance(atuais, str):
            atuais = (atuais,) if atuais else ()
        atuais = [t for t in atuais if t != "zebra"]
        if i % 2 and not atuais:
            atuais.append("zebra")
        tree.item(item, tags=atuais)


def caixa_card(parent, padx=20, pady=20):
    return ttk.Frame(parent, style="Card.TFrame", padding=(padx, pady))


def linha_separadora(parent, cor=None):
    f = tk.Frame(parent, height=1, bg=cor or COR_BORDA)
    f.pack(fill="x", pady=8)
    return f


def centralizar_janela(janela, largura, altura):
    janela.update_idletasks()
    sw = janela.winfo_screenwidth()
    sh = janela.winfo_screenheight()
    x = (sw - largura) // 2
    y = (sh - altura) // 3
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
