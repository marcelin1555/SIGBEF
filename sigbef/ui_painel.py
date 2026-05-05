"""
SIGBEF — Painel principal (administrador, bibliotecário e usuários comuns).

Janela única com sidebar e área de conteúdo trocável. Cada perfil enxerga
um conjunto de abas adequado às suas permissões.
"""
from __future__ import annotations

import csv
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

from . import servicos
from . import ui_tema as tema
from .auth import Sessao
from .formato import data_br, data_hora_br, reais
from .servicos import RegraNegocioError
from .ui_dialogos import (
    DialogoDetalhesLivro,
    DialogoLivro,
    DialogoSelecionarExemplar,
    DialogoUsuario,
)


# ---------------------------------------------------------------------------
# Painel principal
# ---------------------------------------------------------------------------
class PainelPrincipal(tk.Tk):
    def __init__(self, sessao: Sessao):
        super().__init__()
        self.sessao = sessao
        self.title(f"SIGBEF — {sessao.nome} ({sessao.perfil.title()})")
        tema.aplicar_tema(self)
        tema.centralizar_janela(self, 1280, 780)
        self.minsize(1180, 700)

        self._secoes: dict[str, ttk.Frame] = {}
        self._botoes_lateral: dict[str, ttk.Button] = {}
        self._construir()
        self._mostrar_secao(self._secao_inicial())

    # ------------------------------------------------------------------
    def _construir(self):
        # Cabeçalho
        cabecalho = tk.Frame(self, bg=tema.COR_PRIMARIA, height=60)
        cabecalho.pack(fill="x")
        cabecalho.pack_propagate(False)
        tk.Label(cabecalho, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text="SIGBEF", font=("Segoe UI Semibold", 18)
                 ).pack(side="left", padx=20)
        tk.Label(cabecalho, bg=tema.COR_PRIMARIA, fg="#B7CCE5",
                 text="Sistema Integrado de Gestão da Biblioteca",
                 font=("Segoe UI", 11)).pack(side="left")

        info_user = tk.Frame(cabecalho, bg=tema.COR_PRIMARIA)
        info_user.pack(side="right", padx=20)
        tk.Label(info_user, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text=self.sessao.nome,
                 font=("Segoe UI Semibold", 10)).pack(anchor="e")
        tk.Label(info_user, bg=tema.COR_PRIMARIA, fg="#B7CCE5",
                 text=f"{self.sessao.perfil.title()} • matrícula {self.sessao.matricula}",
                 font=("Segoe UI", 9)).pack(anchor="e")
        ttk.Button(cabecalho, text="Sair",
                   command=self._sair).pack(side="right", padx=(0, 12))

        # Corpo (sidebar + área principal)
        corpo = tk.Frame(self, bg=tema.COR_FUNDO)
        corpo.pack(fill="both", expand=True)

        sidebar = tk.Frame(corpo, bg=tema.COR_PRIMARIA, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        principal = ttk.Frame(corpo, padding=24)
        principal.pack(side="right", fill="both", expand=True)

        # Itens da sidebar (filtrados por perfil)
        itens = [("painel", "Painel inicial")]
        if self.sessao.is_bibliotecario:
            itens += [
                ("livros", "Livros e exemplares"),
                ("usuarios", "Usuários"),
                ("emprestimos", "Empréstimos abertos"),
                ("relatorios", "Relatórios"),
            ]
        if self.sessao.is_admin:
            itens.append(("config", "Configurações"))

        # Para alunos/professores, mostrar apenas pesquisa e meus empréstimos
        if not self.sessao.is_bibliotecario:
            itens = [("painel", "Painel inicial"),
                     ("pesquisa_aluno", "Pesquisar livros"),
                     ("meus_emp", "Meus empréstimos")]

        for chave, rotulo in itens:
            btn = ttk.Button(sidebar, text=rotulo,
                              style="Sidebar.TButton",
                              command=lambda k=chave: self._mostrar_secao(k))
            btn.pack(fill="x")
            self._botoes_lateral[chave] = btn

        # Construir frames das seções
        self._principal = principal
        for chave, _ in itens:
            self._construir_secao(chave)

    def _secao_inicial(self) -> str:
        return "painel"

    def _construir_secao(self, chave: str):
        if chave == "painel":
            self._secoes[chave] = SecaoPainel(self._principal, self)
        elif chave == "livros":
            self._secoes[chave] = SecaoLivros(self._principal, self)
        elif chave == "usuarios":
            self._secoes[chave] = SecaoUsuarios(self._principal, self)
        elif chave == "emprestimos":
            self._secoes[chave] = SecaoEmprestimos(self._principal, self)
        elif chave == "relatorios":
            self._secoes[chave] = SecaoRelatorios(self._principal, self)
        elif chave == "config":
            self._secoes[chave] = SecaoConfig(self._principal, self)
        elif chave == "pesquisa_aluno":
            self._secoes[chave] = SecaoPesquisaAluno(self._principal, self)
        elif chave == "meus_emp":
            self._secoes[chave] = SecaoMeusEmprestimos(self._principal, self)

    def _mostrar_secao(self, chave: str):
        for s in self._secoes.values():
            s.pack_forget()
        if chave not in self._secoes:
            return
        self._secoes[chave].pack(fill="both", expand=True)
        self._secoes[chave].atualizar()

    def _sair(self):
        if messagebox.askyesno("Encerrar sessão",
                                "Deseja realmente sair do sistema?",
                                parent=self):
            self.destroy()


# ---------------------------------------------------------------------------
# Mixin: cada seção implementa atualizar()
# ---------------------------------------------------------------------------
class SecaoBase(ttk.Frame):
    def __init__(self, parent, painel: PainelPrincipal):
        super().__init__(parent)
        self.painel = painel
        self.sessao = painel.sessao

    def atualizar(self) -> None:
        """Sobrescreva para recarregar dados ao mostrar a seção."""


# ---------------------------------------------------------------------------
# Painel inicial — dashboard
# ---------------------------------------------------------------------------
class SecaoPainel(SecaoBase):
    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text=f"Olá, {self.sessao.nome.split()[0]}!",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self,
                  text=("Bem-vindo(a) ao SIGBEF. Use o menu lateral para "
                        "acessar as funcionalidades."),
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 16))

        self._cards_frame = ttk.Frame(self)
        self._cards_frame.pack(fill="x")

        self._cards: dict[str, ttk.Label] = {}
        for i, (chave, titulo, _cor) in enumerate([
            ("livros", "Títulos no acervo", tema.COR_PRIMARIA),
            ("exemplares", "Exemplares totais", tema.COR_SECUNDARIA),
            ("disponiveis", "Disponíveis agora", tema.COR_SUCESSO),
            ("emp_abertos", "Empréstimos abertos", tema.COR_DESTAQUE),
            ("atrasados", "Em atraso", tema.COR_ERRO),
            ("usuarios", "Usuários ativos", tema.COR_SECUNDARIA),
        ]):
            card = ttk.Frame(self._cards_frame, style="Card.TFrame",
                              padding=20)
            card.grid(row=i // 3, column=i % 3, sticky="ew",
                       padx=8, pady=8, ipadx=4)
            self._cards_frame.columnconfigure(i % 3, weight=1)
            ttk.Label(card, text=titulo, style="CardHint.TLabel").pack(anchor="w")
            valor = ttk.Label(card, text="—", style="Display.TLabel")
            valor.pack(anchor="w", pady=(6, 0))
            self._cards[chave] = valor

        ttk.Label(self, text="Top 10 livros mais emprestados",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(20, 8))

        self.tree_top = ttk.Treeview(self,
                                       columns=("titulo", "qtd"),
                                       show="headings", height=10)
        self.tree_top.heading("titulo", text="Título")
        self.tree_top.heading("qtd", text="Empréstimos")
        self.tree_top.column("titulo", width=600, anchor="w")
        self.tree_top.column("qtd", width=120, anchor="center")
        self.tree_top.pack(fill="x")

    def atualizar(self):
        st = servicos.estatisticas()
        for k, v in st.items():
            if k in self._cards:
                self._cards[k].configure(text=str(v))
        for item in self.tree_top.get_children():
            self.tree_top.delete(item)
        for r in servicos.relatorio_circulacao(10):
            self.tree_top.insert("", "end",
                                  values=(r["titulo"], r["emprestimos"]))


# ---------------------------------------------------------------------------
# Livros e exemplares
# ---------------------------------------------------------------------------
class SecaoLivros(SecaoBase):
    def __init__(self, parent, painel):
        super().__init__(parent, painel)

        topo = ttk.Frame(self)
        topo.pack(fill="x")
        ttk.Label(topo, text="Livros e exemplares",
                  style="Titulo.TLabel").pack(side="left")
        ttk.Button(topo, text="+ Cadastrar livro",
                    style="Primario.TButton",
                    command=self._novo_livro
                    ).pack(side="right")
        ttk.Button(topo, text="Ver detalhes / código de barras",
                    command=self._detalhes
                    ).pack(side="right", padx=(0, 8))

        # Filtros
        filtros = ttk.Frame(self, padding=(0, 12))
        filtros.pack(fill="x")
        ttk.Label(filtros, text="Buscar:").pack(side="left")
        self.ent_busca = ttk.Entry(filtros, width=40)
        self.ent_busca.pack(side="left", padx=8)
        self.ent_busca.bind("<Return>", lambda e: self.atualizar())
        self.var_disponiveis = tk.BooleanVar(value=False)
        ttk.Checkbutton(filtros, text="Apenas com exemplares disponíveis",
                        variable=self.var_disponiveis,
                        command=self.atualizar).pack(side="left", padx=8)
        ttk.Button(filtros, text="Pesquisar",
                    command=self.atualizar).pack(side="left")

        cols = ("id", "titulo", "autores", "categoria", "ano",
                "total", "disp")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=18)
        self.tree.heading("id", text="ID")
        self.tree.heading("titulo", text="Título")
        self.tree.heading("autores", text="Autor(es)")
        self.tree.heading("categoria", text="Categoria")
        self.tree.heading("ano", text="Ano")
        self.tree.heading("total", text="Exemp.")
        self.tree.heading("disp", text="Disp.")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("titulo", width=320, anchor="w")
        self.tree.column("autores", width=240, anchor="w")
        self.tree.column("categoria", width=140, anchor="w")
        self.tree.column("ano", width=70, anchor="center")
        self.tree.column("total", width=70, anchor="center")
        self.tree.column("disp", width=70, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=(8, 0))
        self.tree.bind("<Double-1>", lambda e: self._detalhes())

    def _novo_livro(self):
        DialogoLivro(self.painel, self.sessao, ao_salvar=self.atualizar)

    def _detalhes(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um livro",
                                  "Escolha um livro na lista.",
                                  parent=self.painel)
            return
        livro_id = int(self.tree.item(sel[0])["values"][0])
        DialogoDetalhesLivro(self.painel, livro_id)

    def atualizar(self):
        for it in self.tree.get_children():
            self.tree.delete(it)
        for liv in servicos.listar_livros(self.ent_busca.get(),
                                            self.var_disponiveis.get()):
            self.tree.insert("", "end", values=(
                liv["id"], liv["titulo"], liv["autores"] or "—",
                liv["categoria"] or "—", liv["ano_publicacao"] or "—",
                liv["total_exemplares"] or 0, liv["disponiveis"] or 0,
            ))


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------
class SecaoUsuarios(SecaoBase):
    def __init__(self, parent, painel):
        super().__init__(parent, painel)

        topo = ttk.Frame(self)
        topo.pack(fill="x")
        ttk.Label(topo, text="Usuários", style="Titulo.TLabel").pack(side="left")
        ttk.Button(topo, text="+ Cadastrar usuário",
                    style="Primario.TButton",
                    command=self._novo_usuario
                    ).pack(side="right")
        ttk.Button(topo, text="Ativar/Desativar",
                    command=self._toggle_status
                    ).pack(side="right", padx=8)

        filtros = ttk.Frame(self, padding=(0, 12))
        filtros.pack(fill="x")
        ttk.Label(filtros, text="Buscar:").pack(side="left")
        self.ent_busca = ttk.Entry(filtros, width=40)
        self.ent_busca.pack(side="left", padx=8)
        self.ent_busca.bind("<Return>", lambda e: self.atualizar())
        ttk.Button(filtros, text="Pesquisar",
                    command=self.atualizar).pack(side="left")

        cols = ("id", "nome", "matricula", "perfil", "email", "cartao",
                "ativo")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=18)
        for c, t, w in [("id", "ID", 50), ("nome", "Nome", 240),
                        ("matricula", "Matrícula", 110),
                        ("perfil", "Perfil", 130),
                        ("email", "E-mail", 220),
                        ("cartao", "Cartão", 200),
                        ("ativo", "Ativo", 70)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(8, 0))

    def _novo_usuario(self):
        DialogoUsuario(self.painel, self.sessao, ao_salvar=self.atualizar)

    def _toggle_status(self):
        sel = self.tree.selection()
        if not sel:
            return
        valores = self.tree.item(sel[0])["values"]
        usuario_id = int(valores[0])
        ativo_atual = str(valores[-1]).lower() == "sim"
        try:
            servicos.alternar_status_usuario(usuario_id, not ativo_atual)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self.painel)
        self.atualizar()

    def atualizar(self):
        for it in self.tree.get_children():
            self.tree.delete(it)
        for u in servicos.listar_usuarios(self.ent_busca.get()):
            self.tree.insert("", "end", values=(
                u["id"], u["nome"], u["matricula"], u["perfil"],
                u.get("email") or "—",
                u.get("codigo_barras") or "—",
                "Sim" if u["ativo"] else "Não",
            ))


# ---------------------------------------------------------------------------
# Empréstimos abertos (balcão)
# ---------------------------------------------------------------------------
class SecaoEmprestimos(SecaoBase):
    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text="Empréstimos e devoluções",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self, text=("Operações de balcão para apoiar o atendimento "
                               "presencial. Aceita código de barras OU número "
                               "de tombo."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 16))

        # ------ Card de empréstimo ------
        emp_card = ttk.Frame(self, style="Card.TFrame", padding=18)
        emp_card.pack(fill="x")
        ttk.Label(emp_card, text="Empréstimo rápido",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 12)).grid(row=0, column=0,
                                                         columnspan=5,
                                                         sticky="w",
                                                         pady=(0, 10))
        ttk.Label(emp_card, text="Matrícula ou cartão:",
                  style="Card.TLabel").grid(row=1, column=0, sticky="e", padx=(0, 6))
        self.ent_emp_matr = ttk.Entry(emp_card, width=20)
        self.ent_emp_matr.grid(row=1, column=1, sticky="w")
        ttk.Button(emp_card, text="Buscar usuário...",
                    command=self._selecionar_usuario
                    ).grid(row=1, column=2, padx=8)

        ttk.Label(emp_card, text="Código ou tombo:",
                  style="Card.TLabel").grid(row=2, column=0, sticky="e",
                                             padx=(0, 6), pady=(8, 0))
        self.ent_emp_cod = ttk.Entry(emp_card, width=26)
        self.ent_emp_cod.grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Button(emp_card, text="Selecionar exemplar...",
                    command=self._selecionar_exemplar_emprestimo
                    ).grid(row=2, column=2, padx=8, pady=(8, 0))
        ttk.Button(emp_card, text="✓ Registrar empréstimo",
                    style="Sucesso.TButton",
                    command=self._emprestar
                    ).grid(row=2, column=3, padx=(8, 0), pady=(8, 0))

        self.lbl_msg_emp = ttk.Label(emp_card, text="",
                                       style="Card.TLabel")
        self.lbl_msg_emp.grid(row=3, column=0, columnspan=5,
                               sticky="w", pady=(10, 0))

        # ------ Card de devolução ------
        dev_card = ttk.Frame(self, style="Card.TFrame", padding=18)
        dev_card.pack(fill="x", pady=(12, 0))
        ttk.Label(dev_card, text="Devolução rápida",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 12)).grid(row=0, column=0,
                                                         columnspan=4,
                                                         sticky="w",
                                                         pady=(0, 10))
        ttk.Label(dev_card, text="Código ou tombo:",
                  style="Card.TLabel").grid(row=1, column=0, sticky="e",
                                             padx=(0, 6))
        self.ent_dev_cod = ttk.Entry(dev_card, width=26)
        self.ent_dev_cod.grid(row=1, column=1, sticky="w")
        ttk.Button(dev_card, text="↻ Registrar devolução",
                    style="Aviso.TButton",
                    command=self._devolver
                    ).grid(row=1, column=2, padx=(8, 0))

        self.ent_emp_cod.bind("<Return>", lambda e: self._emprestar())
        self.ent_emp_matr.bind("<Return>", lambda e: self.ent_emp_cod.focus_set())
        self.ent_dev_cod.bind("<Return>", lambda e: self._devolver())

        # Tabela de empréstimos abertos
        ttk.Label(self, text="Empréstimos em aberto",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(20, 6))

        cols = ("id", "usuario", "matricula", "titulo", "codigo",
                "emprestado", "previsto", "atrasado")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=14)
        for c, t, w in [("id", "ID", 50), ("usuario", "Usuário", 180),
                        ("matricula", "Matrícula", 100),
                        ("titulo", "Título", 280),
                        ("codigo", "Código", 160),
                        ("emprestado", "Empréstimo", 130),
                        ("previsto", "Previsto", 110),
                        ("atrasado", "Atraso?", 80)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("atrasado", background="#FDECEA",
                                  foreground=tema.COR_ERRO)
        self.tree.pack(fill="both", expand=True)

        op = ttk.Frame(self)
        op.pack(fill="x", pady=(8, 0))
        ttk.Button(op, text="Renovar selecionado",
                    command=self._renovar).pack(side="left", padx=(0, 8))
        ttk.Button(op, text="Quitar multa",
                    command=self._quitar).pack(side="left")

    def _selecionar_exemplar_emprestimo(self):
        d = DialogoSelecionarExemplar(self.painel)
        self.painel.wait_window(d)
        if d.codigo_selecionado:
            self.ent_emp_cod.delete(0, "end")
            self.ent_emp_cod.insert(0, d.codigo_selecionado)

    def _selecionar_usuario(self):
        d = _DialogoSelecionarUsuario(self.painel)
        self.painel.wait_window(d)
        if d.matricula_selecionada:
            self.ent_emp_matr.delete(0, "end")
            self.ent_emp_matr.insert(0, d.matricula_selecionada)

    def _emprestar(self):
        try:
            res = servicos.realizar_emprestimo(
                codigo_exemplar=self.ent_emp_cod.get(),
                matricula_usuario=self.ent_emp_matr.get(),
                origem="BALCAO",
                operador_id=self.sessao.id,
            )
        except RegraNegocioError as e:
            self.lbl_msg_emp.configure(
                text=f"⚠ {e}", foreground=tema.COR_ERRO)
            return
        self.lbl_msg_emp.configure(
            text=(f"✓ Empréstimo registrado: '{res['titulo']}' para "
                  f"{res['usuario_nome']}. Devolução prevista: "
                  f"{data_br(res['data_prevista'])} "
                  f"({res['prazo_dias']} dias)."),
            foreground=tema.COR_SUCESSO)
        self.ent_emp_cod.delete(0, "end")
        self.ent_emp_matr.delete(0, "end")
        self.atualizar()

    def _devolver(self):
        try:
            res = servicos.realizar_devolucao(
                codigo_exemplar=self.ent_dev_cod.get(),
                operador_id=self.sessao.id,
            )
        except RegraNegocioError as e:
            messagebox.showwarning("Não foi possível devolver", str(e),
                                    parent=self.painel)
            return
        msg = f"Devolução registrada: {res['titulo']}"
        if res["multa"] > 0:
            msg += (f"\n\nMulta gerada: {reais(res['multa'])} "
                    f"(atraso de {res['dias_atraso']} dia(s))")
        else:
            msg += "\n\nSem multa — devolução em dia."
        messagebox.showinfo("Devolução", msg, parent=self.painel)
        self.ent_dev_cod.delete(0, "end")
        self.atualizar()

    def _renovar(self):
        sel = self.tree.selection()
        if not sel:
            return
        emp_id = int(self.tree.item(sel[0])["values"][0])
        try:
            res = servicos.renovar_emprestimo(emp_id, self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self.painel)
            return
        messagebox.showinfo("Renovado",
                              f"Nova data prevista: {res['data_prevista']}",
                              parent=self.painel)
        self.atualizar()

    def _quitar(self):
        sel = self.tree.selection()
        if not sel:
            return
        emp_id = int(self.tree.item(sel[0])["values"][0])
        if messagebox.askyesno("Quitar multa",
                                "Deseja quitar a multa deste empréstimo?",
                                parent=self.painel):
            servicos.quitar_multa(emp_id, self.sessao.id)
            self.atualizar()

    def atualizar(self):
        for it in self.tree.get_children():
            self.tree.delete(it)
        for e in servicos.listar_emprestimos_em_aberto():
            atrasado = bool(e["atrasado"])
            tag = ("atrasado",) if atrasado else ()
            self.tree.insert("", "end", tags=tag, values=(
                e["id"], e["usuario"], e["matricula"], e["titulo"],
                e["codigo_barras"], data_hora_br(e["data_emprestimo"]),
                data_br(e["data_prevista"]), "SIM" if atrasado else "—",
            ))


# ---------------------------------------------------------------------------
# Diálogo: selecionar usuário
# ---------------------------------------------------------------------------
class _DialogoSelecionarUsuario(tk.Toplevel):
    """Dialogo simples para escolher usuário a partir de uma busca."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Selecionar usuário")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 720, 500)
        self.matricula_selecionada: str = ""

        wrap = ttk.Frame(self, padding=20)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Selecionar usuário",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap, text="Busque pelo nome, matrícula ou e-mail.",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 12))

        f = ttk.Frame(wrap)
        f.pack(fill="x")
        ttk.Label(f, text="Buscar:").pack(side="left")
        self.ent = ttk.Entry(f)
        self.ent.pack(side="left", fill="x", expand=True, padx=8)
        self.ent.bind("<Return>", lambda e: self._buscar())
        ttk.Button(f, text="Pesquisar",
                    command=self._buscar).pack(side="left")

        cols = ("nome", "matricula", "perfil", "email")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", height=14)
        for c, t, w in [("nome", "Nome", 240), ("matricula", "Matrícula", 100),
                         ("perfil", "Perfil", 130),
                         ("email", "E-mail", 220)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(12, 0))
        self.tree.bind("<Double-1>", lambda e: self._confirmar())

        botoes = ttk.Frame(wrap)
        botoes.pack(fill="x", pady=(12, 0))
        ttk.Button(botoes, text="Cancelar",
                    command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Usar usuário selecionado",
                    style="Primario.TButton",
                    command=self._confirmar).pack(side="right")

        self._buscar()
        self.ent.focus_set()

    def _buscar(self):
        for it in self.tree.get_children():
            self.tree.delete(it)
        for u in servicos.listar_usuarios(self.ent.get()):
            if not u["ativo"]:
                continue
            self.tree.insert("", "end", values=(
                u["nome"], u["matricula"], u["perfil"],
                u.get("email") or "—",
            ))

    def _confirmar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nada selecionado",
                                  "Escolha um usuário na lista.",
                                  parent=self)
            return
        self.matricula_selecionada = str(self.tree.item(sel[0])["values"][1])
        self.destroy()


# ---------------------------------------------------------------------------
# Relatórios
# ---------------------------------------------------------------------------
class SecaoRelatorios(SecaoBase):
    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text="Relatórios",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self, text=("Gere relatórios em CSV para análise externa "
                               "(planilhas, BI, etc.)."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 16))

        cards = ttk.Frame(self)
        cards.pack(fill="x")

        for i, (titulo, descricao, callback) in enumerate([
            ("Acervo completo",
             "Lista todos os livros e exemplares cadastrados.",
             self._exportar_acervo),
            ("Empréstimos em aberto",
             "Quem está com livros emprestados agora.",
             self._exportar_abertos),
            ("Usuários cadastrados",
             "Todos os usuários com seus perfis.",
             self._exportar_usuarios),
            ("Top 50 mais emprestados",
             "Livros mais procurados em todo o histórico.",
             self._exportar_circulacao),
        ]):
            card = ttk.Frame(cards, style="Card.TFrame", padding=18)
            card.grid(row=i // 2, column=i % 2, sticky="ew",
                       padx=8, pady=8)
            cards.columnconfigure(i % 2, weight=1)
            ttk.Label(card, text=titulo, style="Card.TLabel",
                      font=("Segoe UI Semibold", 12)).pack(anchor="w")
            ttk.Label(card, text=descricao, style="CardHint.TLabel",
                      wraplength=420).pack(anchor="w", pady=(2, 12))
            ttk.Button(card, text="Exportar CSV",
                        style="Primario.TButton",
                        command=callback).pack(anchor="w")

    def _arquivo_destino(self, sugestao: str) -> str | None:
        return filedialog.asksaveasfilename(
            parent=self.painel,
            initialfile=sugestao,
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
        )

    def _escrever(self, caminho: str, cabecalho: list[str],
                  linhas: list[list]):
        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(cabecalho)
            w.writerows(linhas)

    def _exportar_acervo(self):
        nome = self._arquivo_destino(
            f"acervo_{datetime.now().strftime('%Y%m%d')}.csv")
        if not nome:
            return
        livros = servicos.listar_livros()
        linhas = []
        for liv in livros:
            linhas.append([liv["id"], liv["titulo"], liv["autores"] or "",
                            liv["categoria"] or "", liv["editora"] or "",
                            liv["isbn"] or "", liv["ano_publicacao"] or "",
                            liv["total_exemplares"], liv["disponiveis"]])
        self._escrever(nome,
                        ["ID", "Título", "Autores", "Categoria", "Editora",
                         "ISBN", "Ano", "Total exemplares",
                         "Disponíveis"], linhas)
        messagebox.showinfo("Pronto", f"Arquivo salvo em:\n{nome}",
                              parent=self.painel)

    def _exportar_abertos(self):
        nome = self._arquivo_destino(
            f"emprestimos_abertos_{datetime.now().strftime('%Y%m%d')}.csv")
        if not nome:
            return
        emp = servicos.listar_emprestimos_em_aberto()
        linhas = [[e["id"], e["usuario"], e["matricula"], e["titulo"],
                    e["codigo_barras"], e["data_emprestimo"],
                    e["data_prevista"], "SIM" if e["atrasado"] else "NAO"]
                   for e in emp]
        self._escrever(nome,
                        ["ID", "Usuário", "Matrícula", "Título", "Código",
                         "Data empréstimo", "Data prevista", "Atrasado"],
                        linhas)
        messagebox.showinfo("Pronto", f"Arquivo salvo em:\n{nome}",
                              parent=self.painel)

    def _exportar_usuarios(self):
        nome = self._arquivo_destino(
            f"usuarios_{datetime.now().strftime('%Y%m%d')}.csv")
        if not nome:
            return
        users = servicos.listar_usuarios()
        linhas = [[u["id"], u["nome"], u["matricula"], u["perfil"],
                    u.get("email") or "", u.get("codigo_barras") or "",
                    "SIM" if u["ativo"] else "NAO"] for u in users]
        self._escrever(nome,
                        ["ID", "Nome", "Matrícula", "Perfil", "E-mail",
                         "Código cartão", "Ativo"], linhas)
        messagebox.showinfo("Pronto", f"Arquivo salvo em:\n{nome}",
                              parent=self.painel)

    def _exportar_circulacao(self):
        nome = self._arquivo_destino(
            f"circulacao_{datetime.now().strftime('%Y%m%d')}.csv")
        if not nome:
            return
        rs = servicos.relatorio_circulacao(50)
        linhas = [[i + 1, r["titulo"], r["emprestimos"]] for i, r in enumerate(rs)]
        self._escrever(nome, ["#", "Título", "Empréstimos"], linhas)
        messagebox.showinfo("Pronto", f"Arquivo salvo em:\n{nome}",
                              parent=self.painel)


# ---------------------------------------------------------------------------
# Configurações (somente admin)
# ---------------------------------------------------------------------------
class SecaoConfig(SecaoBase):
    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text="Configurações do sistema",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self, text=("Ajuste prazos, limites e valores de multa. As "
                               "alterações entram em vigor imediatamente."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 16))

        from .database import get_config

        form = ttk.Frame(self, style="Card.TFrame", padding=20)
        form.pack(fill="x")
        self._entries: dict[str, ttk.Entry] = {}
        for i, (chave, rotulo) in enumerate([
            ("PRAZO_ALUNO_DIAS", "Prazo padrão para alunos (dias)"),
            ("PRAZO_PROFESSOR_DIAS", "Prazo padrão para professores (dias)"),
            ("LIMITE_ALUNO", "Limite de empréstimos simultâneos (aluno)"),
            ("LIMITE_PROFESSOR", "Limite de empréstimos simultâneos (professor)"),
            ("MULTA_POR_DIA", "Multa por dia de atraso (R$)"),
            ("MULTA_TETO", "Teto máximo de multa (R$)"),
            ("NOME_INSTITUICAO", "Nome da instituição"),
        ]):
            ttk.Label(form, text=rotulo,
                      style="Card.TLabel").grid(row=i, column=0,
                                                 sticky="w", pady=6)
            ent = ttk.Entry(form, width=40)
            ent.grid(row=i, column=1, sticky="ew", padx=12, pady=6)
            ent.insert(0, get_config(chave) or "")
            form.columnconfigure(1, weight=1)
            self._entries[chave] = ent

        ttk.Button(self, text="Salvar configurações",
                    style="Primario.TButton",
                    command=self._salvar).pack(anchor="e", pady=(16, 0))

    def _salvar(self):
        from .database import set_config
        for chave, ent in self._entries.items():
            set_config(chave, ent.get().strip())
        messagebox.showinfo("Configurações", "Salvo com sucesso.",
                             parent=self.painel)


# ---------------------------------------------------------------------------
# Pesquisa para alunos/professores
# ---------------------------------------------------------------------------
class SecaoPesquisaAluno(SecaoBase):
    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text="Pesquisar livros",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self,
                  text=("Busque por título, autor, categoria ou ISBN. "
                        "Selecione um livro disponível e clique em "
                        "'Pegar emprestado' para registrar o empréstimo."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 16))

        f = ttk.Frame(self)
        f.pack(fill="x")
        self.ent = ttk.Entry(f, font=("Segoe UI", 12))
        self.ent.pack(side="left", fill="x", expand=True, ipady=4)
        self.ent.bind("<Return>", lambda e: self.atualizar())
        self.var_disp = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Apenas disponíveis",
                          variable=self.var_disp,
                          command=self.atualizar).pack(side="left",
                                                         padx=8)
        ttk.Button(f, text="Buscar", style="Primario.TButton",
                    command=self.atualizar).pack(side="left", padx=(8, 0))

        cols = ("id", "titulo", "autores", "categoria", "ano", "disp")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=18)
        self.tree.heading("id", text="ID")
        self.tree.heading("titulo", text="Título")
        self.tree.heading("autores", text="Autor(es)")
        self.tree.heading("categoria", text="Categoria")
        self.tree.heading("ano", text="Ano")
        self.tree.heading("disp", text="Disponíveis")
        self.tree.column("id", width=0, stretch=False)
        self.tree.column("titulo", width=320, anchor="w")
        self.tree.column("autores", width=240, anchor="w")
        self.tree.column("categoria", width=160, anchor="w")
        self.tree.column("ano", width=70, anchor="center")
        self.tree.column("disp", width=110, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=(12, 0))
        self.tree.bind("<Double-1>", lambda e: self._pegar_emprestado())

        rodape = ttk.Frame(self)
        rodape.pack(fill="x", pady=(10, 0))
        self.lbl_msg = ttk.Label(rodape, text="", style="Hint.TLabel")
        self.lbl_msg.pack(side="left")
        ttk.Button(rodape, text="Ver detalhes",
                    command=self._detalhes).pack(side="right", padx=(8, 0))
        ttk.Button(rodape, text="✓ Pegar emprestado",
                    style="Sucesso.TButton",
                    command=self._pegar_emprestado).pack(side="right")

    def _detalhes(self):
        sel = self.tree.selection()
        if not sel:
            return
        livro_id = int(self.tree.item(sel[0])["values"][0])
        from .ui_dialogos import DialogoDetalhesLivro
        DialogoDetalhesLivro(self.painel, livro_id)

    def _pegar_emprestado(self):
        sel = self.tree.selection()
        if not sel:
            self.lbl_msg.configure(text="Selecione um livro na lista.",
                                     foreground=tema.COR_AVISO)
            return
        livro_id = int(self.tree.item(sel[0])["values"][0])
        # Encontrar o primeiro exemplar disponível desse livro
        det = servicos.detalhes_livro(livro_id)
        if not det:
            self.lbl_msg.configure(text="Livro não encontrado.",
                                     foreground=tema.COR_ERRO)
            return
        codigo = next((ex["codigo_barras"] for ex in det["exemplares"]
                        if ex["status"] == "DISPONIVEL"), None)
        if not codigo:
            self.lbl_msg.configure(
                text=f"Nenhum exemplar disponível de '{det['titulo']}'.",
                foreground=tema.COR_AVISO)
            return
        # Confirmar
        if not messagebox.askyesno(
            "Confirmar empréstimo",
            f"Pegar emprestado: {det['titulo']}?",
            parent=self.painel):
            return
        try:
            res = servicos.realizar_emprestimo(
                codigo_exemplar=codigo,
                matricula_usuario=self.sessao.matricula,
                origem="BALCAO",
                operador_id=self.sessao.id,
            )
        except RegraNegocioError as e:
            self.lbl_msg.configure(text=f"⚠ {e}",
                                     foreground=tema.COR_ERRO)
            return
        self.lbl_msg.configure(
            text=(f"✓ '{res['titulo']}' emprestado. Devolva até "
                  f"{data_br(res['data_prevista'])}."),
            foreground=tema.COR_SUCESSO)
        self.atualizar()

    def atualizar(self):
        self.lbl_msg.configure(text="")
        for it in self.tree.get_children():
            self.tree.delete(it)
        for liv in servicos.listar_livros(self.ent.get(),
                                            self.var_disp.get()):
            self.tree.insert("", "end", values=(
                liv["id"], liv["titulo"], liv["autores"] or "—",
                liv["categoria"] or "—",
                liv["ano_publicacao"] or "—",
                f"{liv['disponiveis']}/{liv['total_exemplares']}",
            ))


# ---------------------------------------------------------------------------
# Meus empréstimos (aluno/professor)
# ---------------------------------------------------------------------------
class SecaoMeusEmprestimos(SecaoBase):
    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text="Meus empréstimos",
                  style="Titulo.TLabel").pack(anchor="w")

        self.lbl_status = ttk.Label(self, style="Hint.TLabel", text="")
        self.lbl_status.pack(anchor="w", pady=(0, 16))

        cols = ("codigo", "titulo", "emprestado", "previsto",
                "devolucao", "multa", "origem")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=18)
        for c, t, w in [("codigo", "Código", 160),
                        ("titulo", "Título", 280),
                        ("emprestado", "Empréstimo", 140),
                        ("previsto", "Previsto", 110),
                        ("devolucao", "Devolução", 140),
                        ("multa", "Multa", 90),
                        ("origem", "Origem", 130)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("atrasado", background="#FDECEA",
                                  foreground=tema.COR_ERRO)
        self.tree.tag_configure("devolvido", foreground="#888888")
        self.tree.pack(fill="both", expand=True)

    def atualizar(self):
        st = servicos.status_usuario(self.sessao.id)
        cor = tema.COR_SUCESSO if st.pode_pegar else tema.COR_AVISO
        self.lbl_status.configure(text=st.motivo, foreground=cor)
        for it in self.tree.get_children():
            self.tree.delete(it)
        from datetime import date as _date, datetime as _dt
        hoje = _date.today()
        for e in servicos.listar_emprestimos_usuario(self.sessao.id):
            tags = ()
            if e["data_devolucao"]:
                tags = ("devolvido",)
            else:
                try:
                    prev = _dt.strptime(e["data_prevista"], "%Y-%m-%d").date()
                    if prev < hoje:
                        tags = ("atrasado",)
                except ValueError:
                    pass
            self.tree.insert("", "end", tags=tags, values=(
                e["codigo_barras"],
                e["titulo"],
                data_hora_br(e["data_emprestimo"]),
                data_br(e["data_prevista"]),
                data_hora_br(e["data_devolucao"]) if e["data_devolucao"] else "—",
                reais(e["multa"]),
                e["origem"].title(),
            ))
