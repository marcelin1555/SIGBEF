"""
SIGBEF — Diálogos modais reutilizáveis (cadastro de livro, usuário,
visualização de exemplares e código de barras).
"""
from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
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
        self.tree = tema.criar_tabela(wrap, columns=keys, show="headings",
                                       height=14)
        for key, rotulo, largura_c, ancora in self.COLUNAS:
            self.tree.heading(key, text=rotulo)
            self.tree.column(key, width=largura_c, anchor=ancora)
        tema.empacotar_com_rolagem(self.tree, fill="both", expand=True,
                                   pady=(12, 0))
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
# Diálogo: restaurar uma cópia de segurança
# ---------------------------------------------------------------------------
class DialogoRestaurarBackup(tk.Toplevel):
    """Confirmação em duas camadas, como o resetar — pelo mesmo motivo.

    Restaurar apaga o acervo de hoje e põe outro no lugar. É a segunda
    operação mais destrutiva do sistema e a única que costuma ser feita
    sob pressão, quando algo já deu errado — que é exatamente quando
    ninguém lê caixa de diálogo. Por isso a confirmação é digitada, e
    não um sim/não.

    Os dois lados aparecem com número na frente: o que há hoje e o que
    há no arquivo. Sem isso, "tem certeza?" não dá a ninguém condição de
    decidir — a diferença entre os dois é justamente o que se perde.
    """

    FRASE_CONFIRMACAO = "RESTAURAR"

    def __init__(self, parent, sessao: Sessao, origem: str,
                 ao_restaurar: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        from . import backup

        self.sessao = sessao
        self.origem = origem
        self.ao_restaurar = ao_restaurar
        self.restaurou = False
        self.title("Restaurar backup")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 560, 520)

        self.do_arquivo = backup.conferir(origem)   # pode levantar
        self.hoje = servicos.estatisticas()
        self._construir()

    def _construir(self):
        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Restaurar backup",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap, text=Path(self.origem).name,
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 12))

        quadro = ttk.Frame(wrap, style="Card.TFrame", padding=14)
        quadro.pack(fill="x")
        quadro.columnconfigure(1, weight=1)
        quadro.columnconfigure(2, weight=1)
        cabecalho = ("", "Hoje", "No arquivo")
        linhas = [
            ("Livros", self.hoje["livros"], self.do_arquivo["livros"]),
            ("Exemplares", self.hoje["exemplares"],
             self.do_arquivo["exemplares"]),
            ("Usuários", self.hoje["usuarios"], self.do_arquivo["usuarios"]),
            ("Empréstimos em aberto", self.hoje["emp_abertos"],
             self.do_arquivo["emprestimos_abertos"]),
        ]
        for j, t in enumerate(cabecalho):
            ttk.Label(quadro, text=t, style="Card.TLabel",
                      font=("Segoe UI Semibold", 9)
                      ).grid(row=0, column=j, sticky="w", padx=(0, 16))
        for i, (rotulo, a, b) in enumerate(linhas, start=1):
            ttk.Label(quadro, text=rotulo, style="Card.TLabel"
                      ).grid(row=i, column=0, sticky="w", padx=(0, 16),
                             pady=2)
            for j, valor in ((1, a), (2, b)):
                # O que muda ganha destaque: é a diferença, e não os
                # números em si, que a pessoa precisa enxergar.
                estilo = ("Card.TLabel" if a == b else "CardHint.TLabel")
                lbl = ttk.Label(quadro, text=str(valor), style=estilo)
                if a != b:
                    lbl.configure(foreground=tema.COR_AVISO,
                                  font=("Segoe UI Semibold", 9))
                lbl.grid(row=i, column=j, sticky="w", padx=(0, 16), pady=2)

        ttk.Label(
            wrap,
            text=("Tudo que foi feito depois desse backup se perde — "
                  "empréstimos, devoluções e cadastros. Antes de trocar, "
                  "o sistema guarda uma cópia do banco de hoje na pasta de "
                  "backups, com nome que a limpeza automática não apaga."),
            style="Hint.TLabel", wraplength=500, justify="left"
            ).pack(anchor="w", pady=(14, 4))

        ttk.Label(wrap,
                  text=f'Digite "{self.FRASE_CONFIRMACAO}" para confirmar:',
                  style="Card.TLabel").pack(anchor="w", pady=(14, 4))
        self.ent_confirmacao = ttk.Entry(wrap, width=30,
                                         font=("Segoe UI", 10))
        self.ent_confirmacao.pack(anchor="w")

        self.lbl_msg = ttk.Label(wrap, text="", wraplength=500)
        self.lbl_msg.pack(anchor="w", pady=(10, 0))

        botoes = ttk.Frame(wrap)
        botoes.pack(side="bottom", fill="x", pady=(20, 0))
        ttk.Button(botoes, text="Cancelar",
                   command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Restaurar", style="Perigo.TButton",
                   command=self._confirmar).pack(side="right")
        self.ent_confirmacao.focus_set()

    def _confirmar(self):
        from . import backup
        if self.ent_confirmacao.get().strip().upper() != self.FRASE_CONFIRMACAO:
            self.lbl_msg.configure(
                text='⚠ Digite exatamente "%s" no campo para confirmar.'
                     % self.FRASE_CONFIRMACAO,
                foreground=tema.COR_ERRO)
            return
        try:
            res = backup.restaurar(self.origem, usuario_id=self.sessao.id)
        except backup.BackupInvalido as e:
            messagebox.showerror("Este arquivo não serve", str(e), parent=self)
            return
        except Exception as e:                              # noqa: BLE001
            # A notícia importante não é o erro: é que o banco de hoje
            # continua inteiro, porque `restaurar` confere antes de
            # trocar qualquer coisa.
            messagebox.showerror(
                "Falha ao restaurar",
                "O banco NÃO foi trocado, o acervo de hoje continua como "
                "estava.\n\n%s" % e,
                parent=self)
            return

        self.restaurou = True
        messagebox.showinfo(
            "Backup restaurado",
            "O acervo agora tem %d livros e %d exemplares.\n\n"
            "O banco anterior ficou guardado em:\n%s\n\n"
            "Feche e abra o sistema para todas as telas recarregarem."
            % (res["resumo"]["livros"], res["resumo"]["exemplares"],
               res["salvaguarda"]),
            parent=self)
        if self.ao_restaurar:
            self.ao_restaurar()
        self.destroy()


# ---------------------------------------------------------------------------
# Diálogo: selecionar um título do acervo
# ---------------------------------------------------------------------------
class DialogoSelecionarLivro(DialogoBuscaSelecao):
    """Lista títulos e devolve o id do escolhido em `livro_selecionado`.

    Diferente de `DialogoSelecionarExemplar`, que escolhe uma cópia
    específica: aqui interessa o título, porque quem empresta uma
    coleção não escolhe quais trinta exemplares vão — escolhe o
    livro-texto e diz quantos.
    """

    COLUNAS = [("id", "ID", 60, "center"),
               ("titulo", "Título", 280, "w"),
               ("autores", "Autor(es)", 200, "w"),
               ("disp", "Disponíveis", 90, "center")]
    COLUNA_RETORNO = "id"

    def __init__(self, parent):
        super().__init__(
            parent, "Selecionar livro",
            "Busque pelo título, autor ou ISBN. A coluna “Disponíveis” "
            "diz quantos exemplares podem sair agora.",
            "Usar livro selecionado", largura=760, altura=500)

    def buscar(self, termo: str) -> list[dict]:
        return servicos.listar_livros(termo, limite=200)

    def linha(self, liv: dict) -> tuple:
        return (liv["id"], liv["titulo"], liv.get("autores") or "",
                liv["disponiveis"])

    @property
    def livro_selecionado(self) -> str:
        return self.selecionado


# ---------------------------------------------------------------------------
# Diálogo: empréstimo de coleção para a turma
# ---------------------------------------------------------------------------
class DialogoEmprestimoColecao(tk.Toplevel):
    """Livro-texto para a turma inteira, num registro só.

    A tela pede três coisas e nada mais: qual livro, para qual professor
    e para qual turma. A quantidade vem junto porque é o que distingue
    esta saída de um empréstimo comum.

    O aviso de quantos exemplares existem fica visível ANTES de
    confirmar. Pedir trinta e descobrir que só há vinte e dois é o erro
    mais provável aqui, e descobrir isso por mensagem de recusa depois
    de digitar tudo é pior do que ver o número o tempo todo.
    """

    def __init__(self, parent, sessao: Sessao,
                 ao_salvar: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.sessao = sessao
        self.ao_salvar = ao_salvar
        self.livro_id: Optional[int] = None
        self.title("Emprestar coleção")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 620, 430)

        wrap = ttk.Frame(self, padding=24)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Emprestar coleção",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(
            wrap,
            text=("Vários exemplares do mesmo livro para uma turma, no nome "
                  "do professor. Sai como um registro só e volta de uma vez."),
            style="Hint.TLabel", wraplength=560).pack(anchor="w", pady=(2, 16))

        form = ttk.Frame(wrap)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Livro:").grid(row=0, column=0, sticky="e",
                                            padx=(0, 8), pady=4)
        # `wraplength` porque o texto e longo por natureza: titulo do
        # livro mais a contagem de disponiveis. Sem ele a linha corria
        # por baixo do botao "Selecionar..." e o numero de exemplares --
        # justamente o que evita pedir mais do que existe -- ficava
        # escondido.
        self.lbl_livro = ttk.Label(form, text="(nenhum escolhido)",
                                   style="Hint.TLabel", wraplength=300,
                                   justify="left")
        self.lbl_livro.grid(row=0, column=1, sticky="w", pady=4)
        ttk.Button(form, text="Selecionar...",
                   command=self._escolher_livro
                   ).grid(row=0, column=2, sticky="e", padx=(8, 0), pady=4)

        ttk.Label(form, text="Professor (matrícula):"
                  ).grid(row=1, column=0, sticky="e", padx=(0, 8), pady=4)
        self.ent_prof = ttk.Entry(form)
        self.ent_prof.grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(form, text="Selecionar...",
                   command=self._escolher_professor
                   ).grid(row=1, column=2, sticky="e", padx=(8, 0), pady=4)

        ttk.Label(form, text="Turma:").grid(row=2, column=0, sticky="e",
                                            padx=(0, 8), pady=4)
        self.ent_turma = ttk.Entry(form)
        self.ent_turma.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Quantos exemplares:"
                  ).grid(row=3, column=0, sticky="e", padx=(0, 8), pady=4)
        self.ent_qtd = ttk.Entry(form, width=8)
        self.ent_qtd.grid(row=3, column=1, sticky="w", pady=4)

        self.lbl_msg = ttk.Label(wrap, text="", wraplength=560)
        self.lbl_msg.pack(anchor="w", pady=(14, 0))

        botoes = ttk.Frame(wrap)
        botoes.pack(side="bottom", fill="x", pady=(16, 0))
        ttk.Button(botoes, text="Cancelar",
                   command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Emprestar coleção",
                   style="Primario.TButton",
                   command=self._salvar).pack(side="right")

        self.ent_turma.focus_set()

    def _escolher_livro(self):
        d = DialogoSelecionarLivro(self)
        self.wait_window(d)
        if not d.livro_selecionado:
            return
        self.livro_id = int(d.livro_selecionado)
        liv = servicos.detalhes_livro(self.livro_id)
        livres = sum(1 for ex in liv["exemplares"]
                     if ex["status"] == "DISPONIVEL")
        self.lbl_livro.configure(
            text="%s — %d disponível(is) agora" % (liv["titulo"], livres))
        if not self.ent_qtd.get().strip():
            self.ent_qtd.insert(0, str(livres))

    def _escolher_professor(self):
        d = DialogoSelecionarUsuario(self)
        self.wait_window(d)
        if d.matricula_selecionada:
            self.ent_prof.delete(0, "end")
            self.ent_prof.insert(0, d.matricula_selecionada)

    def _salvar(self):
        if self.livro_id is None:
            self.lbl_msg.configure(text="⚠ Escolha o livro primeiro.",
                                   foreground=tema.COR_ERRO)
            return
        try:
            res = servicos.emprestar_colecao(
                livro_id=self.livro_id,
                matricula_professor=self.ent_prof.get(),
                quantidade=self.ent_qtd.get(),
                turma=self.ent_turma.get(),
                operador_id=self.sessao.id)
        except RegraNegocioError as e:
            self.lbl_msg.configure(text="⚠ %s" % e, foreground=tema.COR_ERRO)
            return

        messagebox.showinfo(
            "Coleção emprestada",
            "%d exemplares de “%s” saíram para a turma %s, no nome de %s.\n\n"
            "Devolução prevista: %s (%d dias)."
            % (res["quantidade"], res["titulo"], res["turma"],
               res["professor"], data_br(res["data_prevista"]),
               res["prazo_dias"]),
            parent=self)
        if self.ao_salvar:
            self.ao_salvar()
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
        # Duas colunas de campos (ver _construir) cabem numa janela bem
        # mais baixa que a versão anterior, de 790 px — que em tela de
        # laboratório escolar (comum em 768 px de altura) nascia com o
        # rodapé, onde ficam os botões, fora da área visível.
        tema.centralizar_janela(self, 660, 600)

        self._construir()

    def _construir(self):
        wrap = ttk.Frame(self, padding=(24, 20, 24, 16))
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Cadastrar livro",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(wrap, text="Preencha os dados do livro e a quantidade "
                  "de exemplares iniciais.",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 12))

        # Botões primeiro (side="bottom"), pra reservar o rodapé antes do
        # scroll ocupar o resto — assim Salvar/Cancelar nunca ficam
        # escondidos atrás do conteúdo, nem em tela pequena.
        botoes = ttk.Frame(wrap)
        botoes.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Button(botoes, text="Cancelar", command=self.destroy
                   ).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Salvar livro",
                   style="Primario.TButton",
                   command=self._salvar).pack(side="right")

        # Área com rolagem: mesmo padrão de SecaoConfig. Com o formulário
        # já compacto isso raramente aciona, mas é rede de segurança pra
        # telas ainda menores ou campos futuros.
        canvas = tk.Canvas(wrap, bg=tema.COR_FUNDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrap, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        form = ttk.Frame(canvas)
        inner_window = canvas.create_window((0, 0), window=form, anchor="nw")

        def _on_canvas_configure(e):
            canvas.itemconfig(inner_window, width=e.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_form_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        form.bind("<Configure>", _on_form_configure)

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<Enter>",
                    lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        def campo(chave, rotulo, linha, coluna=0, largura=26, **kw):
            col_rotulo, col_campo = (0, 1) if coluna == 0 else (2, 3)
            padx = (0, 8) if coluna == 0 else (16, 0)
            ttk.Label(form, text=rotulo).grid(
                row=linha, column=col_rotulo, sticky="w",
                pady=(8, 2), padx=padx)
            ent = ttk.Entry(form, width=largura, font=("Segoe UI", 10), **kw)
            ent.grid(row=linha, column=col_campo, sticky="ew", pady=(8, 2))
            self._campos[chave] = ent
            return ent

        self._campos = {}

        # Título e autores seguem em linha inteira: costumam ser o campo
        # mais longo do formulário, e partir eles em coluna estreita
        # atrapalharia mais do que ajudaria.
        ttk.Label(form, text="Título *").grid(
            row=0, column=0, sticky="w", pady=(8, 2))
        ent_titulo = ttk.Entry(form, font=("Segoe UI", 10))
        ent_titulo.grid(row=0, column=1, columnspan=3, sticky="ew",
                        pady=(8, 2))
        self._campos["titulo"] = ent_titulo

        ttk.Label(form, text="Autor(es) *  (separe por ;)").grid(
            row=1, column=0, sticky="w", pady=(8, 2))
        ent_autores = ttk.Entry(form, font=("Segoe UI", 10))
        ent_autores.grid(row=1, column=1, columnspan=3, sticky="ew",
                         pady=(8, 2))
        self._campos["autores"] = ent_autores

        ttk.Label(form, text="ISBN").grid(
            row=2, column=0, sticky="w", pady=(8, 2))
        ent_isbn = ttk.Entry(form, font=("Segoe UI", 10))
        ent_isbn.grid(row=2, column=1, sticky="ew", pady=(8, 2),
                      columnspan=1 if servicos.isbn_lookup_ativo() else 3)
        self._campos["isbn"] = ent_isbn
        if servicos.isbn_lookup_ativo():
            ttk.Button(form, text="Buscar online",
                       command=self._buscar_isbn).grid(
                           row=2, column=2, columnspan=2, sticky="w",
                           padx=(8, 0), pady=(8, 2))

        campo("editora", "Editora", 3, coluna=0)
        campo("categoria", "Categoria", 3, coluna=1)
        campo("ano", "Ano de publicação", 4, coluna=0)
        campo("edicao", "Edição", 4, coluna=1)
        campo("localizacao", "Localização", 5, coluna=0)

        ttk.Label(form, text="Quantidade de exemplares *").grid(
            row=5, column=2, sticky="w", pady=(8, 2), padx=(16, 0))
        self.spin_qtd = tk.Spinbox(form, from_=1, to=50, width=6,
                                   font=("Segoe UI", 10))
        self.spin_qtd.delete(0, "end")
        self.spin_qtd.insert(0, "1")
        self.spin_qtd.grid(row=5, column=3, sticky="w", pady=(8, 2))

        # O livro físico costuma chegar com o tombo já escrito. Deixar em
        # branco mantém o comportamento antigo: o sistema gera o número.
        ttk.Label(form, text="Tombo(s)").grid(
            row=6, column=0, sticky="w", pady=(8, 2))
        self.ent_tombos = ttk.Entry(form, font=("Segoe UI", 10))
        self.ent_tombos.grid(row=6, column=1, columnspan=3, sticky="ew",
                             pady=(8, 2))
        ttk.Label(form, style="Hint.TLabel",
                  text="Opcional — em branco, o sistema gera. Vários "
                       "exemplares: separe por ;").grid(
            row=7, column=1, columnspan=3, sticky="w")

        ttk.Label(form, text="Sinopse").grid(row=8, column=0, sticky="nw",
                                              pady=(8, 2))
        self.txt_sinopse = tk.Text(form, height=3, font=("Segoe UI", 10))
        self.txt_sinopse.grid(row=8, column=1, columnspan=3, sticky="ew",
                              pady=(8, 2))

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
            # Aceita ; ou / como na importação CSV, para quem já está
            # acostumado com o formato da planilha
            tombos = [t.strip() for t in re.split(
                r"[;/]", self.ent_tombos.get()) if t.strip()]
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
                tombos=tombos,
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
        tema.gravar_arquivo(
            self, destino, lambda: servicos.gerar_modelo_csv(destino),
            titulo_ok="Modelo salvo",
            mensagem_ok="Planilha modelo salva. Preencha no Excel e "
                        "salve como CSV para importar.")

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
        self.tree = tema.criar_tabela(wrap, columns=cols, show="headings",
                                       height=13)
        for c, t, w in [("titulo", "Título", 300), ("quem", "Estava com", 190),
                        ("atraso", "Atraso", 90), ("multa", "Multa", 100)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("atrasado", background="#FDECEA",
                                 foreground=tema.COR_ERRO)
        tema.empacotar_com_rolagem(self.tree, fill="both", expand=True,
                                   pady=(10, 0))

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

    def __init__(self, parent, codigo: str, sessao=None, ao_confirmar=None):
        super().__init__(parent)
        self.codigo = codigo
        self.sessao = sessao
        self.ao_confirmar = ao_confirmar
        self.title("Dar baixa no exemplar")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 520, 430)

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

        # O tombo do exemplar baixado continua ocupado, de propósito: se
        # ele liberasse sozinho, dois exemplares (o baixado e o novo)
        # ficariam com o mesmo número por um instante, e é exatamente
        # essa dupla que faz o balcão emprestar a cópia errada em
        # silêncio. Aqui é o oposto: ação explícita, e só depois que a
        # baixa em si já foi confirmada.
        self._tombo_atual = ex.get("numero_tombo") if ex else None
        self.var_liberar_tombo = tk.BooleanVar(value=False)
        if self._tombo_atual:
            ttk.Checkbutton(
                wrap,
                text=f'Liberar o tombo "{self._tombo_atual}" para usar em '
                     "outro exemplar",
                variable=self.var_liberar_tombo,
            ).pack(anchor="w", pady=(12, 0))

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
        usuario_id = self.sessao.id if self.sessao else None
        try:
            r = servicos.baixar_exemplar(self.codigo, self.var_motivo.get(),
                                         usuario_id=usuario_id)
        except RegraNegocioError as e:
            messagebox.showwarning("Não foi possível", str(e), parent=self)
            return
        extra = ""
        if r["estava_emprestado"]:
            extra = "\n\nO empréstimo foi encerrado."
            if r["multa"]:
                extra += f" Multa lançada: {reais(r['multa'])}."
        if self.var_liberar_tombo.get() and self._tombo_atual:
            try:
                servicos.alterar_tombo_exemplar(self.codigo, "",
                                                usuario_id=usuario_id)
                extra += (f'\n\nO tombo "{self._tombo_atual}" foi liberado '
                          "e já pode ser usado em outro exemplar.")
            except RegraNegocioError as e:
                # A baixa em si já foi feita; isto é só um passo a mais
                # que falhou, então avisa em vez de derrubar a operação
                # que já teve sucesso.
                extra += (f"\n\nA baixa foi registrada, mas não foi "
                          f"possível liberar o tombo: {e}")
        messagebox.showinfo(
            "Baixa registrada",
            f"'{r['titulo']}' saiu do acervo.{extra}", parent=self)
        if self.ao_confirmar:
            self.ao_confirmar()
        self.destroy()


# ---------------------------------------------------------------------------
# Diálogo: reverter uma baixa dada por engano
# ---------------------------------------------------------------------------
class DialogoReverterBaixa(tk.Toplevel):
    """Devolve ao acervo um exemplar baixado por engano.

    Nasceu de um caso real: "Dar baixa no exemplar" fica ao lado de
    "Corrigir tombo" e "Mudar prateleira", e a bibliotecária clicou no
    errado. Não havia volta — e a baixa não é só o exemplar, ela encerra
    o empréstimo e lança a multa de quem está com o livro.

    A tela diz **o que vai voltar** antes de perguntar qualquer coisa. É
    o contrário da que causou o problema, onde o efeito só apareceu
    depois.
    """

    def __init__(self, parent, codigo: str, sessao=None, ao_confirmar=None):
        super().__init__(parent)
        self.codigo = codigo
        self.sessao = sessao
        self.ao_confirmar = ao_confirmar
        self.title("Reverter baixa")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        tema.centralizar_janela(self, 560, 460)

        ex = servicos.localizar_exemplar(codigo)
        self.candidato = servicos.candidato_de_reabertura(codigo)

        wrap = ttk.Frame(self, padding=20)
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="Reverter baixa",
                  style="Titulo.TLabel").pack(anchor="w")
        titulo = ex["titulo"] if ex else "(exemplar não encontrado)"
        ttk.Label(wrap, text=f"{titulo}\nTombo/código: {codigo}",
                  style="Hint.TLabel", justify="left").pack(anchor="w",
                                                            pady=(4, 14))

        ttk.Label(wrap, text="O que volta:", style="Card.TLabel",
                  font=("Segoe UI Semibold", 10)).pack(anchor="w")
        volta = ["• O exemplar volta para o acervo"]
        if self.candidato:
            volta.append(
                "• O empréstimo de %s (matrícula %s) reabre, e a multa "
                "lançada pela baixa é apagada"
                % (self.candidato["nome"], self.candidato["matricula"]))
        else:
            volta.append(
                "• O empréstimo encerrado pela baixa, se houver, reabre — "
                "e a multa que ela lançou é apagada")
        volta.append(
            "• Quem perdeu a reserva porque o exemplar saiu volta para a "
            "fila, na mesma posição")
        ttk.Label(wrap, text="\n".join(volta), style="Hint.TLabel",
                  justify="left", wraplength=500).pack(anchor="w",
                                                       pady=(4, 12))

        # O caso das baixas antigas: o sistema não sabe qual empréstimo a
        # baixa encerrou e não pode adivinhar — livro devolvido
        # normalmente e baixado no mesmo dia casaria pela data também.
        self.var_reabrir = tk.BooleanVar(value=False)
        if self.candidato:
            ttk.Label(
                wrap,
                text=("Esta baixa é anterior à versão que registra qual "
                      "empréstimo foi encerrado. O de baixo é o que bate "
                      "com a data — confirme só se for mesmo ele:"),
                style="Hint.TLabel", wraplength=500, justify="left"
                ).pack(anchor="w")
            ttk.Checkbutton(
                wrap,
                text="Reabrir o empréstimo de %s, de %s"
                     % (self.candidato["nome"],
                        data_br(self.candidato["data_emprestimo"][:10])),
                variable=self.var_reabrir).pack(anchor="w", pady=(4, 12))

        ttk.Label(wrap, text="Por que a baixa está sendo revertida?"
                  ).pack(anchor="w")
        self.ent_justificativa = ttk.Entry(wrap)
        self.ent_justificativa.pack(fill="x", pady=(4, 0))
        ttk.Label(wrap, text="Fica no histórico do exemplar.",
                  style="Hint.TLabel").pack(anchor="w", pady=(2, 0))

        self.lbl_msg = ttk.Label(wrap, text="", wraplength=500)
        self.lbl_msg.pack(anchor="w", pady=(10, 0))

        rodape = ttk.Frame(wrap)
        rodape.pack(side="bottom", fill="x", pady=(16, 0))
        ttk.Button(rodape, text="Cancelar",
                   command=self.destroy).pack(side="right")
        ttk.Button(rodape, text="Reverter baixa", style="Primario.TButton",
                   command=self._confirmar).pack(side="right", padx=(0, 8))
        self.ent_justificativa.focus_set()

    def _confirmar(self):
        reabrir = (self.candidato["id"]
                   if self.candidato and self.var_reabrir.get() else None)
        try:
            r = servicos.reverter_baixa(
                self.codigo, self.ent_justificativa.get(),
                usuario_id=self.sessao.id if self.sessao else None,
                reabrir_emprestimo_id=reabrir)
        except RegraNegocioError as e:
            self.lbl_msg.configure(text="⚠ %s" % e, foreground=tema.COR_ERRO)
            return

        partes = ["“%s” voltou para o acervo." % r["titulo"]]
        if r["emprestimo_reaberto"]:
            partes.append("O empréstimo foi reaberto — o livro continua "
                          "com quem estava.")
            if r["multa_apagada"]:
                partes.append("A multa de %s, lançada pela baixa, foi "
                              "apagada." % reais(r["multa_apagada"]))
        if r["reservas_restauradas"]:
            partes.append("%d reserva(s) voltaram para a fila."
                          % r["reservas_restauradas"])
        if r["reserva_atendida"]:
            partes.append("O exemplar foi separado para %s, que estava "
                          "esperando." % r["reserva_atendida"]["nome"])
        if not r["tombo"]:
            partes.append("Atenção: este exemplar está sem tombo — ele foi "
                          "liberado na baixa. Use “Corrigir tombo” para "
                          "dar um número a ele.")
        messagebox.showinfo("Baixa revertida", "\n\n".join(partes),
                            parent=self)
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
                 sessao=None, ao_confirmar=None):
        super().__init__(parent)
        self.codigo = codigo
        self.sessao = sessao
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
                self.codigo, self.ent_local.get(),
                usuario_id=self.sessao.id if self.sessao else None)
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
                 sessao=None, ao_confirmar=None):
        super().__init__(parent)
        self.codigo = codigo
        self.sessao = sessao
        self.ao_confirmar = ao_confirmar
        self.title("Corrigir tombo")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        # 430, medido: com o botão de liberar o tombo e a explicação
        # dele o conteúdo pede 413 px, e a altura antiga (300) cortava
        # fora Salvar e Cancelar.
        tema.centralizar_janela(self, 520, 430)

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
        ttk.Label(wrap, text="É o número escrito no próprio livro.",
                  style="Hint.TLabel").pack(anchor="w")
        # O caminho para reaproveitar um número.
        #
        # Apagar o campo sempre liberou o tombo, mas isso estava dito
        # como "deixe em branco para tirar o tombo", em letra de apoio —
        # e ninguém liga "tirar" com "usar em outro exemplar". A
        # bibliotecária acabou dando baixa no exemplar tentando
        # conseguir isso, que tira o livro do acervo e nem sequer
        # libera o número.
        ttk.Button(wrap, text="Liberar este tombo para outro exemplar",
                   command=self._liberar).pack(anchor="w", pady=(8, 0))
        ttk.Label(wrap, text="O exemplar continua no acervo, só fica sem "
                  "número até você dar outro a ele.",
                  style="Hint.TLabel").pack(anchor="w")
        ttk.Label(wrap, text="O tombo não pode se repetir no acervo: o balcão "
                  "acha o exemplar pelo tombo, e dois iguais fazem emprestar "
                  "o livro errado. A nova numeração sai impressa na etiqueta.",
                  style="Hint.TLabel", wraplength=460, justify="left"
                  ).pack(anchor="w", pady=(8, 0))

        # `side="bottom"`: o rodapé reserva o lugar dele antes que o
        # texto de apoio acima cresça. Sem isso, Salvar e Cancelar
        # ficavam com poucos pixels de altura — dava para ver a cor dos
        # botões e nada mais.
        rodape = ttk.Frame(wrap)
        rodape.pack(side="bottom", fill="x", pady=(16, 0))
        ttk.Button(rodape, text="Cancelar",
                    command=self.destroy).pack(side="right")
        ttk.Button(rodape, text="Salvar", style="Primario.TButton",
                    command=self._confirmar).pack(side="right", padx=(0, 8))
        self.ent_tombo.bind("<Return>", lambda e: self._confirmar())

    def _liberar(self):
        """Esvazia o campo. Confirmar em seguida solta o número."""
        self.ent_tombo.delete(0, "end")
        self.ent_tombo.focus_set()

    def _confirmar(self):
        try:
            servicos.alterar_tombo_exemplar(
                self.codigo, self.ent_tombo.get(),
                usuario_id=self.sessao.id if self.sessao else None)
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
    def __init__(self, parent, livro_id: int,
                 ao_mudar: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        # Este diálogo não só mostra: dá baixa, corrige tombo e muda
        # prateleira. Sem avisar quem o abriu, a lista do acervo atrás
        # continuava exibindo o exemplar recém-baixado até a tela ser
        # recarregada na mão — e a bibliotecária procurava na prateleira
        # um livro que o próprio sistema já sabia que não existia mais.
        self.ao_mudar = ao_mudar
        # parent é o PainelPrincipal: sempre tem sessao. As três ações
        # de exemplar abaixo (baixa, tombo, prateleira) usam isso para
        # atribuir a ação certa na auditoria, em vez de "Sistema".
        self.sessao = getattr(parent, "sessao", None)
        self.title("Detalhes do livro")
        self.transient(parent)
        self.grab_set()
        self.configure(bg=tema.COR_FUNDO)
        # 800, e nao 720: os quatro botoes do rodape pedem 736 px e a
        # largura antiga dava 672, entao "Dar baixa no exemplar" ficava
        # cortado pela borda. `centralizar_janela` reduz sozinha se a
        # tela for menor que isso.
        tema.centralizar_janela(self, 800, 640)

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
        tree = tema.criar_tabela(wrap, columns=cols, show="headings", height=8)
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
        # As ações em DUAS faixas, e as faixas antes da tabela.
        #
        # Duas coisas foram consertadas aqui de uma vez.
        #
        # A primeira é o de sempre: `pack` reparte na ordem em que é
        # chamado, e a tabela com `expand=True` deixava a faixa de
        # botões com poucos pixels de altura — dava para ver a cor de
        # cada botão e nada mais.
        #
        # A segunda é a que causou o estrago real. "Dar baixa no
        # exemplar" ficava encostado em "Corrigir tombo" e "Mudar
        # prateleira", com a mesma cara, e a bibliotecária clicou no
        # errado: o exemplar saiu do acervo, o empréstimo foi encerrado
        # e a multa foi lançada num aluno que não devia nada. Agora o
        # que **corrige** fica numa linha e o que **tira do acervo**
        # fica em outra, com cor de perigo.
        acoes_acervo = ttk.Frame(wrap)
        acoes_acervo.pack(side="bottom", fill="x", pady=(8, 0))
        ttk.Button(acoes_acervo, text="Dar baixa no exemplar",
                   style="Perigo.TButton",
                   command=self._dar_baixa).pack(side="left")
        ttk.Button(acoes_acervo, text="Reverter baixa",
                   command=self._reverter_baixa).pack(side="left",
                                                      padx=(8, 0))
        ttk.Label(acoes_acervo,
                  text="Tira ou devolve o exemplar ao acervo.",
                  style="Hint.TLabel").pack(side="left", padx=(12, 0))

        correcoes = ttk.Frame(wrap)
        correcoes.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Button(correcoes, text="Imprimir etiquetas (visualizar)",
                   style="Primario.TButton",
                   command=lambda: VisualizadorBarcodes(self, livro)
                   ).pack(side="left")
        ttk.Button(correcoes, text="Corrigir tombo",
                   command=self._corrigir_tombo
                   ).pack(side="left", padx=(8, 0))
        ttk.Button(correcoes, text="Mudar prateleira",
                   command=self._mudar_localizacao
                   ).pack(side="left", padx=(8, 0))

        tema.empacotar_com_rolagem(tree, fill="both", expand=True)

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
        DialogoBaixaExemplar(self, codigo, sessao=self.sessao,
                             ao_confirmar=self._recarregar)

    def _reverter_baixa(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um exemplar",
                                  "Escolha na lista o exemplar que foi "
                                  "baixado por engano.", parent=self)
            return
        valores = self.tree.item(sel[0])["values"]
        codigo = str(valores[1])
        ex = servicos.localizar_exemplar(codigo)
        if not ex or ex["status"] != "BAIXADO":
            messagebox.showinfo(
                "Este exemplar está no acervo",
                "Só dá para reverter a baixa de um exemplar que saiu do "
                "acervo. A situação dele aparece na última coluna.",
                parent=self)
            return
        DialogoReverterBaixa(self, codigo, sessao=self.sessao,
                             ao_confirmar=self._recarregar)

    def _corrigir_tombo(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um exemplar",
                                  "Escolha na lista o exemplar cujo tombo "
                                  "está errado.", parent=self)
            return
        valores = self.tree.item(sel[0])["values"]
        codigo, atual = str(valores[1]), str(valores[0] or "")
        DialogoTomboExemplar(self, codigo, atual, sessao=self.sessao,
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
        DialogoLocalizacaoExemplar(self, codigo, atual, sessao=self.sessao,
                                    ao_confirmar=self._recarregar)

    def _recarregar(self):
        livro = servicos.detalhes_livro(self._livro_id)
        if livro:
            self._preencher_exemplares(livro)
        # Ponto único por onde passam as três ações que mexem no acervo,
        # e por isso o lugar certo para avisar a tela de trás.
        if self.ao_mudar:
            self.ao_mudar()


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
