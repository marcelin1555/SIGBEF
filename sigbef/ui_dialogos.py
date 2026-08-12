"""
SIGBEF — Diálogos modais reutilizáveis (cadastro de livro, usuário,
visualização de exemplares e código de barras).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional

from . import barcode_util
from . import servicos
from . import ui_tema as tema
from .auth import Sessao
from .formato import data_br, reais, status_legivel
from .servicos import RegraNegocioError


# ---------------------------------------------------------------------------
# Diálogo: Sobre o sistema
# ---------------------------------------------------------------------------
class DialogoSobre(tk.Toplevel):
    """Janela 'Sobre o sistema' com versão, licença e autor."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Sobre o SIGBEF")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 540, 480)
        self.resizable(False, False)

        # Topo institucional
        from . import icones
        topo = tk.Frame(self, bg=tema.COR_PRIMARIA, height=110)
        topo.pack(fill="x")
        topo.pack_propagate(False)
        tk.Label(topo, bg=tema.COR_PRIMARIA,
                 image=icones.icone("logoplaca", "original", 48),
                 compound="left",
                 text="  SIGBEF", fg=tema.COR_TEXTO_CLARO,
                 font=("Segoe UI Semibold", 36)
                 ).pack(pady=(14, 0))
        from . import __version__
        tk.Label(topo, bg=tema.COR_PRIMARIA, fg=tema.COR_PRIMARIA_SUAVE,
                 text=f"Versão {__version__}",
                 font=("Segoe UI", 11)).pack()

        # Corpo
        corpo = ttk.Frame(self, padding=24)
        corpo.pack(fill="both", expand=True)

        ttk.Label(corpo,
                  text="Sistema Integrado de Gestão da Biblioteca Escolar",
                  style="Subtitulo.TLabel", wraplength=480, justify="center"
                  ).pack(pady=(0, 12))
        ttk.Label(corpo,
                  text=("Software para automatizar o atendimento da "
                        "biblioteca: cadastro de acervo, empréstimos, "
                        "devoluções, autoatendimento e relatórios."),
                  style="Hint.TLabel", wraplength=480, justify="center"
                  ).pack(pady=(0, 16))

        # Detalhes
        info = ttk.Frame(corpo)
        info.pack()
        linhas = [
            ("Autor", "Marcello Melo de Medeiros Costa"),
            ("Licença", "MIT"),
            ("Tecnologia", "Python 3.10+ • Tkinter • SQLite"),
            ("Repositório", "https://github.com/marcelin1555/SIGBEF"),
        ]
        for k, v in linhas:
            row = ttk.Frame(info)
            row.pack(anchor="w", pady=2)
            ttk.Label(row, text=f"{k}:",
                      font=("Segoe UI Semibold", 10), width=12,
                      anchor="w").pack(side="left")
            ttk.Label(row, text=v,
                      font=("Segoe UI", 10)).pack(side="left")

        ttk.Label(corpo,
                  text="Copyright © 2026 Marcello Melo de Medeiros Costa",
                  style="Hint.TLabel"
                  ).pack(pady=(20, 0))

        ttk.Button(corpo, text="Fechar",
                    style="Primario.TButton",
                    command=self.destroy
                    ).pack(pady=(20, 0))


# ---------------------------------------------------------------------------
# Diálogo: resetar o sistema (apaga tudo)
# ---------------------------------------------------------------------------
class DialogoResetarSistema(tk.Toplevel):
    """Confirmação em duas camadas pra ação mais destrutiva do sistema.

    Não basta um "sim/não": exige digitar a frase exata antes do botão
    de confirmar fazer qualquer coisa. É o único jeito de apagar tudo, e
    "tudo" inclui a própria conta de quem clicou — por isso o programa
    fecha logo depois, em vez de tentar continuar numa sessão que já não
    existe mais no banco.
    """

    FRASE_CONFIRMACAO = "APAGAR TUDO"

    def __init__(self, parent, sessao: Sessao):
        super().__init__(parent)
        self.sessao = sessao
        self.title("Resetar sistema")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 520, 420)
        self._construir()

    def _construir(self):
        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Resetar sistema",
                  style="Titulo.TLabel").pack(anchor="w")

        from . import api
        avisos = [
            "• Todo o acervo, exemplares e categorias/editoras/autores",
            "• Todos os usuários e o histórico de empréstimos e reservas",
            "• Prazos, limites, multas, dados de SMTP e tokens da API "
            "voltam ao padrão de fábrica",
            "• O brasão da instituição é removido",
        ]
        if api.api_ativa():
            avisos.append(
                "• Aparelhos pareados (celulares) vão precisar ser "
                "pareados de novo")
        ttk.Label(
            wrap,
            text="Isto apaga permanentemente:",
            style="Card.TLabel", font=("Segoe UI Semibold", 10)
            ).pack(anchor="w", pady=(12, 4))
        ttk.Label(wrap, text="\n".join(avisos), style="Hint.TLabel",
                  justify="left").pack(anchor="w")
        ttk.Label(
            wrap,
            text="Um backup é feito automaticamente antes de apagar "
            "(as cópias anteriores em \"backups/\" também continuam lá). "
            "Ainda assim, esta ação não tem \"desfazer\" dentro do "
            "sistema.",
            style="Hint.TLabel", wraplength=460, justify="left"
            ).pack(anchor="w", pady=(12, 4))

        ttk.Label(
            wrap,
            text=f'Digite "{self.FRASE_CONFIRMACAO}" para confirmar:',
            style="Card.TLabel").pack(anchor="w", pady=(16, 4))
        self.ent_confirmacao = ttk.Entry(wrap, width=30,
                                          font=("Segoe UI", 10))
        self.ent_confirmacao.pack(anchor="w")

        botoes = ttk.Frame(wrap)
        botoes.pack(fill="x", pady=(24, 0))
        ttk.Button(botoes, text="Cancelar", command=self.destroy
                   ).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Apagar tudo",
                   style="Perigo.TButton",
                   command=self._confirmar).pack(side="right")

    def _confirmar(self):
        if self.ent_confirmacao.get().strip() != self.FRASE_CONFIRMACAO:
            messagebox.showwarning(
                "Confirmação necessária",
                f'Digite exatamente "{self.FRASE_CONFIRMACAO}" no campo '
                "para confirmar.",
                parent=self)
            return

        from . import reset
        try:
            caminho_backup = reset.resetar_sistema()
        except Exception as e:
            messagebox.showerror(
                "Resetar sistema",
                f"Não foi possível concluir o reset: {e}\n\n"
                "Nada foi apagado — o backup de segurança não pôde ser "
                "feito, então a operação parou antes de mexer nos dados.",
                parent=self)
            return

        messagebox.showinfo(
            "Sistema resetado",
            "Todos os dados foram apagados.\n\n"
            f"Backup salvo em:\n{caminho_backup}\n\n"
            "O programa vai fechar agora. Abra o SIGBEF de novo para "
            "configurar o primeiro administrador.",
            parent=self)
        self.destroy()
        # A sessão atual referencia um usuário que não existe mais no
        # banco — a única saída limpa é encerrar o processo, não tentar
        # continuar navegando pelo painel.
        self.master.destroy()


# ---------------------------------------------------------------------------
# Base reutilizável: modal de busca + tabela + seleção
# ---------------------------------------------------------------------------
class DialogoBuscaSelecao(tk.Toplevel):
    """Modal genérico: campo de busca + Treeview; duplo-clique (ou botão)
    devolve o valor da coluna-chave do item escolhido.

    A subclasse define `COLUNAS` (lista de `(key, rótulo, largura,
    âncora)`) e `COLUNA_RETORNO` (a key cujo valor vira o resultado), e
    implementa `buscar(termo) -> list[dict]` e `linha(item) -> tuple`.
    Após `wait_window()`, leia `self.selecionado` (string vazia se
    cancelado).
    """

    COLUNAS: list[tuple[str, str, int, str]] = []
    COLUNA_RETORNO: str = ""

    def __init__(self, parent, titulo: str, dica: str,
                 texto_confirmar: str, largura: int = 820,
                 altura: int = 560):
        super().__init__(parent)
        self.title(titulo)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, largura, altura)
        self.selecionado: str = ""

        wrap = ttk.Frame(self, padding=20)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text=titulo, style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap, text=dica, style="Hint.TLabel"
                  ).pack(anchor="w", pady=(2, 12))

        f = ttk.Frame(wrap)
        f.pack(fill="x")
        ttk.Label(f, text="Buscar:").pack(side="left")
        self.ent = ttk.Entry(f)
        self.ent.pack(side="left", fill="x", expand=True, padx=8)
        self.ent.bind("<Return>", lambda e: self._buscar())
        ttk.Button(f, text="Pesquisar", command=self._buscar).pack(side="left")

        keys = [c[0] for c in self.COLUNAS]
        self.tree = ttk.Treeview(wrap, columns=keys, show="headings",
                                  height=14)
        for key, rotulo, largura_c, ancora in self.COLUNAS:
            self.tree.heading(key, text=rotulo)
            self.tree.column(key, width=largura_c, anchor=ancora)
        self.tree.pack(fill="both", expand=True, pady=(12, 0))
        self.tree.bind("<Double-1>", lambda e: self._confirmar())
        self._idx_retorno = keys.index(self.COLUNA_RETORNO)

        botoes = ttk.Frame(wrap)
        botoes.pack(fill="x", pady=(12, 0))
        ttk.Button(botoes, text="Cancelar",
                    command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text=texto_confirmar, style="Primario.TButton",
                    command=self._confirmar).pack(side="right")

        self._buscar()
        self.ent.focus_set()

    def buscar(self, termo: str) -> list[dict]:
        raise NotImplementedError

    def linha(self, item: dict) -> tuple:
        return tuple(item.get(c[0], "") for c in self.COLUNAS)

    def _buscar(self) -> None:
        for it in self.tree.get_children():
            self.tree.delete(it)
        for item in self.buscar(self.ent.get()):
            self.tree.insert("", "end", values=self.linha(item))
        tema.aplicar_zebra(self.tree)

    def _confirmar(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nada selecionado",
                                  "Escolha um item na lista.", parent=self)
            return
        valores = self.tree.item(sel[0])["values"]
        self.selecionado = str(valores[self._idx_retorno])
        self.destroy()


# ---------------------------------------------------------------------------
# Diálogo: selecionar exemplar disponível para empréstimo
# ---------------------------------------------------------------------------
class DialogoSelecionarExemplar(DialogoBuscaSelecao):
    """Lista os exemplares disponíveis e devolve o código de barras
    escolhido em `codigo_selecionado` (string vazia se cancelado)."""

    COLUNAS = [("titulo", "Título", 240, "w"),
               ("autores", "Autor(es)", 180, "w"),
               ("tombo", "Tombo", 90, "center"),
               ("codigo", "Código de barras", 170, "w"),
               ("loc", "Localização", 120, "w")]
    COLUNA_RETORNO = "codigo"

    def __init__(self, parent, titulo: str = "Selecionar exemplar"):
        super().__init__(
            parent, titulo,
            "Apenas exemplares disponíveis aparecem aqui. Dê um "
            "duplo-clique ou selecione e clique em 'Usar exemplar'.",
            "Usar exemplar selecionado")

    def buscar(self, termo: str) -> list[dict]:
        return servicos.listar_exemplares_disponiveis(termo)

    def linha(self, ex: dict) -> tuple:
        return (ex["titulo"], ex.get("autores") or "", ex["numero_tombo"],
                ex["codigo_barras"], ex.get("localizacao") or "")

    @property
    def codigo_selecionado(self) -> str:
        return self.selecionado


# ---------------------------------------------------------------------------
# Diálogo: selecionar usuário ativo
# ---------------------------------------------------------------------------
class DialogoSelecionarUsuario(DialogoBuscaSelecao):
    """Lista usuários ativos e devolve a matrícula escolhida em
    `matricula_selecionada` (string vazia se cancelado)."""

    COLUNAS = [("nome", "Nome", 240, "w"),
               ("matricula", "Matrícula", 100, "w"),
               ("perfil", "Perfil", 130, "w"),
               ("email", "E-mail", 220, "w")]
    COLUNA_RETORNO = "matricula"

    def __init__(self, parent):
        super().__init__(
            parent, "Selecionar usuário",
            "Busque pelo nome, matrícula ou e-mail.",
            "Usar usuário selecionado", largura=720, altura=500)

    def buscar(self, termo: str) -> list[dict]:
        return [u for u in servicos.listar_usuarios(termo) if u["ativo"]]

    def linha(self, u: dict) -> tuple:
        return (u["nome"], u["matricula"], u["perfil"], u.get("email") or "")

    @property
    def matricula_selecionada(self) -> str:
        return self.selecionado


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

        if servicos.isbn_lookup_ativo():
            ttk.Button(form, text="Buscar online",
                       command=self._buscar_isbn).grid(
                           row=2, column=2, padx=(6, 0), pady=(8, 2))

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

    def _set_campo(self, chave, valor):
        ent = self._campos.get(chave)
        if ent is None:
            return
        ent.delete(0, "end")
        ent.insert(0, valor)

    def _buscar_isbn(self):
        isbn = self._campos["isbn"].get().strip()
        if not isbn:
            messagebox.showinfo("Buscar por ISBN",
                                 "Digite o ISBN primeiro.", parent=self)
            return
        try:
            dados = servicos.buscar_metadados_isbn(isbn)
        except RegraNegocioError as e:
            messagebox.showwarning("Buscar por ISBN", str(e), parent=self)
            return
        if not dados:
            messagebox.showinfo(
                "Buscar por ISBN",
                "Nenhum dado encontrado para esse ISBN nas bases online "
                "(comum em livros brasileiros). Preencha os campos manualmente.",
                parent=self)
            return
        if dados.get("titulo"):
            self._set_campo("titulo", dados["titulo"])
        if dados.get("autores"):
            self._set_campo("autores", "; ".join(dados["autores"]))
        if dados.get("editora"):
            self._set_campo("editora", dados["editora"])
        if dados.get("ano"):
            self._set_campo("ano", str(dados["ano"]))
        messagebox.showinfo(
            "Buscar por ISBN",
            f"Dados preenchidos a partir de {dados.get('fonte', 'online')}. "
            "Confira e ajuste se precisar.", parent=self)

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
# Diálogo: editar livro (só os dados do livro; exemplares têm fluxo próprio)
# ---------------------------------------------------------------------------
class DialogoEditarLivro(tk.Toplevel):
    """Corrige título, autores, ISBN, editora, categoria, ano, edição e
    sinopse de um livro já cadastrado.

    Não mexe em exemplares, quantidade, tombo ou localização — cada um
    desses tem seu próprio caminho (adicionar exemplares, baixa), e
    misturar tudo numa tela só faria a bibliotecária alterar o acervo
    por engano ao só corrigir um título digitado errado.
    """

    def __init__(self, parent, sessao: Sessao, livro_id: int,
                 ao_salvar: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.sessao = sessao
        self.livro_id = livro_id
        self.ao_salvar = ao_salvar
        try:
            self.livro = servicos.detalhes_livro(livro_id)
            if self.livro is None:
                raise RegraNegocioError("Livro não encontrado.")
        except RegraNegocioError:
            # O Toplevel já foi criado por super().__init__(); sem isto,
            # o livro ter sido excluído por outra sessão entre a
            # listagem e o clique em "Editar" deixaria uma janela vazia
            # flutuando na tela.
            self.destroy()
            raise
        self.title("Editar livro")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 600, 660)
        self._construir()

    def _construir(self):
        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Editar livro",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap, text="Corrige os dados do livro. Exemplares, "
                  "tombo e quantidade não mudam aqui.",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 16))

        form = ttk.Frame(wrap)
        form.pack(fill="x")

        self._campos = {}
        linhas = [
            ("titulo", "Título *", 0, self.livro["titulo"]),
            ("autores", "Autor(es) *  (separe por ;)", 1,
             "; ".join(self.livro["autores"])),
            ("isbn", "ISBN", 2, self.livro.get("isbn") or ""),
            ("editora", "Editora", 3, self.livro.get("editora_nome") or ""),
            ("categoria", "Categoria", 4, self.livro.get("categoria_nome") or ""),
            ("ano", "Ano de publicação", 5,
             str(self.livro["ano_publicacao"]) if self.livro.get("ano_publicacao") else ""),
            ("edicao", "Edição", 6, self.livro.get("edicao") or ""),
        ]
        for chave, rotulo, linha, valor_inicial in linhas:
            ttk.Label(form, text=rotulo).grid(
                row=linha, column=0, sticky="w", pady=(8, 2))
            ent = ttk.Entry(form, width=60, font=("Segoe UI", 10))
            ent.insert(0, valor_inicial)
            ent.grid(row=linha, column=1, sticky="ew", pady=(8, 2))
            form.columnconfigure(1, weight=1)
            self._campos[chave] = ent

        ttk.Label(form, text="Sinopse").grid(row=7, column=0, sticky="nw",
                                              pady=(8, 2))
        self.txt_sinopse = tk.Text(form, height=6, width=50,
                                    font=("Segoe UI", 10))
        self.txt_sinopse.insert("1.0", self.livro.get("sinopse") or "")
        self.txt_sinopse.grid(row=7, column=1, sticky="ew", pady=(8, 2))

        botoes = ttk.Frame(wrap)
        botoes.pack(fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Cancelar", command=self.destroy
                   ).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Salvar alterações",
                   style="Primario.TButton",
                   command=self._salvar).pack(side="right")

    def _salvar(self):
        try:
            titulo = self._campos["titulo"].get().strip()
            autores_raw = self._campos["autores"].get().strip()
            autores = [a.strip() for a in autores_raw.split(";") if a.strip()]
            ano_raw = self._campos["ano"].get().strip()
            ano = int(ano_raw) if ano_raw.isdigit() else None
            servicos.editar_livro(
                self.livro_id,
                titulo=titulo,
                autores=autores,
                isbn=self._campos["isbn"].get().strip(),
                editora=self._campos["editora"].get().strip(),
                categoria=self._campos["categoria"].get().strip(),
                ano=ano,
                edicao=self._campos["edicao"].get().strip(),
                sinopse=self.txt_sinopse.get("1.0", "end").strip(),
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
        tema.centralizar_janela(self, 520, 600)
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
            ("turma", "Série / Turma"),
        ]):
            ttk.Label(form, text=rotulo).grid(row=i, column=0, sticky="w",
                                               pady=(6, 2))
            ent = ttk.Entry(form, font=("Segoe UI", 10))
            ent.grid(row=i, column=1, sticky="ew", pady=(6, 2))
            self._campos[chave] = ent

        ttk.Label(form, text="Ex.: 3º Ano Técnico em Informática",
                  style="Hint.TLabel").grid(row=5, column=1, sticky="w",
                                            pady=(0, 6))

        ttk.Label(form, text="Perfil *").grid(row=6, column=0, sticky="w",
                                              pady=(6, 2))
        self.combo_perfil = ttk.Combobox(form, state="readonly",
                                          values=["ALUNO", "PROFESSOR",
                                                   "BIBLIOTECARIO",
                                                   "ADMINISTRADOR"])
        self.combo_perfil.set("ALUNO")
        self.combo_perfil.grid(row=6, column=1, sticky="ew", pady=(6, 2))

        ttk.Label(form, text="Senha *").grid(row=7, column=0, sticky="w",
                                             pady=(6, 2))
        self.ent_senha = ttk.Entry(form, show="•", font=("Segoe UI", 10))
        self.ent_senha.grid(row=7, column=1, sticky="ew", pady=(6, 2))

        self.var_cartao = tk.BooleanVar(value=True)
        ttk.Checkbutton(form,
                        text="Gerar código de barras para o cartão de acesso",
                        variable=self.var_cartao).grid(
                            row=8, column=0, columnspan=2, sticky="w",
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
                turma=self._campos["turma"].get(),
                perfil=self.combo_perfil.get(),
                senha=self.ent_senha.get(),
                gerar_cartao=self.var_cartao.get(),
                usuario_id_executor=self.sessao.id,
            )
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        cartao = res["codigo_barras"] or "(sem cartão)"
        messagebox.showinfo("Usuário cadastrado",
                             f"Usuário #{res['id']} cadastrado.\n"
                             f"Cartão (código de barras): {cartao}",
                             parent=self)
        if self.ao_salvar:
            self.ao_salvar()
        self.destroy()


# ---------------------------------------------------------------------------
# Diálogo: importar acervo via CSV
# ---------------------------------------------------------------------------
class DialogoImportarCSV(tk.Toplevel):
    """Importação de acervo em massa a partir de planilha CSV."""

    def __init__(self, parent, sessao: Sessao,
                 ao_salvar: Optional[Callable] = None):
        super().__init__(parent)
        self.sessao = sessao
        self.ao_salvar = ao_salvar
        self.title("Importar acervo (CSV)")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 660, 560)
        self._construir()

    def _construir(self):
        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Importar acervo (CSV)",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap,
                  text=("Importa vários livros de uma vez a partir de uma "
                         "planilha salva como CSV\n(no Excel: Salvar como → "
                         "CSV)."),
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 10))

        card = tema.caixa_card(wrap, padx=16, pady=12)
        card.pack(fill="x")
        for txt in (
            "• Coluna obrigatória: titulo, as demais são opcionais",
            "• Colunas aceitas: autores, isbn, editora, categoria, ano,",
            "   edicao, sinopse, quantidade, tombo, localizacao",
            "• Vários autores na mesma célula: separe com ; ou /",
            "• Tombo: número de registro do livro físico (um por exemplar,",
            "   separados por / quando a quantidade for maior que 1)",
            "• Separador (; ou ,) e acentuação detectados automaticamente",
            "• Linhas com ISBN já cadastrado são puladas (não duplica)",
        ):
            ttk.Label(card, text=txt, style="Card.TLabel").pack(anchor="w")

        botoes = ttk.Frame(wrap)
        botoes.pack(fill="x", pady=(14, 0))
        ttk.Button(botoes, text="Salvar planilha modelo...",
                   command=self._salvar_modelo).pack(side="left")
        ttk.Button(botoes, text="Escolher CSV e importar...",
                   style="Primario.TButton",
                   command=self._importar).pack(side="right")

        ttk.Label(wrap, text="Resultado",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(16, 4))
        self.txt = tk.Text(wrap, height=9, state="disabled",
                           font=("Consolas", 9), bg="white",
                           relief="solid", borderwidth=1)
        self.txt.pack(fill="both", expand=True)

    def _log(self, linhas: list[str]):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", "\n".join(linhas))
        self.txt.configure(state="disabled")

    def _salvar_modelo(self):
        destino = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv",
            initialfile="modelo_acervo.csv",
            filetypes=[("Planilha CSV", "*.csv")])
        if not destino:
            return
        servicos.gerar_modelo_csv(destino)
        messagebox.showinfo("Modelo salvo",
                             "Planilha modelo salva. Preencha no Excel e "
                             "salve como CSV para importar.",
                             parent=self)

    def _importar(self):
        caminho = filedialog.askopenfilename(
            parent=self,
            filetypes=[("Planilha CSV", "*.csv"), ("Todos", "*.*")])
        if not caminho:
            return
        try:
            res = servicos.importar_acervo_csv(caminho,
                                                usuario_id=self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        except OSError as e:
            messagebox.showerror("Erro ao ler o arquivo", str(e), parent=self)
            return
        linhas = [f"Importados: {res['livros']} livro(s), "
                  f"{res['exemplares']} exemplar(es)."]
        if res["pulados"]:
            linhas.append(f"\nPulados ({len(res['pulados'])}):")
            linhas += [f"  linha {n}: {m}" for n, m in res["pulados"][:10]]
            if len(res["pulados"]) > 10:
                linhas.append(f"  ... e mais {len(res['pulados']) - 10}")
        if res["erros"]:
            linhas.append(f"\nErros ({len(res['erros'])}):")
            linhas += [f"  linha {n}: {m}" for n, m in res["erros"][:10]]
            if len(res["erros"]) > 10:
                linhas.append(f"  ... e mais {len(res['erros']) - 10}")
        # Correções feitas no caminho. Mostradas para a bibliotecária
        # saber o que mudou — importar não deve alterar em silêncio.
        if res.get("ajustes"):
            linhas.append(f"\nCorrigidos automaticamente "
                          f"({len(res['ajustes'])}):")
            linhas += [f"  linha {n}: {m}" for n, m in res["ajustes"][:10]]
            if len(res["ajustes"]) > 10:
                linhas.append(f"  ... e mais {len(res['ajustes']) - 10}")
            linhas.append("  Dica: formate essas colunas como Texto na "
                          "planilha antes de exportar.")
        if not res["livros"] and not res["erros"] and not res["pulados"]:
            linhas.append("Nenhuma linha de dados encontrada no arquivo.")
        self._log(linhas)
        if res["livros"] and self.ao_salvar:
            self.ao_salvar()


# ---------------------------------------------------------------------------
# Diálogo: editar usuário (nome, contato, turma e perfil)
# ---------------------------------------------------------------------------
class DialogoEditarUsuario(tk.Toplevel):
    """Edição dos dados cadastrais de um usuário existente.

    A matrícula é fixa (identidade de login) e a senha tem fluxo próprio —
    aqui editam-se nome, e-mail, telefone, série/turma e perfil.
    """

    def __init__(self, parent, sessao: Sessao, usuario_id: int,
                 ao_salvar: Optional[Callable] = None):
        super().__init__(parent)
        self.sessao = sessao
        self.usuario_id = usuario_id
        self.ao_salvar = ao_salvar
        try:
            self.usuario = servicos.obter_usuario(usuario_id)
        except RegraNegocioError:
            # O Toplevel já foi criado por super().__init__(); sem isto,
            # uma exceção aqui (usuário excluído por outra sessão entre a
            # listagem e o clique em "Editar") deixa uma janela vazia
            # flutuando na tela que ninguém sabe fechar.
            self.destroy()
            raise
        self.title("Editar usuário")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 520, 520)
        self._construir()

    def _construir(self):
        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Editar usuário",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap,
                  text=f"Matrícula: {self.usuario['matricula']} (não editável)",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 0))

        form = ttk.Frame(wrap)
        form.pack(fill="x", pady=(16, 0))
        form.columnconfigure(1, weight=1)

        self._campos = {}
        valores = {
            "nome": self.usuario["nome"] or "",
            "email": self.usuario.get("email") or "",
            "telefone": self.usuario.get("telefone") or "",
            "turma": self.usuario.get("turma") or "",
        }
        for i, (chave, rotulo) in enumerate([
            ("nome", "Nome completo *"),
            ("email", "E-mail"),
            ("telefone", "Telefone"),
            ("turma", "Série / Turma"),
        ]):
            ttk.Label(form, text=rotulo).grid(row=i, column=0, sticky="w",
                                               pady=(6, 2))
            ent = ttk.Entry(form, font=("Segoe UI", 10))
            ent.insert(0, valores[chave])
            ent.grid(row=i, column=1, sticky="ew", pady=(6, 2))
            self._campos[chave] = ent

        ttk.Label(form, text="Ex.: 3º Ano Técnico em Informática",
                  style="Hint.TLabel").grid(row=4, column=1, sticky="w",
                                            pady=(0, 6))

        ttk.Label(form, text="Perfil *").grid(row=5, column=0, sticky="w",
                                              pady=(6, 2))
        self.combo_perfil = ttk.Combobox(form, state="readonly",
                                          values=["ALUNO", "PROFESSOR",
                                                   "BIBLIOTECARIO",
                                                   "ADMINISTRADOR"])
        self.combo_perfil.set(self.usuario["perfil"])
        self.combo_perfil.grid(row=5, column=1, sticky="ew", pady=(6, 2))

        botoes = ttk.Frame(wrap)
        botoes.pack(fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Cancelar",
                   command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Salvar alterações",
                   style="Primario.TButton",
                   command=self._salvar).pack(side="right")

    def _salvar(self):
        try:
            servicos.atualizar_usuario(
                self.usuario_id,
                nome=self._campos["nome"].get(),
                email=self._campos["email"].get(),
                telefone=self._campos["telefone"].get(),
                turma=self._campos["turma"].get(),
                perfil=self.combo_perfil.get(),
                executor_id=self.sessao.id,
            )
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self)
            return
        if self.ao_salvar:
            self.ao_salvar()
        self.destroy()


# ---------------------------------------------------------------------------
# Diálogo: devolução em lote
# ---------------------------------------------------------------------------
class DialogoDevolucaoEmLote(tk.Toplevel):
    """Devolver uma pilha de livros sem uma janela por livro.

    É o fluxo do fim do ano letivo, quando a turma inteira devolve de
    uma vez. O caminho normal (duplo clique na linha, confirmar) é bom
    para um livro e insuportável para trinta.

    Nada de confirmação item a item: cada leitura já devolve e a linha
    aparece na lista. O resumo, com as multas somadas, fica para o fim.
    """

    def __init__(self, parent, sessao: Sessao, ao_fechar=None):
        super().__init__(parent)
        self.sessao = sessao
        self.ao_fechar = ao_fechar
        self.devolvidos: list[dict] = []
        self.recusados = 0

        self.title("Devolução em lote")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 760, 560)

        wrap = ttk.Frame(self, padding=20)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Devolução em lote",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap, text=("Vá passando o leitor nos livros. Cada leitura "
                               "devolve na hora — sem confirmar um a um."),
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 14))

        linha = ttk.Frame(wrap)
        linha.pack(fill="x")
        ttk.Label(linha, text="Código ou tombo:").pack(side="left")
        self.ent = ttk.Entry(linha, width=30, font=("Segoe UI", 13))
        self.ent.pack(side="left", padx=8, ipady=4)
        self.ent.bind("<Return>", lambda e: self._devolver())
        self.ent.focus_set()
        ttk.Button(linha, text="Devolver", style="Primario.TButton",
                    command=self._devolver).pack(side="left")

        self.lbl_ultimo = ttk.Label(wrap, text="", style="Hint.TLabel",
                                      wraplength=700, justify="left")
        self.lbl_ultimo.pack(anchor="w", pady=(10, 0))

        cols = ("titulo", "quem", "atraso", "multa")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings",
                                  height=13)
        for c, t, w in [("titulo", "Título", 300), ("quem", "Estava com", 190),
                        ("atraso", "Atraso", 90), ("multa", "Multa", 100)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("atrasado", background="#FDECEA",
                                 foreground=tema.COR_ERRO)
        self.tree.pack(fill="both", expand=True, pady=(10, 0))

        self.lbl_total = ttk.Label(wrap, text="Nenhum livro devolvido ainda.",
                                     style="Card.TLabel",
                                     font=("Segoe UI Semibold", 11))
        self.lbl_total.pack(anchor="w", pady=(12, 0))

        rodape = ttk.Frame(wrap)
        rodape.pack(fill="x", pady=(12, 0))
        ttk.Button(rodape, text="Concluir", style="Primario.TButton",
                    command=self._concluir).pack(side="right")

    def _devolver(self):
        codigo = self.ent.get().strip()
        if not codigo:
            return
        try:
            r = servicos.realizar_devolucao(codigo_exemplar=codigo,
                                             operador_id=self.sessao.id)
        except RegraNegocioError as e:
            # Um livro recusado não pode parar a pilha: a bibliotecária
            # segue devolvendo os outros e resolve esse no fim.
            self.recusados += 1
            self.lbl_ultimo.configure(text=f"{codigo}: {e}",
                                        foreground=tema.COR_ERRO)
            self.ent.delete(0, tk.END)
            self.ent.focus_set()
            return

        self.devolvidos.append(r)
        dias = r.get("dias_atraso", 0)
        multa = r.get("multa", 0) or 0
        self.tree.insert(
            "", 0,
            values=(r["titulo"], r.get("usuario") or "",
                    f"{dias} dia(s)" if dias else "—",
                    reais(multa) if multa else "—"),
            tags=("atrasado",) if dias else ())

        aviso = ""
        if r.get("reservado_para"):
            # Não pode voltar para a estante: alguém está esperando.
            aviso = (f"  ⚠ SEPARAR para {r['reservado_para']}")
        self.lbl_ultimo.configure(
            text=f"{r['titulo']} devolvido."
                  + (f" Multa: {reais(multa)}." if multa else "")
                  + aviso,
            foreground=tema.COR_AVISO if (multa or aviso)
                       else tema.COR_SUCESSO)
        self.ent.delete(0, tk.END)
        self.ent.focus_set()
        self._atualizar_total()

    def _atualizar_total(self):
        total_multa = sum((d.get("multa") or 0) for d in self.devolvidos)
        atrasados = sum(1 for d in self.devolvidos if d.get("dias_atraso"))
        texto = f"{len(self.devolvidos)} livro(s) devolvido(s)"
        if atrasados:
            texto += f" — {atrasados} com atraso, {reais(total_multa)} em multa"
        if self.recusados:
            texto += f" · {self.recusados} não devolvido(s)"
        self.lbl_total.configure(text=texto)

    def _concluir(self):
        if self.devolvidos:
            total_multa = sum((d.get("multa") or 0) for d in self.devolvidos)
            separar = [d for d in self.devolvidos if d.get("reservado_para")]
            resumo = f"{len(self.devolvidos)} livro(s) devolvido(s)."
            if total_multa:
                resumo += f"\nMultas lançadas: {reais(total_multa)}."
            if separar:
                resumo += ("\n\nSeparar da estante (têm fila de espera):\n"
                           + "\n".join(f"• {d['titulo']} — "
                                        f"{d['reservado_para']}"
                                        for d in separar))
            messagebox.showinfo("Devolução concluída", resumo, parent=self)
        if self.ao_fechar:
            self.ao_fechar()
        self.destroy()


# ---------------------------------------------------------------------------
# Diálogo: baixa de um exemplar
# ---------------------------------------------------------------------------
class DialogoBaixaExemplar(tk.Toplevel):
    """Tira um exemplar do acervo, perguntando por quê.

    O motivo não é burocracia: seis meses depois, "extraviado" e
    "descartado por estar desatualizado" levam a decisões diferentes na
    hora de repor a estante.
    """

    def __init__(self, parent, codigo: str, ao_confirmar=None):
        super().__init__(parent)
        self.codigo = codigo
        self.ao_confirmar = ao_confirmar
        self.title("Dar baixa no exemplar")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 520, 340)

        wrap = ttk.Frame(self, padding=20)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Dar baixa no exemplar",
                  style="Titulo.TLabel").pack(anchor="w")

        ex = servicos.localizar_exemplar(codigo)
        titulo = ex["titulo"] if ex else "(exemplar não encontrado)"
        ttk.Label(wrap, text=f"{titulo}\nTombo/código: {codigo}",
                  style="Hint.TLabel", justify="left").pack(anchor="w",
                                                              pady=(4, 16))

        ttk.Label(wrap, text="Por que este exemplar está saindo do acervo?"
                  ).pack(anchor="w")
        self.var_motivo = tk.StringVar(value="EXTRAVIADO")
        for chave, rotulo in servicos.MOTIVOS_BAIXA.items():
            ttk.Radiobutton(wrap, text=rotulo, value=chave,
                            variable=self.var_motivo).pack(anchor="w",
                                                             pady=2)

        self.lbl_aviso = ttk.Label(wrap, text="", style="Hint.TLabel",
                                     wraplength=460, justify="left")
        self.lbl_aviso.pack(anchor="w", pady=(10, 0))
        if ex and ex["status"] == "EMPRESTADO":
            self.lbl_aviso.configure(
                text="Atenção: este exemplar está emprestado. Dar baixa "
                      "encerra o empréstimo e lança a multa de atraso, se "
                      "houver.",
                foreground=tema.COR_AVISO)

        rodape = ttk.Frame(wrap)
        rodape.pack(fill="x", pady=(16, 0))
        ttk.Button(rodape, text="Cancelar",
                    command=self.destroy).pack(side="right")
        ttk.Button(rodape, text="Confirmar baixa", style="Primario.TButton",
                    command=self._confirmar).pack(side="right", padx=(0, 8))

    def _confirmar(self):
        try:
            r = servicos.baixar_exemplar(self.codigo, self.var_motivo.get())
        except RegraNegocioError as e:
            messagebox.showwarning("Não foi possível", str(e), parent=self)
            return
        extra = ""
        if r["estava_emprestado"]:
            extra = "\n\nO empréstimo foi encerrado."
            if r["multa"]:
                extra += f" Multa lançada: {reais(r['multa'])}."
        messagebox.showinfo(
            "Baixa registrada",
            f"'{r['titulo']}' saiu do acervo.{extra}", parent=self)
        if self.ao_confirmar:
            self.ao_confirmar()
        self.destroy()


# ---------------------------------------------------------------------------
# Diálogo: mudar a prateleira de um exemplar
# ---------------------------------------------------------------------------
class DialogoLocalizacaoExemplar(tk.Toplevel):
    """Muda de lugar um exemplar já cadastrado.

    Vale por exemplar, não pelo título: dois volumes do mesmo livro
    podem estar em estantes diferentes, e é o exemplar que a pessoa tem
    na mão quando percebe que ele está no lugar errado.
    """

    def __init__(self, parent, codigo: str, atual: str = "",
                 ao_confirmar=None):
        super().__init__(parent)
        self.codigo = codigo
        self.ao_confirmar = ao_confirmar
        self.title("Mudar prateleira")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 520, 280)

        wrap = ttk.Frame(self, padding=20)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Mudar prateleira",
                  style="Titulo.TLabel").pack(anchor="w")

        ex = servicos.localizar_exemplar(codigo)
        titulo = ex["titulo"] if ex else "(exemplar não encontrado)"
        ttk.Label(wrap, text=f"{titulo}\nTombo/código: {codigo}",
                  style="Hint.TLabel", justify="left"
                  ).pack(anchor="w", pady=(4, 16))

        ttk.Label(wrap, text="Onde este exemplar fica agora?"
                  ).pack(anchor="w")
        self.ent_local = ttk.Entry(wrap, width=48, font=("Segoe UI", 10))
        self.ent_local.insert(0, atual)
        self.ent_local.pack(anchor="w", pady=(4, 2))
        self.ent_local.focus_set()
        ttk.Label(wrap, text="Ex.: Estante A, Prateleira 2. Deixe em branco "
                  "para tirar a localização.",
                  style="Hint.TLabel").pack(anchor="w")
        ttk.Label(wrap, text="A nova prateleira sai impressa na etiqueta "
                  "deste exemplar.",
                  style="Hint.TLabel", wraplength=460, justify="left"
                  ).pack(anchor="w", pady=(8, 0))

        rodape = ttk.Frame(wrap)
        rodape.pack(fill="x", pady=(16, 0))
        ttk.Button(rodape, text="Cancelar",
                    command=self.destroy).pack(side="right")
        ttk.Button(rodape, text="Salvar", style="Primario.TButton",
                    command=self._confirmar).pack(side="right", padx=(0, 8))
        self.ent_local.bind("<Return>", lambda e: self._confirmar())

    def _confirmar(self):
        try:
            servicos.alterar_localizacao_exemplar(
                self.codigo, self.ent_local.get())
        except RegraNegocioError as e:
            messagebox.showwarning("Não foi possível", str(e), parent=self)
            return
        if self.ao_confirmar:
            self.ao_confirmar()
        self.destroy()


class DialogoTomboExemplar(tk.Toplevel):
    """Corrige o número de tombo escrito no livro físico.

    Diferente da prateleira, o tombo não pode repetir: o balcão procura o
    exemplar por código de barras ou tombo, então dois iguais fazem o
    empréstimo pegar a cópia errada. Quem recusa a duplicata é o serviço;
    aqui o aviso só é mostrado.
    """

    def __init__(self, parent, codigo: str, atual: str = "",
                 ao_confirmar=None):
        super().__init__(parent)
        self.codigo = codigo
        self.ao_confirmar = ao_confirmar
        self.title("Corrigir tombo")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 520, 300)

        wrap = ttk.Frame(self, padding=20)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Corrigir tombo",
                  style="Titulo.TLabel").pack(anchor="w")

        ex = servicos.localizar_exemplar(codigo)
        titulo = ex["titulo"] if ex else "(exemplar não encontrado)"
        ttk.Label(wrap, text=f"{titulo}\nCódigo de barras: {codigo}",
                  style="Hint.TLabel", justify="left"
                  ).pack(anchor="w", pady=(4, 16))

        ttk.Label(wrap, text="Qual o número de tombo deste exemplar?"
                  ).pack(anchor="w")
        self.ent_tombo = ttk.Entry(wrap, width=48, font=("Segoe UI", 10))
        self.ent_tombo.insert(0, atual)
        self.ent_tombo.pack(anchor="w", pady=(4, 2))
        self.ent_tombo.focus_set()
        self.ent_tombo.select_range(0, "end")
        ttk.Label(wrap, text="É o número escrito no próprio livro. Deixe em "
                  "branco para tirar o tombo.",
                  style="Hint.TLabel").pack(anchor="w")
        ttk.Label(wrap, text="O tombo não pode se repetir no acervo: o balcão "
                  "acha o exemplar pelo tombo, e dois iguais fazem emprestar "
                  "o livro errado. A nova numeração sai impressa na etiqueta.",
                  style="Hint.TLabel", wraplength=460, justify="left"
                  ).pack(anchor="w", pady=(8, 0))

        rodape = ttk.Frame(wrap)
        rodape.pack(fill="x", pady=(16, 0))
        ttk.Button(rodape, text="Cancelar",
                    command=self.destroy).pack(side="right")
        ttk.Button(rodape, text="Salvar", style="Primario.TButton",
                    command=self._confirmar).pack(side="right", padx=(0, 8))
        self.ent_tombo.bind("<Return>", lambda e: self._confirmar())

    def _confirmar(self):
        try:
            servicos.alterar_tombo_exemplar(self.codigo, self.ent_tombo.get())
        except RegraNegocioError as e:
            messagebox.showwarning("Não foi possível", str(e), parent=self)
            return
        if self.ao_confirmar:
            self.ao_confirmar()
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
            ("ISBN", livro.get("isbn") or "não informado"),
            ("Editora", livro.get("editora_nome") or "não informada"),
            ("Categoria", livro.get("categoria_nome") or "não informada"),
            ("Edição/Ano",
             f"{livro.get('edicao') or '?'} / {livro.get('ano_publicacao') or '?'}"),
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
        self._livro_id = livro_id
        self.tree = tree
        self._preencher_exemplares(livro)
        tree.pack(fill="both", expand=True)

        botoes = ttk.Frame(wrap)
        botoes.pack(fill="x", pady=(12, 0))
        ttk.Button(botoes, text="Imprimir etiquetas (visualizar)",
                   style="Primario.TButton",
                   command=lambda: VisualizadorBarcodes(self, livro)
                   ).pack(side="left")
        ttk.Button(botoes, text="Corrigir tombo",
                   command=self._corrigir_tombo
                   ).pack(side="left", padx=(8, 0))
        ttk.Button(botoes, text="Mudar prateleira",
                   command=self._mudar_localizacao
                   ).pack(side="left", padx=(8, 0))
        ttk.Button(botoes, text="Dar baixa no exemplar",
                   command=self._dar_baixa).pack(side="left", padx=(8, 0))

    def _preencher_exemplares(self, livro: dict):
        for it in self.tree.get_children():
            self.tree.delete(it)
        for ex in livro["exemplares"]:
            situacao = ex["status"]
            if ex["status"] == "BAIXADO" and ex.get("motivo_baixa"):
                # O motivo importa mais que a palavra "baixado": é o que
                # explica, meses depois, por que aquele exemplar sumiu.
                situacao = servicos.MOTIVOS_BAIXA.get(ex["motivo_baixa"],
                                                       ex["motivo_baixa"])
            self.tree.insert("", "end",
                             values=(ex["numero_tombo"], ex["codigo_barras"],
                                     ex.get("localizacao") or "", situacao))

    def _dar_baixa(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um exemplar",
                                  "Escolha na lista o exemplar que vai sair "
                                  "do acervo.", parent=self)
            return
        valores = self.tree.item(sel[0])["values"]
        codigo = str(valores[1])
        DialogoBaixaExemplar(self, codigo, ao_confirmar=self._recarregar)

    def _corrigir_tombo(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um exemplar",
                                  "Escolha na lista o exemplar cujo tombo "
                                  "está errado.", parent=self)
            return
        valores = self.tree.item(sel[0])["values"]
        codigo, atual = str(valores[1]), str(valores[0] or "")
        DialogoTomboExemplar(self, codigo, atual,
                              ao_confirmar=self._recarregar)

    def _mudar_localizacao(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um exemplar",
                                  "Escolha na lista o exemplar que mudou "
                                  "de lugar.", parent=self)
            return
        valores = self.tree.item(sel[0])["values"]
        codigo, atual = str(valores[1]), str(valores[2] or "")
        DialogoLocalizacaoExemplar(self, codigo, atual,
                                    ao_confirmar=self._recarregar)

    def _recarregar(self):
        livro = servicos.detalhes_livro(self._livro_id)
        if livro:
            self._preencher_exemplares(livro)


# ---------------------------------------------------------------------------
# Visualizador de etiquetas de código de barras
# ---------------------------------------------------------------------------
class VisualizadorBarcodes(tk.Toplevel):
    def __init__(self, parent, livro: dict):
        super().__init__(parent)
        self.title(f"Etiquetas - {livro['titulo']}")
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
                text=f"{ex['numero_tombo']} · {livro['titulo']}",
                font=("Segoe UI Semibold", 10))
            barcode_util.desenhar_barras(canvas, ex["codigo_barras"],
                                          x0=20, y0=y + 22, altura=50,
                                          largura_unit=2)
            y += 110

        canvas.configure(scrollregion=(0, 0, 600, y))

        botoes = ttk.Frame(wrap)
        botoes.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Button(botoes, text="Fechar",
                   command=self.destroy).pack(side="right")
        ttk.Button(botoes, text="Imprimir / Salvar PDF (abre no navegador)",
                   style="Primario.TButton",
                   command=lambda: self._imprimir(livro)
                   ).pack(side="right", padx=(0, 8))

    def _imprimir(self, livro: dict):
        """Gera o HTML de etiquetas e abre no navegador para Ctrl+P."""
        import tempfile
        import webbrowser
        from pathlib import Path
        doc = barcode_util.etiquetas_html(livro["titulo"], livro["exemplares"])
        destino = Path(tempfile.gettempdir()) / "sigbef_etiquetas.html"
        destino.write_text(doc, encoding="utf-8")
        webbrowser.open(destino.as_uri())
