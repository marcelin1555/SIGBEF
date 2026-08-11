"""
SIGBEF — Resetar o sistema (sigbef/reset.py).

O que importa aqui não é só "as tabelas ficam vazias": é que a operação
não segue sem uma rede de segurança (o backup) e que, se algo impedir o
backup, nada é apagado — o reset é tudo ou nada.

Uso:
    python -m unittest tests.test_reset -v
"""
from __future__ import annotations

import sqlite3
import unittest
from unittest.mock import patch

from tests.base import SigbefTestCase

from sigbef import backup, reset, servicos
from sigbef.database import CONFIG_PADRAO, db_cursor, get_config, set_config


class ResetTestCase(SigbefTestCase):
    def popular(self):
        """Um pouco de tudo: livro, usuário, empréstimo, reserva."""
        self.livro = self.criar_livro(exemplares=1)
        self.aluno = self.criar_usuario(matricula="a1")
        self.outro = self.criar_usuario(matricula="a2", nome="Outro Aluno")
        servicos.realizar_emprestimo(
            codigo_exemplar=self.livro["exemplares"][0][1],
            matricula_usuario="a1")
        from sigbef import reservas
        reservas.criar_reserva(self.livro["livro_id"], self.outro["id"])
        # Configuração fora do padrão, pra confirmar que volta.
        set_config("MULTA_POR_DIA", "99.00")
        set_config("PRAZO_ALUNO_DIAS", "1")

    def contagens(self):
        tabelas = ("livro", "exemplar", "livro_autor", "usuario",
                   "emprestimo", "reserva", "auditoria")
        with db_cursor() as cur:
            return {
                t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in tabelas
            }


class TestResetarSistema(ResetTestCase):
    def test_apaga_todos_os_dados(self):
        self.popular()
        reset.resetar_sistema()
        contagens = self.contagens()
        self.assertTrue(all(n == 0 for n in contagens.values()), contagens)

    def test_restaura_configuracao_padrao(self):
        self.popular()
        reset.resetar_sistema()
        for chave, valor in CONFIG_PADRAO.items():
            self.assertEqual(get_config(chave), valor, chave)

    def test_faz_backup_antes_de_apagar(self):
        self.popular()
        antes = set(backup.pasta_destino().glob("sigbef_backup_*.db"))
        caminho = reset.resetar_sistema()
        depois = set(backup.pasta_destino().glob("sigbef_backup_*.db"))
        self.assertEqual(depois - antes, {caminho})
        # O backup tem os dados de ANTES do reset, não depois.
        con = sqlite3.connect(caminho)
        try:
            self.assertEqual(
                con.execute("SELECT COUNT(*) FROM livro").fetchone()[0], 1)
        finally:
            con.close()

    def test_backup_do_reset_e_integro(self):
        self.popular()
        caminho = reset.resetar_sistema()
        con = sqlite3.connect(caminho)
        try:
            self.assertEqual(
                con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        finally:
            con.close()

    def test_falha_no_backup_nao_apaga_nada(self):
        self.popular()
        antes = self.contagens()
        with patch("sigbef.backup.copiar", side_effect=OSError("sem disco")):
            with self.assertRaises(OSError):
                reset.resetar_sistema()
        self.assertEqual(self.contagens(), antes)

    def test_ids_recomecam_do_um(self):
        """Sem limpar sqlite_sequence, o próximo livro viria com um ID
        alto — confuso pra quem acabou de "zerar tudo"."""
        self.popular()
        reset.resetar_sistema()
        novo = self.criar_livro(titulo="Primeiro livro pós-reset")
        self.assertEqual(novo["livro_id"], 1)

    def test_sistema_volta_a_se_comportar_como_instalacao_nova(self):
        from sigbef import seed
        self.popular()
        self.assertFalse(seed.banco_vazio())
        reset.resetar_sistema()
        self.assertTrue(seed.banco_vazio())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
