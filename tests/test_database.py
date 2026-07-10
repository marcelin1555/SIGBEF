"""
SIGBEF — Testes da camada de banco de dados (sigbef.database).

Cobre init_database (idempotência e migração), configuração
(get_config/set_config/CONFIG_PADRAO), auditoria, rollback do
db_cursor e a ativação de FOREIGN KEYs.
"""
from tests.base import SigbefTestCase

import sqlite3
from pathlib import Path

from sigbef import database
from sigbef.database import (
    CONFIG_PADRAO,
    db_cursor,
    get_config,
    init_database,
    registrar_auditoria,
    set_config,
)


class TestInitDatabase(SigbefTestCase):
    """Criação do schema e população das configurações padrão."""

    def test_init_e_idempotente(self):
        """Chamar init_database mais de uma vez não dá erro nem duplica config."""
        init_database()  # segunda chamada (a primeira foi no setUp)
        init_database()  # terceira, por garantia
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM configuracao")
            total = cur.fetchone()["n"]
        self.assertEqual(total, len(CONFIG_PADRAO))

    def test_config_padrao_populada(self):
        """Todas as chaves de CONFIG_PADRAO existem com os valores padrão."""
        self.assertEqual(get_config("PRAZO_ALUNO_DIAS"), "7")
        self.assertEqual(get_config("PRAZO_PROFESSOR_DIAS"), "14")
        self.assertEqual(get_config("LIMITE_ALUNO"), "3")
        self.assertEqual(get_config("LIMITE_PROFESSOR"), "5")
        self.assertEqual(get_config("MULTA_POR_DIA"), "1.50")
        self.assertEqual(get_config("MULTA_TETO"), "60.00")
        self.assertEqual(get_config("ISBN_LOOKUP"), "0")
        for chave, valor in CONFIG_PADRAO.items():
            with self.subTest(chave=chave):
                self.assertEqual(get_config(chave), valor)

    def test_init_nao_sobrescreve_config_alterada(self):
        """init_database usa INSERT OR IGNORE: valores alterados sobrevivem."""
        set_config("PRAZO_ALUNO_DIAS", "10")
        init_database()
        self.assertEqual(get_config("PRAZO_ALUNO_DIAS"), "10")


class TestConfiguracao(SigbefTestCase):
    """get_config e set_config (upsert)."""

    def test_set_config_cria_chave_nova(self):
        set_config("CHAVE_NOVA", "valor1")
        self.assertEqual(get_config("CHAVE_NOVA"), "valor1")

    def test_set_config_sobrescreve_chave_existente(self):
        set_config("CHAVE_X", "antigo")
        set_config("CHAVE_X", "novo")
        self.assertEqual(get_config("CHAVE_X"), "novo")

    def test_get_config_inexistente_retorna_padrao(self):
        self.assertEqual(get_config("NAO_EXISTE", "padrao-x"), "padrao-x")

    def test_get_config_inexistente_sem_padrao_retorna_none(self):
        self.assertIsNone(get_config("NAO_EXISTE"))


class TestAuditoria(SigbefTestCase):
    """registrar_auditoria grava linhas na tabela auditoria."""

    def test_registra_acao_e_detalhes(self):
        usuario = self.criar_usuario(matricula="aud1")
        registrar_auditoria(usuario["id"], "ACAO_TESTE", "detalhe qualquer")
        with db_cursor() as cur:
            cur.execute(
                "SELECT usuario_id, acao, detalhes, timestamp FROM auditoria "
                "WHERE acao = 'ACAO_TESTE'"
            )
            row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["usuario_id"], usuario["id"])
        self.assertEqual(row["acao"], "ACAO_TESTE")
        self.assertEqual(row["detalhes"], "detalhe qualquer")
        self.assertTrue(row["timestamp"])  # default preenchido

    def test_aceita_usuario_id_none(self):
        """Ações do sistema (sem usuário logado) são aceitas com usuario_id NULL."""
        registrar_auditoria(None, "ACAO_SISTEMA", "sem usuário")
        with db_cursor() as cur:
            cur.execute(
                "SELECT usuario_id, detalhes FROM auditoria WHERE acao = 'ACAO_SISTEMA'"
            )
            row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertIsNone(row["usuario_id"])
        self.assertEqual(row["detalhes"], "sem usuário")


class TestMigracao(SigbefTestCase):
    """Migração leve: banco antigo sem a coluna usuario.turma."""

    # Schema da tabela usuario como era ANTES da v1.2.0 (sem a coluna turma)
    SCHEMA_USUARIO_ANTIGO = """
    CREATE TABLE usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        matricula TEXT UNIQUE NOT NULL,
        email TEXT,
        telefone TEXT,
        perfil TEXT NOT NULL CHECK (perfil IN ('ALUNO','PROFESSOR','BIBLIOTECARIO','ADMINISTRADOR')),
        senha_hash TEXT NOT NULL,
        codigo_barras TEXT UNIQUE,
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );
    """

    def test_init_adiciona_coluna_turma_sem_perder_dados(self):
        # Simula um banco antigo: apaga o atual e cria usuario sem turma
        Path(database.DB_PATH).unlink(missing_ok=True)
        conn = sqlite3.connect(database.DB_PATH)
        try:
            conn.executescript(self.SCHEMA_USUARIO_ANTIGO)
            conn.execute(
                "INSERT INTO usuario(nome, matricula, perfil, senha_hash) "
                "VALUES ('Usuária Antiga', 'antiga1', 'ALUNO', 'hash-qualquer')"
            )
            conn.commit()
            # Confirma a premissa: turma NÃO existe no banco antigo
            colunas = {r[1] for r in conn.execute("PRAGMA table_info(usuario)")}
            self.assertNotIn("turma", colunas)
        finally:
            conn.close()

        # Migração: init_database deve adicionar a coluna sem perder linhas
        init_database()

        with db_cursor() as cur:
            cur.execute("PRAGMA table_info(usuario)")
            colunas = {r["name"] for r in cur.fetchall()}
            self.assertIn("turma", colunas)
            cur.execute("SELECT nome, matricula, turma FROM usuario")
            rows = cur.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["nome"], "Usuária Antiga")
        self.assertEqual(rows[0]["matricula"], "antiga1")
        self.assertIsNone(rows[0]["turma"])  # coluna nova vem NULL


class TestDbCursor(SigbefTestCase):
    """Comportamento transacional do context manager db_cursor."""

    def test_rollback_em_excecao(self):
        """Exceção dentro do bloco desfaz o INSERT (rollback automático)."""
        with self.assertRaises(RuntimeError):
            with db_cursor() as cur:
                cur.execute("INSERT INTO editora(nome) VALUES ('Editora Fantasma')")
                raise RuntimeError("falha proposital")

        with db_cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM editora WHERE nome = 'Editora Fantasma'"
            )
            self.assertEqual(cur.fetchone()["n"], 0)

    def test_commit_sem_excecao(self):
        """Sem exceção, o INSERT é comitado normalmente."""
        with db_cursor() as cur:
            cur.execute("INSERT INTO editora(nome) VALUES ('Editora Real')")
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM editora WHERE nome = 'Editora Real'")
            self.assertEqual(cur.fetchone()["n"], 1)


class TestForeignKeys(SigbefTestCase):
    """PRAGMA foreign_keys = ON está ativo nas conexões do módulo."""

    def test_emprestimo_com_exemplar_inexistente_falha(self):
        usuario = self.criar_usuario(matricula="fk1")
        with self.assertRaises(sqlite3.IntegrityError):
            with db_cursor() as cur:
                cur.execute(
                    "INSERT INTO emprestimo(exemplar_id, usuario_id, data_prevista) "
                    "VALUES (?, ?, datetime('now', '+7 days'))",
                    (99999, usuario["id"]),
                )

    def test_emprestimo_com_usuario_inexistente_falha(self):
        livro = self.criar_livro(exemplares=1)
        exemplar_id = livro["exemplares"][0][0]
        with self.assertRaises(sqlite3.IntegrityError):
            with db_cursor() as cur:
                cur.execute(
                    "INSERT INTO emprestimo(exemplar_id, usuario_id, data_prevista) "
                    "VALUES (?, ?, datetime('now', '+7 days'))",
                    (exemplar_id, 99999),
                )


class TestConexao(SigbefTestCase):
    """Configuração da conexão para uso concorrente (balcão + kiosk)."""

    def test_journal_mode_wal(self):
        conn = database.get_connection()
        try:
            modo = conn.execute("PRAGMA journal_mode").fetchone()[0]
            self.assertEqual(modo.lower(), "wal")
        finally:
            conn.close()

    def test_escritas_de_duas_conexoes_abertas(self):
        """Duas conexões abertas ao mesmo tempo escrevem em sequência
        sem 'database is locked'."""
        c1 = database.get_connection()
        c2 = database.get_connection()
        try:
            c1.execute("INSERT INTO configuracao(chave, valor) VALUES ('t1','1')")
            c1.commit()
            c2.execute("INSERT INTO configuracao(chave, valor) VALUES ('t2','2')")
            c2.commit()
            n = c1.execute("SELECT COUNT(*) FROM configuracao "
                           "WHERE chave IN ('t1','t2')").fetchone()[0]
            self.assertEqual(n, 2)
        finally:
            c1.close()
            c2.close()


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
