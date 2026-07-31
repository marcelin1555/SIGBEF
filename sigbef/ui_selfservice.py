"""
SIGBEF — Terminal de autoatendimento (kiosk).

Interface grande, com poucos cliques, para que alunos e professores realizem
empréstimos e devoluções autonomamente. Usa a sessão como contexto.
"""
from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from . import icones
from . import servicos
from . import ui_tema as tema
from .auth import Sessao, autenticar, autenticar_por_codigo
from .servicos import RegraNegocioError


TEMPO_SESSAO_MS = 90_000   # 90 segundos de inatividade até logout automático
TEMPO_AVISO_MS = TEMPO_SESSAO_MS - 15_000   # aviso 15s antes do logout


class TerminalAutoatendimento(tk.Tk):
    def __init__(self):
        super().__init__()
        self.sessao: Sessao | None = None
        self._timer = None
        self._timer_aviso = None
        self._aviso: tk.Label | None = None

        self.title("SIGBEF - Terminal de Autoatendimento")
        tema.aplicar_tema(self)
        icones.aplicar_icone_janela(self)
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 1100, 760)
        self.minsize(960, 700)

        self.bind_all("<Any-KeyPress>", self._reset_timer)
        self.bind_all("<Any-Button>", self._reset_timer)

        self._frame_atual: tk.Widget | None = None
        self._mostrar_login()

    # ------------------------------------------------------------------
    def _trocar(self, builder):
        if self._frame_atual is not None:
            self._frame_atual.destroy()
        self._frame_atual = builder()
        self._frame_atual.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    def _mostrar_login(self):
        self._cancelar_timer()
        self.sessao = None
        self._trocar(self._construir_login)

    def _construir_login(self) -> tk.Widget:
        frame = tk.Frame(self, bg=tema.COR_FUNDO)

        topo = tk.Frame(frame, bg=tema.COR_PRIMARIA, height=120)
        topo.pack(fill="x")
        # Identidade: logo do SIGBEF e, se configurado, o brasão da escola
        marcas = tk.Frame(topo, bg=tema.COR_PRIMARIA)
        marcas.pack(pady=(18, 2))
        img_brasao = icones.brasao(max_altura=56)
        if img_brasao is not None:
            tk.Label(marcas, bg=tema.COR_PRIMARIA, image=img_brasao
                     ).pack(side="left", padx=(0, 14))
        tk.Label(marcas, bg=tema.COR_PRIMARIA,
                 image=icones.icone("logoplaca", "original", 48)
                 ).pack(side="left")
        tk.Label(topo, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text="Bem-vindo à Biblioteca",
                 font=("Segoe UI Semibold", 30)).pack(pady=(4, 4))
        tk.Label(topo, bg=tema.COR_PRIMARIA, fg=tema.COR_PRIMARIA_SUAVE,
                 text="Identifique-se para começar",
                 font=("Segoe UI", 14)).pack(pady=(0, 16))

        centro = tk.Frame(frame, bg=tema.COR_FUNDO)
        centro.pack(expand=True)

        card = tk.Frame(centro, bg=tema.COR_CARD, padx=50, pady=40,
                         highlightbackground=tema.COR_BORDA, highlightthickness=1)
        card.pack(pady=80)

        tk.Label(card, text="Matrícula",
                 bg=tema.COR_CARD, font=("Segoe UI Semibold", 14)
                 ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.ent_matr = tk.Entry(card, font=("Segoe UI", 22), width=22,
                                  bg="white")
        self.ent_matr.grid(row=1, column=0, ipady=10, padx=0, pady=(0, 18),
                            sticky="ew")
        tk.Label(card, text="Senha",
                 bg=tema.COR_CARD, font=("Segoe UI Semibold", 14)
                 ).grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.ent_senha = tk.Entry(card, font=("Segoe UI", 22), width=22,
                                   bg="white", show="•")
        self.ent_senha.grid(row=3, column=0, ipady=10, pady=(0, 18),
                             sticky="ew")

        tk.Button(card, text="Entrar", bg=tema.COR_PRIMARIA,
                  fg=tema.COR_TEXTO_CLARO, font=("Segoe UI Semibold", 18),
                  bd=0, padx=20, pady=14, activebackground=tema.COR_PRIMARIA_ESCURA,
                  command=self._fazer_login_senha
                  ).grid(row=4, column=0, sticky="ew", pady=(0, 10))

        tk.Label(card, text="ou aproxime seu cartão do leitor",
                 bg=tema.COR_CARD, fg="#6B7280",
                 font=("Segoe UI", 11)).grid(row=5, column=0, pady=(20, 6))

        self.ent_cartao = tk.Entry(card, font=("Consolas", 16), width=22,
                                    bg=tema.COR_FUNDO_ESCURO,
                                    justify="center")
        self.ent_cartao.grid(row=6, column=0, ipady=8, sticky="ew")
        self.ent_cartao.bind("<Return>", lambda e: self._fazer_login_cartao())

        self.ent_matr.focus_set()
        self.bind("<Return>", lambda e: self._fazer_login_senha())

        rodape = tk.Frame(frame, bg=tema.COR_FUNDO)
        rodape.pack(side="bottom", fill="x", pady=10)
        tk.Label(rodape, text="SIGBEF · Modo de Autoatendimento",
                 bg=tema.COR_FUNDO, fg="#6B7280",
                 font=("Segoe UI", 10)).pack()

        return frame

    def _fazer_login_senha(self):
        sessao = autenticar(self.ent_matr.get(), self.ent_senha.get())
        if not sessao:
            messagebox.showerror("Acesso negado",
                                  "Matrícula ou senha incorretas.",
                                  parent=self)
            self.ent_senha.delete(0, "end")
            return
        if sessao.perfil not in ("ALUNO", "PROFESSOR"):
            messagebox.showinfo(
                "Atenção",
                "Este terminal é destinado a alunos e professores.\n"
                "Funcionários devem usar a estação do balcão.",
                parent=self)
            self.ent_senha.delete(0, "end")
            return
        self._iniciar_sessao(sessao)

    def _fazer_login_cartao(self):
        codigo = self.ent_cartao.get().strip()
        sessao = autenticar_por_codigo(codigo)
        if not sessao:
            messagebox.showerror("Acesso negado",
                                  "Cartão não reconhecido.",
                                  parent=self)
            self.ent_cartao.delete(0, "end")
            return
        if sessao.perfil not in ("ALUNO", "PROFESSOR"):
            messagebox.showinfo("Atenção",
                                  "Funcionários devem usar a estação do balcão.",
                                  parent=self)
            return
        self._iniciar_sessao(sessao)

    # ------------------------------------------------------------------
    def _iniciar_sessao(self, sessao: Sessao):
        self.sessao = sessao
        self._reset_timer()
        self._mostrar_inicio()

    def _mostrar_inicio(self):
        self._trocar(self._construir_inicio)

    def _construir_inicio(self) -> tk.Widget:
        frame = tk.Frame(self, bg=tema.COR_FUNDO)

        cabecalho = tk.Frame(frame, bg=tema.COR_PRIMARIA, height=110)
        cabecalho.pack(fill="x")
        tk.Label(cabecalho, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text=f"Olá, {self.sessao.nome.split()[0]}!",
                 font=("Segoe UI Semibold", 28)).pack(pady=(20, 0))
        st = servicos.status_usuario(self.sessao.id)
        tk.Label(cabecalho, bg=tema.COR_PRIMARIA, fg=tema.COR_PRIMARIA_SUAVE,
                 text=st.motivo, font=("Segoe UI", 13)).pack()

        centro = tk.Frame(frame, bg=tema.COR_FUNDO)
        centro.pack(fill="both", expand=True, padx=40, pady=30)

        # Botões grandes
        for col, (titulo, descricao, nome_icone, cor, callback) in enumerate([
            ("Pegar emprestado",
             "Pegue um livro escaneando o código de barras.",
             "barcode", tema.COR_SUCESSO, self._mostrar_emprestar),
            ("Devolver",
             "Aproxime o livro do leitor para devolvê-lo.",
             "desfazer", tema.COR_AVISO, self._mostrar_devolver),
            ("Meus empréstimos",
             "Veja os livros que estão com você.",
             "leitor", tema.COR_SECUNDARIA, self._mostrar_meus),
        ]):
            card = tk.Frame(centro, bg=cor, cursor="hand2")
            card.grid(row=0, column=col, padx=10, sticky="nsew",
                       ipadx=20, ipady=20)
            centro.columnconfigure(col, weight=1)
            centro.rowconfigure(0, weight=1)
            card.bind("<Button-1>", lambda e, c=callback: c())
            tk.Label(card, bg=cor,
                     image=icones.icone(nome_icone, "branco", 40)
                     ).pack(pady=(40, 12))
            tk.Label(card, text=titulo, bg=cor,
                     fg=tema.COR_TEXTO_CLARO,
                     font=("Segoe UI Semibold", 22)).pack(pady=(0, 8))
            tk.Label(card, text=descricao, bg=cor,
                     fg=tema.COR_TEXTO_CLARO, wraplength=240,
                     justify="center",
                     font=("Segoe UI", 12)).pack(pady=(0, 40), padx=20)
            for child in card.winfo_children():
                child.bind("<Button-1>",
                           lambda e, c=callback: c())

        rodape = tk.Frame(frame, bg=tema.COR_FUNDO)
        rodape.pack(fill="x", pady=10)
        tk.Button(rodape, text="Encerrar sessão",
                   bg=tema.COR_ERRO, fg=tema.COR_TEXTO_CLARO,
                   font=("Segoe UI Semibold", 12), bd=0, padx=18, pady=8,
                   command=self._mostrar_login).pack(side="right", padx=20)

        return frame

    # ------------------------------------------------------------------
    def _construir_acao(self, titulo_tela: str, instrucao: str,
                         texto_botao: str, cor_botao: str,
                         executar, montar_comprovante) -> tk.Widget:
        """Base compartilhada por 'Pegar emprestado' e 'Devolver': cartão
        com campo de código, confirma via Enter ou botão, mostra erro
        inline ou o comprovante de sucesso."""
        frame = tk.Frame(self, bg=tema.COR_FUNDO)
        self._cabecalho_voltar(frame, titulo_tela)

        card = tk.Frame(frame, bg=tema.COR_CARD,
                         highlightbackground=tema.COR_BORDA,
                         highlightthickness=1)
        card.pack(padx=80, pady=40, fill="x")

        tk.Label(card, bg=tema.COR_CARD, text=instrucao,
                 font=("Segoe UI", 18)).pack(pady=(40, 12))
        tk.Label(card, bg=tema.COR_CARD,
                 text="ou digite o código abaixo:",
                 fg="#6B7280", font=("Segoe UI", 12)).pack()

        ent = tk.Entry(card, font=("Consolas", 22), justify="center",
                        bg=tema.COR_FUNDO_ESCURO, width=22)
        ent.pack(pady=(20, 30), ipady=12)
        ent.focus_set()

        msg = tk.Label(card, bg=tema.COR_CARD, text="",
                        font=("Segoe UI", 13))
        msg.pack(pady=(0, 20))

        def confirmar():
            try:
                res = executar(ent.get())
            except RegraNegocioError as e:
                msg.configure(text=str(e), fg=tema.COR_ERRO)
                ent.delete(0, "end")
                ent.focus_set()
                return
            titulo_comprovante, detalhes = montar_comprovante(res)
            self._mostrar_comprovante(titulo_comprovante, res["titulo"], detalhes)

        ent.bind("<Return>", lambda e: confirmar())
        tk.Button(card, text=texto_botao,
                   bg=cor_botao, fg=tema.COR_TEXTO_CLARO,
                   font=("Segoe UI Semibold", 16), bd=0, padx=20, pady=10,
                   command=confirmar
                   ).pack(pady=(0, 30))

        return frame

    # ------------------------------------------------------------------
    def _mostrar_emprestar(self):
        self._trocar(self._construir_emprestar)

    def _construir_emprestar(self) -> tk.Widget:
        def executar(codigo):
            return servicos.realizar_emprestimo(
                codigo_exemplar=codigo,
                matricula_usuario=self.sessao.matricula,
                origem="AUTOATENDIMENTO",
                operador_id=self.sessao.id,
            )

        def montar_comprovante(res):
            return "Empréstimo realizado", [
                ("Devolução prevista", res["data_prevista"]),
                ("Prazo", f"{res['prazo_dias']} dias"),
                ("Origem", "Autoatendimento"),
            ]

        return self._construir_acao(
            "Pegar livro emprestado",
            "Aproxime o livro do leitor de código de barras",
            "Confirmar empréstimo", tema.COR_SUCESSO,
            executar, montar_comprovante,
        )

    # ------------------------------------------------------------------
    def _mostrar_devolver(self):
        self._trocar(self._construir_devolver)

    def _construir_devolver(self) -> tk.Widget:
        def executar(codigo):
            return servicos.realizar_devolucao(
                codigo_exemplar=codigo,
                operador_id=self.sessao.id,
            )

        def montar_comprovante(res):
            detalhes = [("Atraso", f"{res['dias_atraso']} dia(s)")]
            if res["multa"] > 0:
                detalhes.append(("Multa gerada", f"R$ {res['multa']:.2f}"))
                detalhes.append(("Atenção",
                                  "Compareça ao balcão para quitar a multa."))
            else:
                detalhes.append(("Multa", "Sem multa"))
            if res.get("reservado_para"):
                detalhes.append(("Reserva",
                                  "Este livro tem fila de espera. "
                                  "Entregue-o no balcão."))
            return "Devolução realizada", detalhes

        return self._construir_acao(
            "Devolver livro",
            "Aproxime o livro a ser devolvido do leitor",
            "Confirmar devolução", tema.COR_AVISO,
            executar, montar_comprovante,
        )

    # ------------------------------------------------------------------
    def _mostrar_meus(self):
        self._trocar(self._construir_meus)

    def _construir_meus(self) -> tk.Widget:
        frame = tk.Frame(self, bg=tema.COR_FUNDO)
        self._cabecalho_voltar(frame, "Meus empréstimos")

        emprestimos = servicos.listar_emprestimos_usuario(
            self.sessao.id, somente_abertos=True)

        if not emprestimos:
            tk.Label(frame, bg=tema.COR_FUNDO,
                     text="Você não tem livros emprestados no momento.",
                     font=("Segoe UI", 16)).pack(pady=80)
            return frame

        wrap = tk.Frame(frame, bg=tema.COR_FUNDO)
        wrap.pack(fill="both", expand=True, padx=40, pady=20)

        hoje = datetime.now().strftime("%Y-%m-%d")
        for emp in emprestimos:
            # O aluno vê "Há N em atraso" no topo, mas até aqui não
            # tinha como saber QUAL dos livros da lista é o atrasado —
            # tinha que comparar a data de cabeça. Mesmo destaque em
            # vermelho que o balcão já usa para "Empréstimos abertos".
            atrasado = emp["data_prevista"] < hoje
            card = tk.Frame(wrap, bg=tema.COR_CARD,
                             highlightbackground=(tema.COR_ERRO if atrasado
                                                  else tema.COR_BORDA),
                             highlightthickness=(2 if atrasado else 1))
            card.pack(fill="x", pady=8)
            tk.Label(card, bg=tema.COR_CARD, text=emp["titulo"],
                     anchor="w", font=("Segoe UI Semibold", 16)
                     ).pack(fill="x", padx=20, pady=(16, 4))
            info = (f"Código: {emp['codigo_barras']}    "
                    f"Empréstimo: {emp['data_emprestimo'][:10]}    "
                    f"Devolver até: {emp['data_prevista']}"
                    + ("    ATRASADO" if atrasado else ""))
            tk.Label(card, bg=tema.COR_CARD, text=info, anchor="w",
                     fg=(tema.COR_ERRO if atrasado else "#3B4350"),
                     font=("Segoe UI", 11, "bold" if atrasado else "normal")
                     ).pack(fill="x", padx=20, pady=(0, 14))

        return frame

    # ------------------------------------------------------------------
    def _mostrar_comprovante(self, titulo: str, livro: str,
                              linhas: list[tuple[str, str]]):
        def builder():
            frame = tk.Frame(self, bg=tema.COR_FUNDO)
            top = tk.Frame(frame, bg=tema.COR_SUCESSO, height=120)
            top.pack(fill="x")
            tk.Label(top, bg=tema.COR_SUCESSO, fg=tema.COR_TEXTO_CLARO,
                     text=titulo, font=("Segoe UI Semibold", 30)
                     ).pack(pady=(28, 0))
            tk.Label(top, bg=tema.COR_SUCESSO, fg=tema.COR_TEXTO_CLARO,
                     text=datetime.now().strftime("%d/%m/%Y %H:%M"),
                     font=("Segoe UI", 14)).pack()

            card = tk.Frame(frame, bg=tema.COR_CARD,
                             highlightbackground=tema.COR_BORDA,
                             highlightthickness=1)
            card.pack(padx=80, pady=40, fill="x")
            tk.Label(card, bg=tema.COR_CARD, text=livro,
                     font=("Segoe UI Semibold", 22)
                     ).pack(pady=(30, 16), padx=30)

            for k, v in linhas:
                row = tk.Frame(card, bg=tema.COR_CARD)
                row.pack(fill="x", padx=30, pady=4)
                tk.Label(row, bg=tema.COR_CARD, text=f"{k}:",
                         font=("Segoe UI Semibold", 14)).pack(side="left")
                tk.Label(row, bg=tema.COR_CARD, text=v,
                         font=("Segoe UI", 14)).pack(side="left", padx=10)
            tk.Label(card, bg=tema.COR_CARD, text="",
                     font=("Segoe UI", 8)).pack(pady=(20, 0))

            botoes = tk.Frame(frame, bg=tema.COR_FUNDO)
            botoes.pack(fill="x", pady=20)
            tk.Button(botoes, text="Concluir e voltar",
                       bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                       font=("Segoe UI Semibold", 16), bd=0, padx=24,
                       pady=10, command=self._mostrar_inicio
                       ).pack()
            return frame

        self._trocar(builder)

    # ------------------------------------------------------------------
    def _cabecalho_voltar(self, frame: tk.Frame, titulo: str):
        topo = tk.Frame(frame, bg=tema.COR_PRIMARIA, height=80)
        topo.pack(fill="x")
        topo.pack_propagate(False)
        tk.Button(topo, text="←  Voltar",
                   bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                   activebackground=tema.COR_PRIMARIA_ESCURA,
                   font=("Segoe UI Semibold", 13), bd=0, padx=14,
                   command=self._mostrar_inicio).pack(side="left", padx=18,
                                                        pady=12)
        tk.Label(topo, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text=titulo, font=("Segoe UI Semibold", 22)).pack(
                     side="left", padx=10)

    # ------------------------------------------------------------------
    # Timer de inatividade
    # ------------------------------------------------------------------
    def _reset_timer(self, _=None):
        if self.sessao is None:
            return
        self._cancelar_timer()
        self._timer_aviso = self.after(TEMPO_AVISO_MS, self._mostrar_aviso)
        self._timer = self.after(TEMPO_SESSAO_MS, self._mostrar_login)

    def _mostrar_aviso(self):
        """Faixa no topo avisando que a sessão vai encerrar; qualquer
        toque ou tecla reseta o timer e a faixa some."""
        if self.sessao is None or self._aviso is not None:
            return
        self._aviso = tk.Label(
            self,
            image=icones.icone("relogio", "branco", 16),
            compound="left",
            text="  A sessão será encerrada em 15 segundos. "
                 "Toque na tela para continuar.",
            bg=tema.COR_AVISO, fg=tema.COR_TEXTO_CLARO,
            font=("Segoe UI Semibold", 13), pady=10)
        self._aviso.place(relx=0.5, rely=0, anchor="n", relwidth=1.0)

    def _ocultar_aviso(self):
        if self._aviso is not None:
            self._aviso.destroy()
            self._aviso = None

    def _cancelar_timer(self):
        self._ocultar_aviso()
        for attr in ("_timer", "_timer_aviso"):
            t = getattr(self, attr)
            if t:
                try:
                    self.after_cancel(t)
                except tk.TclError:
                    pass
                setattr(self, attr, None)

    # ------------------------------------------------------------------
    def executar(self):
        self.mainloop()
