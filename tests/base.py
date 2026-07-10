"""
SIGBEF — Base comum dos testes.

Aponta o banco para um arquivo temporário ANTES de importar qualquer módulo
do sigbef (database.py lê SIGBEF_DB_PATH no import) e recria o banco zerado
em cada teste, garantindo isolamento sem tocar no banco real.

Uso:
    from tests.base import SigbefTestCase

    class TestAlgo(SigbefTestCase):
        def test_x(self):
            ...
"""
from __future__ import annotations

import os
import tempfile

# Precisa acontecer antes do primeiro import de sigbef.database
_TMPDIR = tempfile.mkdtemp(prefix="sigbef-tests-")
os.environ.setdefault("SIGBEF_DB_PATH", os.path.join(_TMPDIR, "sigbef-test.db"))

import unittest
from pathlib import Path

from sigbef import database


class SigbefTestCase(unittest.TestCase):
    """TestCase com banco SQLite temporário zerado a cada teste."""

    def setUp(self):
        Path(database.DB_PATH).unlink(missing_ok=True)
        database.init_database()

    # ------------------------------------------------------------------
    # Helpers de massa de dados
    # ------------------------------------------------------------------
    def criar_usuario(self, matricula="aluno1", perfil="ALUNO",
                      nome="Aluno de Teste", senha="senha123", **kw):
        from sigbef import servicos
        return servicos.cadastrar_usuario(
            nome=nome, matricula=matricula, perfil=perfil, senha=senha, **kw)

    def criar_livro(self, titulo="Livro de Teste", exemplares=1, **kw):
        from sigbef import servicos
        kw.setdefault("autores", ["Autora de Teste"])
        return servicos.cadastrar_livro(
            titulo=titulo, quantidade_exemplares=exemplares, **kw)
