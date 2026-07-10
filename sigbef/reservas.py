# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marcello
"""
SIGBEF — Reservas com fila de espera.

Aluno/professor reserva um LIVRO (título) quando não há exemplar
disponível. A fila é por ordem de chegada. Quando um exemplar do livro
é devolvido, ele não volta pra prateleira: fica RESERVADO para o
primeiro da fila por RESERVA_VALIDADE_DIAS (config, padrão 2). Só o
dono da vez consegue emprestá-lo; vencido o prazo, a reserva expira e
o exemplar passa ao próximo da fila (ou volta a ficar disponível).

As funções `_*_cur` operam dentro de uma transação já aberta (cursor
recebido) para que devolução + promoção da fila sejam atômicas.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from .database import db_cursor, registrar_auditoria
from .servicos import RegraNegocioError, _config_int


# ---------------------------------------------------------------------------
# Manutenção da fila (dentro de transação)
# ---------------------------------------------------------------------------
def _promover_fila_cur(cur, livro_id: int, exemplar_id: int) -> Optional[dict]:
    """Entrega `exemplar_id` ao primeiro da fila do livro, se houver.

    Marca o exemplar como RESERVADO e carimba o prazo de retirada.
    Retorna dados da reserva promovida ou None se a fila está vazia.
    """
    cur.execute(
        """SELECT r.id, r.usuario_id, u.nome
           FROM reserva r JOIN usuario u ON u.id = r.usuario_id
           WHERE r.livro_id = ? AND r.status = 'ATIVA'
             AND r.exemplar_id IS NULL
           ORDER BY r.criado_em, r.id LIMIT 1""",
        (livro_id,),
    )
    prox = cur.fetchone()
    if not prox:
        return None
    validade = (date.today()
                + timedelta(days=_config_int("RESERVA_VALIDADE_DIAS", 2))
                ).isoformat()
    cur.execute(
        "UPDATE reserva SET exemplar_id = ?, disponivel_ate = ? WHERE id = ?",
        (exemplar_id, validade, prox["id"]),
    )
    cur.execute(
        "UPDATE exemplar SET status = 'RESERVADO' "
        "WHERE id = ? AND status = 'DISPONIVEL'",
        (exemplar_id,),
    )
    return {"reserva_id": prox["id"], "usuario_id": prox["usuario_id"],
            "usuario_nome": prox["nome"], "disponivel_ate": validade}


def _expirar_vencidas_cur(cur) -> None:
    """Expira reservas cujo prazo de retirada venceu e repassa cada
    exemplar liberado ao próximo da fila."""
    cur.execute(
        """SELECT id, exemplar_id, livro_id FROM reserva
           WHERE status = 'ATIVA' AND exemplar_id IS NOT NULL
             AND date(disponivel_ate) < date('now','localtime')""")
    for r in cur.fetchall():
        cur.execute("UPDATE reserva SET status = 'EXPIRADA' WHERE id = ?",
                    (r["id"],))
        cur.execute(
            "UPDATE exemplar SET status = 'DISPONIVEL' "
            "WHERE id = ? AND status = 'RESERVADO'",
            (r["exemplar_id"],),
        )
        _promover_fila_cur(cur, r["livro_id"], r["exemplar_id"])


# ---------------------------------------------------------------------------
# Operações públicas
# ---------------------------------------------------------------------------
def criar_reserva(livro_id: int, usuario_id: int) -> dict:
    """Entra na fila de espera de um livro sem exemplar disponível.

    Retorna {"id", "titulo", "posicao"} (posição 1 = próximo da fila).
    """
    with db_cursor() as cur:
        _expirar_vencidas_cur(cur)

        cur.execute("SELECT titulo FROM livro WHERE id = ? AND ativo = 1",
                    (livro_id,))
        livro = cur.fetchone()
        if not livro:
            raise RegraNegocioError("Livro não encontrado.")

        cur.execute("SELECT ativo FROM usuario WHERE id = ?", (usuario_id,))
        u = cur.fetchone()
        if not u or not u["ativo"]:
            raise RegraNegocioError("Usuário não encontrado ou inativo.")

        cur.execute(
            "SELECT COUNT(*) AS n FROM exemplar "
            "WHERE livro_id = ? AND status = 'DISPONIVEL'",
            (livro_id,),
        )
        if cur.fetchone()["n"]:
            raise RegraNegocioError(
                "Este livro tem exemplar disponível agora — pegue "
                "emprestado em vez de reservar.")

        cur.execute(
            "SELECT 1 FROM reserva WHERE livro_id = ? AND usuario_id = ? "
            "AND status = 'ATIVA'",
            (livro_id, usuario_id),
        )
        if cur.fetchone():
            raise RegraNegocioError(
                "Você já tem uma reserva ativa deste livro.")

        limite = _config_int("LIMITE_RESERVAS", 3)
        cur.execute(
            "SELECT COUNT(*) AS n FROM reserva "
            "WHERE usuario_id = ? AND status = 'ATIVA'",
            (usuario_id,),
        )
        if cur.fetchone()["n"] >= limite:
            raise RegraNegocioError(
                f"Limite de {limite} reservas ativas atingido. "
                "Cancele uma reserva antes de fazer outra.")

        cur.execute(
            "INSERT INTO reserva(livro_id, usuario_id) VALUES (?, ?)",
            (livro_id, usuario_id),
        )
        reserva_id = cur.lastrowid
        cur.execute(
            "SELECT COUNT(*) AS n FROM reserva "
            "WHERE livro_id = ? AND status = 'ATIVA'",
            (livro_id,),
        )
        posicao = cur.fetchone()["n"]

    registrar_auditoria(usuario_id, "RESERVA_CRIADA",
                         f"reserva_id={reserva_id}; livro_id={livro_id}")
    return {"id": reserva_id, "titulo": livro["titulo"], "posicao": posicao}


def cancelar_reserva(reserva_id: int, usuario_id: Optional[int] = None,
                     executor_id: Optional[int] = None) -> None:
    """Cancela uma reserva ativa.

    Se `usuario_id` for passado (fluxo do aluno), só permite cancelar a
    própria reserva. Se a reserva já tinha exemplar separado, ele passa
    ao próximo da fila (ou volta a ficar disponível).
    """
    with db_cursor() as cur:
        cur.execute(
            "SELECT usuario_id, livro_id, exemplar_id, status "
            "FROM reserva WHERE id = ?",
            (reserva_id,),
        )
        r = cur.fetchone()
        if not r or r["status"] != "ATIVA":
            raise RegraNegocioError("Reserva não encontrada ou já encerrada.")
        if usuario_id is not None and r["usuario_id"] != usuario_id:
            raise RegraNegocioError(
                "Esta reserva pertence a outro usuário.")

        cur.execute("UPDATE reserva SET status = 'CANCELADA' WHERE id = ?",
                    (reserva_id,))
        if r["exemplar_id"]:
            cur.execute(
                "UPDATE exemplar SET status = 'DISPONIVEL' "
                "WHERE id = ? AND status = 'RESERVADO'",
                (r["exemplar_id"],),
            )
            _promover_fila_cur(cur, r["livro_id"], r["exemplar_id"])

    registrar_auditoria(executor_id or usuario_id, "RESERVA_CANCELADA",
                         f"reserva_id={reserva_id}")


def listar_reservas_usuario(usuario_id: int,
                            somente_ativas: bool = True) -> list[dict]:
    """Reservas do usuário com título, posição na fila e prazo de retirada."""
    sql = """
        SELECT r.id, r.livro_id, r.status, r.criado_em, r.disponivel_ate,
               r.exemplar_id, l.titulo,
               (SELECT COUNT(*) FROM reserva r2
                 WHERE r2.livro_id = r.livro_id AND r2.status = 'ATIVA'
                   AND r2.exemplar_id IS NULL
                   AND (r2.criado_em < r.criado_em
                        OR (r2.criado_em = r.criado_em AND r2.id <= r.id))
               ) AS posicao
        FROM reserva r JOIN livro l ON l.id = r.livro_id
        WHERE r.usuario_id = ?
    """
    if somente_ativas:
        sql += " AND r.status = 'ATIVA'"
    sql += " ORDER BY r.criado_em DESC"
    with db_cursor() as cur:
        _expirar_vencidas_cur(cur)
        cur.execute(sql, (usuario_id,))
        return [dict(r) for r in cur.fetchall()]


def fila_do_livro(livro_id: int) -> list[dict]:
    """Fila de reservas ativas de um livro, na ordem de atendimento."""
    with db_cursor() as cur:
        _expirar_vencidas_cur(cur)
        cur.execute(
            """SELECT r.id, r.usuario_id, u.nome, u.matricula,
                       r.criado_em, r.exemplar_id, r.disponivel_ate
               FROM reserva r JOIN usuario u ON u.id = r.usuario_id
               WHERE r.livro_id = ? AND r.status = 'ATIVA'
               ORDER BY r.exemplar_id IS NULL, r.criado_em, r.id""",
            (livro_id,),
        )
        return [dict(r) for r in cur.fetchall()]
