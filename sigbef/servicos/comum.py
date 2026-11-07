"""Peças usadas por mais de um assunto dos serviços."""
from __future__ import annotations

from ..erros import RegraNegocioError


def _codigo_barras_unico(cur, tabela: str, gerador) -> str:
    """Gera um código de barras garantidamente único na tabela.

    Os geradores usam timestamp por segundo + sufixo aleatório de 4
    dígitos; em cadastros em lote (muitos códigos no mesmo segundo)
    colisões são possíveis — aqui a unicidade é conferida no banco
    antes de usar, com novo sorteio em caso de choque.
    """
    for _ in range(1000):
        codigo = gerador()
        cur.execute(f"SELECT 1 FROM {tabela} WHERE codigo_barras = ?",
                    (codigo,))
        if not cur.fetchone():
            return codigo
    raise RegraNegocioError(
        "Não foi possível gerar um código de barras único. Tente novamente.")
