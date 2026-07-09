"""SIGBEF — Helpers de formatação (datas, valores, status)."""
from __future__ import annotations

from datetime import date, datetime


def _parse_data(valor) -> datetime | None:
    """Interpreta date/datetime ou string ISO ('YYYY-MM-DD' ou
    'YYYY-MM-DD HH:MM:SS'). Retorna None se não reconhecer o formato."""
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, date):
        return datetime(valor.year, valor.month, valor.day)
    s = str(valor)
    try:
        if " " in s:
            return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except ValueError:
        return None


def data_br(valor, com_hora: bool = False) -> str:
    """Converte string ISO ou date/datetime para 'dd/mm/yyyy', opcionalmente
    com hora ('dd/mm/yyyy HH:MM' se `com_hora=True` ou se o valor original
    já tinha horário)."""
    if not valor:
        return ""
    dt = _parse_data(valor)
    if dt is None:
        return str(valor)
    mostrar_hora = com_hora or (isinstance(valor, str) and " " in valor)
    return dt.strftime("%d/%m/%Y %H:%M" if mostrar_hora else "%d/%m/%Y")


def data_hora_br(valor) -> str:
    """Converte para 'dd/mm/yyyy HH:MM'."""
    return data_br(valor, com_hora=True)


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
