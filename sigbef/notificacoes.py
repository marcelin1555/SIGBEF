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


def reservas_pendentes() -> list[dict]:
    """Reservas já separadas (exemplar à espera de retirada) de usuários
    com e-mail que ainda não foram avisados de que o livro chegou."""
    with db_cursor() as cur:
        cur.execute(
            """SELECT r.id AS reserva_id, u.nome, u.email,
                       l.titulo, r.disponivel_ate
               FROM reserva r
               JOIN usuario u ON u.id = r.usuario_id
               JOIN livro l ON l.id = r.livro_id
               LEFT JOIN notificacao_reserva n ON n.reserva_id = r.id
               WHERE r.status = 'ATIVA' AND r.exemplar_id IS NOT NULL
                 AND u.email IS NOT NULL AND u.email != ''
                 AND n.id IS NULL
               ORDER BY r.disponivel_ate""")
        return [dict(r) for r in cur.fetchall()]


def _remetente() -> str:
    return get_config("SMTP_REMETENTE") or get_config("SMTP_USUARIO")


def _montar_mensagem(aviso: dict) -> EmailMessage:
    """Monta o e-mail de aviso de vencimento próximo."""
    instituicao = get_config("NOME_INSTITUICAO", "Biblioteca") or "Biblioteca"
    msg = EmailMessage()
    msg["From"] = _remetente()
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


def _montar_mensagem_reserva(aviso: dict) -> EmailMessage:
    """Monta o e-mail avisando que o livro reservado está disponível."""
    instituicao = get_config("NOME_INSTITUICAO", "Biblioteca") or "Biblioteca"
    msg = EmailMessage()
    msg["From"] = _remetente()
    msg["To"] = aviso["email"]
    msg["Subject"] = f"Biblioteca: '{aviso['titulo']}' está te esperando"
    msg.set_content(
        f"Olá, {aviso['nome']}!\n\n"
        f"O livro '{aviso['titulo']}' que você reservou está disponível "
        "para retirada na biblioteca. Ele fica separado para você até "
        f"{data_br(aviso['disponivel_ate'])}; depois disso, passa para o "
        "próximo da fila.\n\n"
        f"{instituicao}\n"
        "(mensagem automática do SIGBEF, não precisa responder)"
    )
    return msg


# ---------------------------------------------------------------------------
# Envio
# ---------------------------------------------------------------------------
class _ConexaoSMTP:
    """Abre a conexão uma vez e manda mensagens uma a uma.

    Existe pra quem chama poder registrar cada envio assim que ele
    acontece, em vez de só no fim do lote inteiro: se a conexão cair no
    meio (depois de enviar 3 de 10, por exemplo), os 3 primeiros não
    podem ser reenviados na próxima tentativa — e antes eram, porque
    nada tinha sido gravado ainda.
    """

    def __init__(self):
        host = (get_config("SMTP_HOST") or "").strip()
        if not host:
            raise RegraNegocioError(
                "Configure o servidor SMTP em Configurações antes de "
                "enviar (host, porta e credenciais do e-mail da "
                "biblioteca).")
        self._host = host
        self._porta = _config_int("SMTP_PORTA", 587)
        self._usuario = (get_config("SMTP_USUARIO") or "").strip()
        self._senha = get_config("SMTP_SENHA") or ""
        self._smtp: Optional[smtplib.SMTP] = None

    def __enter__(self) -> "_ConexaoSMTP":
        try:
            self._smtp = smtplib.SMTP(self._host, self._porta, timeout=15)
            self._smtp.ehlo()
            if self._smtp.has_extn("starttls"):
                self._smtp.starttls()
                self._smtp.ehlo()
            if self._usuario:
                self._smtp.login(self._usuario, self._senha)
        except (smtplib.SMTPException, OSError) as e:
            raise RegraNegocioError(
                f"Falha ao enviar pelos dados SMTP configurados: {e}. "
                "Confira host, porta, usuário e senha em Configurações.")
        return self

    def __exit__(self, *exc) -> None:
        if self._smtp is not None:
            try:
                self._smtp.quit()
            except Exception:
                pass

    def enviar(self, msg: EmailMessage) -> None:
        try:
            self._smtp.send_message(msg)
        except (smtplib.SMTPException, OSError) as e:
            raise RegraNegocioError(
                f"Falha ao enviar pelos dados SMTP configurados: {e}. "
                "Confira host, porta, usuário e senha em Configurações.")


def enviar_avisos(
    transporte: Optional[Callable[[list[EmailMessage]], None]] = None,
    executor_id: Optional[int] = None,
) -> dict:
    """Envia todos os avisos pendentes (vencimento próximo e reserva
    disponível) de uma vez.

    Retorna {"enviados": total, "vencimento": n, "reserva": m}.
    `transporte` permite injetar um envio alternativo (testes) — nesse
    caso o registro segue em lote, tudo ou nada. No envio real, cada
    mensagem é registrada assim que sai (ver `_ConexaoSMTP`): o que já
    foi enviado não volta a aparecer como pendente, e só quem não saiu
    continua pendente pra próxima tentativa.
    """
    if not avisos_ativos():
        raise RegraNegocioError(
            "Os avisos por e-mail estão desligados. "
            "Ative em Configurações → Integrações.")
    venc = emails_pendentes()
    res = reservas_pendentes()
    if not venc and not res:
        return {"enviados": 0, "vencimento": 0, "reserva": 0}

    itens = ([("VENCIMENTO", a["emprestimo_id"], _montar_mensagem(a))
              for a in venc]
             + [("RESERVA", a["reserva_id"], _montar_mensagem_reserva(a))
                for a in res])

    enviados_venc = enviados_res = 0

    def registrar(tipo: str, chave: int) -> None:
        nonlocal enviados_venc, enviados_res
        with db_cursor() as cur:
            if tipo == "VENCIMENTO":
                cur.execute(
                    "INSERT INTO notificacao(emprestimo_id, tipo) "
                    "VALUES (?, 'VENCIMENTO')", (chave,))
                enviados_venc += 1
            else:
                cur.execute(
                    "INSERT INTO notificacao_reserva(reserva_id) VALUES (?)",
                    (chave,))
                enviados_res += 1

    if transporte is not None:
        transporte([msg for _, _, msg in itens])
        for tipo, chave, _ in itens:
            registrar(tipo, chave)
    else:
        with _ConexaoSMTP() as conexao:
            for tipo, chave, msg in itens:
                conexao.enviar(msg)
                registrar(tipo, chave)

    total = enviados_venc + enviados_res
    registrar_auditoria(executor_id, "EMAIL_AVISOS",
                         f"enviados={total}; vencimento={enviados_venc}; "
                         f"reserva={enviados_res}")
    return {"enviados": total, "vencimento": enviados_venc,
            "reserva": enviados_res}
