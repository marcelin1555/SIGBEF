# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marcello
"""
SIGBEF — Ponto de entrada.

Fluxo de inicialização:
  1. Cria/atualiza o schema do banco de dados.
  2. Se ainda não há nenhum usuário cadastrado, abre o assistente de
     primeira execução para criar o administrador inicial.
  3. Mostra a tela de login (ou abre direto o terminal de autoatendimento
     se executado com --autoatendimento).
  4. Encaminha para o painel adequado ao perfil do usuário.
"""
from __future__ import annotations

import sys

from . import seed
from .database import init_database
from .ui_login import JanelaLogin
from .ui_painel import PainelPrincipal
from .ui_selfservice import TerminalAutoatendimento
from .ui_setup import JanelaPrimeiraExecucao


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]

    # 1. Banco de dados
    init_database()

    # 1.5 Modo servidor: `--api` roda só a API REST, sem interface
    if "--api" in argv:
        from . import api
        if not api.api_ativa():
            print("A API REST está desligada. Abra o SIGBEF, ative em "
                  "Configurações > Integrações e rode este comando de novo.")
            return 1
        servidor = api.criar_servidor()
        porta = servidor.server_address[1]
        print(f"API do SIGBEF no ar: http://localhost:{porta}/api/v1/ping")
        print("Somente leitura. Ctrl+C para encerrar.")
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            servidor.server_close()
        return 0

    # 2. Primeira execução: nenhum usuário cadastrado
    if seed.banco_vazio():
        # Modo desenvolvedor — popular dados de demo via flag
        if "--demo" in argv or "--popular-demo" in argv:
            seed.popular_se_vazio()
        else:
            wizard = JanelaPrimeiraExecucao()
            ok = wizard.executar()
            if not ok:
                return 0  # Usuário fechou o wizard sem concluir

    # 3. Modo direto: --autoatendimento abre direto o kiosk
    if "--autoatendimento" in argv or "--kiosk" in argv:
        TerminalAutoatendimento().executar()
        return 0

    # 4. Tela de login
    login = JanelaLogin()
    sessao, usar_kiosk = login.executar()
    if not sessao:
        return 0

    # 5. Encaminha conforme escolha
    if usar_kiosk:
        TerminalAutoatendimento().executar()
        return 0

    PainelPrincipal(sessao).mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
