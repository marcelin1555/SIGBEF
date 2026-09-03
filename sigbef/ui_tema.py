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


def aplicar_tema(root):
    global COR_PRIMARIA_SUAVE, COR_PRIMARIA_ESCURA
    carregar_personalizacao()
    COR_PRIMARIA_SUAVE = _mesclar_branco(COR_PRIMARIA, 0.65)
    COR_PRIMARIA_ESCURA = _ajustar_cor(COR_PRIMARIA, 0.72)
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
    return tabela


def empacotar_com_rolagem(tabela, **pack_kw):
    """Mostra a tabela com barra de rolagem vertical.

    `pack_kw` vale para o conjunto (tabela + barra), do mesmo jeito que
    valeria para a tabela sozinha. A ordem interna — barra à direita
    primeiro, tabela depois — é o que garante que a barra não nasça
    com largura zero, e mora aqui para não ser reescrita em cada uma
    das catorze telas que têm tabela.

    @param tabela   Treeview criada por `criar_tabela`.
    @param pack_kw  o que seria passado ao `pack` da tabela.
    @return a barra criada, para quem precisar dela depois.
    """
    caixa = getattr(tabela, "_caixa", None) or tabela.master
    barra = ttk.Scrollbar(caixa, orient="vertical", command=tabela.yview)
    tabela.configure(yscrollcommand=barra.set)
    barra.pack(side="right", fill="y")
    tabela.pack(side="left", fill="both", expand=True)
    caixa.pack(**pack_kw)
    return barra


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
