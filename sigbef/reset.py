"""
SIGBEF — Resetar o sistema (apagar tudo).

Existe pra quem terminou de testar/demonstrar o sistema e quer começar a
usar de verdade, sem carregar acervo, usuários e empréstimos de mentira.
Apaga literalmente tudo — acervo, usuários, empréstimos, reservas — e
devolve `configuracao` ao padrão de fábrica. Depois disso o sistema volta
a se comportar como uma instalação nova: a próxima abertura cai direto no
assistente de primeira configuração (`seed.banco_vazio()` passa a ser
verdadeiro de novo).

É a operação mais destrutiva do sistema, então o cuidado é proporcional:
diferente de `backup.executar_se_necessario()` — que nunca levanta
exceção, porque um backup perdido não pode travar o fechamento do
sistema —, aqui é o oposto de propósito. Sem uma cópia de segurança
válida antes, a operação é arriscada demais para seguir calada, então
`resetar_sistema()` levanta a exceção original se o backup falhar, e não
apaga nada.
"""
from __future__ import annotations

from pathlib import Path

from . import backup
from .database import db_cursor, init_database

# Ordem que respeita as FKs (PRAGMA foreign_keys = ON está ativo em toda
# conexão — ver database.py) — filhos antes dos pais. `sqlite_sequence`
# por último: sem limpá-la, o próximo livro cadastrado viria com um ID
# alto em vez de recomeçar do 1, o que é inofensivo mas confunde quem
# acabou de "zerar tudo" esperando IDs baixos de novo.
_TABELAS_EM_ORDEM = (
    "inventario_item",
    "notificacao",
    "notificacao_reserva",
    "reserva",
    "emprestimo",
    "sessao_app",
    "auditoria",
    "inventario",
    "livro_autor",
    "exemplar",
    "livro",
    "usuario",
    "autor",
    "editora",
    "categoria",
    "configuracao",
)


def resetar_sistema() -> Path:
    """Apaga todos os dados e restaura `configuracao` ao padrão.

    Retorna o caminho do backup feito antes do reset.
    """
    caminho_backup = backup.copiar()

    with db_cursor() as cur:
        for tabela in _TABELAS_EM_ORDEM:
            cur.execute(f"DELETE FROM {tabela}")
        # Reinicia os contadores AUTOINCREMENT. sqlite_sequence só passa
        # a existir depois que alguma tabela AUTOINCREMENT recebe a
        # primeira linha — num banco realmente virgem ela não existiria,
        # daí a checagem antes do DELETE.
        cur.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'sqlite_sequence'")
        if cur.fetchone():
            cur.execute(
                "DELETE FROM sqlite_sequence WHERE name IN ({})".format(
                    ", ".join("?" * len(_TABELAS_EM_ORDEM))),
                _TABELAS_EM_ORDEM,
            )

    # CREATE TABLE IF NOT EXISTS + INSERT OR IGNORE são no-op estrutural
    # numa segunda chamada — é a forma mais simples e correta de
    # repopular `configuracao` com CONFIG_PADRAO depois do DELETE acima.
    init_database()

    return caminho_backup
