# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marcello
"""
SIGBEF — Assistente de primeira execução.

Quando o banco de dados está vazio (nenhum usuário cadastrado), em vez
de mostrar o login, exibimos este assistente que coleta as informações
da instituição e cria a primeira conta de administrador.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from . import ui_tema as tema
from . import servicos
from .database import set_config
from .servicos import RegraNegocioError


class JanelaPrimeiraExecucao(tk.Tk):
    """Assistente exibido apenas na primeira execução."""

    def __init__(self):
        super().__init__()
        self.sucesso: bool = False
        self.title("SIGBEF — Configuração inicial")
        tema.aplicar_tema(self)
        tema.centralizar_janela(self, 1000, 680)
        self.minsize(960, 640)

        self._passo_atual = 0
        self._dados = {
            "instituicao": "",
            "nome": "",
            "matricula": "admin",
            "email": "",
            "senha": "",
        }
        self._construir()

    # ------------------------------------------------------------------
    def _construir(self):
        # Cabeçalho
        topo = tk.Frame(self, bg=tema.COR_PRIMARIA, height=80)
        topo.pack(fill="x")
        topo.pack_propagate(False)
        tk.Label(topo, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text="SIGBEF", font=("Segoe UI Semibold", 22)
                 ).pack(side="left", padx=24, pady=18)
        tk.Label(topo, bg=tema.COR_PRIMARIA, fg="#B7CCE5",
                 text="Configuração inicial do sistema",
                 font=("Segoe UI", 13)).pack(side="left", pady=22)

        # Corpo
        self._corpo = ttk.Frame(self, padding=(40, 30))
        self._corpo.pack(fill="both", expand=True)
        self._mostrar_passo(0)

    # ------------------------------------------------------------------
    def _limpar_corpo(self):
        for w in self._corpo.winfo_children():
            w.destroy()

    def _mostrar_passo(self, n: int):
        self._passo_atual = n
        self._limpar_corpo()
        if n == 0:
            self._passo_boas_vindas()
        elif n == 1:
            self._passo_instituicao()
        elif n == 2:
            self._passo_admin()
        elif n == 3:
            self._passo_concluido()

    # ------------------------------------------------------------------
    def _passo_boas_vindas(self):
        ttk.Label(self._corpo, text="Bem-vindo ao SIGBEF",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self._corpo,
                  text=("Esta é a primeira vez que o sistema é executado. "
                        "Vamos configurar a sua biblioteca em 3 passos rápidos."),
                  style="Hint.TLabel", wraplength=860
                  ).pack(anchor="w", pady=(6, 24))

        card = ttk.Frame(self._corpo, style="Card.TFrame", padding=24)
        card.pack(fill="x")
        ttk.Label(card, text="O que vamos fazer:",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 12)
                  ).pack(anchor="w", pady=(0, 12))
        passos = [
            ("1.", "Identificar a instituição",
                  "Nome da escola/biblioteca que aparecerá no sistema."),
            ("2.", "Criar a conta de administrador",
                  "Primeira conta com acesso total — você vai usar para configurar o resto."),
            ("3.", "Pronto para começar",
                  "O sistema abre e você pode começar a cadastrar livros e usuários."),
        ]
        for num, titulo, desc in passos:
            linha = ttk.Frame(card, style="Card.TFrame")
            linha.pack(fill="x", pady=4)
            tk.Label(linha, text=num, bg=tema.COR_CARD,
                     fg=tema.COR_PRIMARIA,
                     font=("Segoe UI Semibold", 14)).pack(side="left", padx=(0, 12))
            txt = ttk.Frame(linha, style="Card.TFrame")
            txt.pack(side="left", fill="x", expand=True)
            ttk.Label(txt, text=titulo, style="Card.TLabel",
                      font=("Segoe UI Semibold", 11)).pack(anchor="w")
            ttk.Label(txt, text=desc, style="CardHint.TLabel"
                      ).pack(anchor="w")

        self._botoes_navegacao(prox=lambda: self._mostrar_passo(1),
                                prox_label="Começar →")

    # ------------------------------------------------------------------
    def _passo_instituicao(self):
        ttk.Label(self._corpo, text="Passo 1 de 3 — Instituição",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self._corpo,
                  text="Como sua biblioteca será identificada no sistema?",
                  style="Hint.TLabel").pack(anchor="w", pady=(6, 24))

        card = ttk.Frame(self._corpo, style="Card.TFrame", padding=24)
        card.pack(fill="x")

        ttk.Label(card, text="Nome da instituição *",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 11)).pack(anchor="w")
        ttk.Label(card,
                  text="Ex.: CEFE — Centro Educacional Felinto Elísio",
                  style="CardHint.TLabel").pack(anchor="w", pady=(0, 8))
        self.ent_inst = ttk.Entry(card, font=("Segoe UI", 12), width=60)
        self.ent_inst.pack(fill="x", ipady=4)
        self.ent_inst.insert(0, self._dados["instituicao"] or
                              "CEFE — Centro Educacional Felinto Elísio")
        self.ent_inst.focus_set()
        self.ent_inst.bind("<Return>", lambda e: self._avancar_instituicao())

        self._botoes_navegacao(volt=lambda: self._mostrar_passo(0),
                                prox=self._avancar_instituicao)

    def _avancar_instituicao(self):
        nome = self.ent_inst.get().strip()
        if not nome:
            messagebox.showwarning(
                "Campo obrigatório",
                "Informe o nome da instituição.",
                parent=self)
            return
        self._dados["instituicao"] = nome
        self._mostrar_passo(2)

    # ------------------------------------------------------------------
    def _passo_admin(self):
        ttk.Label(self._corpo, text="Passo 2 de 3 — Conta de administrador",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self._corpo,
                  text=("Crie a primeira conta de acesso. Ela terá controle "
                        "total sobre o sistema."),
                  style="Hint.TLabel").pack(anchor="w", pady=(6, 24))

        card = ttk.Frame(self._corpo, style="Card.TFrame", padding=24)
        card.pack(fill="x")
        card.columnconfigure(1, weight=1)

        campos = [
            ("nome", "Nome completo *",
                "Ex.: Maria Silva — bibliotecária responsável"),
            ("matricula", "Matrícula / usuário *",
                "Apelido curto que você vai digitar no login (ex.: 'admin', 'maria')"),
            ("email", "E-mail (opcional)",
                "Usado para contato. Pode deixar em branco."),
            ("senha", "Senha *",
                "Mínimo 6 caracteres. Use algo difícil de adivinhar."),
            ("senha2", "Confirme a senha *", ""),
        ]
        self._entries: dict[str, ttk.Entry] = {}
        for i, (chave, rotulo, hint) in enumerate(campos):
            ttk.Label(card, text=rotulo,
                      style="Card.TLabel",
                      font=("Segoe UI Semibold", 10)
                      ).grid(row=i*2, column=0, columnspan=2,
                              sticky="w", pady=(6, 2))
            ent = ttk.Entry(card, font=("Segoe UI", 11))
            if chave.startswith("senha"):
                ent.configure(show="•")
            ent.grid(row=i*2 + 1, column=0, columnspan=2,
                     sticky="ew", pady=(0, 6), ipady=2)
            valor = self._dados.get(chave, "")
            if valor:
                ent.insert(0, valor)
            if hint:
                ttk.Label(card, text=hint, style="CardHint.TLabel",
                          font=("Segoe UI", 9)
                          ).grid(row=i*2 + 1, column=2, sticky="w",
                                  padx=(12, 0))
            self._entries[chave] = ent
        self._entries["nome"].focus_set()

        self._botoes_navegacao(volt=lambda: self._mostrar_passo(1),
                                prox=self._avancar_admin,
                                prox_label="Criar conta →")

    def _avancar_admin(self):
        nome = self._entries["nome"].get().strip()
        matricula = self._entries["matricula"].get().strip()
        email = self._entries["email"].get().strip()
        senha = self._entries["senha"].get()
        senha2 = self._entries["senha2"].get()

        if not nome:
            messagebox.showwarning("Atenção",
                                     "Informe seu nome completo.",
                                     parent=self)
            return
        if not matricula:
            messagebox.showwarning("Atenção",
                                     "Informe uma matrícula/usuário.",
                                     parent=self)
            return
        if len(senha) < 6:
            messagebox.showwarning(
                "Senha fraca",
                "A senha do administrador deve ter pelo menos 6 caracteres.",
                parent=self)
            return
        if senha != senha2:
            messagebox.showwarning("Atenção",
                                     "As senhas não conferem.",
                                     parent=self)
            return

        self._dados.update({
            "nome": nome,
            "matricula": matricula,
            "email": email,
            "senha": senha,
        })

        # Persistir tudo agora
        try:
            set_config("NOME_INSTITUICAO", self._dados["instituicao"])
            servicos.cadastrar_usuario(
                nome=nome,
                matricula=matricula,
                email=email,
                perfil="ADMINISTRADOR",
                senha=senha,
                gerar_cartao=True,
            )
        except RegraNegocioError as e:
            messagebox.showerror("Erro",
                                  f"Não foi possível criar a conta:\n{e}",
                                  parent=self)
            return
        except Exception as e:
            messagebox.showerror("Erro",
                                  f"Erro inesperado: {e}",
                                  parent=self)
            return

        self.sucesso = True
        self._mostrar_passo(3)

    # ------------------------------------------------------------------
    def _passo_concluido(self):
        ttk.Label(self._corpo, text="Pronto!",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self._corpo,
                  text="A configuração inicial está concluída.",
                  style="Hint.TLabel").pack(anchor="w", pady=(6, 24))

        card = ttk.Frame(self._corpo, style="Card.TFrame", padding=24)
        card.pack(fill="x")

        check = tk.Frame(card, bg=tema.COR_CARD)
        check.pack(fill="x", pady=(0, 10))
        tk.Label(check, text="✓", bg=tema.COR_CARD,
                 fg=tema.COR_SUCESSO,
                 font=("Segoe UI Semibold", 28)
                 ).pack(side="left", padx=(0, 12))
        cont = tk.Frame(check, bg=tema.COR_CARD)
        cont.pack(side="left", fill="x", expand=True, anchor="w")
        ttk.Label(cont, text="Conta de administrador criada",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 12)).pack(anchor="w")
        ttk.Label(cont,
                  text=(f"Usuário: {self._dados['matricula']}"),
                  style="CardHint.TLabel").pack(anchor="w")

        ttk.Label(card,
                  text="Próximos passos sugeridos:",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 11)
                  ).pack(anchor="w", pady=(20, 8))
        for t in [
            "1. Cadastrar bibliotecários e funcionários em Usuários.",
            "2. Cadastrar o acervo em Livros e exemplares.",
            "3. Imprimir as etiquetas de código de barras dos exemplares.",
            "4. Cadastrar alunos/professores conforme novos usuários chegarem.",
            "5. Ajustar prazos e multas em Configurações se necessário.",
        ]:
            ttk.Label(card, text=t, style="Card.TLabel"
                      ).pack(anchor="w", pady=2)

        ttk.Label(card,
                  text=("Dica: se quiser ver o sistema funcionando com dados "
                        "de demonstração antes de cadastrar os reais, vá em "
                        "Configurações → 'Carregar dados de demonstração'."),
                  style="CardHint.TLabel", wraplength=820
                  ).pack(anchor="w", pady=(20, 0))

        bot = ttk.Frame(self._corpo)
        bot.pack(fill="x", pady=(30, 0))
        ttk.Button(bot, text="Entrar no sistema agora",
                    style="Primario.TButton",
                    command=self._finalizar).pack(side="right")

    def _finalizar(self):
        self.destroy()

    # ------------------------------------------------------------------
    def _botoes_navegacao(self, volt=None, prox=None,
                          prox_label: str = "Avançar →"):
        bot = ttk.Frame(self._corpo)
        bot.pack(fill="x", pady=(30, 0), side="bottom")
        if volt:
            ttk.Button(bot, text="← Voltar",
                        command=volt).pack(side="left")
        if prox:
            ttk.Button(bot, text=prox_label,
                        style="Primario.TButton",
                        command=prox).pack(side="right")

    # ------------------------------------------------------------------
    def executar(self) -> bool:
        """Mostra o assistente. Retorna True se a configuração foi concluída."""
        self.mainloop()
        return self.sucesso
