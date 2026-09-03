# -*- coding: utf-8 -*-
"""
SIGBEF — Teste de fumaça das telas: abre o painel e aperta os botões.

Por que existe, e por que não está em `tests/`
----------------------------------------------
A suíte cobre bem serviço e dados, e `tests/test_ui_nomes.py` e
`tests/test_bugs_de_tela.py` cobrem a interface pelo que dá para provar
lendo o código: nome que não existe, tabela sem barra de rolagem,
gravação sem aviso. O que nenhum dos dois alcança é **o clique**: se o
botão chama a função certa, se a lista de trás recarrega, se a
confirmação digitada realmente segura a ação.

Isso exige abrir janela de verdade, e por isso mora aqui e não na suíte:
`python -m unittest discover` precisa rodar em qualquer lugar, inclusive
onde não há tela. Este script precisa de uma.

Ele **não toca o banco real**: monta um banco temporário próprio e
aponta `SIGBEF_DB_PATH` para ele antes de importar qualquer coisa do
sigbef.

Uso:
    python tools/fumaca_telas.py
    echo $?        # 0 = tudo passou
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
BANCO = pathlib.Path(tempfile.mkdtemp(prefix="sigbef-fumaca-")) / "sigbef.db"
os.environ["SIGBEF_DB_PATH"] = str(BANCO)
sys.path.insert(0, str(RAIZ))

from sigbef import backup, database, servicos, ui_dialogos, ui_painel  # noqa: E402
from sigbef.auth import autenticar  # noqa: E402


class CaixaMuda:
    """Substitui `messagebox`: registra o que a tela diria.

    Sem isto, a primeira confirmação pararia o script esperando um
    clique que ninguém vai dar.
    """

    def __init__(self):
        self.ditos: list[tuple[str, str, str]] = []

    def showinfo(self, titulo, msg, **kw):
        self.ditos.append(("info", titulo, msg))

    def showwarning(self, titulo, msg, **kw):
        self.ditos.append(("aviso", titulo, msg))

    def showerror(self, titulo, msg, **kw):
        self.ditos.append(("erro", titulo, msg))

    def askyesno(self, titulo, msg, **kw):
        self.ditos.append(("pergunta", titulo, msg))
        return True


falhas: list[str] = []


def conferir(condicao: bool, ok: str, erro: str) -> None:
    if condicao:
        print("  ok   " + ok)
    else:
        falhas.append(erro)
        print("  FALHA " + erro)


def preparar():
    """Massa mínima: um professor, um livro-texto e um backup."""
    database.init_database()
    servicos.cadastrar_usuario(nome="Admin de Fumaça", matricula="admin",
                               perfil="ADMINISTRADOR", senha="admin123")
    servicos.cadastrar_usuario(nome="Professora Ana", matricula="ana",
                               perfil="PROFESSOR", senha="ana12345")
    livro = servicos.cadastrar_livro(titulo="Livro-texto da turma",
                                     autores=["Autoria"],
                                     quantidade_exemplares=20)
    database.set_config("BACKUP_PASTA", str(BANCO.parent / "backups"))
    copia = backup.copiar()          # o acervo com UM livro
    servicos.cadastrar_livro(titulo="Cadastrado depois do backup",
                             autores=["Outra"], quantidade_exemplares=1)
    return livro, copia


def main() -> int:
    livro, copia = preparar()
    sessao = autenticar("admin", "admin123")

    painel = ui_painel.PainelPrincipal(sessao)
    painel.geometry("1200x700+0+0")
    painel._mostrar_secao("emprestimos")
    bater(painel)

    # Os dois módulos importam `messagebox` por conta própria, então os
    # dois precisam ser trocados.
    muda = CaixaMuda()
    ui_dialogos.messagebox = muda
    ui_painel.messagebox = muda

    # O diálogo é aberto pelo BOTÃO da seção, e não construído à mão: é
    # o caminho real que precisa ser provado, inclusive o callback que
    # manda a lista de trás recarregar. O espião só guarda a instância
    # para o script poder preencher os campos.
    abertos: list = []
    Original = ui_dialogos.DialogoEmprestimoColecao

    class Espiao(Original):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            abertos.append(self)

    ui_dialogos.DialogoEmprestimoColecao = Espiao
    ui_painel.DialogoEmprestimoColecao = Espiao

    secao = painel._secoes["emprestimos"]

    print("Empréstimo de coleção")
    secao._emprestar_colecao()
    dlg = abertos[-1]
    dlg.livro_id = livro["livro_id"]
    dlg.ent_prof.insert(0, "ana")
    dlg.ent_turma.insert(0, "3º Ano B")
    dlg.ent_qtd.insert(0, "12")
    dlg._salvar()
    bater(painel)

    colecoes = servicos.listar_colecoes_em_aberto()
    conferir(len(colecoes) == 1 and colecoes[0]["quantidade"] == 12,
             "saíram 12 exemplares num registro só",
             "coleção não foi criada como esperado: %r" % colecoes)
    conferir(bool(colecoes) and colecoes[0]["turma"] == "3º Ano B",
             "a turma ficou registrada",
             "turma errada: %r" % (colecoes[0]["turma"] if colecoes else None))
    conferir(any(i.startswith("col:") for i in secao.tree.get_children()),
             "a lista atrás recarregou e mostra a linha de coleção",
             "a tabela não mostra a coleção depois de emprestar")

    print("Coleção sem turma")
    secao._emprestar_colecao()
    sem_turma = abertos[-1]
    sem_turma.livro_id = livro["livro_id"]
    sem_turma.ent_prof.insert(0, "ana")
    sem_turma.ent_qtd.insert(0, "2")
    sem_turma._salvar()
    conferir("turma" in sem_turma.lbl_msg.cget("text").lower(),
             "a tela recusa e explica o motivo",
             "sem turma a tela não reclamou: %r" % sem_turma.lbl_msg.cget("text"))
    sem_turma.destroy()

    print("Devolução da coleção")
    iid = [i for i in secao.tree.get_children() if i.startswith("col:")]
    conferir(bool(iid), "a linha de coleção existe para ser selecionada",
             "não há linha de coleção na tabela")
    if iid:
        secao.tree.selection_set(iid[0])
        secao._devolver_colecao()
        bater(painel)
        conferir(not servicos.listar_colecoes_em_aberto(),
                 "os 12 voltaram de uma vez",
                 "a coleção continuou aberta depois de devolver")

    print("Restaurar backup")
    antes = len(servicos.listar_livros())
    restaurar = ui_dialogos.DialogoRestaurarBackup(painel, sessao, str(copia))
    restaurar.ent_confirmacao.insert(0, "quero sim")
    restaurar._confirmar()
    conferir(not restaurar.restaurou and len(servicos.listar_livros()) == antes,
             "frase errada não restaura nada",
             "frase errada restaurou mesmo assim")

    restaurar.ent_confirmacao.delete(0, "end")
    restaurar.ent_confirmacao.insert(0, "RESTAURAR")
    restaurar._confirmar()
    depois = [l["titulo"] for l in servicos.listar_livros()]
    conferir(depois == ["Livro-texto da turma"],
             "a palavra certa trouxe o acervo do arquivo",
             "a restauração não trouxe o acervo do arquivo: %r" % depois)
    conferir(bool(list((BANCO.parent / "backups")
                       .glob("sigbef_antes_da_restauracao_*.db"))),
             "o banco de hoje foi guardado antes da troca",
             "não guardou o banco de hoje antes de trocar")

    painel.destroy()

    print()
    if falhas:
        print("%d falha(s)." % len(falhas))
        return 1
    print("Todos os fluxos passaram.")
    return 0


def bater(janela, vezes: int = 6) -> None:
    """Deixa o Tk processar o que ficou pendente, sem `mainloop`."""
    for _ in range(vezes):
        janela.update_idletasks()
        janela.update()


if __name__ == "__main__":
    sys.exit(main())
