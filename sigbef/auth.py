"""
SIGBEF — Autenticação e gerenciamento de senhas.

Usa hashlib + sal aleatório (PBKDF2-SHA256) para evitar dependência externa.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Optional

from .database import db_cursor, get_config, registrar_auditoria

ITERACOES = 200_000


def _config_int(chave: str, padrao: int) -> int:
    try:
        return int(get_config(chave) or padrao)
    except (TypeError, ValueError):
        return padrao


# ---------------------------------------------------------------------------
# Bloqueio temporário por tentativas falhas (anti força-bruta de senha)
# ---------------------------------------------------------------------------
def _falhas_recentes(cur, usuario_id: int) -> int:
    """Conta LOGIN_FALHA do usuário dentro da janela de bloqueio, contando
    só as falhas ocorridas DEPOIS do último login bem-sucedido dele (um
    acerto zera o contador)."""
    minutos = _config_int("LOGIN_BLOQUEIO_MIN", 15)
    cur.execute(
        f"""SELECT COUNT(*) AS n FROM auditoria
            WHERE usuario_id = ? AND acao = 'LOGIN_FALHA'
              AND timestamp >= datetime('now','localtime','-{minutos} minutes')
              AND timestamp > COALESCE((
                    SELECT MAX(timestamp) FROM auditoria
                    WHERE usuario_id = ? AND acao IN ('LOGIN','LOGIN_CARTAO')
                  ), '0')""",
        (usuario_id, usuario_id),
    )
    return cur.fetchone()["n"]


def _conta_bloqueada(cur, usuario_id: int) -> bool:
    return _falhas_recentes(cur, usuario_id) >= _config_int(
        "LOGIN_MAX_TENTATIVAS", 5)


def minutos_bloqueio_restantes(matricula: str) -> int:
    """Se a conta da matrícula está bloqueada, retorna quantos minutos
    faltam pro desbloqueio; 0 se não está bloqueada. Uso: mensagem da UI."""
    matricula = (matricula or "").strip()
    if not matricula:
        return 0
    minutos = _config_int("LOGIN_BLOQUEIO_MIN", 15)
    with db_cursor() as cur:
        cur.execute("SELECT id FROM usuario WHERE matricula = ?", (matricula,))
        row = cur.fetchone()
        if not row or not _conta_bloqueada(cur, row["id"]):
            return 0
        # Minutos até a falha mais antiga da janela sair dela
        cur.execute(
            f"""SELECT CAST((julianday(MIN(timestamp))
                    + {minutos}/1440.0 - julianday('now','localtime'))
                    * 1440 AS INTEGER) + 1 AS faltam
                FROM auditoria
                WHERE usuario_id = ? AND acao = 'LOGIN_FALHA'
                  AND timestamp >= datetime('now','localtime','-{minutos} minutes')""",
            (row["id"],),
        )
        faltam = cur.fetchone()["faltam"]
        return max(1, faltam or 1)

# Hash de uma senha aleatória, gerado sob demanda. Usado para manter o
# tempo de resposta constante quando a matrícula não existe: sem ele, o
# login falho de matrícula inexistente retorna instantâneo (sem PBKDF2)
# e permite enumerar matrículas válidas medindo o tempo.
_HASH_FANTASMA: Optional[str] = None


def _hash_fantasma() -> str:
    global _HASH_FANTASMA
    if _HASH_FANTASMA is None:
        _HASH_FANTASMA = gerar_hash(os.urandom(16).hex())
    return _HASH_FANTASMA


# ---------------------------------------------------------------------------
# Hash de senha
# ---------------------------------------------------------------------------
def gerar_hash(senha: str) -> str:
    """Gera hash PBKDF2-SHA256 com sal aleatório. Formato: pbkdf2$iter$salt$hash."""
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERACOES)
    return f"pbkdf2${ITERACOES}${salt.hex()}${derived.hex()}"


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    """Compara senha em texto puro com o hash gerado por gerar_hash."""
    try:
        algo, iteracoes, salt_hex, hash_hex = hash_armazenado.split("$")
        if algo != "pbkdf2":
            return False
        salt = bytes.fromhex(salt_hex)
        esperado = bytes.fromhex(hash_hex)
        derived = hashlib.pbkdf2_hmac(
            "sha256", senha.encode("utf-8"), salt, int(iteracoes)
        )
        # Comparação em tempo constante (não vaza posição da divergência)
        return hmac.compare_digest(derived, esperado)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Sessão
# ---------------------------------------------------------------------------
@dataclass
class Sessao:
    id: int
    nome: str
    matricula: str
    perfil: str
    email: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        return self.perfil == "ADMINISTRADOR"

    @property
    def is_bibliotecario(self) -> bool:
        return self.perfil in ("BIBLIOTECARIO", "ADMINISTRADOR")

    @property
    def is_aluno(self) -> bool:
        return self.perfil == "ALUNO"

    @property
    def is_professor(self) -> bool:
        return self.perfil == "PROFESSOR"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
def autenticar(matricula: str, senha: str) -> Optional[Sessao]:
    """Retorna uma Sessao se as credenciais forem válidas; caso contrário None."""
    matricula = (matricula or "").strip()
    if not matricula or not senha:
        return None

    with db_cursor() as cur:
        cur.execute(
            "SELECT id, nome, matricula, email, perfil, senha_hash, ativo "
            "FROM usuario WHERE matricula = ?",
            (matricula,),
        )
        row = cur.fetchone()
        if not row or not row["ativo"]:
            # Gasta o mesmo tempo de um login válido antes de negar
            verificar_senha(senha, _hash_fantasma())
            registrar_auditoria(None, "LOGIN_FALHA",
                                 f"matricula={matricula[:40]}")
            return None
        # Conta bloqueada: nem testa a senha (barra força-bruta mesmo que
        # a tentativa atual traga a senha certa, durante a janela)
        if _conta_bloqueada(cur, row["id"]):
            verificar_senha(senha, _hash_fantasma())
            registrar_auditoria(row["id"], "LOGIN_BLOQUEADO",
                                 "muitas tentativas")
            return None
        if not verificar_senha(senha, row["senha_hash"]):
            registrar_auditoria(row["id"], "LOGIN_FALHA", "senha incorreta")
            return None

    registrar_auditoria(row["id"], "LOGIN", f"Perfil={row['perfil']}")
    return Sessao(
        id=row["id"],
        nome=row["nome"],
        matricula=row["matricula"],
        perfil=row["perfil"],
        email=row["email"],
    )


def autenticar_por_codigo(codigo_barras: str) -> Optional[Sessao]:
    """Login alternativo via código de barras do cartão (autoatendimento)."""
    codigo = (codigo_barras or "").strip()
    if not codigo:
        return None
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, nome, matricula, email, perfil, ativo "
            "FROM usuario WHERE codigo_barras = ?",
            (codigo,),
        )
        row = cur.fetchone()
        if not row or not row["ativo"]:
            registrar_auditoria(None, "LOGIN_FALHA",
                                 f"cartao={codigo[:40]}")
            return None
    registrar_auditoria(row["id"], "LOGIN_CARTAO", f"Perfil={row['perfil']}")
    return Sessao(
        id=row["id"],
        nome=row["nome"],
        matricula=row["matricula"],
        perfil=row["perfil"],
        email=row["email"],
    )
