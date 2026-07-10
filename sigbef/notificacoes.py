# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marcello
"""
SIGBEF — Avisos de vencimento por e-mail (opcional, opt-in).

Desligado por padrão (config EMAIL_AVISOS=0): o sistema continua 100%
offline pra quem não usar. Quando ligado em Configurações, o botão
"Enviar avisos agora" manda um e-mail pra cada empréstimo que vence
nos próximos EMAIL_DIAS_ANTES dias (usuários com e-mail cadastrado),
uma única vez por empréstimo (a tabela `notificacao` registra o envio).

Usa só a biblioteca padrão (smtplib + email). O transporte é injetável
para testes, que rodam sem rede.
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Callable, Optional

from .database import db_cursor, get_config, set_config, registrar_auditoria
from .formato import data_br
from .servicos import RegraNegocioError, _config_int


# ---------------------------------------------------------------------------
# Liga/desliga
# ---------------------------------------------------------------------------
def avisos_ativos() -> bool:
    return (get_config("EMAIL_AVISOS", "0") or "0").strip() == "1"


def definir_avisos(ativo: bool) -> None:
    set_config("EMAIL_AVISOS", "1" if ativo else "0")


# ---------------------------------------------------------------------------
# Seleção dos avisos
# ---------------------------------------------------------------------------
def emails_pendentes() -> list[dict]:
    """Empréstimos abertos vencendo em até EMAIL_DIAS_ANTES dias, de
    usuários com e-mail, que ainda não receberam aviso."""
    dias = _config_int("EMAIL_DIAS_ANTES", 2)
    with db_cursor() as cur:
        cur.execute(
            """SELECT e.id AS emprestimo_id, u.nome, u.email,
                       l.titulo, e.data_prevista
               FROM emprestimo e
               JOIN usuario u ON u.id = e.usuario_id
               JOIN exemplar ex ON ex.id = e.exemplar_id
               JOIN livro l ON l.id = ex.livro_id
               LEFT JOIN notificacao n ON n.emprestimo_id = e.id
                                       AND n.tipo = 'VENCIMENTO'
               WHERE e.data_devolucao IS NULL
                 AND u.email IS NOT NULL AND u.email != ''
                 AND n.id IS NULL
                 AND date(e.data_prevista) >= date('now','localtime')
                 AND date(e.data_prevista)
                     <= date('now','localtime', ?)
               ORDER BY e.data_prevista""",
            (f"+{dias} days",),
        )
        return [dict(r) for r in cur.fetchall()]


def _montar_mensagem(aviso: dict) -> EmailMessage:
    instituicao = get_config("NOME_INSTITUICAO", "Biblioteca") or "Biblioteca"
    msg = EmailMessage()
    msg["From"] = get_config("SMTP_REMETENTE") or get_config("SMTP_USUARIO")
    msg["To"] = aviso["email"]
    msg["Subject"] = (f"Biblioteca: devolva '{aviso['titulo']}' até "
                      f"{data_br(aviso['data_prevista'])}")
    msg.set_content(
        f"Olá, {aviso['nome']}!\n\n"
        f"O prazo do livro '{aviso['titulo']}' está chegando: devolva na "
        f"biblioteca até {data_br(aviso['data_prevista'])} para não gerar "
        "multa.\n\n"
        "Se precisar de mais tempo, procure a biblioteca e peça a "
        "renovação.\n\n"
        f"{instituicao}\n"
        "(mensagem automática do SIGBEF, não precisa responder)"
    )
    return msg


# ---------------------------------------------------------------------------
# Envio
# ---------------------------------------------------------------------------
def _transporte_smtp(mensagens: list[EmailMessage]) -> None:
    """Envia via SMTP configurado (STARTTLS quando o servidor oferece)."""
    host = (get_config("SMTP_HOST") or "").strip()
    if not host:
        raise RegraNegocioError(
            "Configure o servidor SMTP em Configurações antes de enviar "
            "(host, porta e credenciais do e-mail da biblioteca).")
    porta = _config_int("SMTP_PORTA", 587)
    usuario = (get_config("SMTP_USUARIO") or "").strip()
    senha = get_config("SMTP_SENHA") or ""
    try:
        with smtplib.SMTP(host, porta, timeout=15) as smtp:
            smtp.ehlo()
            if smtp.has_extn("starttls"):
                smtp.starttls()
                smtp.ehlo()
            if usuario:
                smtp.login(usuario, senha)
            for msg in mensagens:
                smtp.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        raise RegraNegocioError(
            f"Falha ao enviar pelos dados SMTP configurados: {e}. "
            "Confira host, porta, usuário e senha em Configurações.")


def enviar_avisos(
    transporte: Optional[Callable[[list[EmailMessage]], None]] = None,
    executor_id: Optional[int] = None,
) -> dict:
    """Envia os avisos pendentes. Retorna {"enviados": N}.

    `transporte` permite injetar um envio alternativo (testes). O
    registro em `notificacao` só acontece se o envio inteiro der certo,
    então uma falha permite tentar de novo sem perder ninguém.
    """
    if not avisos_ativos():
        raise RegraNegocioError(
            "Os avisos por e-mail estão desligados. "
            "Ative em Configurações → Integrações.")
    pendentes = emails_pendentes()
    if not pendentes:
        return {"enviados": 0}

    mensagens = [_montar_mensagem(a) for a in pendentes]
    (transporte or _transporte_smtp)(mensagens)

    with db_cursor() as cur:
        for a in pendentes:
            cur.execute(
                "INSERT INTO notificacao(emprestimo_id, tipo) "
                "VALUES (?, 'VENCIMENTO')",
                (a["emprestimo_id"],),
            )
    registrar_auditoria(executor_id, "EMAIL_AVISOS",
                         f"enviados={len(pendentes)}")
    return {"enviados": len(pendentes)}
