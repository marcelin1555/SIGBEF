"""Consulta da auditoria: quem fez o quê."""
from __future__ import annotations

from typing import Optional

from ..database import db_cursor


# ---------------------------------------------------------------------------
# Auditoria — quem fez o quê
#
# `registrar_auditoria` grava desde a v1.0, mas até a v1.10.2 não havia
# como ler. "Quem excluiu esse livro?" virou pergunta séria depois que a
# exclusão em massa e o reset do sistema entraram no acervo do
# bibliotecário; estas consultas são o que a tela usa para responder.
# ---------------------------------------------------------------------------
def _filtro_de_auditoria(termo: str, acao: Optional[str]):
    """Monta o WHERE compartilhado entre listar e contar (mesmo motivo de
    `_filtro_de_livros`: total e lista não podem discordar)."""
    termo_like = f"%{termo.strip()}%" if termo else "%"
    params: list = [termo_like, termo_like, termo_like]
    onde = """(
                a.acao LIKE ?
                OR IFNULL(a.detalhes, '') LIKE ?
                OR IFNULL(u.nome, '') LIKE ?
              )"""
    if acao:
        onde += " AND a.acao = ?"
        params.append(acao)
    return onde, params


def contar_auditoria(termo: str = "", acao: Optional[str] = None) -> int:
    """Quantos registros a busca encontra, sem trazer nenhum."""
    onde, params = _filtro_de_auditoria(termo, acao)
    with db_cursor() as cur:
        cur.execute(
            f"""SELECT COUNT(*) FROM auditoria a
                LEFT JOIN usuario u ON u.id = a.usuario_id
                WHERE {onde}""", params)
        return cur.fetchone()[0]


def listar_auditoria(termo: str = "", acao: Optional[str] = None,
                     limite: Optional[int] = None,
                     offset: int = 0) -> list[dict]:
    """Lista o registro de auditoria, mais recente primeiro.

    `termo` busca livre na ação, nos detalhes e no nome de quem fez.
    `acao` filtra por um código exato — os valores válidos vêm de
    `listar_acoes_auditoria`, não de uma lista fixa aqui, porque uma
    lista fixa ficaria desatualizada a cada ação nova (já aconteceu com
    o manual do usuário, seis versões desatualizado num ponto parecido).

    `usuario_id` vem `None` para ações do próprio sistema (backup
    automático, por exemplo); a tela mostra "Sistema" nesse caso.
    """
    onde, params = _filtro_de_auditoria(termo, acao)
    paginacao = ""
    if limite is not None:
        paginacao = " LIMIT ? OFFSET ?"
        params = params + [int(limite), int(offset)]
    with db_cursor() as cur:
        cur.execute(
            f"""SELECT a.id, a.timestamp, a.acao, a.detalhes,
                       a.usuario_id, u.nome AS usuario
                FROM auditoria a
                LEFT JOIN usuario u ON u.id = a.usuario_id
                WHERE {onde}
                ORDER BY a.id DESC{paginacao}""", params)
        return [dict(r) for r in cur.fetchall()]


def listar_acoes_auditoria() -> list[str]:
    """Códigos de ação distintos já gravados, em ordem alfabética.

    Alimenta o filtro da tela — dinâmico de propósito, veja o
    docstring de `listar_auditoria`.
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT DISTINCT acao FROM auditoria ORDER BY acao")
        return [r["acao"] for r in cur.fetchall()]
