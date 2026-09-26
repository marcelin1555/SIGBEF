"""
SIGBEF — Tema visual e helpers de UI compartilhados.

Paleta de cores, fontes, estilos ttk e utilitarios. As cores marcadas
com * podem ser personalizadas em Configuracoes -> Aparencia (salvas no
banco, recarregadas no boot).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

# Paleta institucional padrao -------------------------------------------------
COR_PRIMARIA = "#1F4E79"
COR_SECUNDARIA = "#2E75B6"
COR_DESTAQUE = "#F2A900"
COR_FUNDO = "#F5F7FA"
COR_SUCESSO = "#276B2B"
COR_ERRO = "#C62828"
# Verde e laranja escurecidos de propósito. O laranja anterior (#EF6C00)
# tinha contraste de 2,9:1 como texto sobre o fundo; o verde (#2E7D32)
# caía para 4,2:1 no fundo da predefinição Roxo. O mínimo da WCAG para
# texto do tamanho que usamos é 4,5:1, em qualquer predefinição.
COR_AVISO = "#B23C0A"
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


#: Tamanhos de texto oferecidos em Configurações → Aparência.
#: chave gravada no banco → (rótulo, fator sobre o tamanho normal)
TAMANHOS_TEXTO = {
    "normal": ("Normal", 1.0),
    "grande": ("Grande", 1.15),
    "muito_grande": ("Muito grande", 1.3),
}
#: Fator em uso, lido do banco em carregar_personalizacao().
ESCALA = 1.0


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
    global COR_PRIMARIA, COR_SECUNDARIA, COR_DESTAQUE, COR_FUNDO, ESCALA
    try:
        from .database import get_config
    except Exception:
        return
    try:
        COR_PRIMARIA = get_config("tema.cor_primaria", COR_PRIMARIA) or COR_PRIMARIA
        COR_SECUNDARIA = get_config("tema.cor_secundaria", COR_SECUNDARIA) or COR_SECUNDARIA
        COR_DESTAQUE = get_config("tema.cor_destaque", COR_DESTAQUE) or COR_DESTAQUE
        COR_FUNDO = get_config("tema.cor_fundo", COR_FUNDO) or COR_FUNDO
        tamanho = get_config("tema.tamanho_texto", "normal") or "normal"
        ESCALA = TAMANHOS_TEXTO.get(tamanho, TAMANHOS_TEXTO["normal"])[1]
    except Exception:
        pass


def salvar_tamanho_texto(chave: str, executor_id=None) -> bool:
    """Grava o tamanho de texto escolhido (vale a partir da próxima abertura)."""
    if chave not in TAMANHOS_TEXTO:
        return False
    from .servicos import definir_config_auditada
    definir_config_auditada("tema.tamanho_texto", chave, executor_id,
                            "TEMA_ALTERADO")
    return True


def escalar(pixels: int) -> int:
    """Converte uma medida pensada para o texto normal ao tamanho em uso.

    Para larguras e alturas fixas em pixels (menu lateral, cabeçalho,
    altura de linha das tabelas): o texto cresce com o `tk scaling`, mas
    o que foi medido em pixels não — e o texto maior seria cortado.
    """
    return round(pixels * ESCALA)


#: Ordem fixa das chaves de cor — usada pelas três funções abaixo.
CHAVES_COR = ("tema.cor_primaria", "tema.cor_secundaria",
              "tema.cor_destaque", "tema.cor_fundo")


def _gravar_cores(cores, executor_id=None):
    """Grava as quatro cores deixando rastro na auditoria.

    Passa por `servicos.definir_config_auditada` em vez de `set_config`
    direto: mudança de aparência é mudança de configuração do sistema e
    precisa aparecer no histórico como qualquer outra.
    """
    from .servicos import definir_config_auditada
    for chave, valor in zip(CHAVES_COR, cores):
        definir_config_auditada(chave, valor, executor_id, "TEMA_ALTERADO")


def aplicar_preset(chave_preset, executor_id=None):
    preset = PRESETS.get(chave_preset)
    if not preset:
        return False
    _gravar_cores((preset["primaria"], preset["secundaria"],
                   preset["destaque"], preset["fundo"]), executor_id)
    return True


def salvar_cores(primaria, secundaria, destaque, fundo, executor_id=None):
    _gravar_cores((primaria, secundaria, destaque, fundo), executor_id)


def restaurar_padrao(executor_id=None):
    aplicar_preset("padrao", executor_id)


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


def _luminancia(cor_hex: str) -> float:
    """Luminância relativa (0 = preto, 1 = branco), fórmula WCAG."""
    cor_hex = cor_hex.lstrip("#")
    try:
        canais = [int(cor_hex[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    except (ValueError, IndexError):
        return 0.0
    lin = [(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
           for c in canais]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contraste(cor1: str, cor2: str) -> float:
    """Razão de contraste WCAG entre duas cores (1 a 21)."""
    l1, l2 = _luminancia(cor1), _luminancia(cor2)
    claro, escuro = max(l1, l2), min(l1, l2)
    return (claro + 0.05) / (escuro + 0.05)


def primaria_clara_demais(cor_primaria: str) -> bool:
    """True se texto/ícones brancos ficariam ilegíveis sobre a cor.

    A sidebar, o cabeçalho e vários botões usam branco sobre a cor
    primária. Abaixo de ~3:1 de contraste com o branco, o branco some.
    """
    return contraste(cor_primaria, "#FFFFFF") < 3.0


def legivel_com_branco(cor_hex: str, minimo: float = 4.5) -> str:
    """Escurece a cor até o texto branco sobre ela ter contraste `minimo`.

    Os botões e a linha selecionada das tabelas põem texto branco sobre a
    cor secundária. Nas paletas personalizadas — e na predefinição Verde
    Floresta, com 3,3:1 — essa cor pode ser clara demais. Em vez de
    recusar a escolha, usamos um tom mais escuro da mesma cor só onde
    há texto por cima.
    """
    cor = cor_hex
    for _ in range(30):
        if contraste(cor, "#FFFFFF") >= minimo:
            return cor
        cor = _ajustar_cor(cor, 0.93)
    return cor


def _mesclar_branco(cor_hex: str, proporcao: float) -> str:
    """Mistura a cor com branco (proporcao 0..1 = quanto de branco).

    Diferente de _ajustar_cor (multiplicativo), esta mistura desloca a
    cor em direção ao branco preservando o matiz — ideal pra derivar o
    tom "suave" de texto secundário sobre a cor primária de QUALQUER
    paleta, no lugar dos azuis-claros fixos que só combinavam com o
    tema padrão.
    """
    cor_hex = cor_hex.lstrip("#")
    try:
        r, g, b = (int(cor_hex[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return f"#{cor_hex}"
    r, g, b = (round(c + (255 - c) * proporcao) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


# Derivadas da primária, recalculadas em aplicar_tema() (acompanham a
# paleta escolhida, inclusive personalizada)
COR_PRIMARIA_SUAVE = _mesclar_branco(COR_PRIMARIA, 0.65)
COR_PRIMARIA_ESCURA = _ajustar_cor(COR_PRIMARIA, 0.72)


def _suave_sobre_primaria(cor_primaria: str) -> str:
    """Tom claro para texto secundário sobre a cor primária, com 4,5:1."""
    proporcao = 0.65
    suave = _mesclar_branco(cor_primaria, proporcao)
    while contraste(suave, cor_primaria) < 4.5 and proporcao < 0.95:
        proporcao += 0.05
        suave = _mesclar_branco(cor_primaria, proporcao)
    return suave


def aplicar_tema(root):
    global COR_PRIMARIA_SUAVE, COR_PRIMARIA_ESCURA
    carregar_personalizacao()
    COR_PRIMARIA_SUAVE = _suave_sobre_primaria(COR_PRIMARIA)
    COR_PRIMARIA_ESCURA = _ajustar_cor(COR_PRIMARIA, 0.72)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Tamanho do texto: o `tk scaling` diz quantos pixels vale um ponto,
    # então aumentá-lo aumenta toda fonte dada em pontos — que são todas
    # as do sistema — sem mexer em cada tela. O valor original fica
    # guardado para o fator não se acumular se o tema for reaplicado.
    base = getattr(root, "_escala_base", None)
    if base is None:
        base = float(root.tk.call("tk", "scaling"))
        root._escala_base = base
    root.tk.call("tk", "scaling", base * ESCALA)

    root.configure(bg=COR_FUNDO)

    # Onde há texto branco sobre a secundária, a versão legível dela
    sec = legivel_com_branco(COR_SECUNDARIA)

    # Estados derivados da paleta ativa (funciona com qualquer preset)
    hover_prim = _ajustar_cor(COR_PRIMARIA, 0.80)
    press_prim = _ajustar_cor(COR_PRIMARIA, 0.65)
    hover_sec = _ajustar_cor(sec, 0.85)
    press_sec = _ajustar_cor(sec, 0.70)

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
    # A borda de 1 px mudando de cor é sutil demais para quem enxerga
    # pouco: o campo em foco também ganha um fundo levemente colorido.
    fundo_foco = _mesclar_branco(COR_SECUNDARIA, 0.88)
    style.map("TEntry",
              fieldbackground=[("focus", fundo_foco)],
              bordercolor=[("focus", sec)],
              lightcolor=[("focus", sec)],
              darkcolor=[("focus", sec)])
    style.configure("TCombobox", fieldbackground="white", padding=4,
                    bordercolor=COR_BORDA, arrowcolor=COR_PRIMARIA)
    style.map("TCombobox", bordercolor=[("focus", sec)])
    style.configure("TSpinbox", fieldbackground="white", padding=4,
                    bordercolor=COR_BORDA, arrowcolor=COR_PRIMARIA)
    style.map("TSpinbox", bordercolor=[("focus", sec)],
              fieldbackground=[("focus", fundo_foco)])

    # Anel de foco branco: o padrão do clam é escuro e some sobre os
    # botões coloridos — quem usa o teclado não via onde estava.
    style.configure("TButton", font=FONTE_BOTAO, padding=(14, 8),
                    background=sec, foreground=COR_TEXTO_CLARO, borderwidth=0,
                    focuscolor=COR_TEXTO_CLARO, focusthickness=2)
    style.map("TButton", background=[("pressed", press_sec), ("active", hover_sec),
                                      ("disabled", "#A9B2BD")])

    style.configure("Primario.TButton", font=FONTE_BOTAO_GRANDE,
                    background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO, padding=(18, 10))
    style.map("Primario.TButton", background=[("pressed", press_prim), ("active", hover_prim),
                                               ("disabled", "#A9B2BD")])

    style.configure("Sucesso.TButton", background=COR_SUCESSO, foreground=COR_TEXTO_CLARO)
    style.map("Sucesso.TButton", background=[("active", "#1B5E20"), ("disabled", "#A9B2BD")])

    style.configure("Perigo.TButton", background=COR_ERRO, foreground=COR_TEXTO_CLARO)
    style.map("Perigo.TButton", background=[("active", "#8E1F1F"), ("disabled", "#D9A0A0")])

    style.configure("Aviso.TButton", background=COR_AVISO, foreground=COR_TEXTO_CLARO)
    style.map("Aviso.TButton", background=[("active", _ajustar_cor(COR_AVISO, 0.8)),
                                           ("disabled", "#E0B79A")])

    # Botões secundários discretos: fundo branco, texto na cor primária.
    # Cada tela tem UM botão colorido (a ação principal); o resto fica
    # nesta aparência calma, para o olho achar logo o que importa.
    style.configure("Discreto.TButton", font=FONTE_BOTAO, padding=(14, 7),
                    background=COR_CARD, foreground=COR_PRIMARIA,
                    bordercolor=COR_BORDA, lightcolor=COR_CARD,
                    darkcolor=COR_CARD, borderwidth=1,
                    focuscolor=COR_PRIMARIA, focusthickness=1)
    style.map("Discreto.TButton",
              background=[("pressed", COR_FUNDO_ESCURO), ("active", COR_FUNDO)],
              bordercolor=[("active", COR_PRIMARIA), ("focus", COR_PRIMARIA)],
              foreground=[("disabled", "#8A94A0")])
    # O menu "Mais ▾" tem a mesma aparência discreta
    style.configure("TMenubutton", font=FONTE_BOTAO, padding=(14, 7),
                    background=COR_CARD, foreground=COR_PRIMARIA,
                    bordercolor=COR_BORDA, lightcolor=COR_CARD,
                    darkcolor=COR_CARD, borderwidth=1,
                    arrowcolor=COR_PRIMARIA, focuscolor=COR_PRIMARIA)
    style.map("TMenubutton",
              background=[("pressed", COR_FUNDO_ESCURO), ("active", COR_FUNDO)],
              bordercolor=[("active", COR_PRIMARIA), ("focus", COR_PRIMARIA)])

    style.configure("Sidebar.TButton", font=FONTE_BOTAO_GRANDE,
                    background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO,
                    padding=(20, 14), borderwidth=0, anchor="w",
                    focuscolor=COR_TEXTO_CLARO, focusthickness=2)
    style.map("Sidebar.TButton",
              background=[("active", sec), ("selected", sec),
                          ("focus", _mesclar_branco(COR_PRIMARIA, 0.15))])

    # Checkbuttons/radios sem "flash" cinza no hover
    style.configure("TCheckbutton", background=COR_FUNDO)
    style.map("TCheckbutton", background=[("active", COR_FUNDO)])
    style.configure("TRadiobutton", background=COR_FUNDO)
    style.map("TRadiobutton", background=[("active", COR_FUNDO)])
    style.configure("Card.TRadiobutton", background=COR_CARD)
    style.map("Card.TRadiobutton", background=[("active", COR_CARD)])

    style.configure("Treeview", background="white", fieldbackground="white",
                    foreground=COR_TEXTO, rowheight=escalar(30), borderwidth=0,
                    font=("Segoe UI", 10))
    style.configure("Treeview.Heading", background=COR_PRIMARIA, foreground=COR_TEXTO_CLARO,
                    font=("Segoe UI Semibold", 10), padding=(8, 7), relief="flat")
    style.map("Treeview.Heading",
              background=[("pressed", press_prim), ("active", sec)])
    style.map("Treeview", background=[("selected", sec)],
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

    # Botão com foco responde a Enter, não só à barra de espaço (o
    # padrão do Tk, que ninguém descobre sozinho).
    # O "break" impede que o Enter chegue também ao atalho da janela
    # (a tela de login liga Enter a "Entrar" — seriam dois logins).
    def acionar(evento):
        evento.widget.invoke()
        return "break"

    for tecla in ("<Return>", "<KP_Enter>"):
        root.bind_class("TButton", tecla, acionar)
        root.bind_class("TMenubutton", tecla, _abrir_menubutton)

    root.bind_all("<Escape>", _esc_fecha_dialogo, add="+")
    return style


def _esc_fecha_dialogo(evento):
    """Esc fecha a janela de diálogo em que o foco está.

    Faz o mesmo que o X da janela — inclusive qualquer pergunta que o
    diálogo tenha registrado para o fechamento —, então nunca é um
    atalho mais perigoso que o mouse. A janela principal (tk.Tk) nunca
    é fechada por Esc.
    """
    widget = evento.widget
    if isinstance(widget, str):
        return None  # lista aberta de um combobox: o próprio Tk trata o Esc
    try:
        janela = widget.winfo_toplevel()
    except (tk.TclError, AttributeError):
        return None
    if not isinstance(janela, tk.Toplevel):
        return None
    comando = janela.protocol("WM_DELETE_WINDOW")
    if comando:
        janela.tk.call(comando)
    else:
        janela.destroy()
    return "break"


def _abrir_menubutton(evento):
    """Enter abre o menu "Mais ▾" (o Tk só abre com espaço ou clique)."""
    try:
        evento.widget.tk.call("ttk::menubutton::Popdown", evento.widget)
    except tk.TclError:
        pass
    return "break"


def _montar_menu(pai, itens) -> tk.Menu:
    """Menu a partir de [(rótulo, comando), None (separador), ...]."""
    menu = tk.Menu(pai, tearoff=0, font=FONTE_BASE,
                   activebackground=legivel_com_branco(COR_SECUNDARIA),
                   activeforeground=COR_TEXTO_CLARO)
    for item in itens:
        if item is None:
            menu.add_separator()
        else:
            rotulo, comando = item
            menu.add_command(label=rotulo, command=comando)
    return menu


def botao_menu(pai, texto: str, itens) -> ttk.Menubutton:
    """Botão "Mais ▾": junta ações usadas de vez em quando num só lugar.

    As telas tinham um botão para cada coisa — Livros chegou a sete na
    mesma faixa. A ação do dia a dia fica à vista; o resto mora aqui,
    a um clique, sem disputar atenção.
    """
    botao = ttk.Menubutton(pai, text=texto)
    botao["menu"] = _montar_menu(botao, itens)
    return botao


def menu_de_linha(tabela, itens) -> tk.Menu:
    """Menu das ações de uma linha: botão direito, Shift+F10 ou tecla Menu.

    Substitui a fileira de botões "Editar · Excluir · Ver detalhes" que
    ficava sobre cada tabela. Pelo mouse, o botão direito marca a linha
    clicada antes de abrir, para a ação cair na linha certa.
    """
    menu = _montar_menu(tabela, itens)

    def abrir(x, y):
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def pelo_mouse(evento):
        linha = tabela.identify_row(evento.y)
        if not linha:
            return
        if linha not in tabela.selection():
            tabela.selection_set(linha)
        tabela.focus(linha)
        abrir(evento.x_root, evento.y_root)

    def pelo_teclado(_evento):
        linha = tabela.focus() or next(iter(tabela.selection()), "")
        if linha:
            caixa = tabela.bbox(linha) or (0, 0, 0, 0)
            abrir(tabela.winfo_rootx() + 40,
                  tabela.winfo_rooty() + caixa[1] + caixa[3])
        return "break"

    tabela.bind("<Button-3>", pelo_mouse, add="+")
    for tecla in ("<Shift-F10>", "<App>"):
        try:
            tabela.bind(tecla, pelo_teclado)
        except tk.TclError:
            pass  # tecla Menu não existe neste sistema
    return menu


def busca_ao_digitar(campo, acao, atraso: int = 350) -> None:
    """Pesquisa enquanto a pessoa digita, sem botão "Pesquisar".

    Espera uma pausa curta na digitação para não pesquisar a cada letra.
    Enter continua pesquisando na hora.
    """
    estado = {"agendado": None, "ultimo": campo.get()}

    def cancelar():
        if estado["agendado"]:
            campo.after_cancel(estado["agendado"])
            estado["agendado"] = None

    def disparar():
        estado["agendado"] = None
        acao()

    def ao_soltar_tecla(_evento):
        texto = campo.get()
        if texto == estado["ultimo"]:
            return  # setas, Shift, Tab: nada mudou
        estado["ultimo"] = texto
        cancelar()
        estado["agendado"] = campo.after(atraso, disparar)

    def agora(_evento):
        cancelar()
        estado["ultimo"] = campo.get()
        acao()
        return "break"

    campo.bind("<KeyRelease>", ao_soltar_tecla, add="+")
    campo.bind("<Return>", agora)
    campo.bind("<KP_Enter>", agora)


def ao_ativar_linha(tabela, acao) -> None:
    """Liga a ação de uma linha ao duplo clique **e** ao Enter.

    Antes, abrir os detalhes de um livro, editar um usuário ou devolver
    um empréstimo só funcionava com duplo clique: quem navega pelo
    teclado chegava na linha e não tinha como abri-la.
    """
    def executar(_evento):
        acao()
        return "break"

    for evento in ("<Double-1>", "<Return>", "<KP_Enter>"):
        tabela.bind(evento, executar)


def _foco_na_primeira_linha(evento) -> None:
    """Ao chegar numa tabela pelo Tab, deixa uma linha marcada.

    Sem isso a tabela recebia o foco sem linha nenhuma em foco: as setas
    não faziam nada e não havia sinal visível de onde se estava.
    """
    tabela = evento.widget
    try:
        if tabela.focus():
            return
        selecionadas = tabela.selection()
        filhos = tabela.get_children()
        alvo = selecionadas[0] if selecionadas else (filhos[0] if filhos else "")
        if alvo:
            tabela.focus(alvo)
            if not selecionadas:
                tabela.selection_set(alvo)
            tabela.see(alvo)
    except (tk.TclError, AttributeError):
        pass


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


def centralizar_janela(janela, largura, altura, minimo=None):
    """Centraliza, sem deixar a janela nascer maior que a tela.

    Sem o limite, uma janela pedida maior que a tela do computador da
    escola (comum em laboratório com monitor pequeno) nasce com o topo
    ou o rodapé fora da área visível — e como cada diálogo pede um
    tamanho fixo, o rodapé cortado costuma ser justo onde ficam os
    botões Salvar/Cancelar.

    `minimo`, quando informado, é a tupla (largura, altura) abaixo da
    qual a janela não deve encolher — e é aplicado **aqui**, limitado ao
    tamanho da tela, em vez de por um `minsize()` do lado de quem chama.

    O motivo é concreto: até a v1.10.4 as janelas principais faziam
    `centralizar_janela(...)` e logo abaixo `self.minsize(1180, 700)`.
    O `minsize` desfazia o limite — num laboratório de 1366x768 a 125%
    de escala (cerca de 1093x614 úteis), a janela ficava presa em
    1180x700, com a faixa de botões fora da tela e sem como
    redimensionar nem rolar. Um limite que pode ser desfeito pela linha
    seguinte não é limite.
    """
    janela.update_idletasks()
    # Texto maior precisa de janela maior, senão os botões do rodapé
    # saem da área visível. O limite de tela logo abaixo continua valendo.
    largura, altura = escalar(largura), escalar(altura)
    if minimo:
        minimo = (escalar(minimo[0]), escalar(minimo[1]))
    sw = janela.winfo_screenwidth()
    sh = janela.winfo_screenheight()
    # Folga pra barra de tarefas e pra moldura da janela, que a API de
    # tela não inclui.
    max_larg = max(320, sw - 40)
    max_alt = max(240, sh - 80)
    largura = min(largura, max_larg)
    altura = min(altura, max_alt)
    x = max(0, (sw - largura) // 2)
    y = max(0, (sh - altura) // 3)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    if minimo:
        janela.minsize(min(minimo[0], max_larg), min(minimo[1], max_alt))


def criar_tabela(parent, **kw):
    """Cria uma Treeview já dentro do quadro que vai abrigar a barra.

    O quadro existe para que a tabela e a barra ocupem **um** lugar só
    na disposição do pai. Sem ele, a tabela teria que ser empacotada
    com `side="left"` para caber ao lado da barra, e aí tudo que fosse
    empacotado depois dela no mesmo pai — um rodapé, um total, uma
    faixa de botões — ficaria sem espaço. Esse é exatamente o
    defeito de `pack` que já sumiu com a barra de ações antes.
    """
    caixa = ttk.Frame(parent)
    tabela = ttk.Treeview(caixa, **kw)
    tabela._caixa = caixa
    tabela.bind("<FocusIn>", _foco_na_primeira_linha, add="+")
    return tabela


def _largura_das_colunas(tabela) -> int:
    """Quanto a tabela precisaria para mostrar tudo sem cortar."""
    total = 0
    for coluna in tabela["columns"]:
        try:
            total += int(tabela.column(coluna, "width"))
        except (tk.TclError, ValueError, TypeError):
            pass
    return total


def empacotar_com_rolagem(tabela, **pack_kw):
    """Mostra a tabela com as barras de rolagem de que ela precisa.

    `pack_kw` vale para o conjunto (tabela + barras), do mesmo jeito que
    valeria para a tabela sozinha. A ordem interna — barra à direita
    primeiro, tabela depois — é o que garante que a barra não nasça
    com largura zero, e mora aqui para não ser reescrita em cada uma
    das catorze telas que têm tabela.

    **A barra horizontal aparece e some sozinha.** Numa tela de 1366 px,
    a tabela de empréstimos tem nove colunas que somam mais que a área
    disponível, e as duas últimas — "Previsto" e "Atraso?" — ficavam
    fora da vista sem nada indicando que existiam. Deixá-la sempre
    visível seria pior: rouba altura de tabela em toda tela onde as
    colunas cabem. Então ela é empacotada e desempacotada conforme a
    largura, no `<Configure>`.

    @param tabela   Treeview criada por `criar_tabela`.
    @param pack_kw  o que seria passado ao `pack` da tabela.
    @return a barra vertical, para quem precisar dela depois.
    """
    caixa = getattr(tabela, "_caixa", None) or tabela.master

    # A horizontal vai no rodapé da caixa e é reservada ANTES da tabela,
    # pelo mesmo motivo de sempre: `pack` reparte na ordem em que é
    # chamado, e a tabela com `expand=True` não deixa sobra.
    barra_h = ttk.Scrollbar(caixa, orient="horizontal", command=tabela.xview)
    tabela.configure(xscrollcommand=barra_h.set)

    barra_v = ttk.Scrollbar(caixa, orient="vertical", command=tabela.yview)
    tabela.configure(yscrollcommand=barra_v.set)
    barra_v.pack(side="right", fill="y")
    tabela.pack(side="left", fill="both", expand=True)
    caixa.pack(**pack_kw)

    def ajustar(_evento=None):
        precisa = _largura_das_colunas(tabela) > tabela.winfo_width() + 1
        visivel = bool(barra_h.winfo_manager())
        if precisa and not visivel:
            # `before=tabela` põe a barra antes da tabela na ordem de
            # empacotamento sem precisar refazer os dois.
            barra_h.pack(side="bottom", fill="x", before=tabela)
        elif not precisa and visivel:
            barra_h.pack_forget()

    tabela.bind("<Configure>", ajustar, add="+")
    tabela.after_idle(ajustar)
    return barra_v


class FaixaDeBotoes(ttk.Frame):
    """Faixa de botões que quebra linha quando falta largura.

    Com `pack(side="right")`, quando os botões somam mais que a largura
    o último empacotado é espremido até sumir — já aconteceu com
    "Importar CSV", e voltava a acontecer com o texto em tamanho Grande.
    Aqui, o que não cabe desce para uma segunda linha e continua inteiro.

    Cada linha é um quadro próprio, e os botões são empacotados dentro
    dele (`in_`). Assim quem calcula a altura da faixa é o próprio Tk.
    A primeira versão posicionava os botões com `place` e ajustava a
    altura na mão a cada `<Configure>`: quando esse evento não chegava
    na hora certa, a faixa ficava com 1 pixel e os botões sumiam — no
    cabeçalho de Livros sobrou só um risco onde deviam estar "Mais" e
    "Cadastrar livro". Agora, sem medida nenhuma, tudo fica numa linha
    só, visível.

    Os botões são criados com esta faixa como pai e registrados com
    `adicionar`, na ordem em que aparecem da esquerda para a direita.
    """

    def __init__(self, parent, espaco: int = 8, alinhar: str = "right", **kw):
        super().__init__(parent, **kw)
        self._espaco = espaco
        self._alinhar = alinhar
        self._botoes: list = []
        self._quadros: list = []
        self._arranjo: list = []
        self.bind("<Configure>", self._arrumar, add="+")

    def adicionar(self, widget):
        self._botoes.append(widget)
        self._arrumar()
        return widget

    def _linhas(self, largura: int) -> list:
        linhas: list = [[]]
        usada = 0
        for botao in self._botoes:
            w = botao.winfo_reqwidth()
            if linhas[-1] and usada + self._espaco + w > largura:
                linhas.append([])
                usada = 0
            usada += (self._espaco if linhas[-1] else 0) + w
            linhas[-1].append(botao)
        return linhas

    def _arrumar(self, _evento=None):
        try:
            largura = self.winfo_width()
            if largura <= 1:
                largura = 10 ** 6  # ainda sem medida: tudo numa linha
            linhas = self._linhas(largura)
            arranjo = [[str(b) for b in linha] for linha in linhas]
            if arranjo == self._arranjo:
                return  # nada mudou; evita laço com o próprio <Configure>
            self._arranjo = arranjo

            for botao in self._botoes:
                botao.pack_forget()
            for quadro in self._quadros:
                quadro.pack_forget()
            while len(self._quadros) < len(linhas):
                self._quadros.append(ttk.Frame(self))

            lado = "e" if self._alinhar == "right" else "w"
            for n, (quadro, linha) in enumerate(zip(self._quadros, linhas)):
                quadro.pack(side="top", anchor=lado,
                            pady=(self._espaco if n else 0, 0))
                for i, botao in enumerate(linha):
                    botao.pack(in_=quadro, side="left",
                               padx=(self._espaco if i else 0, 0))
                    # O quadro foi criado depois do botão e ficaria por
                    # cima dele, escondendo-o.
                    botao.lift(quadro)
        except tk.TclError:
            pass  # janela sendo fechada


def area_com_rolagem(pai):
    """Área com barra de rolagem vertical; devolve o quadro interno.

    Roda do mouse só enquanto o ponteiro está em cima dela, e o Tab
    leva a rolagem junto (rolar_ate_o_foco).
    """
    canvas = tk.Canvas(pai, bg=COR_FUNDO, highlightthickness=0)
    barra = ttk.Scrollbar(pai, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=barra.set)
    barra.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    interior = ttk.Frame(canvas)
    janela = canvas.create_window((0, 0), window=interior, anchor="nw")
    canvas.bind("<Configure>",
                lambda e: canvas.itemconfig(janela, width=e.width))
    interior.bind("<Configure>",
                  lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    def rodinha(evento):
        canvas.yview_scroll(int(-1 * (evento.delta / 120)), "units")
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", rodinha))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    rolar_ate_o_foco(canvas, interior)
    return interior


def rolar_ate_o_foco(canvas, interior) -> None:
    """Faz um formulário com rolagem acompanhar o Tab.

    Nos formulários longos (cadastro de livro, Configurações), o Tab
    levava o foco para um campo abaixo da área visível e a tela ficava
    parada: a pessoa digitava sem ver onde.
    """
    prefixo = str(interior) + "."

    def ao_focar(evento):
        widget = evento.widget
        if isinstance(widget, str) or not str(widget).startswith(prefixo):
            return
        try:
            total = interior.winfo_height()
            visivel = canvas.winfo_height()
            if total <= visivel:
                return
            topo_campo = widget.winfo_rooty() - interior.winfo_rooty()
            base_campo = topo_campo + widget.winfo_height()
            topo_vista = canvas.canvasy(0)
            margem = 16
            if topo_campo < topo_vista:
                canvas.yview_moveto(max(0, topo_campo - margem) / total)
            elif base_campo > topo_vista + visivel:
                canvas.yview_moveto((base_campo + margem - visivel) / total)
        except tk.TclError:
            pass

    canvas.winfo_toplevel().bind("<FocusIn>", ao_focar, add="+")


def gravar_arquivo(parent, destino: str, escrever, titulo_ok: str = "Pronto",
                   mensagem_ok: str = "") -> bool:
    """Executa uma gravação em disco avisando quando ela falha.

    Antes, cada tela que exportava CSV chamava `open(...)` solta. Se o
    arquivo estivesse aberto no Excel, se o pen drive tivesse sido
    tirado ou se a pasta fosse só de leitura, o erro subia até o laço
    do Tk e morria no console — que ninguém vê numa escola. A
    bibliotecária clicava em "Exportar", não aparecia nada, e ela
    concluía que o sistema estava travado.

    O `_backup` já fazia certo; esta função é aquele mesmo cuidado num
    lugar só, para as outras exportações não precisarem repetir.

    @param escrever  função sem argumentos que grava o arquivo.
    @return True se gravou.
    """
    try:
        escrever()
    except OSError as e:
        messagebox.showerror(
            "Não foi possível salvar",
            "O arquivo não pôde ser gravado em:\n%s\n\n%s\n\n"
            "Verifique se ele não está aberto em outro programa e se a "
            "pasta escolhida aceita gravação." % (destino, e),
            parent=parent)
        return False
    messagebox.showinfo(titulo_ok,
                        mensagem_ok or "Arquivo salvo em:\n%s" % destino,
                        parent=parent)
    return True
