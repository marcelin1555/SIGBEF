"""
SIGBEF — Tela de login.

Exibe um diálogo modal com matrícula e senha. Em caso de sucesso, retorna
o objeto Sessao para o chamador.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from . import __version__
from . import icones
from .auth import autenticar, Sessao
from . import ui_tema as tema


def modo_demonstracao() -> bool:
    """A tela deve mostrar as credenciais de teste?

    So quando alguem pede explicitamente, com `--demo` na linha de
    comando (que liga SIGBEF_DEMO) ou com a variavel de ambiente posta a
    mao. As credenciais ficaram expostas na tela ate a v1.0.0 e foram
    tiradas de proposito: numa biblioteca de verdade, senha impressa na
    tela de entrada e a porta destrancada. Numa banca de feira, e o
    contrario -- quem for demonstrar precisa entrar sem decorar nada.
    """
    return os.environ.get("SIGBEF_DEMO", "").strip().lower() in (
        "1", "true", "sim")


class JanelaLogin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.sessao: Optional[Sessao] = None
        self.modo_autoatendimento = tk.BooleanVar(value=False)

        self.title("SIGBEF - Acesso ao Sistema")
        tema.aplicar_tema(self)
        icones.aplicar_icone_janela(self)
        self._construir()
        # O cartao de demonstracao acrescenta seis linhas de conta abaixo
        # do botao Entrar; medido, pede 150 px a mais. Sem isso a janela
        # de 620 mostrava so as duas primeiras contas e cortava o resto.
        altura = 790 if modo_demonstracao() else 620
        tema.centralizar_janela(self, 1000, altura, minimo=(960, 600))
        self.bind("<Return>", lambda e: self._fazer_login())

    # ------------------------------------------------------------------
    def _construir(self):
        # Lateral institucional (azul)
        lateral = tk.Frame(self, bg=tema.COR_PRIMARIA)
        lateral.pack(side="left", fill="both", expand=False)
        lateral.configure(width=440)

        tk.Label(lateral, bg=tema.COR_PRIMARIA,
                 image=icones.icone("logoplaca", "original", 56)
                 ).pack(pady=(64, 0), padx=40, anchor="w")
        tk.Label(lateral, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text="SIGBEF", font=("Segoe UI Semibold", 56)
                 ).pack(pady=(12, 0), padx=40, anchor="w")

        tk.Label(lateral, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text="Sistema Integrado de Gestão\nda Biblioteca Escolar",
                 font=("Segoe UI", 16), justify="left"
                 ).pack(padx=40, anchor="w", pady=(8, 30))

        tk.Frame(lateral, bg=tema.COR_DESTAQUE, height=4, width=120
                 ).pack(padx=40, anchor="w")

        # Brasão da instituição, quando configurado (Configurações,
        # Aparência). Deixa a tela com a identidade da escola.
        img_brasao = icones.brasao(max_altura=120)
        if img_brasao is not None:
            tk.Label(lateral, bg=tema.COR_PRIMARIA, image=img_brasao
                     ).pack(padx=40, anchor="w", pady=(24, 0))

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
            lateral, bg=tema.COR_PRIMARIA, fg=tema.COR_PRIMARIA_SUAVE,
            text=f"Versão {__version__} · produto em produção",
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

        if modo_demonstracao():
            self._cartao_demo(direita)
        else:
            self._cartao_institucional(direita)

        self.ent_matricula.focus_set()

    # ------------------------------------------------------------------
    def _cartao_institucional(self, pai):
        info = ttk.Frame(pai, style="Card.TFrame", padding=(16, 14))
        info.pack(fill="x", pady=(28, 0))
        try:
            from .database import get_config
            nome_inst = get_config("NOME_INSTITUICAO", "CEFE")
        except Exception:
            nome_inst = "CEFE"
        ttk.Label(info, text=nome_inst, style="Card.TLabel",
                  font=("Segoe UI Semibold", 11)).pack(anchor="w")
        ttk.Label(info,
                  text=("Em caso de esquecimento de senha, procure o "
                        "administrador do sistema."),
                  style="CardHint.TLabel",
                  wraplength=420).pack(anchor="w", pady=(4, 0))

    def _cartao_demo(self, pai):
        """Lista as contas de teste, com a senha ao lado.

        Uma linha por perfil, e clicar preenche os campos: numa
        demonstracao ao vivo, digitar matricula errada na frente da
        banca custa mais caro que o minuto que se economiza."""
        from .seed import USUARIOS_PADRAO

        cartao = ttk.Frame(pai, style="Card.TFrame", padding=(16, 12))
        cartao.pack(fill="x", pady=(20, 0))
        ttk.Label(cartao, text="Contas de demonstração",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 11)).pack(anchor="w")
        ttk.Label(cartao, text="Clique numa linha para preencher.",
                  style="CardHint.TLabel").pack(anchor="w", pady=(0, 8))

        for nome, matricula, perfil, senha, _email, _turma in USUARIOS_PADRAO:
            # Sem Frame por linha: ele nascia com a largura do cartao e
            # deixava um risco branco a direita de cada conta.
            texto = f"{perfil.capitalize():<14} {matricula} / {senha}"
            rot = ttk.Label(cartao, text=texto, style="CardHint.TLabel",
                            font=("Consolas", 10), cursor="hand2")
            rot.pack(anchor="w", pady=1)
            rot.bind("<Button-1>",
                     lambda _e, m=matricula, s=senha: self._preencher(m, s))

    def _preencher(self, matricula, senha):
        self.ent_matricula.delete(0, "end")
        self.ent_matricula.insert(0, matricula)
        self.ent_senha.delete(0, "end")
        self.ent_senha.insert(0, senha)
        self.ent_senha.focus_set()

    # ------------------------------------------------------------------
    def _fazer_login(self):
        matricula = self.ent_matricula.get().strip()
        senha = self.ent_senha.get()
        sessao = autenticar(matricula, senha)
        if not sessao:
            from .auth import minutos_bloqueio_restantes
            faltam = minutos_bloqueio_restantes(matricula)
            if faltam:
                messagebox.showwarning(
                    "Conta temporariamente bloqueada",
                    f"Muitas tentativas de senha. Tente novamente em "
                    f"{faltam} minuto(s), ou procure o administrador.",
                    parent=self)
            else:
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
