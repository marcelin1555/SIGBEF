"""
SIGBEF — Boas-vindas: um passo a passo curto na primeira vez que a pessoa entra.

Aparece uma vez por usuário (cada bibliotecária vê a sua) e pode ser
reaberto a qualquer hora pelo botão "Como usar" do cabeçalho ou pela
tecla F1. O conteúdo muda com o perfil: quem trabalha na biblioteca
aprende o balcão; aluno e professor aprendem a pesquisar e pegar livro.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from . import icones
from . import ui_tema as tema
from .database import get_config, set_config


def _chave(usuario_id: int) -> str:
    return f"boas_vindas.vista.{usuario_id}"


def ja_viu(usuario_id: int) -> bool:
    return (get_config(_chave(usuario_id), "") or "") == "1"


def marcar_como_vista(usuario_id: int) -> None:
    set_config(_chave(usuario_id), "1")


# Cada passo: (nome curto no índice, título, [(destaque, texto), ...])
PASSOS_BIBLIOTECA = [
    ("Boas-vindas", "Bem-vinda(o) ao SIGBEF", [
        ("", "Este é o sistema da biblioteca: acervo, leitores, "
             "empréstimos e devoluções num lugar só."),
        ("", "São cinco passos curtos. Dá para pular agora e rever "
             "depois no botão Como usar, no alto da tela, ou com F1."),
        ("Funciona sem internet", "Tudo fica guardado neste computador, "
         "e o sistema faz uma cópia de segurança sozinho quando você sai."),
    ]),
    ("O menu", "Tudo começa pelo menu da esquerda", [
        ("Livros e exemplares", "O acervo: cadastrar, procurar e imprimir "
         "etiquetas."),
        ("Usuários", "Alunos, professores e equipe, com o cartão de cada um."),
        ("Empréstimos abertos", "O balcão: emprestar, devolver e ver quem "
         "está com o quê."),
        ("Atalho", "Ctrl+1, Ctrl+2... abrem as seções na ordem do menu."),
    ]),
    ("O balcão", "Emprestar e devolver", [
        ("Para emprestar", "Em Empréstimos abertos, passe o cartão do "
         "leitor e depois o código do livro. O prazo é calculado sozinho."),
        ("Para devolver", "Passe o código do livro no quadro Devolver. Se "
         "houver atraso, a multa aparece na hora."),
        ("Sem leitor de código?", "Digite a matrícula e o número de tombo: "
         "funciona do mesmo jeito."),
    ]),
    ("Achar as ações", "Menos botões, tudo à mão", [
        ("Pesquisar é só digitar", "Acento e maiúscula não importam, e "
         "também acha por tombo ou ISBN."),
        ("Enter abre a linha marcada", "O livro, o cadastro do usuário, a "
         "devolução. Duplo clique faz o mesmo."),
        ("Botão direito mostra o resto", "Editar, excluir, renovar, "
         "imprimir cartão: o que dá para fazer com aquela linha."),
        ("O menu Mais", "Guarda o que se usa de vez em quando, como "
         "importar planilha."),
    ]),
    ("Pronto", "Pronto para começar", [
        ("Esc fecha a janela aberta", "Igual ao X."),
        ("F5 atualiza a tela", "E Ctrl+F leva direto à busca."),
        ("Letra pequena?", "Em Configurações, na aba Aparência, dá para "
         "aumentar o texto de todas as telas."),
        ("Dúvida?", "Esta explicação fica no botão Como usar, no alto da "
         "tela."),
    ]),
]

PASSOS_LEITOR = [
    ("Boas-vindas", "Bem-vindo(a) à biblioteca", [
        ("", "Aqui você procura livros, pega emprestado e acompanha o que "
             "está com você."),
        ("", "São três passos curtos. Dá para rever depois no botão Como "
             "usar, no alto da tela, ou com F1."),
    ]),
    ("Pesquisar", "Achar um livro", [
        ("Digite título, autor ou assunto", "Os resultados aparecem "
         "enquanto você digita. Acento e maiúscula não importam."),
        ("Coluna Disponíveis", "Mostra quantos exemplares estão na "
         "estante agora."),
    ]),
    ("Pegar", "Pegar emprestado ou entrar na fila", [
        ("Tem na estante?", "Marque o livro e clique em Pegar emprestado, "
         "ou aperte Enter. O prazo aparece na hora."),
        ("Não tem?", "O mesmo botão vira Entrar na fila de espera. Quando "
         "alguém devolver, o livro fica separado para você."),
        ("Meus empréstimos", "Mostra o que está com você, o prazo e a sua "
         "posição nas filas."),
    ]),
]


class DialogoBoasVindas(tk.Toplevel):
    """Passo a passo com índice à esquerda e navegação por teclado."""

    def __init__(self, parent, sessao, ao_fechar=None):
        super().__init__(parent)
        self.sessao = sessao
        self.ao_fechar = ao_fechar
        self.passos = (PASSOS_BIBLIOTECA if sessao.is_bibliotecario
                       else PASSOS_LEITOR)
        self.atual = 0
        self.title("Como usar o SIGBEF")
        self.transient(parent)
        self.configure(bg=tema.COR_FUNDO)
        icones.aplicar_icone_janela(self)
        tema.centralizar_janela(self, 840, 540)
        self.protocol("WM_DELETE_WINDOW", self._fechar)

        # ---- Índice à esquerda: mostra onde se está e quanto falta ----
        lateral = tk.Frame(self, bg=tema.COR_PRIMARIA,
                           width=tema.escalar(220))
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)
        tk.Label(lateral, bg=tema.COR_PRIMARIA,
                 image=icones.icone("logoplaca", "original", 48)
                 ).pack(anchor="w", padx=24, pady=(28, 20))
        self._itens_indice = []
        for i, (nome, _titulo, _corpo) in enumerate(self.passos):
            rotulo = tk.Label(lateral, text=f"{i + 1}   {nome}",
                              bg=tema.COR_PRIMARIA, anchor="w",
                              font=("Segoe UI", 11), cursor="hand2")
            rotulo.pack(fill="x", padx=24, pady=4)
            rotulo.bind("<Button-1>", lambda e, n=i: self._ir(n))
            self._itens_indice.append(rotulo)

        # ---- Conteúdo ----
        direita = ttk.Frame(self, padding=(36, 32, 36, 24))
        direita.pack(side="left", fill="both", expand=True)

        rodape = ttk.Frame(direita)
        rodape.pack(side="bottom", fill="x")
        self.btn_pular = ttk.Button(rodape, text="Pular",
                                    style="Discreto.TButton",
                                    command=self._fechar)
        self.btn_pular.pack(side="left")
        self.btn_proximo = ttk.Button(rodape, text="Próximo",
                                      style="Primario.TButton",
                                      command=self._proximo)
        self.btn_proximo.pack(side="right")
        self.btn_voltar = ttk.Button(rodape, text="Voltar",
                                     style="Discreto.TButton",
                                     command=self._voltar)
        self.btn_voltar.pack(side="right", padx=(0, 8))

        self.lbl_passo = ttk.Label(direita, text="", style="Hint.TLabel")
        self.lbl_passo.pack(anchor="w")
        self.lbl_titulo = ttk.Label(direita, text="",
                                    style="Titulo.TLabel")
        self.lbl_titulo.pack(anchor="w", pady=(2, 16))
        self.corpo = ttk.Frame(direita)
        self.corpo.pack(fill="both", expand=True)

        for tecla in ("<Right>", "<Next>"):
            self.bind(tecla, lambda e: self._proximo())
        for tecla in ("<Left>", "<Prior>"):
            self.bind(tecla, lambda e: self._voltar())
        self._mostrar()
        self.btn_proximo.focus_set()
        self.grab_set()

    # ------------------------------------------------------------------
    def _mostrar(self):
        nome, titulo, corpo = self.passos[self.atual]
        total = len(self.passos)
        self.lbl_passo.configure(text=f"Passo {self.atual + 1} de {total}")
        self.lbl_titulo.configure(text=titulo)
        for filho in self.corpo.winfo_children():
            filho.destroy()
        largura = tema.escalar(500)
        for destaque, texto in corpo:
            if destaque:
                ttk.Label(self.corpo, text=destaque,
                          foreground=tema.COR_PRIMARIA,
                          font=("Segoe UI Semibold", 11)
                          ).pack(anchor="w")
            ttk.Label(self.corpo, text=texto, wraplength=largura,
                      justify="left", font=("Segoe UI", 11)
                      ).pack(anchor="w", pady=(0, 12))

        for i, rotulo in enumerate(self._itens_indice):
            ativo = i == self.atual
            rotulo.configure(
                fg=(tema.COR_TEXTO_CLARO if ativo or i < self.atual
                    else tema.COR_PRIMARIA_SUAVE),
                font=("Segoe UI Semibold" if ativo else "Segoe UI", 11))
        ultimo = self.atual == total - 1
        self.btn_proximo.configure(text="Começar a usar" if ultimo
                                   else "Próximo")
        if self.atual == 0:
            self.btn_voltar.pack_forget()
        elif not self.btn_voltar.winfo_manager():
            # `after`: com side="right", quem é empacotado depois fica à
            # esquerda — Voltar tem de ficar à esquerda de Próximo.
            self.btn_voltar.pack(side="right", padx=(0, 8),
                                 after=self.btn_proximo)
        # No último passo não há o que pular
        if ultimo:
            self.btn_pular.pack_forget()
        elif not self.btn_pular.winfo_manager():
            self.btn_pular.pack(side="left")

    def _ir(self, indice: int):
        self.atual = max(0, min(indice, len(self.passos) - 1))
        self._mostrar()

    def _proximo(self):
        if self.atual >= len(self.passos) - 1:
            self._fechar()
        else:
            self._ir(self.atual + 1)
        return "break"

    def _voltar(self):
        self._ir(self.atual - 1)
        return "break"

    def _fechar(self):
        marcar_como_vista(self.sessao.id)
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
        if self.ao_fechar:
            self.ao_fechar()
