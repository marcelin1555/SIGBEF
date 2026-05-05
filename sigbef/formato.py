"""SIGBEF — Helpers de formatação (datas, valores, status)."""
from __future__ import annotations

from datetime import date, datetime


def data_br(valor) -> str:
    """Converte string ISO ou date/datetime para 'dd/mm/yyyy'."""
    if not valor:
        return ""
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    s = str(valor)
    # Aceita 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS'
    try:
        if " " in s:
            dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return s


def data_hora_br(valor) -> str:
    """Converte para 'dd/mm/yyyy HH:MM'."""
    if not valor:
        return ""
    s = str(valor)
    try:
        if " " in s:
            dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return s


def reais(valor) -> str:
    """Formata um valor float como 'R$ 0,00'."""
    try:
        return f"R$ {float(valor):.2f}".replace(".", ",")
    except (TypeError, ValueError):
        return "R$ 0,00"


STATUS_LABELS = {
    "DISPONIVEL": "Disponível",
    "EMPRESTADO": "Emprestado",
    "RESERVADO": "Reservado",
    "MANUTENCAO": "Em manutenção",
    "BAIXADO": "Baixado",
}


def status_legivel(status: str) -> str:
    return STATUS_LABELS.get(status, status)
