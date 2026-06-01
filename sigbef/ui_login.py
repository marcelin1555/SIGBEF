"""
SIGBEF — Tela de login.

Exibe um diálogo modal com matrícula e senha. Em caso de sucesso, retorna
o objeto Sessao para o chamador.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from .auth import autenticar, Sessao
from . import ui_tema as tema


class JanelaLogin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.sessao: Optional[Sessao] = None
        self.modo_autoatendimento = tk.BooleanVar(value=False)

        self.title("SIGBEF — Acesso ao Sistema")
        tema.aplicar_tema(self)
        self._construir()
        tema.centralizar_janela(self, 1000, 620)
        self.minsize(960, 600)
        self.bind("<Return>", lambda e: self._fazer_login())

    # ------------------------------------------------------------------
    def _construir(self):
        # Lateral institucional (azul)
        lateral = tk.Frame(self, bg=tema.COR_PRIMARIA)
        lateral.pack(side="left", fill="both", expand=False)
        lateral.configure(width=440)

        tk.Label(lateral, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text="SIGBEF", font=("Segoe UI Semibold", 56)
                 ).pack(pady=(80, 0), padx=40, anchor="w")

        tk.Label(lateral, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text="Sistema Integrado de Gestão\nda Biblioteca Escolar",
                 font=("Segoe UI", 16), justify="left"
                 ).pack(padx=40, anchor="w", pady=(8, 30))

        tk.Frame(lateral, bg=tema.COR_DESTAQUE, height=4, width=120
                 ).pack(padx=40, anchor="w")

        descricao = (
            "• Cadastro e busca de livros\n"
            "• Empréstimos e devoluções\n"
            "• Autoatendimento por código de barras\n"
            "• Relatórios e gestão de usuários"
        )
        tk.Label(lateral, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text=descricao, font=("Segoe UI", 11), justify="left"
                 ).pack(padx=40, anchor="w", pady=(30, 0))

        rodape_lat = tk.Label(
            lateral, bg=tema.COR_PRIMARIA, fg="#9CB7D6",
            text="Versão 1.2.0 — produto em produção",
            font=("Segoe UI", 9))
        rodape_lat.pack(side="bottom", pady=20)

        # Formulário
        direita = ttk.Frame(self, padding=(50, 50))
        direita.pack(side="right", fill="both", expand=True)

        ttk.Label(direita, text="Acessar o sistema",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(direita, text="Informe sua matrícula e senha para continuar.",
                  style="Hint.TLabel").pack(anchor="w", pady=(4, 30))

        ttk.Label(direita, text="Matrícula").pack(anchor="w")
        self.ent_matricula = ttk.Entry(direita, font=("Segoe UI", 12))
        self.ent_matricula.pack(fill="x", pady=(4, 18), ipady=4)

        ttk.Label(direita, text="Senha").pack(anchor="w")
        self.ent_senha = ttk.Entry(direita, show="•", font=("Segoe UI", 12))
        self.ent_senha.pack(fill="x", pady=(4, 18), ipady=4)

        ttk.Checkbutton(direita,
                        text="Iniciar em modo de Autoatendimento (kiosk)",
                        variable=self.modo_autoatendimento
                        ).pack(anchor="w", pady=(0, 24))

        ttk.Button(direita, text="Entrar", style="Primario.TButton",
                   command=self._fazer_login).pack(fill="x", ipady=4)

        # Informações institucionais (não mais credenciais expostas)
        info = ttk.Frame(direita, style="Card.TFrame", padding=(16, 14))
        info.pack(fill="x", pady=(28, 0))
        try:
            from .database import get_config
            nome_inst = get_config("NOME_INSTITUICAO", "CEFE")
        except Exception:
            nome_inst = "CEFE"
        ttk.Label(info, text=nome_inst,
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 11)).pack(anchor="w")
        ttk.Label(info,
                  text=("Em caso de esquecimento de senha, procure o "
                        "administrador do sistema."),
                  style="CardHint.TLabel",
                  wraplength=420).pack(anchor="w", pady=(4, 0))

        self.ent_matricula.focus_set()

    # ------------------------------------------------------------------
    def _fazer_login(self):
        matricula = self.ent_matricula.get().strip()
        senha = self.ent_senha.get()
        sessao = autenticar(matricula, senha)
        if not sessao:
            messagebox.showerror("Acesso negado",
                                 "Matrícula ou senha incorretas.",
                                 parent=self)
            self.ent_senha.delete(0, "end")
            self.ent_senha.focus_set()
            return
        self.sessao = sessao
        self.destroy()

    # ------------------------------------------------------------------
    def executar(self) -> tuple[Optional[Sessao], bool]:
        """Executa o mainloop e retorna (sessao, modo_autoatendimento)."""
        self.mainloop()
        return self.sessao, self.modo_autoatendimento.get()
