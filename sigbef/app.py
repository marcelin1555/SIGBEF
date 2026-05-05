"""
SIGBEF — Ponto de entrada.

Inicializa o banco de dados (criando o schema e populando dados de
demonstração na primeira execução), exibe a tela de login e abre o painel
adequado ao perfil escolhido (ou o terminal de autoatendimento, se a opção
foi marcada na tela de login).
"""
from __future__ import annotations

import sys

from . import seed
from .database import init_database
from .ui_login import JanelaLogin
from .ui_painel import PainelPrincipal
from .ui_selfservice import TerminalAutoatendimento


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]

    # 1. Banco de dados
    init_database()
    if seed.banco_vazio():
        seed.popular_se_vazio()

    # 2. Modo direto: --autoatendimento abre direto o kiosk
    if "--autoatendimento" in argv or "--kiosk" in argv:
        TerminalAutoatendimento().executar()
        return 0

    # 3. Tela de login
    login = JanelaLogin()
    sessao, usar_kiosk = login.executar()
    if not sessao:
        return 0

    # 4. Encaminha conforme escolha
    if usar_kiosk:
        TerminalAutoatendimento().executar()
        return 0

    PainelPrincipal(sessao).mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
