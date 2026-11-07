"""Prazos, limites e multa: as regras da escola lidas das configurações."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from ..database import get_config_float, get_config_int


def _atraso_e_multa(data_prevista: str,
                     ate: Optional[date] = None) -> tuple[int, float]:
    """Dias de atraso e multa correspondente, na regra da escola.

    Uma função só porque agora há dois caminhos que encerram um
    empréstimo — a devolução no balcão e a baixa de um exemplar perdido —
    e a conta precisa ser a mesma nos dois. O teto (`MULTA_TETO`) existe
    para o esquecimento de um ano não virar uma dívida impagável.
    """
    prevista = datetime.strptime(data_prevista, "%Y-%m-%d").date()
    dias = max(((ate or date.today()) - prevista).days, 0)
    if not dias:
        return 0, 0.0
    multa = min(get_config_float("MULTA_POR_DIA", 1.5) * dias,
                get_config_float("MULTA_TETO", 60.0))
    return dias, round(multa, 2)


def _prazo_para_perfil(perfil: str) -> int:
    if perfil == "PROFESSOR":
        return get_config_int("PRAZO_PROFESSOR_DIAS", 14)
    return get_config_int("PRAZO_ALUNO_DIAS", 7)


def _limite_para_perfil(perfil: str) -> int:
    if perfil == "PROFESSOR":
        return get_config_int("LIMITE_PROFESSOR", 5)
    return get_config_int("LIMITE_ALUNO", 3)


def _prazo_colecao() -> int:
    return get_config_int("PRAZO_COLECAO_DIAS", 60)


def _teto_colecao() -> int:
    return get_config_int("LIMITE_COLECAO_EXEMPLARES", 40)
