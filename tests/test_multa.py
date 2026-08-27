"""
SIGBEF — Modelo de multa: lançado, recebido e isento são três números.

Até a v1.10.4 existia uma coluna só, `multa`, servindo ao mesmo tempo de
**valor lançado** e de **saldo devedor**. Duas consequências reais:

1. `quitar_multa` fazia `UPDATE emprestimo SET multa = 0`. Depois de
   receber o dinheiro, o sistema não tinha mais registro de que a multa
   tinha existido. Não dava para conferir caixa, nem responder "quanto a
   biblioteca arrecadou em multa este ano".

2. `relatorio_movimentacao` somava essa mesma coluna e mostrava o total
   sob o rótulo **"Multas lançadas (R$)"**. Como quitar zerava a coluna,
   o número apresentado à direção era, na verdade, "multas que ninguém
   pagou" — e diminuía toda vez que alguém pagava.

Não havia isenção: perdoar uma multa só era possível fingindo que ela
nunca existiu, pelo mesmo botão de quitar.
"""
from __future__ import annotations

from datetime import date, timedelta

from tests.base import SigbefTestCase

from sigbef import servicos
from sigbef.database import db_cursor
from sigbef.servicos import RegraNegocioError


class MultaTestCase(SigbefTestCase):
    """Monta um empréstimo devolvido com atraso — o único jeito de existir
    multa no sistema."""

    def criar_emprestimo_com_multa(self, matricula="a1", dias_atraso=4):
        self.criar_usuario(matricula=matricula, nome="Aluno " + matricula)
        livro = self.criar_livro(titulo="Livro " + matricula)
        codigo = livro["exemplares"][0][1]
        emp = servicos.realizar_emprestimo(codigo_exemplar=codigo,
                                           matricula_usuario=matricula)
        passada = (date.today() - timedelta(days=dias_atraso)).isoformat()
        with db_cursor() as cur:
            cur.execute("UPDATE emprestimo SET data_prevista = ? WHERE id = ?",
                        (passada, emp["id"]))
        servicos.realizar_devolucao(codigo_exemplar=codigo)
        return emp["id"]

    def multa_lancada(self, emprestimo_id):
        with db_cursor() as cur:
            cur.execute("SELECT multa FROM emprestimo WHERE id = ?",
                        (emprestimo_id,))
            return round(float(cur.fetchone()["multa"]), 2)


class TestQuitar(MultaTestCase):

    def test_quitar_nao_apaga_o_valor_lancado(self):
        """É o defeito de origem: quitar destruía o histórico."""
        emp = self.criar_emprestimo_com_multa()
        lancado = self.multa_lancada(emp)
        self.assertGreater(lancado, 0)

        servicos.quitar_multa(emp)

        self.assertEqual(self.multa_lancada(emp), lancado,
                         "o valor lançado tem que sobreviver à quitação")
        self.assertEqual(servicos.saldo_multa(emp), 0.0)

    def test_quitar_zera_o_saldo_do_usuario(self):
        emp = self.criar_emprestimo_com_multa()
        usuario_id = servicos.listar_usuarios("a1")[0]["id"]
        self.assertGreater(
            servicos.status_usuario(usuario_id).multas_em_aberto, 0)
        servicos.quitar_multa(emp)
        st = servicos.status_usuario(usuario_id)
        self.assertEqual(st.multas_em_aberto, 0.0)
        self.assertTrue(st.pode_pegar)

    def test_pagamento_parcial_deixa_o_resto_em_aberto(self):
        emp = self.criar_emprestimo_com_multa(dias_atraso=4)
        saldo = servicos.saldo_multa(emp)
        metade = round(saldo / 2, 2)
        restante = servicos.quitar_multa(emp, valor=metade)
        self.assertAlmostEqual(restante, saldo - metade, places=2)
        self.assertGreater(servicos.saldo_multa(emp), 0)

    def test_nao_aceita_receber_mais_que_o_saldo(self):
        emp = self.criar_emprestimo_com_multa()
        with self.assertRaises(RegraNegocioError):
            servicos.quitar_multa(emp, valor=servicos.saldo_multa(emp) + 10)

    def test_quitar_duas_vezes_e_recusado(self):
        emp = self.criar_emprestimo_com_multa()
        servicos.quitar_multa(emp)
        with self.assertRaises(RegraNegocioError):
            servicos.quitar_multa(emp)

    def test_quitacao_fica_na_auditoria_com_o_valor(self):
        emp = self.criar_emprestimo_com_multa()
        saldo = servicos.saldo_multa(emp)
        servicos.quitar_multa(emp)
        reg = [r for r in servicos.listar_auditoria()
               if r["acao"] == "QUITAR_MULTA"]
        self.assertEqual(len(reg), 1)
        self.assertIn("recebido={:.2f}".format(saldo), reg[0]["detalhes"])


class TestIsentar(MultaTestCase):

    def test_isentar_zera_o_saldo_sem_apagar_o_lancado(self):
        emp = self.criar_emprestimo_com_multa()
        lancado = self.multa_lancada(emp)
        servicos.isentar_multa(emp, "Livro danificado por infiltração da sala")
        self.assertEqual(self.multa_lancada(emp), lancado)
        self.assertEqual(servicos.saldo_multa(emp), 0.0)

    def test_motivo_e_obrigatorio(self):
        emp = self.criar_emprestimo_com_multa()
        for vazio in ("", "   ", None):
            with self.subTest(motivo=vazio):
                with self.assertRaises(RegraNegocioError):
                    servicos.isentar_multa(emp, vazio)
        self.assertGreater(servicos.saldo_multa(emp), 0,
                           "recusar a isenção não pode ter mexido no saldo")

    def test_motivo_fica_gravado_e_auditado(self):
        emp = self.criar_emprestimo_com_multa()
        servicos.isentar_multa(emp, "Atraso por feriado municipal")
        with db_cursor() as cur:
            cur.execute("SELECT multa_motivo_isencao AS m "
                        "FROM emprestimo WHERE id = ?", (emp,))
            self.assertEqual(cur.fetchone()["m"],
                             "Atraso por feriado municipal")
        reg = [r for r in servicos.listar_auditoria()
               if r["acao"] == "ISENTAR_MULTA"]
        self.assertEqual(len(reg), 1)
        self.assertIn("Atraso por feriado municipal", reg[0]["detalhes"])

    def test_isentar_e_quitar_sao_acoes_distintas_na_auditoria(self):
        """Perdoar e receber contam histórias diferentes.

        Antes as duas coisas passavam pelo mesmo botão, então o histórico
        não distinguia dinheiro que entrou de dívida que foi perdoada.
        """
        a = self.criar_emprestimo_com_multa("a1")
        b = self.criar_emprestimo_com_multa("a2")
        servicos.quitar_multa(a)
        servicos.isentar_multa(b, "Aluno transferido de escola")
        acoes = [r["acao"] for r in servicos.listar_auditoria()]
        self.assertIn("QUITAR_MULTA", acoes)
        self.assertIn("ISENTAR_MULTA", acoes)


class TestRelatorioNaoMente(MultaTestCase):

    def test_multas_lancadas_nao_encolhe_quando_alguem_paga(self):
        """O rótulo diz "Multas lançadas". Tem que ser isso mesmo."""
        emp = self.criar_emprestimo_com_multa()
        antes = servicos.relatorio_movimentacao()["multa_total"]
        self.assertGreater(antes, 0)

        servicos.quitar_multa(emp)

        depois = servicos.relatorio_movimentacao()
        self.assertEqual(depois["multa_total"], antes,
                         "pagar a multa não pode reduzir o total lançado")
        self.assertEqual(depois["multa_recebida"], antes)
        self.assertEqual(depois["multa_em_aberto"], 0.0)

    def test_isento_aparece_separado_do_recebido(self):
        a = self.criar_emprestimo_com_multa("a1", dias_atraso=3)
        b = self.criar_emprestimo_com_multa("a2", dias_atraso=5)
        valor_a = servicos.saldo_multa(a)
        valor_b = servicos.saldo_multa(b)

        servicos.quitar_multa(a)
        servicos.isentar_multa(b, "Situação familiar")

        rel = servicos.relatorio_movimentacao()
        self.assertAlmostEqual(rel["multa_recebida"], valor_a, places=2)
        self.assertAlmostEqual(rel["multa_isenta"], valor_b, places=2)
        self.assertAlmostEqual(rel["multa_total"], valor_a + valor_b, places=2)
        self.assertEqual(rel["multa_em_aberto"], 0.0)

    def test_em_aberto_reflete_o_que_falta_receber(self):
        self.criar_emprestimo_com_multa("a1")
        rel = servicos.relatorio_movimentacao()
        self.assertAlmostEqual(rel["multa_em_aberto"], rel["multa_total"],
                               places=2)
        self.assertEqual(rel["multa_recebida"], 0.0)
        self.assertEqual(rel["multa_isenta"], 0.0)


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
