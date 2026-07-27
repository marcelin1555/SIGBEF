"""
SIGBEF — Cópia de segurança.

O que se testa aqui não é "o arquivo foi criado": é que a cópia serve.
Backup que existe mas não abre, ou que abre com dados de ontem, é pior
que backup nenhum — dá uma sensação de proteção que não se confirma no
dia em que faz falta.

Uso:
    python -m unittest tests.test_backup -v
"""
from __future__ import annotations

import os
import sqlite3
import threading
import time
import unittest

from tests.base import SigbefTestCase

from sigbef import backup, servicos
from sigbef.database import DB_PATH, db_cursor, get_config, set_config


class BackupTestCase(SigbefTestCase):
    def setUp(self):
        super().setUp()
        # Cada teste com sua pasta, ao lado do banco temporário.
        self.pasta = str(backup.Path(DB_PATH).parent / "backups")
        set_config("BACKUP_PASTA", self.pasta)
        set_config("BACKUP_ULTIMO", "")
        set_config("BACKUP_AUTO", "1")
        for antigo in backup.pasta_destino().glob("*"):
            antigo.unlink()

    def contar(self, caminho, tabela="livro"):
        con = sqlite3.connect(caminho)
        try:
            return con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        finally:
            con.close()


class TestCopia(BackupTestCase):

    def test_copia_abre_e_tem_os_mesmos_dados(self):
        for i in range(3):
            self.criar_livro(titulo=f"Livro {i}")
        destino = backup.copiar()
        self.assertTrue(destino.exists())
        self.assertEqual(self.contar(destino), 3)

    def test_copia_passa_no_integrity_check(self):
        self.criar_livro()
        destino = backup.copiar()
        con = sqlite3.connect(destino)
        try:
            self.assertEqual(
                con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        finally:
            con.close()

    def test_copia_com_escrita_acontecendo_ao_mesmo_tempo(self):
        """O caso que motivou trocar `shutil.copy2` pela API do SQLite.

        Com o banco em WAL, parte das transações vive no arquivo `-wal`
        até o checkpoint. A garantia que se quer aqui é que a cópia saia
        consistente mesmo com o balcão trabalhando.
        """
        self.criar_livro(titulo="Base")
        parar = threading.Event()

        def escrevendo():
            while not parar.is_set():
                try:
                    with db_cursor() as cur:
                        cur.execute(
                            "INSERT INTO auditoria (usuario_id, acao) "
                            "VALUES (NULL, 'RUIDO')")
                except Exception:
                    pass

        th = threading.Thread(target=escrevendo, daemon=True)
        th.start()
        time.sleep(0.2)
        try:
            destino = backup.copiar()
        finally:
            parar.set()
            th.join(timeout=5)

        con = sqlite3.connect(destino)
        try:
            self.assertEqual(
                con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            # O livro de antes da pancadaria tem que estar lá.
            self.assertEqual(
                con.execute("SELECT COUNT(*) FROM livro").fetchone()[0], 1)
        finally:
            con.close()

    def test_duas_copias_seguidas_nao_se_sobrescrevem(self):
        """Um backup manual e o automático caem no mesmo segundo."""
        self.criar_livro()
        primeira = backup.copiar()
        segunda = backup.copiar()
        self.assertNotEqual(primeira, segunda)
        self.assertTrue(primeira.exists() and segunda.exists())

    def test_destino_explicito_e_respeitado(self):
        self.criar_livro()
        alvo = backup.pasta_destino() / "escolhido_pela_bibliotecaria.db"
        backup.copiar(alvo)
        self.assertTrue(alvo.exists())
        self.assertEqual(self.contar(alvo), 1)


class TestRotacao(BackupTestCase):

    def criar_copias(self, quantas):
        feitas = []
        for i in range(quantas):
            p = backup.copiar()
            os.utime(p, (time.time() + i, time.time() + i))
            feitas.append(p)
        return feitas

    def test_mantem_a_quantidade_configurada(self):
        set_config("BACKUP_MANTER", "3")
        self.criar_livro()
        self.criar_copias(6)
        backup.limpar_antigos()
        sobraram = list(backup.pasta_destino().glob("sigbef_backup_*.db"))
        self.assertEqual(len(sobraram), 3)

    def test_guarda_as_mais_novas(self):
        set_config("BACKUP_MANTER", "2")
        self.criar_livro()
        feitas = self.criar_copias(5)
        backup.limpar_antigos()
        sobraram = {p.name for p in
                    backup.pasta_destino().glob("sigbef_backup_*.db")}
        self.assertEqual(sobraram, {p.name for p in feitas[-2:]})

    def test_nao_apaga_arquivo_que_nao_e_nosso(self):
        """A pasta de backup pode ter outras coisas dentro."""
        set_config("BACKUP_MANTER", "1")
        self.criar_livro()
        self.criar_copias(3)
        alheio = backup.pasta_destino() / "planilha_da_escola.xlsx"
        alheio.write_text("não me apague")
        backup.limpar_antigos()
        self.assertTrue(alheio.exists())


class TestAutomatico(BackupTestCase):

    def test_faz_uma_copia_por_dia(self):
        self.criar_livro()
        self.assertIsNotNone(backup.executar_se_necessario())
        self.assertIsNone(backup.executar_se_necessario())

    def test_desligado_nao_copia(self):
        set_config("BACKUP_AUTO", "0")
        self.criar_livro()
        self.assertIsNone(backup.executar_se_necessario())

    def test_registra_a_data_para_nao_repetir(self):
        self.criar_livro()
        backup.executar_se_necessario()
        self.assertTrue(get_config("BACKUP_ULTIMO"))

    def test_pasta_invalida_nao_derruba_o_fechamento(self):
        """A bibliotecária não pode ficar presa numa janela de erro na
        hora de ir embora."""
        set_config("BACKUP_PASTA", "Z:/pasta/que/nao/existe")
        self.criar_livro()
        self.assertIsNone(backup.executar_se_necessario())

    def test_falha_fica_registrada_na_auditoria(self):
        set_config("BACKUP_PASTA", "Z:/pasta/que/nao/existe")
        self.criar_livro()
        backup.executar_se_necessario()
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM auditoria "
                        "WHERE acao = 'BACKUP_FALHOU'")
            self.assertGreaterEqual(cur.fetchone()[0], 1)

    def test_sucesso_fica_registrado_na_auditoria(self):
        self.criar_livro()
        backup.executar_se_necessario()
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM auditoria "
                        "WHERE acao = 'BACKUP_AUTOMATICO'")
            self.assertEqual(cur.fetchone()[0], 1)


class TestUltimo(BackupTestCase):

    def test_sem_copia_devolve_nada(self):
        self.assertIsNone(backup.ultimo())

    def test_descreve_a_copia_mais_recente(self):
        self.criar_livro()
        backup.copiar()
        u = backup.ultimo()
        self.assertEqual(u["total"], 1)
        self.assertGreaterEqual(u["mb"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
