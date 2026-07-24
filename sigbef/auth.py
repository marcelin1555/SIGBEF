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


# ---------------------------------------------------------------------------
# Sessões do aplicativo de celular (R2)
# ---------------------------------------------------------------------------
# Cada aparelho pareado recebe um token próprio, preso a UM aluno. Isso
# substitui o uso do token de sistema no app: com o token de sistema,
# qualquer aluno conseguiria ler os empréstimos dos colegas.
SESSAO_APP_DIAS_PADRAO = 30


def _hash_token(token: str) -> str:
    """Hash do token de sessão. Diferente da senha: aqui não precisa de
    fator de trabalho (o token já é aleatório e longo), só de não guardar
    o valor em claro no banco."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def criar_sessao_app(usuario_id: int, dias: Optional[int] = None) -> str:
    """Cria uma sessão para um aparelho e devolve o token em claro.

    O token só existe em claro neste retorno — no banco fica o hash.
    """
    import secrets

    if dias is None:
        dias = _config_int("API_SESSAO_DIAS", SESSAO_APP_DIAS_PADRAO)
    token = secrets.token_urlsafe(32)
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO sessao_app (usuario_id, token_hash, expira_em) "
            "VALUES (?, ?, datetime('now', 'localtime', ?))",
            # :+d preserva o sinal (+30 days / -1 days); "+-1" seria inválido
            (usuario_id, _hash_token(token), f"{int(dias):+d} days"),
        )
    registrar_auditoria(usuario_id, "APP_PAREADO",
                        f"sessao valida por {dias} dias")
    return token


def sessao_app_valida(token: str) -> Optional[Sessao]:
    """Devolve a Sessao do dono do token, ou None se inválido/expirado."""
    token = (token or "").strip()
    if not token:
        return None
    with db_cursor() as cur:
        cur.execute(
            "SELECT u.id, u.nome, u.matricula, u.email, u.perfil, u.ativo "
            "FROM sessao_app s JOIN usuario u ON u.id = s.usuario_id "
            "WHERE s.token_hash = ? AND s.revogada = 0 "
            "  AND s.expira_em > datetime('now', 'localtime')",
            (_hash_token(token),),
        )
        row = cur.fetchone()
    if not row or not row["ativo"]:
        return None
    return Sessao(
        id=row["id"],
        nome=row["nome"],
        matricula=row["matricula"],
        perfil=row["perfil"],
        email=row["email"],
    )


def revogar_sessoes_app(usuario_id: Optional[int] = None,
                        executor_id: Optional[int] = None) -> int:
    """Revoga sessões (de um aluno, ou todas). Devolve quantas caíram.

    Usado quando um aparelho é perdido ou quando a escola quer desconectar
    todo mundo de uma vez.
    """
    with db_cursor() as cur:
        if usuario_id is None:
            cur.execute("UPDATE sessao_app SET revogada = 1 "
                        "WHERE revogada = 0")
        else:
            cur.execute("UPDATE sessao_app SET revogada = 1 "
                        "WHERE revogada = 0 AND usuario_id = ?",
                        (usuario_id,))
        total = cur.rowcount
    registrar_auditoria(executor_id, "APP_SESSOES_REVOGADAS",
                        f"alvo={'todos' if usuario_id is None else usuario_id};"
                        f" total={total}")
    return total


def sessoes_app_ativas() -> int:
    """Quantos aparelhos estão pareados agora (para mostrar na interface)."""
    with db_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS qt FROM sessao_app "
            "WHERE revogada = 0 AND expira_em > datetime('now', 'localtime')"
        )
        return cur.fetchone()["qt"]
