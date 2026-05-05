"""
SIGBEF — Autenticação e gerenciamento de senhas.

Usa hashlib + sal aleatório (PBKDF2-SHA256) para evitar dependência externa.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Optional

from .database import db_cursor, registrar_auditoria

ITERACOES = 200_000


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
        return derived == esperado
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
            return None
        if not verificar_senha(senha, row["senha_hash"]):
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
            return None
    registrar_auditoria(row["id"], "LOGIN_CARTAO", f"Perfil={row['perfil']}")
    return Sessao(
        id=row["id"],
        nome=row["nome"],
        matricula=row["matricula"],
        perfil=row["perfil"],
        email=row["email"],
    )
