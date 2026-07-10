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

from .database import db_cursor, registrar_auditoria

ITERACOES = 200_000

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
