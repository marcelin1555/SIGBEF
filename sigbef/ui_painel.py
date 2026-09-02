"""
SIGBEF — Painel principal (administrador, bibliotecário e usuários comuns).

Janela única com sidebar e área de conteúdo trocável. Cada perfil enxerga
um conjunto de abas adequado às suas permissões.
"""
from __future__ import annotations

import csv
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import ttk, messagebox, filedialog, simpledialog

from . import barcode_util
from . import icones
from . import servicos
from . import ui_graficos as graficos
from . import ui_tema as tema
from .auth import Sessao
from .formato import data_br, data_hora_br, reais
from .servicos import RegraNegocioError
from .ui_dialogos import (
    DialogoDetalhesLivro,
    DialogoDevolucaoEmLote,
    DialogoEditarLivro,
    DialogoEditarUsuario,
    DialogoImportarCSV,
    DialogoLivro,
    DialogoResetarSistema,
    DialogoSelecionarExemplar,
    DialogoSelecionarUsuario,
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
        icones.aplicar_icone_janela(self)
        tema.centralizar_janela(self, 1280, 780, minimo=(1180, 700))

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
        tk.Label(cabecalho, bg=tema.COR_PRIMARIA,
                 image=icones.icone("logoplaca", "original", 36)
                 ).pack(side="left", padx=(16, 0))
        tk.Label(cabecalho, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text="SIGBEF", font=("Segoe UI Semibold", 18)
                 ).pack(side="left", padx=12)
        tk.Label(cabecalho, bg=tema.COR_PRIMARIA, fg=tema.COR_PRIMARIA_SUAVE,
                 text="Sistema Integrado de Gestão da Biblioteca",
                 font=("Segoe UI", 11)).pack(side="left")

        info_user = tk.Frame(cabecalho, bg=tema.COR_PRIMARIA)
        info_user.pack(side="right", padx=20)

        # Brasão da instituição no cabeçalho, quando configurado
        img_brasao = icones.brasao(max_altura=40)
        if img_brasao is not None:
            tk.Label(cabecalho, bg=tema.COR_PRIMARIA, image=img_brasao
                     ).pack(side="right", padx=(0, 4))
        tk.Label(info_user, bg=tema.COR_PRIMARIA, fg=tema.COR_TEXTO_CLARO,
                 text=self.sessao.nome,
                 font=("Segoe UI Semibold", 10)).pack(anchor="e")
        tk.Label(info_user, bg=tema.COR_PRIMARIA, fg=tema.COR_PRIMARIA_SUAVE,
                 text=f"{self.sessao.perfil.title()} • matrícula {self.sessao.matricula}",
                 font=("Segoe UI", 9)).pack(anchor="e")
        ttk.Button(cabecalho, text="Sair",
                   image=icones.icone("sair"), compound="left",
                   command=self._sair).pack(side="right", padx=(0, 12))

        # Corpo (sidebar + área principal)
        corpo = tk.Frame(self, bg=tema.COR_FUNDO)
        corpo.pack(fill="both", expand=True)

        # 240 cortava a letra final de "Empréstimos abertos" (o rótulo
        # mais largo da sidebar) em telas com escala do Windows acima de
        # 100%, porque o Tk não redimensiona frames de largura fixa
        # junto com a fonte.
        sidebar = tk.Frame(corpo, bg=tema.COR_PRIMARIA, width=264)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        principal = ttk.Frame(corpo, padding=24)
        principal.pack(side="right", fill="both", expand=True)

        # Itens da sidebar (filtrados por perfil): chave, rótulo, ícone
        itens = [("painel", "Painel inicial", "home")]
        if self.sessao.is_bibliotecario:
            itens += [
                ("livros", "Livros e exemplares", "livro"),
                ("usuarios", "Usuários", "usuarios"),
                ("emprestimos", "Empréstimos abertos", "troca"),
                ("reservas", "Fila de espera", "leitor"),
                ("uso", "Uso do acervo", "grafico"),
                ("inventario", "Conferir acervo", "busca"),
                ("relatorios", "Relatórios", "grafico"),
                ("auditoria", "Auditoria", "relogio"),
            ]
        if self.sessao.is_admin:
            itens.append(("config", "Configurações", "engrenagem"))

        # Para alunos/professores, mostrar apenas pesquisa e meus empréstimos
        if not self.sessao.is_bibliotecario:
            itens = [("painel", "Painel inicial", "home"),
                     ("pesquisa_aluno", "Pesquisar livros", "busca"),
                     ("meus_emp", "Meus empréstimos", "leitor")]

        for chave, rotulo, nome_icone in itens:
            btn = ttk.Button(sidebar, text=" " + rotulo,
                              image=icones.icone(nome_icone),
                              compound="left",
                              style="Sidebar.TButton",
                              command=lambda k=chave: self._mostrar_secao(k))
            btn.pack(fill="x")
            self._botoes_lateral[chave] = btn

        # Construir frames das seções
        self._principal = principal
        for chave, _rotulo, _icone in itens:
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
        elif chave == "reservas":
            self._secoes[chave] = SecaoReservas(self._principal, self)
        elif chave == "uso":
            self._secoes[chave] = SecaoUso(self._principal, self)
        elif chave == "inventario":
            self._secoes[chave] = SecaoInventario(self._principal, self)
        elif chave == "relatorios":
            self._secoes[chave] = SecaoRelatorios(self._principal, self)
        elif chave == "auditoria":
            self._secoes[chave] = SecaoAuditoria(self._principal, self)
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
            self._backup_ao_sair()
            self.destroy()

    def _backup_ao_sair(self):
        """Cópia de segurança do dia, na saída.

        É o momento certo: o movimento do dia já aconteceu e ninguém
        está esperando a tela responder. `executar_se_necessario` não
        levanta exceção e pula se já houve cópia hoje, então isto não
        atrasa nem trava o fechamento.
        """
        from . import backup
        caminho = backup.executar_se_necessario(self.sessao.id)
        if caminho:
            self.title(f"SIGBEF — salvando cópia de segurança…")
            self.update_idletasks()


# Quantos livros a lista carrega por vez. 500 preenche a tela com folga
# e insere em poucos centésimos de segundo; o acervo inteiro de uma vez
# travava a janela por segundos, porque o Treeview insere linha a linha
# na mesma thread que desenha.
LIVROS_POR_BLOCO = 500


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
        for i, (chave, titulo, nome_icone, cor_icone) in enumerate([
            ("livros", "Títulos no acervo", "livro", "cinza"),
            ("exemplares", "Exemplares totais", "barcode", "cinza"),
            ("disponiveis", "Disponíveis agora", "check", "verde"),
            ("emp_abertos", "Empréstimos abertos", "troca", "cinza"),
            ("atrasados", "Em atraso", "alerta", "vermelho"),
            ("usuarios", "Usuários ativos", "usuarios", "cinza"),
        ]):
            card = ttk.Frame(self._cards_frame, style="Card.TFrame",
                              padding=20)
            card.grid(row=i // 3, column=i % 3, sticky="ew",
                       padx=8, pady=8, ipadx=4)
            self._cards_frame.columnconfigure(i % 3, weight=1)
            ttk.Label(card, text=" " + titulo,
                      image=icones.icone(nome_icone, cor_icone, 20),
                      compound="left",
                      style="CardHint.TLabel").pack(anchor="w")
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

        # Os botões ficam numa faixa própria, abaixo do título.
        #
        # Eram seis, na mesma linha do título. Somados, passavam da
        # largura útil, e o último empacotado — "Importar CSV" — era
        # espremido até desaparecer, sobrando só uma lasca azul colada no
        # título. A função existia e não tinha como ser alcançada.
        topo = ttk.Frame(self)
        topo.pack(fill="x", pady=(10, 0))
        ttk.Button(topo, text=" Cadastrar livro",
                    image=icones.icone("mais", "branco", 14),
                    compound="left",
                    style="Primario.TButton",
                    command=self._novo_livro
                    ).pack(side="right")
        ttk.Button(topo, text="Ver detalhes / código de barras",
                    command=self._detalhes
                    ).pack(side="right", padx=(0, 8))
        ttk.Button(topo, text="Editar",
                    command=self._editar
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
        self.ent_busca = ttk.Entry(filtros, width=32)
        self.ent_busca.pack(side="left", padx=8)
        self.ent_busca.bind("<Return>", lambda e: self.atualizar())
        ttk.Label(filtros, text="Categoria:").pack(side="left")
        self.cbo_categoria = ttk.Combobox(filtros, width=18, state="readonly")
        self.cbo_categoria.pack(side="left", padx=(4, 8))
        self.cbo_categoria.bind("<<ComboboxSelected>>",
                                 lambda e: self.atualizar())
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
        # Rodapé de paginação. A lista carrega por blocos porque o
        # Treeview insere linha por linha na mesma thread que desenha a
        # janela: um acervo grande travava a tela por segundos antes de
        # mostrar qualquer coisa.
        #
        # Empacotado ANTES da tabela e no rodapé, pelo mesmo motivo da
        # barra de botões de Empréstimos: a tabela com `expand=True`
        # tomava a área toda e este rodapé ficava com altura zero. Numa
        # tela pequena, a contagem "Mostrando 500 de 2.868" e o botão
        # "Carregar mais" desapareciam — e sem eles não havia como
        # chegar ao resto do acervo.
        rodape = ttk.Frame(self, padding=(0, 8))
        rodape.pack(side="bottom", fill="x")

        self.tree.pack(fill="both", expand=True, pady=(8, 0))
        self.tree.bind("<Double-1>", lambda e: self._detalhes())
        self.lbl_contagem = ttk.Label(rodape, text="")
        self.lbl_contagem.pack(side="left")
        self.btn_mais = ttk.Button(rodape, text="Carregar mais",
                                    command=self._carregar_mais)
        self.btn_mais.pack(side="right")
        self.btn_mais.pack_forget()
        self._carregados = 0
        self._total = 0

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

    def _editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um livro",
                                  "Escolha um livro na lista.",
                                  parent=self.painel)
            return
        if len(sel) > 1:
            messagebox.showinfo("Selecione um livro",
                                  "Escolha apenas um livro para editar.",
                                  parent=self.painel)
            return
        livro_id = int(self.tree.item(sel[0])["values"][0])
        try:
            DialogoEditarLivro(self.painel, self.sessao, livro_id,
                               ao_salvar=self.atualizar)
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self.painel)

    def _excluir(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selecione um livro",
                                  "Escolha um livro na lista.",
                                  parent=self.painel)
            return

        itens = [(int(self.tree.item(i)["values"][0]),
                  self.tree.item(i)["values"][1]) for i in sel]

        if len(itens) == 1:
            livro_id, titulo = itens[0]
            if not messagebox.askyesno(
                    "Excluir do acervo",
                    f'Excluir "{titulo}" do acervo?\n\n'
                    "Os exemplares disponíveis serão baixados e o livro "
                    "deixa de aparecer nas buscas. O histórico de "
                    "empréstimos é preservado.",
                    parent=self.painel):
                return
            try:
                servicos.excluir_livro(livro_id, self.sessao.id)
            except RegraNegocioError as e:
                messagebox.showwarning("Atenção", str(e), parent=self.painel)
            self.atualizar()
            return

        # Vários selecionados: um livro com empréstimo em aberto não pode
        # travar os outros — cada um é tentado por si, e o resumo no fim
        # diz o que passou e o que precisa de atenção manual.
        if not messagebox.askyesno(
                "Excluir do acervo",
                f"Excluir {len(itens)} livros do acervo?\n\n"
                "Os exemplares disponíveis serão baixados e os livros "
                "deixam de aparecer nas buscas. O histórico de "
                "empréstimos é preservado.",
                parent=self.painel):
            return

        falhas = []
        excluidos = 0
        for livro_id, titulo in itens:
            try:
                servicos.excluir_livro(livro_id, self.sessao.id)
                excluidos += 1
            except RegraNegocioError as e:
                falhas.append(f"{titulo}: {e}")

        self.atualizar()
        resumo = f"{excluidos} livro(s) excluído(s)."
        if falhas:
            resumo += (f"\n{len(falhas)} não excluído(s):\n"
                       + "\n".join(falhas))
            messagebox.showwarning("Exclusão em massa", resumo,
                                   parent=self.painel)
        else:
            messagebox.showinfo("Exclusão em massa", resumo,
                                parent=self.painel)

    def _etiquetas_massa(self):
        """Gera etiquetas e abre no navegador para Ctrl+P / Salvar PDF.

        Se houver livros marcados na lista, imprime só os marcados. É o
        caso comum: chegaram seis livros novos, e reimprimir a etiqueta
        do acervo inteiro para colar seis é desperdício de papel. Sem
        seleção, mantém o comportamento antigo e usa a busca atual.
        """
        sel = self.tree.selection()
        termo = self.ent_busca.get()
        if sel:
            ids = [int(self.tree.item(i)["values"][0]) for i in sel]
            exemplares = servicos.listar_exemplares_para_etiquetas(
                livro_ids=ids)
            escopo = f"dos {len(ids)} livro(s) selecionado(s)"
            rotulo = f"{len(ids)} livro(s) selecionado(s)"
            vazio = ("Os livros selecionados não têm exemplar ativo. "
                     "Exemplares baixados não recebem etiqueta.")
        else:
            exemplares = servicos.listar_exemplares_para_etiquetas(termo)
            escopo = ("da busca atual" if termo.strip()
                      else "do acervo inteiro")
            rotulo = "acervo" if not termo.strip() else f'busca "{termo}"'
            vazio = "Nenhum exemplar encontrado para a busca atual."

        if not exemplares:
            messagebox.showinfo("Nada a imprimir", vazio, parent=self.painel)
            return
        titulos = len({ex["titulo"] for ex in exemplares})
        if not messagebox.askyesno(
                "Etiquetas em massa",
                f"Gerar etiquetas de {len(exemplares)} exemplar(es) de "
                f"{titulos} livro(s) {escopo}?\n\n"
                "A página abre no navegador para imprimir ou salvar em PDF.",
                parent=self.painel):
            return
        import tempfile
        import webbrowser
        doc = barcode_util.etiquetas_lote_html(exemplares, rotulo)
        destino = Path(tempfile.gettempdir()) / "sigbef_etiquetas_lote.html"
        destino.write_text(doc, encoding="utf-8")
        webbrowser.open(destino.as_uri())

    def atualizar(self):
        self._recarregar_categorias()
        for it in self.tree.get_children():
            self.tree.delete(it)
        self._carregados = 0
        self._total = servicos.contar_livros(
            self.ent_busca.get(), self.var_disponiveis.get(),
            categoria=self.cbo_categoria.get() or None)
        self._carregar_mais()

    def _carregar_mais(self):
        cat = self.cbo_categoria.get()
        for liv in servicos.listar_livros(
                self.ent_busca.get(), self.var_disponiveis.get(),
                categoria=cat or None,
                limite=LIVROS_POR_BLOCO, offset=self._carregados):
            self.tree.insert("", "end", values=(
                liv["id"], liv["titulo"], liv["autores"] or "",
                liv["categoria"] or "", liv["ano_publicacao"] or "",
                liv["total_exemplares"] or 0, liv["disponiveis"] or 0,
            ))
            self._carregados += 1
        tema.aplicar_zebra(self.tree)
        self._atualizar_rodape()

    def _atualizar_rodape(self):
        if self._total == 0:
            self.lbl_contagem.config(text="Nenhum livro encontrado.")
        elif self._carregados >= self._total:
            self.lbl_contagem.config(
                text=f"{self._total} livro(s).")
        else:
            self.lbl_contagem.config(
                text=f"Mostrando {self._carregados} de {self._total} "
                      f"livro(s). Refine a busca para chegar mais perto.")
        if self._carregados < self._total:
            self.btn_mais.pack(side="right")
        else:
            self.btn_mais.pack_forget()

    def _recarregar_categorias(self):
        """Mantém o combo de categorias em dia (opção vazia = Todas)."""
        atual = self.cbo_categoria.get()
        valores = [""] + servicos.listar_categorias()
        if list(self.cbo_categoria["values"]) != valores:
            self.cbo_categoria["values"] = valores
            if atual not in valores:
                self.cbo_categoria.set("")


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------
class SecaoUsuarios(SecaoBase):
    def __init__(self, parent, painel):
        super().__init__(parent, painel)

        topo = ttk.Frame(self)
        topo.pack(fill="x")
        ttk.Label(topo, text="Usuários", style="Titulo.TLabel").pack(side="left")
        ttk.Button(topo, text=" Cadastrar usuário",
                    image=icones.icone("mais", "branco", 14),
                    compound="left",
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
        ttk.Button(emp_card, text=" Registrar empréstimo",
                    image=icones.icone("confirmar", "branco", 14),
                    compound="left",
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
        ttk.Button(dev_card, text=" Registrar devolução",
                    image=icones.icone("desfazer", "branco", 14),
                    compound="left",
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
        # A barra de botões é empacotada ANTES da tabela, e no rodapé.
        #
        # A ordem é o conserto, não estilo. O `pack` do Tk atende na ordem
        # em que é chamado: a tabela, com `expand=True`, tomava a área
        # inteira e a faixa de botões — empacotada depois — ficava com
        # altura zero. Numa tela pequena, "Devolver selecionado",
        # "Quitar multa", "Isentar multa" e "Devolver em lote"
        # simplesmente não existiam, sem aviso e sem rolagem.
        #
        # Limitar o tamanho da janela à tela (v1.11.0) não resolveu isto:
        # aquilo fez a janela caber no monitor, e este faz o conteúdo
        # caber na janela. São dois problemas diferentes.
        op = ttk.Frame(self)
        op.pack(side="bottom", fill="x", pady=(8, 0))

        self.tree.pack(fill="both", expand=True)
        # Devolução com um clique: duplo clique na linha devolve o livro
        self.tree.bind("<Double-1>", lambda e: self._devolver_selecionado())

        ttk.Button(op, text=" Devolver selecionado",
                    image=icones.icone("confirmar", "branco", 14),
                    compound="left",
                    style="Sucesso.TButton",
                    command=self._devolver_selecionado
                    ).pack(side="left", padx=(0, 8))
        ttk.Button(op, text="Renovar selecionado",
                    command=self._renovar).pack(side="left", padx=(0, 8))
        ttk.Button(op, text="Quitar multa",
                    command=self._quitar).pack(side="left")
        ttk.Button(op, text="Isentar multa",
                    command=self._isentar).pack(side="left", padx=(8, 0))
        ttk.Button(op, text="Devolver em lote",
                    command=self._devolver_em_lote).pack(side="left",
                                                          padx=(8, 0))
        ttk.Label(op, text="Dica: duplo clique numa linha devolve o livro.",
                  style="Hint.TLabel").pack(side="left", padx=(16, 0))

    def _devolver_em_lote(self):
        DialogoDevolucaoEmLote(self.painel, self.sessao,
                                ao_fechar=self.atualizar)

    def _selecionar_exemplar_emprestimo(self):
        d = DialogoSelecionarExemplar(self.painel)
        self.painel.wait_window(d)
        if d.codigo_selecionado:
            self.ent_emp_cod.delete(0, "end")
            self.ent_emp_cod.insert(0, d.codigo_selecionado)

    def _selecionar_usuario(self):
        d = DialogoSelecionarUsuario(self.painel)
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

    def _emprestimo_selecionado(self, acao):
        """Id da linha selecionada, ou None (com aviso) se não houver."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(
                "Selecione um empréstimo",
                f"Clique numa linha da tabela antes de {acao}.",
                parent=self.painel)
            return None
        return int(self.tree.item(sel[0])["values"][0])

    def _quitar(self):
        emp_id = self._emprestimo_selecionado("quitar a multa")
        if emp_id is None:
            return
        try:
            saldo = servicos.saldo_multa(emp_id)
        except RegraNegocioError as e:
            messagebox.showwarning("Quitar multa", str(e), parent=self.painel)
            return
        if saldo <= 0:
            messagebox.showinfo(
                "Sem multa em aberto",
                "Este empréstimo não tem multa a receber.",
                parent=self.painel)
            return
        if not messagebox.askyesno(
                "Quitar multa",
                f"Registrar o recebimento de {reais(saldo)}?\n\n"
                "O valor lançado continua no histórico e no relatório — "
                "quitar registra que o dinheiro entrou, não apaga a multa.",
                parent=self.painel):
            return
        try:
            servicos.quitar_multa(emp_id, self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showwarning("Quitar multa", str(e), parent=self.painel)
            return
        self.atualizar()

    def _isentar(self):
        """Perdoa a multa — com motivo, que é o que diferencia de quitar.

        Sem isto, a única forma de perdoar era clicar em "Quitar multa" e
        deixar registrado que a escola recebeu um dinheiro que nunca
        entrou.
        """
        emp_id = self._emprestimo_selecionado("isentar a multa")
        if emp_id is None:
            return
        try:
            saldo = servicos.saldo_multa(emp_id)
        except RegraNegocioError as e:
            messagebox.showwarning("Isentar multa", str(e), parent=self.painel)
            return
        if saldo <= 0:
            messagebox.showinfo(
                "Sem multa em aberto",
                "Este empréstimo não tem multa a isentar.",
                parent=self.painel)
            return
        motivo = simpledialog.askstring(
            "Isentar multa",
            f"Isentar {reais(saldo)} deste empréstimo.\n\n"
            "Motivo da isenção (obrigatório):",
            parent=self.painel)
        if motivo is None:
            return
        try:
            servicos.isentar_multa(emp_id, motivo, self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showwarning("Isentar multa", str(e), parent=self.painel)
            return
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


class SecaoUso(SecaoBase):
    """Painel de uso do acervo — o que os relatórios em CSV não mostram.

    O CSV responde "o que aconteceu"; esta tela responde "o que fazer".
    Daí a escolha dos quatro recortes: o movimento ao longo do ano (a
    biblioteca está viva?), turmas e categorias (quem lê o quê) e, o
    mais acionável de todos, o acervo que nunca saiu da estante.

    Os gráficos são desenhados à mão em Canvas (`ui_graficos`) porque o
    sistema não carrega dependência externa — a mesma regra que fez o
    código de barras e o QR nascerem em Python puro.
    """

    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text="Uso do acervo",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self,
                  text=("Como a biblioteca está sendo usada. Serve para "
                        "planejar compra, montar exposição e mostrar "
                        "resultado à direção."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 16))

        # ------ Números em destaque ------
        cartoes = tk.Frame(self, bg=tema.COR_FUNDO)
        cartoes.pack(fill="x", pady=(0, 16))
        self.cartoes = {}
        for chave, titulo in [
                ("cobertura", "do acervo já foi emprestado"),
                ("parados", "livros nunca emprestados"),
                ("leitores", "leitores nos últimos 30 dias"),
                ("atraso", "das devoluções vieram atrasadas")]:
            c = graficos.CartaoNumero(cartoes, titulo)
            c.pack(side="left", fill="both", expand=True, padx=(0, 10))
            self.cartoes[chave] = c

        # ------ Acervo parado (rodapé) ------
        # Empacotado ANTES do resto, com side="bottom": assim ele reserva
        # o próprio espaço e não é espremido para fora da janela quando o
        # conteúdo acima cresce (foi o que aconteceu na primeira versão).
        rodape = ttk.Frame(self)
        rodape.pack(side="bottom", fill="x", pady=(12, 0))
        self.lbl_parados = ttk.Label(rodape, text="", style="Hint.TLabel")
        self.lbl_parados.pack(side="left")
        ttk.Button(rodape, text="Ver livros parados",
                    command=self._ver_parados).pack(side="right", padx=(8, 0))
        ttk.Button(rodape, text="Exportar CSV",
                    command=self._exportar_parados).pack(side="right")

        # ------ Movimento mês a mês ------
        ttk.Label(self, text="Empréstimos por mês",
                  style="Subtitulo.TLabel").pack(anchor="w")
        self.g_meses = graficos.GraficoLinha(self, altura=150)
        self.g_meses.pack(fill="x", pady=(4, 14))

        # ------ Turmas e categorias, lado a lado ------
        colunas = tk.Frame(self, bg=tema.COR_FUNDO)
        colunas.pack(fill="both", expand=True)

        esq = tk.Frame(colunas, bg=tema.COR_FUNDO)
        esq.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ttk.Label(esq, text="Turmas que mais leem",
                  style="Subtitulo.TLabel").pack(anchor="w")
        self.g_turmas = graficos.GraficoBarras(esq, largura_rotulo=110)
        self.g_turmas.pack(fill="x", pady=(4, 0))

        dir_ = tk.Frame(colunas, bg=tema.COR_FUNDO)
        dir_.pack(side="left", fill="both", expand=True)
        ttk.Label(dir_, text="Categorias mais procuradas",
                  style="Subtitulo.TLabel").pack(anchor="w")
        self.g_categorias = graficos.GraficoBarras(dir_, largura_rotulo=130)
        self.g_categorias.pack(fill="x", pady=(4, 0))

    # ------------------------------------------------------------------
    def atualizar(self) -> None:
        try:
            resumo = servicos.resumo_de_uso()
            meses = servicos.emprestimos_por_mes(12)
            turmas = servicos.emprestimos_por_turma(8)
            categorias = servicos.emprestimos_por_categoria(8)
        except Exception:
            self.lbl_parados.configure(
                text="Não foi possível calcular as estatísticas.")
            return

        self.cartoes["cobertura"].atualizar(
            f"{resumo['cobertura']:g}%",
            f"{resumo['ja_sairam']} de {resumo['acervo']} títulos")
        self.cartoes["parados"].atualizar(
            f"{resumo['nunca_sairam']}",
            "nunca saíram da estante",
            cor=tema.COR_AVISO if resumo["nunca_sairam"] else None)
        self.cartoes["leitores"].atualizar(f"{resumo['leitores_30_dias']}")
        # Atraso alto é problema de operação, não de leitura: destaca em
        # vermelho a partir de 20% para virar assunto na reunião.
        self.cartoes["atraso"].atualizar(
            f"{resumo['taxa_atraso']:g}%",
            f"de {resumo['devolvidos']} devoluções",
            cor=tema.COR_ERRO if resumo["taxa_atraso"] >= 20 else None)

        self.g_meses.mostrar([(m["mes"], m["emprestimos"]) for m in meses])
        self.g_turmas.mostrar(
            [(t["turma"], t["emprestimos"]) for t in turmas])
        self.g_categorias.mostrar(
            [(c["categoria"], c["emprestimos"]) for c in categorias],
            cor=tema.COR_PRIMARIA_ESCURA)

        n = resumo["nunca_sairam"]
        self.lbl_parados.configure(
            text=("Todo o acervo já foi emprestado ao menos uma vez."
                  if not n else
                  f"{n} livro{'s' if n > 1 else ''} nunca "
                  f"{'saíram' if n > 1 else 'saiu'} da estante."))

    # ------------------------------------------------------------------
    def _ver_parados(self) -> None:
        parados = servicos.livros_nunca_emprestados()
        if not parados:
            messagebox.showinfo(
                "Acervo em movimento",
                "Todo o acervo já foi emprestado ao menos uma vez.",
                parent=self.painel)
            return

        janela = tk.Toplevel(self.painel)
        janela.title("Livros que nunca foram emprestados")
        janela.configure(bg=tema.COR_FUNDO)
        icones.aplicar_icone_janela(janela)
        tema.centralizar_janela(janela, 760, 520)
        janela.transient(self.painel)

        ttk.Label(janela,
                  text=f"{len(parados)} títulos sem nenhum empréstimo",
                  style="Subtitulo.TLabel").pack(anchor="w", padx=16,
                                                  pady=(16, 4))
        ttk.Label(janela,
                  text=("Candidatos a exposição, indicação em sala ou "
                        "revisão da próxima compra."),
                  style="Hint.TLabel").pack(anchor="w", padx=16, pady=(0, 10))

        cols = ("titulo", "categoria", "ano", "exemplares")
        tree = ttk.Treeview(janela, columns=cols, show="headings")
        for c, t, w in [("titulo", "Título", 330),
                        ("categoria", "Categoria", 190),
                        ("ano", "Ano", 70),
                        ("exemplares", "Exemplares", 90)]:
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor="w")
        for liv in parados:
            tree.insert("", "end", values=(liv["titulo"], liv["categoria"],
                                            liv["ano_publicacao"] or "",
                                            liv["exemplares"]))
        tree.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        ttk.Button(janela, text="Fechar",
                    command=janela.destroy).pack(pady=(0, 16))

    def _exportar_parados(self) -> None:
        parados = servicos.livros_nunca_emprestados()
        if not parados:
            messagebox.showinfo(
                "Nada a exportar",
                "Todo o acervo já foi emprestado ao menos uma vez.",
                parent=self.painel)
            return
        nome = filedialog.asksaveasfilename(
            parent=self.painel,
            initialfile=f"acervo_parado_{datetime.now():%Y%m%d}.csv",
            defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not nome:
            return
        with open(nome, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["ID", "Título", "Categoria", "Ano", "Exemplares"])
            w.writerows([[_neutralizar_celula_csv(v) for v in
                          (l["id"], l["titulo"], l["categoria"],
                           l["ano_publicacao"] or "", l["exemplares"])]
                         for l in parados])
        messagebox.showinfo("Pronto", f"Arquivo salvo em:\n{nome}",
                              parent=self.painel)


class SecaoReservas(SecaoBase):
    """Fila de espera da biblioteca inteira.

    Antes, toda reserva nascia no balcão: a bibliotecária sabia da fila
    porque ela mesma a criava. Com o aplicativo, o aluno entra na fila
    sozinho, do celular, e ela ficaria sem saber quem está esperando o
    quê. Esta tela é a resposta a isso.

    O topo mostra os exemplares já separados, que são os que correm
    prazo: passado o prazo de retirada, o livro volta para a fila ou
    para a estante — e é o único caso aqui que exige ação de alguém.
    """

    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text="Fila de espera",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self,
                  text=("Quem está esperando cada livro. As reservas "
                        "chegam do balcão e também do aplicativo dos "
                        "alunos."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 16))

        self.lbl_resumo = ttk.Label(self, text="", style="Subtitulo.TLabel")
        self.lbl_resumo.pack(anchor="w", pady=(0, 6))

        # Sem coluna de ID: é número interno, não diz nada a quem atende.
        # O id da reserva vive no iid da linha, que é o que o cancelamento
        # usa. Isso libera a largura para a Situação, que é o que importa.
        cols = ("titulo", "usuario", "matricula", "turma",
                "posicao", "desde", "situacao")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=12)
        for c, t, w in [("titulo", "Livro", 200),
                        ("usuario", "Quem espera", 150),
                        ("matricula", "Matrícula", 85),
                        ("turma", "Série / Turma", 100),
                        ("posicao", "Posição", 72),
                        ("desde", "Na fila desde", 95),
                        ("situacao", "Situação", 263)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        # Separado = tem exemplar guardado esperando o aluno aparecer.
        self.tree.tag_configure("separado",
                                  background=tema.COR_PRIMARIA_SUAVE)
        self.tree.pack(fill="both", expand=True)

        op = ttk.Frame(self)
        op.pack(fill="x", pady=(8, 0))
        ttk.Button(op, text="Cancelar reserva selecionada",
                    command=self._cancelar).pack(side="left", padx=(0, 8))
        ttk.Button(op, text="Atualizar",
                    command=self.atualizar).pack(side="left")
        ttk.Label(op,
                  text=("Dica: quem aparece destacado já tem o exemplar "
                        "separado no balcão."),
                  style="Hint.TLabel").pack(side="left", padx=(16, 0))

    def atualizar(self) -> None:
        from . import reservas

        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            fila = reservas.listar_reservas_ativas()
        except Exception:
            self.lbl_resumo.configure(
                text="Não foi possível ler a fila de espera.")
            return

        separados = 0
        for r in fila:
            if r["exemplar_id"]:
                separados += 1
                # Sem a palavra "separado": o destaque da linha e a dica
                # do rodapé já dizem isso, e ela roubava a largura do
                # tombo — que é o que faz achar o livro na prateleira.
                prazo = data_br(str(r["disponivel_ate"])[:10])
                codigo = r["numero_tombo"] or r["codigo_barras"] or ""
                situacao = f"Retirar até {prazo}"
                if codigo:
                    situacao += f" · {codigo}"
                tags = ("separado",)
            else:
                situacao = "Aguardando devolução"
                tags = ()
            self.tree.insert(
                "", "end", iid=str(r["id"]),
                # criado_em vem com hora; aqui basta o dia, e a hora
                # roubaria espaço da coluna de situação.
                values=(r["titulo"], r["usuario"], r["matricula"],
                        r["turma"] or "", r["posicao"],
                        data_br(str(r["criado_em"])[:10]), situacao),
                tags=tags)

        if not fila:
            self.lbl_resumo.configure(
                text="Ninguém na fila de espera no momento.")
        elif separados:
            self.lbl_resumo.configure(
                text=(f"{len(fila)} na fila — {separados} com exemplar "
                      f"separado aguardando retirada."))
        else:
            self.lbl_resumo.configure(
                text=f"{len(fila)} na fila, nenhum exemplar separado ainda.")

    def _cancelar(self) -> None:
        from . import reservas

        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(
                "Selecione uma reserva",
                "Clique numa linha da tabela antes de cancelar.",
                parent=self.painel)
            return
        reserva_id = sel[0]          # o iid da linha é o id da reserva
        v = self.tree.item(sel[0])["values"]
        titulo, quem = v[0], v[1]
        if not messagebox.askyesno(
                "Cancelar reserva",
                f"Tirar {quem} da fila de \"{titulo}\"?",
                parent=self.painel):
            return
        try:
            # Sem usuario_id: é a bibliotecária cancelando a reserva de
            # outra pessoa, o que o módulo só permite quando quem executa
            # não é o dono. executor_id deixa isso registrado na auditoria.
            reservas.cancelar_reserva(int(reserva_id),
                                       executor_id=self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showerror("Não foi possível cancelar", str(e),
                                  parent=self.painel)
            return
        self.atualizar()


class SecaoInventario(SecaoBase):
    """Conferência do acervo: passar o leitor na estante e ver o que falta.

    A tela é feita para ser usada de pé, com o leitor na mão: o campo de
    código já vem focado e volta a focar sozinho a cada leitura, então a
    bibliotecária não precisa tocar no mouse entre um livro e outro.
    """

    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text="Conferir acervo",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self, text=("Passe o leitor em cada exemplar da estante. "
                               "No fim, o sistema mostra o que não foi "
                               "encontrado."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 16))

        # --- barra de comando: muda conforme há conferência aberta
        self.barra = ttk.Frame(self, style="Card.TFrame", padding=14)
        self.barra.pack(fill="x")

        self.lbl_estado = ttk.Label(self.barra, style="Card.TLabel",
                                     font=("Segoe UI Semibold", 11))
        self.lbl_estado.pack(anchor="w")

        self.linha_leitura = ttk.Frame(self.barra, style="Card.TFrame")
        self.linha_leitura.pack(fill="x", pady=(10, 0))
        ttk.Label(self.linha_leitura, text="Código ou tombo:",
                  style="Card.TLabel").pack(side="left")
        self.ent_codigo = ttk.Entry(self.linha_leitura, width=28,
                                     font=("Segoe UI", 12))
        self.ent_codigo.pack(side="left", padx=8, ipady=3)
        self.ent_codigo.bind("<Return>", lambda e: self._ler())
        ttk.Button(self.linha_leitura, text="Registrar",
                    style="Primario.TButton",
                    command=self._ler).pack(side="left")
        self.btn_encerrar = ttk.Button(self.linha_leitura,
                                        text="Encerrar conferência",
                                        command=self._encerrar)
        self.btn_encerrar.pack(side="right")

        self.btn_abrir = ttk.Button(self.barra, text="Iniciar conferência",
                                     style="Primario.TButton",
                                     command=self._abrir)

        self.lbl_ultima = ttk.Label(self, style="Hint.TLabel", text="")
        self.lbl_ultima.pack(anchor="w", pady=(10, 0))

        # --- lista do que já foi lido nesta sessão de trabalho
        cols = ("hora", "titulo", "codigo", "situacao")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=14)
        for c, t, w in [("hora", "Hora", 80), ("titulo", "Título", 340),
                        ("codigo", "Código", 200),
                        ("situacao", "Situação", 220)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(8, 0))

        rodape = ttk.Frame(self)
        rodape.pack(fill="x", pady=(10, 0))
        ttk.Button(rodape, text="Ver resultado parcial",
                    command=self._resultado_parcial).pack(side="left")
        ttk.Button(rodape, text="Exportar último resultado (CSV)",
                    command=self._exportar).pack(side="left", padx=(8, 0))

    # ------------------------------------------------------------------
    def atualizar(self):
        from . import inventario
        self.aberta = inventario.em_andamento()
        if self.aberta:
            inv = inventario.obter(self.aberta["id"])
            self.lbl_estado.configure(
                text=f"Conferência em andamento desde "
                      f"{data_hora_br(inv['iniciado_em'])} — "
                      f"{inv['lidos']} exemplar(es) lido(s).")
            self.btn_abrir.pack_forget()
            self.linha_leitura.pack(fill="x", pady=(10, 0))
            self.ent_codigo.focus_set()
        else:
            ultimas = inventario.listar(1)
            if ultimas:
                self.lbl_estado.configure(
                    text=f"Nenhuma conferência aberta. A última foi "
                          f"encerrada em "
                          f"{data_hora_br(ultimas[0]['encerrado_em'])}.")
            else:
                self.lbl_estado.configure(
                    text="Nenhuma conferência foi feita ainda.")
            self.linha_leitura.pack_forget()
            self.btn_abrir.pack(anchor="w", pady=(10, 0))

    def _abrir(self):
        from . import inventario
        try:
            inv = inventario.abrir(usuario_id=self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showwarning("Atenção", str(e), parent=self.painel)
            return
        for it in self.tree.get_children():
            self.tree.delete(it)
        self.atualizar()

    def _ler(self):
        from . import inventario
        codigo = self.ent_codigo.get().strip()
        if not codigo or not self.aberta:
            return
        try:
            r = inventario.registrar_leitura(self.aberta["id"], codigo)
        except RegraNegocioError as e:
            self.lbl_ultima.configure(text=str(e), foreground=tema.COR_ERRO)
            self.ent_codigo.delete(0, tk.END)
            self.ent_codigo.focus_set()
            return

        if r["repetido"]:
            situacao, cor = "Já tinha sido lido", tema.COR_AVISO
        elif r["inesperado"]:
            situacao = ("Estava emprestado!" if r["status"] == "EMPRESTADO"
                        else "Estava baixado!")
            cor = tema.COR_AVISO
        else:
            situacao, cor = "Conferido", tema.COR_SUCESSO

        self.tree.insert("", 0, values=(datetime.now().strftime("%H:%M"),
                                         r["titulo"], r["codigo_barras"],
                                         situacao))
        tema.aplicar_zebra(self.tree)
        self.lbl_ultima.configure(text=f"{r['titulo']} — {situacao}",
                                    foreground=cor)
        self.ent_codigo.delete(0, tk.END)
        self.ent_codigo.focus_set()
        self.atualizar_contador()

    def atualizar_contador(self):
        from . import inventario
        inv = inventario.obter(self.aberta["id"])
        self.lbl_estado.configure(
            text=f"Conferência em andamento desde "
                  f"{data_hora_br(inv['iniciado_em'])} — "
                  f"{inv['lidos']} exemplar(es) lido(s).")

    def _encerrar(self):
        from . import inventario
        if not self.aberta:
            return
        if not messagebox.askyesno(
                "Encerrar conferência",
                "Encerrar a conferência e gerar o resultado?\n\n"
                "Depois disso não dá para registrar mais leituras nela.",
                parent=self.painel):
            return
        res = inventario.encerrar(self.aberta["id"], self.sessao.id)
        self.atualizar()
        self._mostrar_resultado(res)

    def _resultado_parcial(self):
        from . import inventario
        alvo = self.aberta or (inventario.listar(1) or [None])[0]
        if not alvo:
            messagebox.showinfo("Sem conferência",
                                  "Nenhuma conferência foi feita ainda.",
                                  parent=self.painel)
            return
        self._mostrar_resultado(inventario.resultado(alvo["id"]))

    def _mostrar_resultado(self, res: dict):
        self._ultimo_resultado = res
        faltando = len(res["nao_encontrados"])
        messagebox.showinfo(
            "Resultado da conferência",
            f"Exemplares no acervo: {res['no_acervo']}\n"
            f"Lidos na estante: {res['lidos']}\n\n"
            f"Não encontrados: {faltando}\n"
            f"Emprestados (fora, como esperado): "
            f"{len(res['fora_como_esperado'])}\n"
            f"Apareceram sem estar previstos: {len(res['apareceram'])}\n\n"
            + ("Exporte o CSV para ver a lista item a item."
               if faltando else "Nenhum exemplar sumido. Acervo bate."),
            parent=self.painel)

    def _exportar(self):
        from . import inventario
        res = getattr(self, "_ultimo_resultado", None)
        if res is None:
            alvo = self.aberta or (inventario.listar(1) or [None])[0]
            if not alvo:
                messagebox.showinfo("Sem conferência",
                                      "Nenhuma conferência foi feita ainda.",
                                      parent=self.painel)
                return
            res = inventario.resultado(alvo["id"])

        nome = filedialog.asksaveasfilename(
            parent=self.painel,
            initialfile=f"conferencia_{datetime.now().strftime('%Y%m%d')}.csv",
            defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not nome:
            return

        linhas = [["NÃO ENCONTRADOS (procurar na estante)", "Situação",
                   "", ""]]
        linhas += [[x["titulo"], x.get("status") or "",
                     x["codigo_barras"], x.get("localizacao") or ""]
                   for x in res["nao_encontrados"]]
        linhas += [["", "", "", ""],
                   ["EMPRESTADOS (fora, como esperado)", "Com quem",
                    "Devolução prevista", ""]]
        linhas += [[x["titulo"], x.get("com_quem") or "",
                     data_br(x.get("data_prevista")) if x.get("data_prevista")
                     else "", x["codigo_barras"]]
                   for x in res["fora_como_esperado"]]
        linhas += [["", "", "", ""],
                   ["APARECERAM (corrigir o cadastro)", "Situação no sistema",
                    "", ""]]
        linhas += [[x["titulo"], x["status"], x.get("motivo_baixa") or "",
                     x["codigo_barras"]]
                   for x in res["apareceram"]]

        with open(nome, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Título", "Detalhe", "Detalhe", "Código"])
            w.writerows([[_neutralizar_celula_csv(v) for v in linha]
                          for linha in linhas])
        messagebox.showinfo("Pronto", f"Arquivo salvo em:\n{nome}",
                              parent=self.painel)


class SecaoRelatorios(SecaoBase):
    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text="Relatórios",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self, text=("Gere relatórios em CSV para análise externa "
                               "(planilhas, BI, etc.)."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 16))

        self._construir_periodo()

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
            ("Mais emprestados",
             "Livros mais procurados. Respeita o período escolhido.",
             self._exportar_circulacao),
            ("Pendências dos leitores",
             "Quem está com livro atrasado ou multa em aberto.",
             self._exportar_inadimplentes),
            ("Movimentação do período",
             "Empréstimos, devoluções, atrasos e multas, por mês e por "
             "turma. É o relatório para a direção.",
             self._exportar_movimentacao),
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

    # ------------------------------------------------------------------
    # Período
    # ------------------------------------------------------------------
    def _construir_periodo(self):
        """Faixa de datas que vale para os relatórios de movimento.

        Tk não traz seletor de data, e desenhar um calendário seria muito
        código para pouco uso: na prática a bibliotecária quer "este mês"
        ou "este ano", e é nos atalhos que ela vai clicar. Os campos
        ficam para o caso raro de um intervalo fechado específico.
        """
        faixa = ttk.Frame(self, style="Card.TFrame", padding=14)
        faixa.pack(fill="x", pady=(0, 14))

        linha = ttk.Frame(faixa, style="Card.TFrame")
        linha.pack(fill="x")
        ttk.Label(linha, text="Período:", style="Card.TLabel",
                  font=("Segoe UI Semibold", 10)).pack(side="left")
        ttk.Label(linha, text="de", style="CardHint.TLabel").pack(
            side="left", padx=(12, 4))
        self.ent_inicio = ttk.Entry(linha, width=12)
        self.ent_inicio.pack(side="left")
        ttk.Label(linha, text="até", style="CardHint.TLabel").pack(
            side="left", padx=4)
        self.ent_fim = ttk.Entry(linha, width=12)
        self.ent_fim.pack(side="left")
        ttk.Label(linha, text="(dd/mm/aaaa)",
                  style="CardHint.TLabel").pack(side="left", padx=(8, 0))

        atalhos = ttk.Frame(faixa, style="Card.TFrame")
        atalhos.pack(fill="x", pady=(10, 0))
        for rotulo, fn in [("Este mês", self._periodo_mes),
                           ("Este bimestre", self._periodo_bimestre),
                           ("Este ano", self._periodo_ano),
                           ("Tudo", self._periodo_tudo)]:
            ttk.Button(atalhos, text=rotulo, command=fn).pack(
                side="left", padx=(0, 8))

        self.lbl_periodo = ttk.Label(atalhos, text="Sem recorte: todo o "
                                                     "histórico.",
                                      style="CardHint.TLabel")
        self.lbl_periodo.pack(side="left", padx=(12, 0))

    def _definir_periodo(self, inicio, fim):
        self.ent_inicio.delete(0, tk.END)
        self.ent_fim.delete(0, tk.END)
        if inicio:
            self.ent_inicio.insert(0, inicio.strftime("%d/%m/%Y"))
        if fim:
            self.ent_fim.insert(0, fim.strftime("%d/%m/%Y"))
        self._descrever_periodo()

    def _periodo_mes(self):
        hoje = date.today()
        self._definir_periodo(hoje.replace(day=1), hoje)

    def _periodo_bimestre(self):
        """Bimestre letivo corrente, contado de janeiro."""
        hoje = date.today()
        primeiro_mes = ((hoje.month - 1) // 2) * 2 + 1
        self._definir_periodo(hoje.replace(month=primeiro_mes, day=1), hoje)

    def _periodo_ano(self):
        hoje = date.today()
        self._definir_periodo(hoje.replace(month=1, day=1), hoje)

    def _periodo_tudo(self):
        self._definir_periodo(None, None)

    def _ler_data(self, entry, rotulo) -> str | None:
        """dd/mm/aaaa -> AAAA-MM-DD. Campo vazio é ausência, não erro."""
        texto = entry.get().strip()
        if not texto:
            return None
        for formato in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto, formato).date().isoformat()
            except ValueError:
                continue
        raise RegraNegocioError(
            f"Data {rotulo} inválida: '{texto}'.\n\n"
            "Use o formato dd/mm/aaaa, por exemplo 01/05/2026.")

    def _periodo(self) -> tuple[str | None, str | None]:
        inicio = self._ler_data(self.ent_inicio, "inicial")
        fim = self._ler_data(self.ent_fim, "final")
        if inicio and fim and inicio > fim:
            raise RegraNegocioError(
                "A data final é anterior à inicial.\n\n"
                "Confira o período antes de gerar o relatório.")
        return inicio, fim

    def _descrever_periodo(self):
        try:
            inicio, fim = self._periodo()
        except RegraNegocioError:
            self.lbl_periodo.configure(text="Período inválido.")
            return
        if not inicio and not fim:
            self.lbl_periodo.configure(text="Sem recorte: todo o histórico.")
        else:
            de = inicio or "o começo"
            ate = fim or "hoje"
            self.lbl_periodo.configure(text=f"De {de} até {ate}.")

    def _sufixo_periodo(self) -> str:
        """Pedaço do nome do arquivo, para não sobrescrever o do mês passado."""
        try:
            inicio, fim = self._periodo()
        except RegraNegocioError:
            return ""
        if not inicio and not fim:
            return ""
        return f"_{(inicio or 'inicio')}_a_{(fim or 'hoje')}"

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
        try:
            inicio, fim = self._periodo()
        except RegraNegocioError as e:
            messagebox.showwarning("Período", str(e), parent=self.painel)
            return
        nome = self._arquivo_destino(
            f"circulacao{self._sufixo_periodo()}.csv")
        if not nome:
            return
        rs = servicos.relatorio_circulacao(50, inicio, fim)
        linhas = [[i + 1, r["titulo"], r["emprestimos"]] for i, r in enumerate(rs)]
        self._escrever(nome, ["#", "Título", "Empréstimos"], linhas)
        messagebox.showinfo("Pronto", f"Arquivo salvo em:\n{nome}",
                              parent=self.painel)

    def _exportar_movimentacao(self):
        """O relatório que vai para a direção no fim do período."""
        try:
            inicio, fim = self._periodo()
        except RegraNegocioError as e:
            messagebox.showwarning("Período", str(e), parent=self.painel)
            return
        mov = servicos.relatorio_movimentacao(inicio, fim)
        if not mov["emprestimos"]:
            messagebox.showinfo(
                "Nada no período",
                "Nenhum empréstimo foi registrado no período escolhido.",
                parent=self.painel)
            return
        nome = self._arquivo_destino(
            f"movimentacao{self._sufixo_periodo()}.csv")
        if not nome:
            return

        # Um CSV com três blocos: o resumo que responde a pergunta, e as
        # duas quebras que explicam o número. Separar em três arquivos
        # daria mais trabalho para quem só quer abrir e olhar.
        linhas = [
            ["RESUMO", "", ""],
            ["Empréstimos no período", mov["emprestimos"], ""],
            ["Devoluções no período", mov["devolucoes"], ""],
            ["Devoluções com atraso", mov["com_atraso"],
             f"{mov['taxa_atraso']}%"],
            ["Multas lançadas (R$)", f"{mov['multa_total']:.2f}", ""],
            ["  das quais recebidas (R$)",
             f"{mov['multa_recebida']:.2f}", ""],
            ["  das quais isentas (R$)", f"{mov['multa_isenta']:.2f}", ""],
            ["  ainda em aberto (R$)", f"{mov['multa_em_aberto']:.2f}", ""],
            ["Leitores diferentes", mov["leitores"], ""],
            ["", "", ""],
            ["POR MÊS", "Empréstimos", ""],
        ]
        linhas += [[m["mes"], m["total"], ""] for m in mov["por_mes"]]
        linhas += [["", "", ""], ["POR TURMA", "Empréstimos", "Leitores"]]
        linhas += [[t["turma"], t["total"], t["leitores"]]
                   for t in mov["por_turma"]]

        self._escrever(nome, ["", "", ""], linhas)
        messagebox.showinfo(
            "Pronto",
            f"{mov['emprestimos']} empréstimo(s) e "
            f"{mov['devolucoes']} devolução(ões) no período.\n\n"
            f"Arquivo salvo em:\n{nome}",
            parent=self.painel)

    def _exportar_inadimplentes(self):
        pendentes = servicos.relatorio_inadimplentes()
        if not pendentes:
            messagebox.showinfo(
                "Nenhuma pendência",
                "Nenhum leitor está com livro atrasado ou multa em aberto.",
                parent=self.painel)
            return
        nome = self._arquivo_destino(
            f"pendencias_{datetime.now().strftime('%Y%m%d')}.csv")
        if not nome:
            return
        # O e-mail entra porque a lista costuma virar cobrança, e sem ele
        # a bibliotecária teria que voltar ao cadastro um por um.
        linhas = [[r["nome"], r["matricula"], r["turma"], r["email"],
                    r["em_atraso"], r["dias_atraso"], f"{r['multa']:.2f}"]
                   for r in pendentes]
        self._escrever(nome,
                        ["Nome", "Matrícula", "Série / Turma", "E-mail",
                         "Exemplares em atraso", "Dias do atraso mais antigo",
                         "Multa (R$)"], linhas)
        messagebox.showinfo(
            "Pronto",
            f"{len(pendentes)} leitor(es) com pendência.\n\n"
            f"Arquivo salvo em:\n{nome}",
            parent=self.painel)


# ---------------------------------------------------------------------------
# Auditoria — quem fez o quê
# ---------------------------------------------------------------------------
AUDITORIA_POR_BLOCO = 200


class SecaoAuditoria(SecaoBase):
    """Leitura do registro de auditoria. Sem escrita nenhuma: a tela só
    mostra o que `registrar_auditoria` já grava desde a v1.0."""

    def __init__(self, parent, painel):
        super().__init__(parent, painel)
        ttk.Label(self, text="Auditoria",
                  style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self, text=("Quem fez o quê no sistema, mais recente "
                               "primeiro."),
                  style="Hint.TLabel").pack(anchor="w", pady=(0, 16))

        filtros = ttk.Frame(self, padding=(0, 0, 0, 12))
        filtros.pack(fill="x")
        ttk.Label(filtros, text="Buscar:").pack(side="left")
        self.ent_busca = ttk.Entry(filtros, width=32)
        self.ent_busca.pack(side="left", padx=8)
        self.ent_busca.bind("<Return>", lambda e: self.atualizar())
        ttk.Label(filtros, text="Ação:").pack(side="left")
        self.cbo_acao = ttk.Combobox(filtros, width=22, state="readonly")
        self.cbo_acao.pack(side="left", padx=(4, 8))
        self.cbo_acao.bind("<<ComboboxSelected>>", lambda e: self.atualizar())
        ttk.Button(filtros, text="Pesquisar",
                    command=self.atualizar).pack(side="left")

        cols = ("quando", "usuario", "acao", "detalhes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=18)
        self.tree.heading("quando", text="Quando")
        self.tree.heading("usuario", text="Quem")
        self.tree.heading("acao", text="Ação")
        self.tree.heading("detalhes", text="Detalhes")
        self.tree.column("quando", width=140, anchor="w")
        self.tree.column("usuario", width=160, anchor="w")
        self.tree.column("acao", width=160, anchor="w")
        self.tree.column("detalhes", width=420, anchor="w")
        self.tree.pack(fill="both", expand=True)

        rodape = ttk.Frame(self, padding=(0, 8, 0, 0))
        rodape.pack(fill="x")
        self.lbl_contagem = ttk.Label(rodape, style="Hint.TLabel")
        self.lbl_contagem.pack(side="left")
        self.btn_mais = ttk.Button(rodape, text="Carregar mais",
                                    command=self._carregar_mais)

        self._carregados = 0
        self._total = 0

    def atualizar(self):
        self._recarregar_acoes()
        for it in self.tree.get_children():
            self.tree.delete(it)
        self._carregados = 0
        self._total = servicos.contar_auditoria(
            self.ent_busca.get(), acao=self.cbo_acao.get() or None)
        self._carregar_mais()

    def _carregar_mais(self):
        for reg in servicos.listar_auditoria(
                self.ent_busca.get(), acao=self.cbo_acao.get() or None,
                limite=AUDITORIA_POR_BLOCO, offset=self._carregados):
            self.tree.insert("", "end", values=(
                data_hora_br(reg["timestamp"]),
                reg["usuario"] or "Sistema",
                reg["acao"],
                reg["detalhes"] or "",
            ))
            self._carregados += 1
        tema.aplicar_zebra(self.tree)
        self._atualizar_rodape()

    def _atualizar_rodape(self):
        if self._total == 0:
            self.lbl_contagem.config(text="Nenhum registro encontrado.")
        elif self._carregados >= self._total:
            self.lbl_contagem.config(text=f"{self._total} registro(s).")
        else:
            self.lbl_contagem.config(
                text=f"Mostrando {self._carregados} de {self._total} "
                      f"registro(s).")
        if self._carregados < self._total:
            self.btn_mais.pack(side="right")
        else:
            self.btn_mais.pack_forget()

    def _recarregar_acoes(self):
        """Mantém o combo de ações em dia (opção vazia = Todas).

        Dinâmico igual ao combo de categorias de `SecaoLivros`: uma
        lista fixa aqui ficaria desatualizada a cada ação nova.
        """
        atual = self.cbo_acao.get()
        valores = [""] + servicos.listar_acoes_auditoria()
        if list(self.cbo_acao["values"]) != valores:
            self.cbo_acao["values"] = valores
            if atual not in valores:
                self.cbo_acao.set("")


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

        smtp_form = ttk.Frame(integ, style="CardInner.TFrame")
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

        botoes_email = ttk.Frame(integ, style="CardInner.TFrame")
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

        api_form = ttk.Frame(integ, style="CardInner.TFrame")
        api_form.pack(fill="x")
        api_form.columnconfigure(1, weight=1)
        ttk.Label(api_form, text="Porta:", style="Card.TLabel"
                  ).grid(row=0, column=0, sticky="w", pady=3)
        self.ent_api_porta = ttk.Entry(api_form, width=8)
        self.ent_api_porta.insert(0, str(api.porta_configurada()))
        self.ent_api_porta.grid(row=0, column=1, sticky="w", padx=12)
        ttk.Label(api_form, text="Token completo:", style="Card.TLabel"
                  ).grid(row=1, column=0, sticky="w", pady=3)
        self.ent_api_token = ttk.Entry(api_form, width=50, show="•")
        self.ent_api_token.grid(row=1, column=1, sticky="w", padx=12)
        ttk.Label(api_form,
                  text="acervo + dados de leitores e circulação",
                  style="CardHint.TLabel"
                  ).grid(row=2, column=1, sticky="w", padx=12)
        ttk.Label(api_form, text="Token de consulta:", style="Card.TLabel"
                  ).grid(row=3, column=0, sticky="w", pady=(8, 3))
        self.ent_api_token_consulta = ttk.Entry(api_form, width=50, show="•")
        self.ent_api_token_consulta.grid(row=3, column=1, sticky="w", padx=12)
        ttk.Label(api_form,
                  text="só o acervo público (sem dados de alunos)",
                  style="CardHint.TLabel"
                  ).grid(row=4, column=1, sticky="w", padx=12)
        # Os tokens dão acesso a dados de leitores por rede; deixá-los em
        # texto puro na tela é o tipo de coisa que vaza numa captura de
        # tela ou por cima do ombro. "Copiar completo" já cobre quem
        # precisa levar o token pra outro lugar sem nunca precisar lê-lo.
        self.var_mostrar_token = tk.BooleanVar(value=False)
        ttk.Checkbutton(api_form, text="Mostrar tokens",
                        variable=self.var_mostrar_token,
                        command=self._alternar_visibilidade_token
                        ).grid(row=5, column=1, sticky="w", padx=12,
                               pady=(6, 0))
        self._refrescar_token_api()

        botoes_api = ttk.Frame(integ, style="CardInner.TFrame")
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
        ttk.Button(botoes_api, text="Parear celular",
                    command=self._parear_celular
                    ).pack(side="right", padx=(0, 8))

        # Aparelhos pareados
        aparelhos = ttk.Frame(integ, style="CardInner.TFrame")
        aparelhos.pack(fill="x", pady=(10, 0))
        self.lbl_aparelhos = ttk.Label(aparelhos, text="",
                                        style="CardHint.TLabel")
        self.lbl_aparelhos.pack(side="left")
        ttk.Button(aparelhos, text="Desconectar celulares",
                    command=self._revogar_sessoes_app
                    ).pack(side="right")
        self._refrescar_aparelhos()

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
        presets_frame = ttk.Frame(aparencia, style="CardInner.TFrame")
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

        # Brasão da instituição
        tk.Frame(aparencia, height=1, bg=tema.COR_BORDA
                 ).grid(row=5, column=0, columnspan=4, sticky="ew",
                        pady=12)
        ttk.Label(aparencia, text="Brasão da instituição",
                  style="Card.TLabel",
                  font=("Segoe UI Semibold", 10)
                  ).grid(row=6, column=0, sticky="w")
        self.lbl_brasao = ttk.Label(aparencia, text="",
                                     style="CardHint.TLabel")
        self.lbl_brasao.grid(row=7, column=0, columnspan=2, sticky="w")
        ttk.Label(aparencia,
                  text=("Aparece na tela de login e no cabeçalho. "
                        "PNG ou GIF, até 512 KB."),
                  style="CardHint.TLabel"
                  ).grid(row=8, column=0, columnspan=3, sticky="w")
        botoes_brasao = ttk.Frame(aparencia, style="CardInner.TFrame")
        botoes_brasao.grid(row=6, column=2, columnspan=2, rowspan=2,
                           sticky="e", padx=(12, 0))
        ttk.Button(botoes_brasao, text="Escolher imagem...",
                   command=self._escolher_brasao).pack(side="left")
        ttk.Button(botoes_brasao, text="Remover",
                   command=self._remover_brasao
                   ).pack(side="left", padx=(8, 0))
        self._refrescar_status_brasao()

        # Botoes de acao
        botoes_aparencia = ttk.Frame(body)
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

        # ---------------- Zona de risco ----------------
        # Sempre por último na tela, de propósito: é a última coisa que
        # a bibliotecária deveria clicar sem pensar duas vezes.
        ttk.Label(body, text="Zona de risco",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(24, 8))
        risco = ttk.Frame(body, style="Card.TFrame", padding=16)
        risco.pack(fill="x")
        linha_risco = ttk.Frame(risco, style="CardInner.TFrame")
        linha_risco.pack(fill="x")
        ttk.Label(
            linha_risco,
            text="Resetar sistema", style="Card.TLabel",
            font=("Segoe UI Semibold", 10)
            ).pack(anchor="w")
        ttk.Label(
            linha_risco,
            text="Apaga acervo, usuários, empréstimos e configurações — "
            "volta o sistema ao estado de instalação nova. Útil pra "
            "tirar dados de teste antes de começar a usar de verdade.",
            style="CardHint.TLabel", wraplength=560
            ).pack(anchor="w", pady=(2, 10))
        ttk.Button(linha_risco, text="Resetar sistema (apagar tudo)",
                   style="Perigo.TButton",
                   command=self._resetar_sistema).pack(anchor="w")

    def _resetar_sistema(self):
        DialogoResetarSistema(self.painel, self.sessao)

    def _salvar(self):
        """Valida antes de gravar — e só diz que salvou se salvou mesmo.

        Antes daqui saía "Salvo com sucesso" para qualquer coisa digitada:
        "0,50" na multa era recusado silenciosamente lá no fundo e o
        sistema continuava cobrando o valor antigo.
        """
        from .database import get_config
        valores = {chave: ent.get() for chave, ent in self._entries.items()}
        try:
            alterados = servicos.salvar_configuracoes(
                valores, executor_id=self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showwarning("Configuração inválida", str(e),
                                    parent=self.painel)
            return
        # Recoloca o valor canônico na tela: quem digitou "0,50" vê "0.50",
        # que é o que o sistema realmente vai usar.
        for chave, ent in self._entries.items():
            ent.delete(0, "end")
            ent.insert(0, get_config(chave) or "")
        if alterados:
            messagebox.showinfo(
                "Configurações",
                "Salvo com sucesso.\n\nAlterado: "
                + ", ".join(alterados) + ".",
                parent=self.painel)
        else:
            messagebox.showinfo("Configurações",
                                 "Nenhuma alteração a salvar.",
                                 parent=self.painel)

    # ---- Brasão da instituição ----
    def _refrescar_status_brasao(self):
        b64 = servicos.obter_brasao()
        if b64:
            kb = (len(b64) * 3 // 4) // 1024
            self.lbl_brasao.configure(text=f"Brasão definido ({kb} KB).")
        else:
            self.lbl_brasao.configure(text="Nenhum brasão definido.")

    def _escolher_brasao(self):
        caminho = filedialog.askopenfilename(
            parent=self.painel,
            title="Escolher brasão da instituição",
            filetypes=[("Imagens PNG ou GIF", "*.png *.gif"),
                       ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return
        try:
            servicos.salvar_brasao(caminho, self.sessao.id)
        except RegraNegocioError as e:
            messagebox.showerror("Brasão da instituição", str(e),
                                   parent=self.painel)
            return
        except OSError as e:
            messagebox.showerror("Brasão da instituição",
                                   f"Não foi possível ler o arquivo:\n{e}",
                                   parent=self.painel)
            return
        icones.invalidar_brasao()
        self._refrescar_status_brasao()
        messagebox.showinfo(
            "Brasão da instituição",
            "Brasão salvo. Ele aparece na tela de login e no cabeçalho "
            "na próxima vez que o sistema abrir.",
            parent=self.painel)

    def _remover_brasao(self):
        if not servicos.obter_brasao():
            return
        servicos.remover_brasao(self.sessao.id)
        icones.invalidar_brasao()
        self._refrescar_status_brasao()
        messagebox.showinfo("Brasão da instituição",
                             "Brasão removido.", parent=self.painel)

    def _backup(self):
        from . import backup
        sugestao = f"sigbef_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
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
            # Passa pelo mesmo caminho do backup automático, que usa a
            # API do SQLite em vez de copiar o arquivo: com o banco em
            # WAL, copiar o .db no meio de uma escrita gera uma cópia
            # que abre mas está desatualizada.
            backup.copiar(destino)
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
        for chave, ent in self._smtp_entries.items():
            servicos.definir_config_auditada(
                chave, ent.get().strip(), executor_id=self.sessao.id,
                acao="CONFIG_EMAIL_ALTERADA")
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
        # Um token novo some de novo por baixo dos pontinhos: mostrar o
        # token trocado sem ninguém pedir seria o mesmo vazamento que o
        # "Mostrar tokens" existe para evitar.
        self.var_mostrar_token.set(False)
        self._alternar_visibilidade_token()

    def _alternar_visibilidade_token(self):
        caractere = "" if self.var_mostrar_token.get() else "•"
        self.ent_api_token.configure(show=caractere)
        self.ent_api_token_consulta.configure(show=caractere)

    def _refrescar_aparelhos(self):
        from .auth import sessoes_app_ativas
        qtd = sessoes_app_ativas()
        if qtd == 0:
            texto = "Nenhum celular pareado."
        elif qtd == 1:
            texto = "1 celular pareado."
        else:
            texto = f"{qtd} celulares pareados."
        self.lbl_aparelhos.configure(text=texto)

    def _revogar_sessoes_app(self):
        """Desconecta todos os aparelhos (aparelho perdido, fim de ano...)."""
        from .auth import revogar_sessoes_app, sessoes_app_ativas
        if sessoes_app_ativas() == 0:
            messagebox.showinfo("Celulares", "Nenhum celular está pareado.",
                                parent=self)
            return
        if not messagebox.askyesno(
                "Desconectar celulares",
                "Todos os celulares pareados vão perder o acesso e os alunos "
                "terão que entrar de novo no aplicativo.\n\nConfirma?",
                parent=self):
            return
        total = revogar_sessoes_app(executor_id=self.sessao.id)
        self._refrescar_aparelhos()
        messagebox.showinfo("Celulares",
                            f"{total} celular(es) desconectado(s).",
                            parent=self)

    def _parear_celular(self):
        """Mostra o QR code que o aplicativo do aluno escaneia."""
        from . import api, qr_util

        endereco = api.endereco_pareamento()

        janela = tk.Toplevel(self)
        janela.title("Parear celular")
        janela.transient(self)
        janela.configure(bg=tema.COR_CARD)
        icones.aplicar_icone_janela(janela)

        corpo = ttk.Frame(janela, style="Card.TFrame", padding=24)
        corpo.pack(fill="both", expand=True)

        ttk.Label(corpo, text="Parear celular",
                  style="Subtitulo.TLabel").pack(anchor="w")

        if endereco is None:
            ttk.Label(corpo, wraplength=380, style="Hint.TLabel",
                      text=("Este computador não está conectado a nenhuma "
                            "rede. Conecte-o ao Wi-Fi ou ao cabo da escola "
                            "e abra esta janela de novo.")
                      ).pack(anchor="w", pady=(8, 16))
        else:
            if not api.api_ativa():
                ttk.Label(corpo, wraplength=380, style="Hint.TLabel",
                          foreground=tema.COR_AVISO,
                          text=("A API está desligada. Ligue a opção acima "
                                "para que o celular consiga se conectar.")
                          ).pack(anchor="w", pady=(8, 0))

            ttk.Label(corpo, wraplength=380, style="Hint.TLabel",
                      text=("No aplicativo do aluno, toque em Escanear QR "
                            "code e aponte a câmera para a imagem abaixo.")
                      ).pack(anchor="w", pady=(8, 12))

            lado = qr_util.matriz(endereco)
            modulo = 7
            px = (len(lado) + 8) * modulo
            canvas = tk.Canvas(corpo, width=px, height=px,
                               highlightthickness=0, bg="#FFFFFF")
            canvas.pack()
            qr_util.desenhar_qr(canvas, endereco, modulo=modulo,
                                cor=tema.COR_PRIMARIA)

            ttk.Label(corpo, text="Ou digite este endereço no aplicativo:",
                      style="Hint.TLabel").pack(anchor="w", pady=(16, 2))
            ttk.Label(corpo, text=endereco,
                      style="Subtitulo.TLabel").pack(anchor="w")
            ttk.Label(corpo, wraplength=380, style="Hint.TLabel",
                      text=("O celular precisa estar na mesma rede da "
                            "escola. O código não contém senha: cada aluno "
                            "entra com a própria matrícula.")
                      ).pack(anchor="w", pady=(12, 0))

        ttk.Button(corpo, text="Fechar", command=janela.destroy
                   ).pack(anchor="e", pady=(20, 0))
        tema.centralizar_janela(janela, 460, 620 if endereco else 240)

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
        ligar = self.var_api.get()
        porta_txt = self.ent_api_porta.get().strip()
        if porta_txt.isdigit():
            servicos.definir_config_auditada(
                "API_PORTA", porta_txt, executor_id=self.sessao.id,
                acao="CONFIG_API_ALTERADA")
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
            if chave == "primaria" and tema.primaria_clara_demais(cor):
                messagebox.showwarning(
                    "Cor primária clara demais",
                    "Essa cor primária é muito clara: o texto e os "
                    "ícones brancos do menu e do cabeçalho ficariam "
                    "quase invisíveis.\n\nEscolha um tom mais escuro "
                    "para a cor primária.",
                    parent=self.painel)

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
        if tema.primaria_clara_demais(valores["primaria"]):
            messagebox.showwarning(
                "Cor primária clara demais",
                "A cor primária escolhida é muito clara. O menu "
                "lateral e o cabeçalho usam texto e ícones brancos, "
                "que ficariam ilegíveis sobre ela.\n\nEscolha uma cor "
                "primária mais escura antes de salvar.",
                parent=self.painel)
            return
        tema.salvar_cores(valores["primaria"], valores["secundaria"],
                          valores["destaque"], valores["fundo"],
                          executor_id=self.sessao.id)
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
        tema.restaurar_padrao(executor_id=self.sessao.id)
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
        self.cbo_categoria = ttk.Combobox(f, width=16, state="readonly")
        self.cbo_categoria.pack(side="left", padx=8)
        self.cbo_categoria.bind("<<ComboboxSelected>>",
                                 lambda e: self.atualizar())
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
        # Contagem separada da mensagem: uma diz quanto tem, a outra diz
        # o que deu errado, e elas não podem apagar uma à outra.
        self.lbl_contagem = ttk.Label(rodape, text="", style="Hint.TLabel")
        self.lbl_contagem.pack(side="left", padx=(12, 0))
        self.btn_mais = ttk.Button(rodape, text="Carregar mais",
                                    command=self._carregar_mais)
        self.btn_mais.pack(side="left", padx=(12, 0))
        self.btn_mais.pack_forget()
        self._carregados = 0
        self._total = 0
        ttk.Button(rodape, text="Ver detalhes",
                    command=self._detalhes).pack(side="right", padx=(8, 0))
        ttk.Button(rodape, text=" Pegar emprestado",
                    image=icones.icone("confirmar", "branco", 14),
                    compound="left",
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
        atual = self.cbo_categoria.get()
        valores = [""] + servicos.listar_categorias()
        if list(self.cbo_categoria["values"]) != valores:
            self.cbo_categoria["values"] = valores
            if atual not in valores:
                self.cbo_categoria.set("")
        for it in self.tree.get_children():
            self.tree.delete(it)
        self._carregados = 0
        self._total = servicos.contar_livros(
            self.ent.get(), self.var_disp.get(),
            categoria=self.cbo_categoria.get() or None)
        self._carregar_mais()

    def _carregar_mais(self):
        for liv in servicos.listar_livros(
                self.ent.get(), self.var_disp.get(),
                categoria=self.cbo_categoria.get() or None,
                limite=LIVROS_POR_BLOCO, offset=self._carregados):
            self.tree.insert("", "end", values=(
                liv["id"], liv["titulo"], liv["autores"] or "",
                liv["categoria"] or "",
                liv["ano_publicacao"] or "",
                f"{liv['disponiveis']}/{liv['total_exemplares']}",
            ))
            self._carregados += 1
        tema.aplicar_zebra(self.tree)
        if self._carregados >= self._total:
            self.lbl_contagem.configure(
                text=f"{self._total} livro(s)." if self._total else "")
            self.btn_mais.pack_forget()
        else:
            self.lbl_contagem.configure(
                text=f"{self._carregados} de {self._total} livro(s)")
            self.btn_mais.pack(side="left", padx=(12, 0))


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
