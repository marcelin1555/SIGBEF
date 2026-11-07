"""Erro de regra de negócio, compartilhado pelos serviços e pelas reservas.

Fica fora do pacote `servicos` para que `reservas` possa usá-lo sem
importar os serviços, que por sua vez importam `reservas`.
"""


class RegraNegocioError(Exception):
    """Erro tratado de regra de negócio (mensagens amigáveis ao usuário)."""
