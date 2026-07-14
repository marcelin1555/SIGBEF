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

from . import barcode_util
from . import servicos
from . import ui_tema as tema
from .auth import Sessao
from .formato import data_br, data_hora_br, reais
from .servicos import RegraNegocioError
from .ui_dialogos import (
    DialogoDetalhesLivro,
    DialogoEditarUsuario,
    DialogoImportarCSV,
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
        self.title(f"SIGBEF - {sessao.nome} ({sessao.perfil.title()})")
        tema.aplicar_tema(self)
        tema.centralizar_janela(self, 1280, 780)
        self.minsize(1180, 700)

        self._secoes: dict[str, ttk.Frame] = {}
        self._botoes_lateral: dict[str, ttk.Button] = {}
        self._secao_atual: str | None = None
        self._construir()
        self._mostrar_secao(self._secao_inicial())

        # Atalhos globais: F5 recarrega a seção, Ctrl+F foca a busca
        self.bind("<F5>", lambda e: self._atualizar_secao_atual())
        self.bind("<Control-f>", lambda e: self._focar_busca())
        self.bind("<Control-F>", lambda e: self._focar_busca())

        # API REST opt-in: sobe junto com o painel quando está ativa
        from . import api
        if api.api_ativa():
            try:
                api.iniciar_em_thread()
            except OSError:
                pass  # porta ocupada: segue sem API; config mostra o estado

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
        self._secao_atual = chave
        # Destaca na sidebar onde o usuário está
        for k, btn in self._botoes_lateral.items():
            btn.state(["selected"] if k == chave else ["!selected"])
        self._secoes[chave].pack(fill="both", expand=True)
        self._secoes[chave].atualizar()

    def _atualizar_secao_atual(self):
        if self._secao_atual in self._secoes:
            self._secoes[self._secao_atual].atualizar()

    def _focar_busca(self):
        """Ctrl+F: foca o campo de busca (ou 1º campo) da seção visível."""
        secao = self._secoes.get(self._secao_atual)
        if secao is None:
            return
        for attr in ("ent_busca", "ent", "ent_emp_matr"):
            campo = getattr(secao, attr, None)
            if campo is not None:
                campo.focus_set()
                campo.select_range(0, "end")
                return

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
            valor = ttk.Label(card, text="", style="Display.TLabel")
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
        tema.aplicar_zebra(self.tree_top)


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
        ttk.Button(topo, text="Excluir do acervo",
                    command=self._excluir
                    ).pack(side="right", padx=(0, 8))
        ttk.Button(topo, text="Etiquetas em massa",
                    command=self._etiquetas_massa
                    ).pack(side="right", padx=(0, 8))
        ttk.Button(topo, text="Importar CSV",
                    command=self._importar_csv
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

    def _importar_csv(self):
        DialogoImportarCSV(self.painel, self.sessao, ao_salvar=self.atualizar)

    def _detalhes(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um livro",
                                  "Escolha um livro na lista.",
                                  parent=self.painel)
            return
        livro_id = int(self.tree.item(sel[0])["values"][0])
        DialogoDetalhesLivro(self.painel, livro_id)

    def _excluir(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um livro",
                                  "Escolha um livro na lista.",
                                  parent=self.painel)
            return
        valores = self.tree.item(sel[0])["values"]
        livro_id, titulo = int(valores[0]), valores[1]
        if not messagebox.askyesno(
                "Excluir do acervo",
                f'Excluir "{titulo}" do acervo?\n\n'
                "Os exemplares disponíveis serão baixados e o livro deixa "
                "de aparecer nas buscas. O histórico de empréstimos é "
                "preservado.",
                parent=self.painel):
            return
        try:
            servicos.excluir_livro(livro_id, self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self.painel)
        self.atualizar()

    def _etiquetas_massa(self):
        """Gera etiquetas de todos os exemplares da busca atual (ou do
        acervo inteiro) e abre no navegador para Ctrl+P / Salvar PDF."""
        termo = self.ent_busca.get()
        exemplares = servicos.listar_exemplares_para_etiquetas(termo)
        if not exemplares:
            messagebox.showinfo("Nada a imprimir",
                                  "Nenhum exemplar encontrado para a busca "
                                  "atual.",
                                  parent=self.painel)
            return
        titulos = len({ex["titulo"] for ex in exemplares})
        escopo = ("da busca atual" if termo.strip()
                  else "do acervo inteiro")
        if not messagebox.askyesno(
                "Etiquetas em massa",
                f"Gerar etiquetas de {len(exemplares)} exemplar(es) de "
                f"{titulos} livro(s) {escopo}?\n\n"
                "A página abre no navegador para imprimir ou salvar em PDF.",
                parent=self.painel):
            return
        import tempfile
        import webbrowser
        doc = barcode_util.etiquetas_lote_html(
            exemplares, "acervo" if not termo.strip() else f'busca "{termo}"')
        destino = Path(tempfile.gettempdir()) / "sigbef_etiquetas_lote.html"
        destino.write_text(doc, encoding="utf-8")
        webbrowser.open(destino.as_uri())

    def atualizar(self):
        for it in self.tree.get_children():
            self.tree.delete(it)
        for liv in servicos.listar_livros(self.ent_busca.get(),
                                            self.var_disponiveis.get()):
            self.tree.insert("", "end", values=(
                liv["id"], liv["titulo"], liv["autores"] or "",
                liv["categoria"] or "", liv["ano_publicacao"] or "",
                liv["total_exemplares"] or 0, liv["disponiveis"] or 0,
            ))
        tema.aplicar_zebra(self.tree)


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
        ttk.Button(topo, text="Excluir",
                    command=self._excluir
                    ).pack(side="right")
        ttk.Button(topo, text="Imprimir cartão",
                    command=self._imprimir_cartao
                    ).pack(side="right", padx=8)
        ttk.Button(topo, text="Editar",
                    command=self._editar
                    ).pack(side="right")

        filtros = ttk.Frame(self, padding=(0, 12))
        filtros.pack(fill="x")
        ttk.Label(filtros, text="Buscar:").pack(side="left")
        self.ent_busca = ttk.Entry(filtros, width=40)
        self.ent_busca.pack(side="left", padx=8)
        self.ent_busca.bind("<Return>", lambda e: self.atualizar())
        ttk.Button(filtros, text="Pesquisar",
                    command=self.atualizar).pack(side="left")

        cols = ("id", "nome", "matricula", "turma", "perfil", "email",
                "cartao", "ativo")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=18)
        for c, t, w in [("id", "ID", 50), ("nome", "Nome", 220),
                        ("matricula", "Matrícula", 100),
                        ("turma", "Série / Turma", 180),
                        ("perfil", "Perfil", 120),
                        ("email", "E-mail", 200),
                        ("cartao", "Cartão", 180),
                        ("ativo", "Ativo", 60)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(8, 0))
        self.tree.bind("<Double-1>", lambda e: self._editar())

    def _novo_usuario(self):
        DialogoUsuario(self.painel, self.sessao, ao_salvar=self.atualizar)

    def _editar(self):
        selecao = self._selecionado()
        if not selecao:
            return
        usuario_id, _ = selecao
        try:
            DialogoEditarUsuario(self.painel, self.sessao, usuario_id,
                                 ao_salvar=self.atualizar)
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self.painel)

    def _toggle_status(self):
        sel = self.tree.selection()
        if not sel:
            return
        valores = self.tree.item(sel[0])["values"]
        usuario_id = int(valores[0])
        ativo_atual = str(valores[-1]).lower() == "sim"
        try:
            servicos.alternar_status_usuario(usuario_id, not ativo_atual,
                                             executor_id=self.sessao.id)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self.painel)
        self.atualizar()

    def _selecionado(self) -> tuple[int, str] | None:
        """Retorna (id, nome) do usuário selecionado, ou None."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um usuário",
                                  "Escolha um usuário na lista.",
                                  parent=self.painel)
            return None
        valores = self.tree.item(sel[0])["values"]
        return int(valores[0]), str(valores[1])

    def _excluir(self):
        selecao = self._selecionado()
        if not selecao:
            return
        usuario_id, nome = selecao
        if not messagebox.askyesno(
                "Excluir usuário",
                f'Excluir definitivamente "{nome}"?\n\n'
                "Só é possível excluir usuários sem histórico de "
                "empréstimos. Para bloquear o acesso preservando o "
                "histórico, use 'Ativar/Desativar'.",
                parent=self.painel):
            return
        try:
            servicos.excluir_usuario(usuario_id, self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self.painel)
        self.atualizar()

    def _imprimir_cartao(self):
        """Gera o HTML do cartão do usuário e abre no navegador para Ctrl+P."""
        selecao = self._selecionado()
        if not selecao:
            return
        usuario_id, _ = selecao
        try:
            usuario = servicos.obter_usuario(usuario_id)
            if not usuario["codigo_barras"]:
                if not messagebox.askyesno(
                        "Usuário sem cartão",
                        f"{usuario['nome']} ainda não tem código de barras "
                        "de cartão.\nGerar um agora?",
                        parent=self.painel):
                    return
                usuario["codigo_barras"] = servicos.gerar_cartao_usuario(
                    usuario_id, self.sessao.id)
                self.atualizar()
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self.painel)
            return
        import tempfile
        import webbrowser
        doc = barcode_util.cartoes_html([usuario])
        destino = Path(tempfile.gettempdir()) / "sigbef_cartao.html"
        destino.write_text(doc, encoding="utf-8")
        webbrowser.open(destino.as_uri())

    def atualizar(self):
        for it in self.tree.get_children():
            self.tree.delete(it)
        for u in servicos.listar_usuarios(self.ent_busca.get()):
            self.tree.insert("", "end", values=(
                u["id"], u["nome"], u["matricula"],
                u.get("turma") or "",
                u["perfil"],
                u.get("email") or "",
                u.get("codigo_barras") or "",
                "Sim" if u["ativo"] else "Não",
            ))
        tema.aplicar_zebra(self.tree)


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

        self.lbl_msg_dev = ttk.Label(dev_card, text="", style="Card.TLabel")
        self.lbl_msg_dev.grid(row=2, column=0, columnspan=4,
                               sticky="w", pady=(10, 0))

        self.ent_emp_cod.bind("<Return>", lambda e: self._emprestar())
        self.ent_emp_matr.bind("<Return>", lambda e: self.ent_emp_cod.focus_set())
        self.ent_dev_cod.bind("<Return>", lambda e: self._devolver())

        # Tabela de empréstimos abertos
        ttk.Label(self, text="Empréstimos em aberto",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(20, 6))

        cols = ("id", "usuario", "matricula", "turma", "titulo", "codigo",
                "emprestado", "previsto", "atrasado")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=14)
        for c, t, w in [("id", "ID", 50), ("usuario", "Usuário", 160),
                        ("matricula", "Matrícula", 90),
                        ("turma", "Série / Turma", 170),
                        ("titulo", "Título", 240),
                        ("codigo", "Código", 150),
                        ("emprestado", "Empréstimo", 120),
                        ("previsto", "Previsto", 100),
                        ("atrasado", "Atraso?", 70)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("atrasado", background="#FDECEA",
                                  foreground=tema.COR_ERRO)
        self.tree.pack(fill="both", expand=True)
        # Devolução com um clique: duplo clique na linha devolve o livro
        self.tree.bind("<Double-1>", lambda e: self._devolver_selecionado())

        op = ttk.Frame(self)
        op.pack(fill="x", pady=(8, 0))
        ttk.Button(op, text="✓ Devolver selecionado",
                    style="Sucesso.TButton",
                    command=self._devolver_selecionado
                    ).pack(side="left", padx=(0, 8))
        ttk.Button(op, text="Renovar selecionado",
                    command=self._renovar).pack(side="left", padx=(0, 8))
        ttk.Button(op, text="Quitar multa",
                    command=self._quitar).pack(side="left")
        ttk.Label(op, text="Dica: duplo clique numa linha devolve o livro.",
                  style="Hint.TLabel").pack(side="left", padx=(16, 0))

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
        # Pronto pro próximo atendimento sem tocar no mouse
        self.ent_emp_matr.focus_set()
        self.atualizar()

    def _devolver(self):
        self._executar_devolucao(self.ent_dev_cod.get())

    def _devolver_selecionado(self):
        """Devolução com um clique a partir da tabela de empréstimos."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(
                "Selecione um empréstimo",
                "Clique numa linha da tabela antes de devolver.",
                parent=self.painel)
            return
        v = self.tree.item(sel[0])["values"]
        titulo, usuario, codigo = v[4], v[1], str(v[5])
        if not messagebox.askyesno(
                "Confirmar devolução",
                f"Registrar a devolução de '{titulo}'\n"
                f"emprestado a {usuario}?",
                parent=self.painel):
            return
        self._executar_devolucao(codigo)

    def _executar_devolucao(self, codigo: str):
        try:
            res = servicos.realizar_devolucao(
                codigo_exemplar=codigo,
                operador_id=self.sessao.id,
            )
        except RegraNegocioError as e:
            self.lbl_msg_dev.configure(text=f"⚠ {e}",
                                        foreground=tema.COR_ERRO)
            self.ent_dev_cod.select_range(0, "end")
            self.ent_dev_cod.focus_set()
            return
        if res["multa"] > 0:
            # Multa exige atenção do operador: mantém o aviso em destaque
            messagebox.showwarning(
                "Devolução com multa",
                f"Devolução registrada: {res['titulo']}\n\n"
                f"Multa gerada: {reais(res['multa'])} "
                f"(atraso de {res['dias_atraso']} dia(s)).\n"
                "Registre o recebimento ou use 'Quitar multa' na tabela.",
                parent=self.painel)
            self.lbl_msg_dev.configure(
                text=(f"⚠ '{res['titulo']}' devolvido com multa de "
                      f"{reais(res['multa'])}."),
                foreground=tema.COR_AVISO)
        else:
            # Sem multa: mensagem inline, sem modal — permite devolver
            # uma pilha de livros só escaneando (scan, Enter, scan...)
            self.lbl_msg_dev.configure(
                text=f"✓ '{res['titulo']}' devolvido em dia, sem multa.",
                foreground=tema.COR_SUCESSO)
        if res.get("reservado_para"):
            # Livro com fila: o operador precisa separar o exemplar
            messagebox.showinfo(
                "Livro com fila de espera",
                f"'{res['titulo']}' está reservado para "
                f"{res['reservado_para']}.\n\nSepare o exemplar: retirada "
                f"até {data_br(res['reserva_ate'])}.",
                parent=self.painel)
            self.lbl_msg_dev.configure(
                text=(f"✓ '{res['titulo']}' devolvido. Separado para "
                      f"{res['reservado_para']} até "
                      f"{data_br(res['reserva_ate'])}."),
                foreground=tema.COR_AVISO)
        self.ent_dev_cod.delete(0, "end")
        self.ent_dev_cod.focus_set()
        self.atualizar()

    def _renovar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(
                "Selecione um empréstimo",
                "Clique numa linha da tabela antes de renovar.",
                parent=self.painel)
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
            messagebox.showinfo(
                "Selecione um empréstimo",
                "Clique numa linha da tabela antes de quitar a multa.",
                parent=self.painel)
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
                e["id"], e["usuario"], e["matricula"],
                e.get("turma") or "",
                e["titulo"],
                e["codigo_barras"], data_hora_br(e["data_emprestimo"]),
                data_br(e["data_prevista"]), "SIM" if atrasado else "",
            ))
        tema.aplicar_zebra(self.tree)


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
                u.get("email") or "",
            ))
        tema.aplicar_zebra(self.tree)

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
_CARACTERES_FORMULA_CSV = ("=", "+", "-", "@", "\t", "\r")


def _neutralizar_celula_csv(valor):
    """Evita injeção de fórmula em CSV (CWE-1236): células que começam
    com =, +, -, @ (ou tab/CR) são interpretadas como fórmula pelo
    Excel/LibreOffice ao abrir o arquivo. Como título de livro, nome de
    usuário etc. vêm de cadastro livre, um valor tipo
    '=HYPERLINK(...)' salvo hoje viraria fórmula executável no
    relatório de amanhã. Prefixar com apóstrofo faz a planilha tratar
    como texto literal, sem mudar o que aparece na célula."""
    texto = str(valor)
    if texto and texto[0] in _CARACTERES_FORMULA_CSV:
        return "'" + texto
    return valor


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
            w.writerows([[_neutralizar_celula_csv(v) for v in linha]
                        for linha in linhas])

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

        # ---- Scroll container (conteudo passa do tamanho da viewport) ----
        canvas = tk.Canvas(self, bg=tema.COR_FUNDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        body = ttk.Frame(canvas)
        inner_window = canvas.create_window((0, 0), window=body,
                                            anchor="nw")

        def _on_canvas_configure(e):
            canvas.itemconfig(inner_window, width=e.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_inner_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        body.bind("<Configure>", _on_inner_configure)

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<Enter>",
                    lambda e: canvas.bind_all("<MouseWheel>",
                                              _on_mousewheel))
        canvas.bind("<Leave>",
                    lambda e: canvas.unbind_all("<MouseWheel>"))

        ttk.Label(body, text="Configurações do sistema",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(body, text=("Ajuste prazos, limites e valores de multa. As "
                               "alterações entram em vigor imediatamente."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 16))

        from .database import get_config

        form = ttk.Frame(body, style="Card.TFrame", padding=20)
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

        ttk.Button(body, text="Salvar configurações",
                    style="Primario.TButton",
                    command=self._salvar).pack(anchor="e", pady=(16, 0))

        # ---------------- Ferramentas adicionais ----------------
        ttk.Label(body, text="Ferramentas",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(24, 8))

        ferramentas = ttk.Frame(body, style="Card.TFrame", padding=16)
        ferramentas.pack(fill="x")
        ferramentas.columnconfigure(1, weight=1)

        # Backup
        ttk.Label(ferramentas, text="Backup do banco de dados",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 10)
                  ).grid(row=0, column=0, sticky="w", pady=(0, 2))
        ttk.Label(ferramentas,
                  text=("Cria uma cópia do banco em um local seguro. "
                        "Faça backup periodicamente."),
                  style="CardHint.TLabel"
                  ).grid(row=1, column=0, sticky="w")
        ttk.Button(ferramentas, text="Fazer backup agora",
                    command=self._backup
                    ).grid(row=0, column=1, rowspan=2, sticky="e", padx=12)

        # Dados de demo
        ttk.Label(ferramentas, text="Dados de demonstração",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 10)
                  ).grid(row=2, column=0, sticky="w", pady=(14, 2))
        ttk.Label(ferramentas,
                  text=("Adiciona 10 livros e 4 usuários de exemplo. "
                        "Útil para testar o sistema antes do uso real."),
                  style="CardHint.TLabel", wraplength=600
                  ).grid(row=3, column=0, sticky="w")
        ttk.Button(ferramentas, text="Carregar dados de demonstração",
                    command=self._carregar_demo
                    ).grid(row=2, column=1, rowspan=2, sticky="e",
                            padx=12, pady=(14, 0))

        # Sobre
        ttk.Label(ferramentas, text="Sobre o sistema",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 10)
                  ).grid(row=4, column=0, sticky="w", pady=(14, 2))
        ttk.Label(ferramentas,
                  text="Versão, licença, autor e informações de contato.",
                  style="CardHint.TLabel"
                  ).grid(row=5, column=0, sticky="w")
        ttk.Button(ferramentas, text="Mostrar sobre...",
                    command=self._sobre
                    ).grid(row=4, column=1, rowspan=2, sticky="e",
                            padx=12, pady=(14, 0))

        # ---------------- Integrações ----------------
        ttk.Label(body, text="Integrações (online)",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(24, 8))
        integ = ttk.Frame(body, style="Card.TFrame", padding=16)
        integ.pack(fill="x")
        self.var_isbn = tk.BooleanVar(value=servicos.isbn_lookup_ativo())
        ttk.Checkbutton(
            integ,
            text="Buscar dados do livro por ISBN (Open Library / Google Books)",
            variable=self.var_isbn,
            command=self._toggle_isbn).pack(anchor="w")
        ttk.Label(
            integ,
            text=("Desligado por padrão. Quando ligado, o cadastro de livro "
                  "ganha um botão que busca título, autor, editora e ano pela "
                  "internet. Requer conexão; o resto do sistema continua "
                  "funcionando offline."),
            style="CardHint.TLabel", wraplength=700
            ).pack(anchor="w", pady=(4, 0))

        # ---- Avisos de vencimento por e-mail ----
        from . import notificacoes
        from .database import get_config as _gc
        tk.Frame(integ, height=1, bg=tema.COR_BORDA).pack(fill="x", pady=12)
        self.var_email = tk.BooleanVar(value=notificacoes.avisos_ativos())
        ttk.Checkbutton(
            integ,
            text="Avisar por e-mail (vencimento próximo e reserva pronta)",
            variable=self.var_email,
            command=lambda: notificacoes.definir_avisos(self.var_email.get())
            ).pack(anchor="w")
        ttk.Label(
            integ,
            text=("Avisa usuários com e-mail cadastrado quando um empréstimo "
                  "está perto do prazo ou quando um livro reservado por eles "
                  "fica disponível. Um aviso por situação. Use o e-mail da "
                  "biblioteca (ex.: Gmail com senha de app)."),
            style="CardHint.TLabel", wraplength=700
            ).pack(anchor="w", pady=(4, 8))

        smtp_form = ttk.Frame(integ, style="Card.TFrame")
        smtp_form.pack(fill="x")
        smtp_form.columnconfigure(1, weight=1)
        self._smtp_entries: dict[str, ttk.Entry] = {}
        for i, (chave, rotulo, largura) in enumerate([
            ("SMTP_HOST", "Servidor SMTP (ex.: smtp.gmail.com)", 34),
            ("SMTP_PORTA", "Porta (587 na maioria)", 8),
            ("SMTP_USUARIO", "Usuário / e-mail de envio", 34),
            ("SMTP_SENHA", "Senha (ou senha de app)", 24),
            ("SMTP_REMETENTE", "Remetente exibido (opcional)", 34),
            ("EMAIL_DIAS_ANTES", "Avisar quantos dias antes", 8),
        ]):
            ttk.Label(smtp_form, text=rotulo, style="Card.TLabel"
                      ).grid(row=i, column=0, sticky="w", pady=3)
            ent = ttk.Entry(smtp_form, width=largura)
            if chave == "SMTP_SENHA":
                ent.configure(show="•")
            ent.insert(0, _gc(chave) or "")
            ent.grid(row=i, column=1, sticky="w", padx=12, pady=3)
            self._smtp_entries[chave] = ent

        botoes_email = ttk.Frame(integ, style="Card.TFrame")
        botoes_email.pack(fill="x", pady=(10, 0))
        self.lbl_email_msg = ttk.Label(botoes_email, text="",
                                        style="CardHint.TLabel")
        self.lbl_email_msg.pack(side="left")
        ttk.Button(botoes_email, text="Enviar avisos agora",
                    style="Primario.TButton",
                    command=self._enviar_avisos_email
                    ).pack(side="right")
        ttk.Button(botoes_email, text="Salvar dados de e-mail",
                    command=self._salvar_email
                    ).pack(side="right", padx=(0, 8))

        # ---- API REST somente leitura ----
        from . import api
        tk.Frame(integ, height=1, bg=tema.COR_BORDA).pack(fill="x", pady=12)
        self.var_api = tk.BooleanVar(value=api.api_ativa())
        ttk.Checkbutton(
            integ,
            text="API REST somente leitura (integração com outros sistemas)",
            variable=self.var_api,
            command=self._toggle_api).pack(anchor="w")
        ttk.Label(
            integ,
            text=("Permite que sistemas da escola consultem acervo e "
                  "empréstimos pela rede local, protegido por token. "
                  "Nenhuma rota altera dados. Guia completo em docs/API.md."),
            style="CardHint.TLabel", wraplength=700
            ).pack(anchor="w", pady=(4, 8))

        api_form = ttk.Frame(integ, style="Card.TFrame")
        api_form.pack(fill="x")
        ttk.Label(api_form, text="Porta:", style="Card.TLabel"
                  ).grid(row=0, column=0, sticky="w", pady=3)
        self.ent_api_porta = ttk.Entry(api_form, width=8)
        self.ent_api_porta.insert(0, str(api.porta_configurada()))
        self.ent_api_porta.grid(row=0, column=1, sticky="w", padx=12)
        ttk.Label(api_form, text="Token completo:", style="Card.TLabel"
                  ).grid(row=1, column=0, sticky="w", pady=3)
        self.ent_api_token = ttk.Entry(api_form, width=50)
        self.ent_api_token.grid(row=1, column=1, sticky="w", padx=12)
        ttk.Label(api_form,
                  text="acervo + dados de leitores e circulação",
                  style="CardHint.TLabel"
                  ).grid(row=2, column=1, sticky="w", padx=12)
        ttk.Label(api_form, text="Token de consulta:", style="Card.TLabel"
                  ).grid(row=3, column=0, sticky="w", pady=(8, 3))
        self.ent_api_token_consulta = ttk.Entry(api_form, width=50)
        self.ent_api_token_consulta.grid(row=3, column=1, sticky="w", padx=12)
        ttk.Label(api_form,
                  text="só o acervo público (sem dados de alunos)",
                  style="CardHint.TLabel"
                  ).grid(row=4, column=1, sticky="w", padx=12)
        self._refrescar_token_api()

        botoes_api = ttk.Frame(integ, style="Card.TFrame")
        botoes_api.pack(fill="x", pady=(10, 0))
        self.lbl_api_msg = ttk.Label(botoes_api, text="",
                                      style="CardHint.TLabel")
        self.lbl_api_msg.pack(side="left")
        self._refrescar_status_api()
        ttk.Button(botoes_api, text="Novo token completo",
                    command=lambda: self._gerar_token_api("completo")
                    ).pack(side="right")
        ttk.Button(botoes_api, text="Novo token de consulta",
                    command=lambda: self._gerar_token_api("consulta")
                    ).pack(side="right", padx=(0, 8))
        ttk.Button(botoes_api, text="Copiar completo",
                    command=lambda: self._copiar_token_api("completo")
                    ).pack(side="right", padx=(0, 8))

        # ---------------- Aparencia ----------------
        ttk.Label(body, text="Aparência",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(24, 8))
        ttk.Label(body,
                  text=("Personalize as cores da interface. As cores de "
                        "sucesso, erro e aviso seguem convenção universal "
                        "de UI e não são editáveis."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 8))

        aparencia = ttk.Frame(body, style="Card.TFrame", padding=16)
        aparencia.pack(fill="x")

        # Predefinicoes
        ttk.Label(aparencia, text="Predefinições",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 10)
                  ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        presets_frame = ttk.Frame(aparencia, style="Card.TFrame")
        presets_frame.grid(row=0, column=1, columnspan=3, sticky="w",
                           padx=12, pady=(0, 8))
        for chave_p, preset in tema.PRESETS.items():
            ttk.Button(presets_frame, text=preset["nome"],
                       command=lambda c=chave_p: self._aplicar_preset_aparencia(c)
                       ).pack(side="left", padx=(0, 6))

        # 4 cores editaveis
        self._cor_entries = {}
        self._cor_swatches = {}
        from .database import get_config
        cores_edicao = [
            ("primaria", "Cor primária", "tema.cor_primaria", tema.COR_PRIMARIA),
            ("secundaria", "Cor secundária", "tema.cor_secundaria", tema.COR_SECUNDARIA),
            ("destaque", "Cor de destaque", "tema.cor_destaque", tema.COR_DESTAQUE),
            ("fundo", "Cor de fundo", "tema.cor_fundo", tema.COR_FUNDO),
        ]
        for i, (chave_c, rotulo, db_chave, padrao) in enumerate(cores_edicao):
            ttk.Label(aparencia, text=rotulo, style="Card.TLabel"
                      ).grid(row=i + 1, column=0, sticky="w", pady=6)
            valor = get_config(db_chave, padrao) or padrao
            swatch = tk.Frame(aparencia, bg=valor, width=32, height=24,
                              highlightthickness=1,
                              highlightbackground=tema.COR_BORDA)
            swatch.grid(row=i + 1, column=1, padx=(8, 8))
            swatch.grid_propagate(False)
            ent = ttk.Entry(aparencia, width=10)
            ent.insert(0, valor)
            ent.grid(row=i + 1, column=2, sticky="w", padx=(0, 8))
            ttk.Button(aparencia, text="Escolher",
                       command=lambda c=chave_c: self._escolher_cor(c)
                       ).grid(row=i + 1, column=3, sticky="w")
            self._cor_entries[chave_c] = ent
            self._cor_swatches[chave_c] = swatch

        # Botoes de acao
        botoes_aparencia = ttk.Frame(self)
        botoes_aparencia.pack(fill="x", pady=(12, 0))
        ttk.Button(botoes_aparencia, text="Salvar aparência",
                   style="Primario.TButton",
                   command=self._salvar_aparencia
                   ).pack(side="right")
        ttk.Button(botoes_aparencia, text="Restaurar padrão",
                   command=self._restaurar_aparencia_padrao
                   ).pack(side="right", padx=(0, 8))
        ttk.Label(body,
                  text="As alterações de cor têm efeito após reiniciar o sistema.",
                  style="Hint.TLabel").pack(anchor="w", pady=(8, 0))

    def _salvar(self):
        from .database import set_config
        for chave, ent in self._entries.items():
            set_config(chave, ent.get().strip())
        messagebox.showinfo("Configurações", "Salvo com sucesso.",
                             parent=self.painel)

    def _backup(self):
        from datetime import datetime as _dt
        import shutil
        from .database import DB_PATH
        sugestao = f"sigbef_backup_{_dt.now().strftime('%Y%m%d_%H%M')}.db"
        destino = filedialog.asksaveasfilename(
            parent=self.painel,
            title="Salvar backup do banco de dados",
            initialfile=sugestao,
            defaultextension=".db",
            filetypes=[("Banco SQLite", "*.db"), ("Todos", "*.*")],
        )
        if not destino:
            return
        try:
            shutil.copy2(DB_PATH, destino)
        except Exception as e:
            messagebox.showerror("Erro no backup",
                                   f"Não foi possível copiar o banco:\n{e}",
                                   parent=self.painel)
            return
        messagebox.showinfo("Backup concluído",
                              f"Arquivo gerado em:\n{destino}",
                              parent=self.painel)

    def _carregar_demo(self):
        from . import seed
        if not seed.banco_vazio():
            # Banco já tem dados — confirmar
            if not messagebox.askyesno(
                "Carregar dados de demonstração",
                ("O banco já contém dados.\n\n"
                 "Os dados de demonstração serão ADICIONADOS aos existentes. "
                 "Deseja continuar?"),
                parent=self.painel):
                return
        try:
            seed.popular_dados_demo()
        except Exception as e:
            messagebox.showerror("Erro",
                                   f"Falha ao carregar demo:\n{e}",
                                   parent=self.painel)
            return
        messagebox.showinfo(
            "Dados carregados",
            "Foram adicionados livros e usuários de demonstração.\n\n"
            "As credenciais dos usuários de demo são:\n"
            "  laiane / laiane123\n"
            "  jaqueline / jaqueline123\n"
            "  macilene / macilene123\n"
            "  2024001 / lucas123\n"
            "  2024002 / beatriz123\n\n"
            "TROQUE essas senhas antes de usar em produção.",
            parent=self.painel)

    def _sobre(self):
        from .ui_dialogos import DialogoSobre
        DialogoSobre(self.painel)

    def _toggle_isbn(self):
        servicos.definir_isbn_lookup(self.var_isbn.get())

    # ---------------- Avisos por e-mail ----------------
    def _salvar_email(self):
        from .database import set_config
        for chave, ent in self._smtp_entries.items():
            set_config(chave, ent.get().strip())
        self.lbl_email_msg.configure(text="✓ Dados de e-mail salvos.",
                                      foreground=tema.COR_SUCESSO)

    def _enviar_avisos_email(self):
        from . import notificacoes
        self._salvar_email()   # garante que o que está na tela vale
        self.lbl_email_msg.configure(text="Enviando...",
                                      foreground=tema.COR_TEXTO)
        self.painel.update_idletasks()
        try:
            res = notificacoes.enviar_avisos(executor_id=self.sessao.id)
        except RegraNegocioError as e:
            self.lbl_email_msg.configure(text=f"⚠ {e}",
                                          foreground=tema.COR_ERRO)
            return
        if res["enviados"]:
            texto = f"✓ {res['enviados']} aviso(s) enviado(s)."
        else:
            texto = "Nenhum aviso pendente no momento."
        self.lbl_email_msg.configure(text=texto,
                                      foreground=tema.COR_SUCESSO)

    # ---------------- API REST ----------------
    def _refrescar_token_api(self):
        from . import api
        for ent, token in (
                (self.ent_api_token, api.obter_token()),
                (self.ent_api_token_consulta, api.obter_token_consulta())):
            ent.configure(state="normal")
            ent.delete(0, "end")
            ent.insert(0, token or "(gerado ao ativar)")
            ent.configure(state="readonly")

    def _refrescar_status_api(self):
        from . import api
        if api.esta_no_ar():
            porta = api.porta_configurada()
            self.lbl_api_msg.configure(
                text=f"✓ API no ar na porta {porta} (somente leitura).",
                foreground=tema.COR_SUCESSO)
        elif api.api_ativa():
            self.lbl_api_msg.configure(
                text="API ativa; sobe junto com o aplicativo.",
                foreground=tema.COR_TEXTO)
        else:
            self.lbl_api_msg.configure(text="API desligada.",
                                        foreground=tema.COR_TEXTO)

    def _toggle_api(self):
        from . import api
        from .database import set_config
        ligar = self.var_api.get()
        porta_txt = self.ent_api_porta.get().strip()
        if porta_txt.isdigit():
            set_config("API_PORTA", porta_txt)
        api.definir_api(ligar, executor_id=self.sessao.id)
        if ligar:
            try:
                api.iniciar_em_thread()
            except OSError as e:
                self.lbl_api_msg.configure(
                    text=f"⚠ Não consegui abrir a porta: {e}",
                    foreground=tema.COR_ERRO)
                return
        else:
            api.parar()
        self._refrescar_token_api()
        self._refrescar_status_api()

    def _copiar_token_api(self, nivel="completo"):
        from . import api
        token = (api.obter_token() if nivel == "completo"
                 else api.obter_token_consulta())
        if not token:
            self.lbl_api_msg.configure(text="Ative a API primeiro.",
                                        foreground=tema.COR_AVISO)
            return
        self.painel.clipboard_clear()
        self.painel.clipboard_append(token)
        self.lbl_api_msg.configure(text=f"✓ Token {nivel} copiado.",
                                    foreground=tema.COR_SUCESSO)

    def _gerar_token_api(self, nivel="completo"):
        from . import api
        if not messagebox.askyesno(
                "Gerar novo token",
                f"O token {nivel} atual deixa de funcionar e os sistemas "
                "que o usam precisarão do novo. Continuar?",
                parent=self.painel):
            return
        if nivel == "completo":
            api.gerar_novo_token(executor_id=self.sessao.id)
        else:
            api.gerar_novo_token_consulta(executor_id=self.sessao.id)
        self._refrescar_token_api()
        self.lbl_api_msg.configure(text=f"✓ Novo token {nivel} gerado.",
                                    foreground=tema.COR_SUCESSO)

    # ---------------- Aparencia ----------------
    def _aplicar_preset_aparencia(self, chave_preset):
        preset = tema.PRESETS.get(chave_preset)
        if not preset:
            return
        mapa = {
            "primaria": preset["primaria"],
            "secundaria": preset["secundaria"],
            "destaque": preset["destaque"],
            "fundo": preset["fundo"],
        }
        for chave, valor in mapa.items():
            ent = self._cor_entries[chave]
            ent.delete(0, "end")
            ent.insert(0, valor)
            self._cor_swatches[chave].configure(bg=valor)

    def _escolher_cor(self, chave):
        from tkinter import colorchooser
        atual = self._cor_entries[chave].get().strip()
        resultado = colorchooser.askcolor(color=atual or None,
                                          parent=self.painel,
                                          title="Escolher cor")
        if resultado and resultado[1]:
            cor = resultado[1].upper()
            self._cor_entries[chave].delete(0, "end")
            self._cor_entries[chave].insert(0, cor)
            self._cor_swatches[chave].configure(bg=cor)

    def _salvar_aparencia(self):
        valores = {}
        for chave, ent in self._cor_entries.items():
            v = ent.get().strip().upper()
            if not v.startswith("#") or len(v) != 7:
                messagebox.showwarning(
                    "Cor invalida",
                    f"O valor '{v}' nao e uma cor hex valida "
                    "(esperado #RRGGBB).",
                    parent=self.painel)
                return
            valores[chave] = v
        tema.salvar_cores(valores["primaria"], valores["secundaria"],
                          valores["destaque"], valores["fundo"])
        messagebox.showinfo(
            "Aparência salva",
            "As novas cores foram salvas.\n\n"
            "Reinicie o SIGBEF para ver as mudancas.",
            parent=self.painel)

    def _restaurar_aparencia_padrao(self):
        if not messagebox.askyesno(
            "Restaurar padrao",
            "Voltar ao tema azul institucional padrao?\n\n"
            "As cores personalizadas serao substituidas.",
            parent=self.painel):
            return
        tema.restaurar_padrao()
        self._aplicar_preset_aparencia("padrao")
        messagebox.showinfo(
            "Padrao restaurado",
            "Tema padrao restaurado.\n\nReinicie o SIGBEF para aplicar.",
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
        ttk.Button(rodape, text="Reservar",
                    command=self._reservar).pack(side="right", padx=(0, 8))

    def _reservar(self):
        """Entra na fila de espera de um livro sem exemplar disponível."""
        sel = self.tree.selection()
        if not sel:
            self.lbl_msg.configure(text="Selecione um livro na lista.",
                                     foreground=tema.COR_AVISO)
            return
        valores = self.tree.item(sel[0])["values"]
        livro_id = int(valores[0])
        if not messagebox.askyesno(
                "Reservar",
                f"Entrar na fila de espera de '{valores[1]}'?\n\n"
                "Quando um exemplar for devolvido, ele fica separado "
                "pra você retirar na biblioteca.",
                parent=self.painel):
            return
        from . import reservas
        try:
            r = reservas.criar_reserva(livro_id, self.sessao.id)
        except RegraNegocioError as e:
            self.lbl_msg.configure(text=f"⚠ {e}",
                                     foreground=tema.COR_ERRO)
            return
        self.lbl_msg.configure(
            text=(f"✓ Reserva feita: '{r['titulo']}'. Você é o "
                  f"{r['posicao']}º da fila. Acompanhe em 'Meus empréstimos'."),
            foreground=tema.COR_SUCESSO)

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
                liv["id"], liv["titulo"], liv["autores"] or "",
                liv["categoria"] or "",
                liv["ano_publicacao"] or "",
                f"{liv['disponiveis']}/{liv['total_exemplares']}",
            ))
        tema.aplicar_zebra(self.tree)


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

        # ------ Minhas reservas ------
        ttk.Label(self, text="Minhas reservas",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(14, 4))
        self.tree_res = ttk.Treeview(
            self, columns=("rid", "rtitulo", "situacao"),
            show="headings", height=4)
        self.tree_res.heading("rid", text="ID")
        self.tree_res.heading("rtitulo", text="Título")
        self.tree_res.heading("situacao", text="Situação")
        self.tree_res.column("rid", width=0, stretch=False)
        self.tree_res.column("rtitulo", width=300, anchor="w")
        self.tree_res.column("situacao", width=380, anchor="w")
        self.tree_res.tag_configure("pronta", background="#FFF6E5")
        self.tree_res.pack(fill="x")
        bot_res = ttk.Frame(self)
        bot_res.pack(fill="x", pady=(6, 0))
        ttk.Button(bot_res, text="Cancelar reserva selecionada",
                    command=self._cancelar_reserva).pack(side="right")

    def _cancelar_reserva(self):
        from . import reservas
        sel = self.tree_res.selection()
        if not sel:
            messagebox.showinfo("Selecione uma reserva",
                                  "Clique numa reserva da lista primeiro.",
                                  parent=self.painel)
            return
        valores = self.tree_res.item(sel[0])["values"]
        if not messagebox.askyesno(
                "Cancelar reserva",
                f"Cancelar a reserva de '{valores[1]}'?",
                parent=self.painel):
            return
        try:
            reservas.cancelar_reserva(int(valores[0]),
                                      usuario_id=self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self.painel)
        self.atualizar()

    def atualizar(self):
        from . import reservas
        for it in self.tree_res.get_children():
            self.tree_res.delete(it)
        for r in reservas.listar_reservas_usuario(self.sessao.id):
            if r["exemplar_id"]:
                situacao = ("Separado pra você! Retire na biblioteca até "
                            f"{data_br(r['disponivel_ate'])}.")
                tags = ("pronta",)
            else:
                situacao = f"{r['posicao']}º da fila de espera"
                tags = ()
            self.tree_res.insert("", "end", tags=tags,
                                  values=(r["id"], r["titulo"], situacao))

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
                data_hora_br(e["data_devolucao"]) if e["data_devolucao"] else "",
                reais(e["multa"]),
                e["origem"].title(),
            ))
        tema.aplicar_zebra(self.tree)
