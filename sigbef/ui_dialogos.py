"""
SIGBEF — Diálogos modais reutilizáveis (cadastro de livro, usuário,
visualização de exemplares e código de barras).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from . import barcode_util
from . import servicos
from . import ui_tema as tema
from .auth import Sessao
from .formato import data_br, reais, status_legivel
from .servicos import RegraNegocioError


# ---------------------------------------------------------------------------
# Diálogo: selecionar exemplar disponível para empréstimo
# ---------------------------------------------------------------------------
class DialogoSelecionarExemplar(tk.Toplevel):
    """Lista os exemplares disponíveis e devolve o selecionado.

    Use o atributo `codigo_selecionado` após `wait_window()` para obter
    o código de barras do exemplar escolhido (string vazia se cancelado).
    """

    def __init__(self, parent, titulo: str = "Selecionar exemplar"):
        super().__init__(parent)
        self.title(titulo)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 820, 560)
        self.codigo_selecionado: str = ""

        wrap = ttk.Frame(self, padding=20)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text=titulo,
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap,
                  text=("Apenas exemplares disponíveis aparecem aqui. "
                        "Dê um duplo-clique ou selecione e clique em 'Usar exemplar'."),
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 12))

        f = ttk.Frame(wrap)
        f.pack(fill="x")
        ttk.Label(f, text="Buscar:").pack(side="left")
        self.ent = ttk.Entry(f)
        self.ent.pack(side="left", fill="x", expand=True, padx=8)
        self.ent.bind("<Return>", lambda e: self._buscar())
        ttk.Button(f, text="Pesquisar",
                    command=self._buscar).pack(side="left")

        cols = ("titulo", "autores", "tombo", "codigo", "loc")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings",
                                  height=14)
        self.tree.heading("titulo", text="Título")
        self.tree.heading("autores", text="Autor(es)")
        self.tree.heading("tombo", text="Tombo")
        self.tree.heading("codigo", text="Código de barras")
        self.tree.heading("loc", text="Localização")
        self.tree.column("titulo", width=240, anchor="w")
        self.tree.column("autores", width=180, anchor="w")
        self.tree.column("tombo", width=90, anchor="center")
        self.tree.column("codigo", width=170, anchor="w")
        self.tree.column("loc", width=120, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(12, 0))
        self.tree.bind("<Double-1>", lambda e: self._confirmar())

        botoes = ttk.Frame(wrap)
        botoes.pack(fill="x", pady=(12, 0))
        ttk.Button(botoes, text="Cancelar",
                    command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Usar exemplar selecionado",
                    style="Primario.TButton",
                    command=self._confirmar).pack(side="right")

        self._buscar()
        self.ent.focus_set()

    def _buscar(self):
        for it in self.tree.get_children():
            self.tree.delete(it)
        for ex in servicos.listar_exemplares_disponiveis(self.ent.get()):
            self.tree.insert("", "end", values=(
                ex["titulo"], ex.get("autores") or "—",
                ex["numero_tombo"], ex["codigo_barras"],
                ex.get("localizacao") or "—",
            ))

    def _confirmar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nada selecionado",
                                  "Escolha um exemplar na lista.",
                                  parent=self)
            return
        valores = self.tree.item(sel[0])["values"]
        # codigo está na coluna 3 (index)
        self.codigo_selecionado = str(valores[3])
        self.destroy()


# ---------------------------------------------------------------------------
# Diálogo de cadastro/edição de livro
# ---------------------------------------------------------------------------
class DialogoLivro(tk.Toplevel):
    def __init__(self, parent, sessao: Sessao,
                 ao_salvar: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.sessao = sessao
        self.ao_salvar = ao_salvar
        self.title("Cadastrar livro")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 600, 720)

        self._construir()

    def _construir(self):
        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Cadastrar livro",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap, text="Preencha os dados do livro e a quantidade "
                  "de exemplares iniciais.",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 16))

        form = ttk.Frame(wrap)
        form.pack(fill="x")

        self._campos = {}
        linhas = [
            ("titulo", "Título *", 0),
            ("autores", "Autor(es) *  (separe por ;)", 1),
            ("isbn", "ISBN", 2),
            ("editora", "Editora", 3),
            ("categoria", "Categoria", 4),
            ("ano", "Ano de publicação", 5),
            ("edicao", "Edição", 6),
            ("localizacao", "Localização", 7),
        ]
        for chave, rotulo, linha in linhas:
            ttk.Label(form, text=rotulo).grid(
                row=linha, column=0, sticky="w", pady=(8, 2))
            ent = ttk.Entry(form, width=60, font=("Segoe UI", 10))
            ent.grid(row=linha, column=1, sticky="ew", pady=(8, 2))
            form.columnconfigure(1, weight=1)
            self._campos[chave] = ent

        ttk.Label(form, text="Quantidade de exemplares *").grid(
            row=8, column=0, sticky="w", pady=(8, 2))
        self.spin_qtd = tk.Spinbox(form, from_=1, to=50, width=6,
                                   font=("Segoe UI", 10))
        self.spin_qtd.delete(0, "end")
        self.spin_qtd.insert(0, "1")
        self.spin_qtd.grid(row=8, column=1, sticky="w", pady=(8, 2))

        ttk.Label(form, text="Sinopse").grid(row=9, column=0, sticky="nw",
                                              pady=(8, 2))
        self.txt_sinopse = tk.Text(form, height=6, width=50,
                                    font=("Segoe UI", 10))
        self.txt_sinopse.grid(row=9, column=1, sticky="ew", pady=(8, 2))

        botoes = ttk.Frame(wrap)
        botoes.pack(fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Cancelar", command=self.destroy
                   ).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Salvar livro",
                   style="Primario.TButton",
                   command=self._salvar).pack(side="right")

    def _salvar(self):
        try:
            titulo = self._campos["titulo"].get().strip()
            autores_raw = self._campos["autores"].get().strip()
            autores = [a.strip() for a in autores_raw.split(";") if a.strip()]
            ano_raw = self._campos["ano"].get().strip()
            ano = int(ano_raw) if ano_raw.isdigit() else None
            qtd = int(self.spin_qtd.get())
            res = servicos.cadastrar_livro(
                titulo=titulo,
                autores=autores,
                isbn=self._campos["isbn"].get().strip(),
                editora=self._campos["editora"].get().strip(),
                categoria=self._campos["categoria"].get().strip(),
                ano=ano,
                edicao=self._campos["edicao"].get().strip(),
                sinopse=self.txt_sinopse.get("1.0", "end").strip(),
                quantidade_exemplares=qtd,
                localizacao=self._campos["localizacao"].get().strip(),
                usuario_id=self.sessao.id,
            )
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        except ValueError:
            messagebox.showwarning("Atenção",
                                   "Verifique os campos numéricos.",
                                   parent=self)
            return

        messagebox.showinfo(
            "Livro cadastrado",
            f"Livro #{res['livro_id']} cadastrado com {len(res['exemplares'])} "
            "exemplar(es).\nUse a aba 'Etiquetas' para imprimir os códigos de barras.",
            parent=self,
        )
        if self.ao_salvar:
            self.ao_salvar()
        self.destroy()


# ---------------------------------------------------------------------------
# Diálogo de cadastro de usuário
# ---------------------------------------------------------------------------
class DialogoUsuario(tk.Toplevel):
    def __init__(self, parent, sessao: Sessao,
                 ao_salvar: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.sessao = sessao
        self.ao_salvar = ao_salvar
        self.title("Cadastrar usuário")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 520, 520)
        self._construir()

    def _construir(self):
        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Cadastrar usuário",
                  style="Titulo.TLabel").pack(anchor="w")

        form = ttk.Frame(wrap)
        form.pack(fill="x", pady=(16, 0))
        form.columnconfigure(1, weight=1)

        self._campos = {}
        for i, (chave, rotulo) in enumerate([
            ("nome", "Nome completo *"),
            ("matricula", "Matrícula *"),
            ("email", "E-mail"),
            ("telefone", "Telefone"),
        ]):
            ttk.Label(form, text=rotulo).grid(row=i, column=0, sticky="w",
                                               pady=(6, 2))
            ent = ttk.Entry(form, font=("Segoe UI", 10))
            ent.grid(row=i, column=1, sticky="ew", pady=(6, 2))
            self._campos[chave] = ent

        ttk.Label(form, text="Perfil *").grid(row=4, column=0, sticky="w",
                                              pady=(6, 2))
        self.combo_perfil = ttk.Combobox(form, state="readonly",
                                          values=["ALUNO", "PROFESSOR",
                                                   "BIBLIOTECARIO",
                                                   "ADMINISTRADOR"])
        self.combo_perfil.set("ALUNO")
        self.combo_perfil.grid(row=4, column=1, sticky="ew", pady=(6, 2))

        ttk.Label(form, text="Senha *").grid(row=5, column=0, sticky="w",
                                             pady=(6, 2))
        self.ent_senha = ttk.Entry(form, show="•", font=("Segoe UI", 10))
        self.ent_senha.grid(row=5, column=1, sticky="ew", pady=(6, 2))

        self.var_cartao = tk.BooleanVar(value=True)
        ttk.Checkbutton(form,
                        text="Gerar código de barras para o cartão de acesso",
                        variable=self.var_cartao).grid(
                            row=6, column=0, columnspan=2, sticky="w",
                            pady=(12, 0))

        botoes = ttk.Frame(wrap)
        botoes.pack(fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Cancelar",
                   command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Cadastrar",
                   style="Primario.TButton",
                   command=self._salvar).pack(side="right")

    def _salvar(self):
        try:
            res = servicos.cadastrar_usuario(
                nome=self._campos["nome"].get(),
                matricula=self._campos["matricula"].get(),
                email=self._campos["email"].get(),
                telefone=self._campos["telefone"].get(),
                perfil=self.combo_perfil.get(),
                senha=self.ent_senha.get(),
                gerar_cartao=self.var_cartao.get(),
                usuario_id_executor=self.sessao.id,
            )
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        cartao = res["codigo_barras"] or "—"
        messagebox.showinfo("Usuário cadastrado",
                             f"Usuário #{res['id']} cadastrado.\n"
                             f"Cartão (código de barras): {cartao}",
                             parent=self)
        if self.ao_salvar:
            self.ao_salvar()
        self.destroy()


# ---------------------------------------------------------------------------
# Diálogo: detalhes do livro + código de barras dos exemplares
# ---------------------------------------------------------------------------
class DialogoDetalhesLivro(tk.Toplevel):
    def __init__(self, parent, livro_id: int):
        super().__init__(parent)
        self.title("Detalhes do livro")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 720, 640)

        livro = servicos.detalhes_livro(livro_id)
        if not livro:
            messagebox.showerror("Erro", "Livro não encontrado.", parent=self)
            self.destroy()
            return

        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text=livro["titulo"],
                  style="Titulo.TLabel").pack(anchor="w")
        sub = ", ".join(livro["autores"]) or "(sem autor cadastrado)"
        ttk.Label(wrap, text=sub, style="Hint.TLabel").pack(anchor="w")

        infos = [
            ("ISBN", livro.get("isbn") or "—"),
            ("Editora", livro.get("editora_nome") or "—"),
            ("Categoria", livro.get("categoria_nome") or "—"),
            ("Edição/Ano",
             f"{livro.get('edicao') or '—'} / {livro.get('ano_publicacao') or '—'}"),
        ]
        info_box = ttk.Frame(wrap)
        info_box.pack(fill="x", pady=(12, 8))
        for i, (k, v) in enumerate(infos):
            ttk.Label(info_box, text=f"{k}:",
                      font=("Segoe UI Semibold", 10)
                      ).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Label(info_box, text=v).grid(row=i, column=1, sticky="w",
                                              padx=(8, 0))

        if livro.get("sinopse"):
            ttk.Label(wrap, text="Sinopse",
                      style="Subtitulo.TLabel").pack(anchor="w", pady=(8, 2))
            tk.Label(wrap, text=livro["sinopse"], wraplength=660,
                     justify="left", bg=tema.COR_FUNDO, fg=tema.COR_TEXTO,
                     font=("Segoe UI", 10)).pack(anchor="w")

        ttk.Label(wrap, text="Exemplares e códigos de barras",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(16, 4))

        cols = ("tombo", "codigo", "loc", "status")
        tree = ttk.Treeview(wrap, columns=cols, show="headings", height=8)
        tree.heading("tombo", text="Tombo")
        tree.heading("codigo", text="Código de barras")
        tree.heading("loc", text="Localização")
        tree.heading("status", text="Status")
        tree.column("tombo", width=110, anchor="w")
        tree.column("codigo", width=200, anchor="w")
        tree.column("loc", width=180, anchor="w")
        tree.column("status", width=110, anchor="w")
        for ex in livro["exemplares"]:
            tree.insert("", "end",
                        values=(ex["numero_tombo"], ex["codigo_barras"],
                                ex.get("localizacao") or "—", ex["status"]))
        tree.pack(fill="both", expand=True)

        ttk.Button(wrap, text="Imprimir etiquetas (visualizar)",
                   style="Primario.TButton",
                   command=lambda: VisualizadorBarcodes(self, livro)
                   ).pack(pady=(12, 0))


# ---------------------------------------------------------------------------
# Visualizador de etiquetas de código de barras
# ---------------------------------------------------------------------------
class VisualizadorBarcodes(tk.Toplevel):
    def __init__(self, parent, livro: dict):
        super().__init__(parent)
        self.title(f"Etiquetas — {livro['titulo']}")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 700, 600)

        wrap = ttk.Frame(self, padding=20)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text=livro["titulo"],
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap, text=f"Total de exemplares: {len(livro['exemplares'])}",
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 12))

        canvas = tk.Canvas(wrap, bg="white", highlightthickness=1,
                            highlightbackground=tema.COR_BORDA)
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        y = 20
        for ex in livro["exemplares"]:
            canvas.create_text(
                20, y, anchor="nw",
                text=f"{ex['numero_tombo']} — {livro['titulo']}",
                font=("Segoe UI Semibold", 10))
            barcode_util.desenhar_barras(canvas, ex["codigo_barras"],
                                          x0=20, y0=y + 22, altura=50,
                                          largura_unit=2)
            y += 110

        canvas.configure(scrollregion=(0, 0, 600, y))

        ttk.Button(wrap, text="Fechar",
                   command=self.destroy).pack(side="bottom", pady=(12, 0))
