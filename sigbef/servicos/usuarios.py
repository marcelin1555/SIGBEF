"""Leitores e equipe: cadastro, edição, senha e cartão."""
from __future__ import annotations

from typing import Optional

from ..auth import gerar_hash
from ..barcode_util import gerar_codigo_usuario
from ..database import db_cursor, registrar_auditoria
from ..erros import RegraNegocioError

from .comum import _codigo_barras_unico


def cadastrar_usuario(
    *,
    nome: str,
    matricula: str,
    perfil: str,
    senha: str,
    email: str = "",
    telefone: str = "",
    turma: str = "",
    gerar_cartao: bool = True,
    usuario_id_executor: Optional[int] = None,
) -> dict:
    nome = (nome or "").strip()
    matricula = (matricula or "").strip()
    turma = (turma or "").strip()
    if not nome or not matricula:
        raise RegraNegocioError("Nome e matrícula são obrigatórios.")
    if perfil not in ("ALUNO", "PROFESSOR", "BIBLIOTECARIO", "ADMINISTRADOR"):
        raise RegraNegocioError("Perfil inválido.")
    if not senha or len(senha) < 4:
        raise RegraNegocioError("Senha deve ter pelo menos 4 caracteres.")

    senha_hash = gerar_hash(senha)
    with db_cursor() as cur:
        cur.execute("SELECT 1 FROM usuario WHERE matricula = ?", (matricula,))
        if cur.fetchone():
            raise RegraNegocioError("Já existe um usuário com esta matrícula.")
        cartao = (_codigo_barras_unico(cur, "usuario", gerar_codigo_usuario)
                  if gerar_cartao else None)
        cur.execute(
            """INSERT INTO usuario(nome, matricula, email, telefone, turma,
                                   perfil, senha_hash, codigo_barras)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (nome, matricula, email or None, telefone or None,
             turma or None, perfil, senha_hash, cartao),
        )
        novo_id = cur.lastrowid
    registrar_auditoria(usuario_id_executor, "CADASTRO_USUARIO",
                         f"id={novo_id}; perfil={perfil}")
    return {"id": novo_id, "matricula": matricula, "codigo_barras": cartao}


def listar_usuarios(termo: str = "") -> list[dict]:
    termo_like = f"%{termo.strip()}%" if termo else "%"
    with db_cursor() as cur:
        cur.execute(
            """SELECT id, nome, matricula, email, turma, perfil,
                      codigo_barras, ativo
               FROM usuario
               WHERE nome LIKE ? OR matricula LIKE ? OR IFNULL(email,'') LIKE ?
                  OR IFNULL(turma,'') LIKE ?
               ORDER BY nome""",
            (termo_like, termo_like, termo_like, termo_like),
        )
        return [dict(r) for r in cur.fetchall()]


def alterar_senha(usuario_id: int, nova_senha: str) -> None:
    if not nova_senha or len(nova_senha) < 4:
        raise RegraNegocioError("Senha deve ter pelo menos 4 caracteres.")
    with db_cursor() as cur:
        cur.execute(
            "UPDATE usuario SET senha_hash = ? WHERE id = ?",
            (gerar_hash(nova_senha), usuario_id),
        )
    registrar_auditoria(usuario_id, "TROCA_SENHA", "")


def alternar_status_usuario(usuario_id: int, ativo: bool,
                            executor_id: Optional[int] = None) -> None:
    with db_cursor() as cur:
        cur.execute("UPDATE usuario SET ativo = ? WHERE id = ?",
                    (1 if ativo else 0, usuario_id))
    # Auditoria registra QUEM executou; o usuário afetado vai no detalhe
    registrar_auditoria(executor_id, "STATUS_USUARIO",
                         f"alvo={usuario_id}; ativo={'sim' if ativo else 'nao'}")


def obter_usuario(usuario_id: int) -> dict:
    with db_cursor() as cur:
        cur.execute(
            """SELECT id, nome, matricula, email, telefone, turma, perfil,
                      codigo_barras, ativo
               FROM usuario WHERE id = ?""",
            (usuario_id,),
        )
        row = cur.fetchone()
    if not row:
        raise RegraNegocioError("Usuário não encontrado.")
    return dict(row)


def atualizar_usuario(
    usuario_id: int,
    *,
    nome: str,
    perfil: str,
    email: str = "",
    telefone: str = "",
    turma: str = "",
    executor_id: Optional[int] = None,
) -> None:
    """Atualiza os dados cadastrais de um usuário (nome, contato, turma
    e perfil). A matrícula é fixa; senha tem fluxo próprio."""
    nome = (nome or "").strip()
    if not nome:
        raise RegraNegocioError("Nome é obrigatório.")
    if perfil not in ("ALUNO", "PROFESSOR", "BIBLIOTECARIO", "ADMINISTRADOR"):
        raise RegraNegocioError("Perfil inválido.")
    with db_cursor() as cur:
        cur.execute("SELECT perfil FROM usuario WHERE id = ?", (usuario_id,))
        row = cur.fetchone()
        if not row:
            raise RegraNegocioError("Usuário não encontrado.")
        if (executor_id is not None and usuario_id == executor_id
                and row["perfil"] != perfil):
            raise RegraNegocioError(
                "Você não pode alterar o próprio perfil de acesso.")
        cur.execute(
            """UPDATE usuario SET nome = ?, email = ?, telefone = ?,
                                  turma = ?, perfil = ?
               WHERE id = ?""",
            (nome, (email or "").strip() or None,
             (telefone or "").strip() or None,
             (turma or "").strip() or None, perfil, usuario_id),
        )
    registrar_auditoria(executor_id, "EDICAO_USUARIO",
                         f"id={usuario_id}; perfil={perfil}")


def excluir_usuario(usuario_id: int, executor_id: Optional[int] = None) -> None:
    """Exclui definitivamente um usuário sem histórico de empréstimos.

    Quem já emprestou algum dia não pode ser excluído (o histórico seria
    perdido) — nesse caso use `alternar_status_usuario` para bloquear o
    acesso preservando os registros.
    """
    if executor_id is not None and usuario_id == executor_id:
        raise RegraNegocioError("Você não pode excluir o próprio usuário logado.")
    with db_cursor() as cur:
        cur.execute("SELECT matricula FROM usuario WHERE id = ?", (usuario_id,))
        row = cur.fetchone()
        if not row:
            raise RegraNegocioError("Usuário não encontrado.")
        cur.execute(
            "SELECT COUNT(*) AS n FROM emprestimo WHERE usuario_id = ?",
            (usuario_id,),
        )
        if cur.fetchone()["n"]:
            raise RegraNegocioError(
                "Este usuário possui histórico de empréstimos e não pode ser "
                "excluído. Use 'Ativar/Desativar' para bloquear o acesso "
                "preservando o histórico."
            )
        # Desvincula as entradas de auditoria (o log em si é preservado)
        cur.execute("UPDATE auditoria SET usuario_id = NULL WHERE usuario_id = ?",
                    (usuario_id,))
        cur.execute("DELETE FROM usuario WHERE id = ?", (usuario_id,))
    registrar_auditoria(executor_id, "EXCLUSAO_USUARIO",
                         f"id={usuario_id}; matricula={row['matricula']}")


def gerar_cartao_usuario(usuario_id: int,
                          executor_id: Optional[int] = None) -> str:
    """Garante que o usuário tenha código de barras de cartão e o retorna."""
    with db_cursor() as cur:
        cur.execute("SELECT codigo_barras FROM usuario WHERE id = ?",
                    (usuario_id,))
        row = cur.fetchone()
        if not row:
            raise RegraNegocioError("Usuário não encontrado.")
        if row["codigo_barras"]:
            return row["codigo_barras"]
        codigo = _codigo_barras_unico(cur, "usuario", gerar_codigo_usuario)
        cur.execute("UPDATE usuario SET codigo_barras = ? WHERE id = ?",
                    (codigo, usuario_id))
    registrar_auditoria(executor_id, "CARTAO_GERADO", f"usuario_id={usuario_id}")
    return codigo
