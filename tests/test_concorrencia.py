"""
SIGBEF — Dois pedidos ao mesmo tempo.

O módulo sqlite3 só abre a transação no primeiro INSERT/UPDATE. Os
SELECTs que conferem o limite rodavam fora dela, então dois empréstimos
simultâneos (balcão e app, ou duas bibliotecárias) liam o mesmo número
e os dois gravavam. Aqui o primeiro pedido é segurado exatamente entre
conferir e gravar, enquanto o segundo tenta passar.
"""
from __future__ import annotations

import threading
from unittest import mock

from tests.base import SigbefTestCase

from sigbef import database, servicos
from sigbef.database import db_cursor, set_config
from sigbef.servicos import RegraNegocioError

_GRAVACAO = "UPDATE exemplar SET status = 'EMPRESTADO'"


class TestEmprestimoSimultaneo(SigbefTestCase):

    def test_dois_pedidos_juntos_nao_furam_o_limite(self):
        set_config("LIMITE_ALUNO", "1")
        aluno = self.criar_usuario(matricula="corrida1")
        livro = self.criar_livro(exemplares=2)
        cod_a, cod_b = (c for _, c in livro["exemplares"])

        chegou = threading.Event()   # o pedido A conferiu e vai gravar
        b_acabou = threading.Event()
        original = database.get_connection

        def conexao_espiada():
            conn = original()
            if threading.current_thread().name == "A":
                def parar_antes_de_gravar(sql):
                    if sql.lstrip().startswith(_GRAVACAO):
                        chegou.set()
                        # Com a trava certa, B nem consegue começar e
                        # este tempo esgota; sem ela, B termina aqui.
                        b_acabou.wait(1.0)
                conn.set_trace_callback(parar_antes_de_gravar)
            return conn

        erros = {}

        def emprestar(nome, codigo):
            try:
                servicos.realizar_emprestimo(
                    codigo_exemplar=codigo,
                    matricula_usuario=aluno["matricula"])
            except RegraNegocioError as e:
                erros[nome] = e

        with mock.patch.object(database, "get_connection", conexao_espiada):
            a = threading.Thread(target=emprestar, args=("A", cod_a), name="A")
            a.start()
            self.assertTrue(chegou.wait(5), "pedido A não chegou a gravar")
            b = threading.Thread(target=emprestar, args=("B", cod_b), name="B")
            b.start()
            b.join(15)
            b_acabou.set()
            a.join(15)

        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM emprestimo "
                        "WHERE usuario_id = ? AND data_devolucao IS NULL",
                        (aluno["id"],))
            abertos = cur.fetchone()["n"]
        self.assertEqual(abertos, 1, "o aluno passou do limite de 1")
        self.assertIn("B", erros)
        self.assertIn("Limite", str(erros["B"]))
