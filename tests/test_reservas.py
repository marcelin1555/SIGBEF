"""Testes das reservas com fila de espera (sigbef/reservas.py)."""
from __future__ import annotations

from tests.base import SigbefTestCase

from sigbef import reservas, servicos
from sigbef.database import db_cursor
from sigbef.servicos import RegraNegocioError


class ReservasTestCase(SigbefTestCase):
    """Cenário base: 1 livro com 1 exemplar, emprestado pro usuário A."""

    def setUp(self):
        super().setUp()
        self.ua = self.criar_usuario(matricula="ua", nome="Ana A")
        self.ub = self.criar_usuario(matricula="ub", nome="Beto B")
        self.uc = self.criar_usuario(matricula="uc", nome="Caio C")
        self.livro = self.criar_livro(titulo="Único Exemplar", exemplares=1)
        self.livro_id = self.livro["livro_id"]
        self.ex_id, self.codigo = self.livro["exemplares"][0]
        servicos.realizar_emprestimo(codigo_exemplar=self.codigo,
                                     matricula_usuario="ua")

    # ------------------------------------------------------------------
    def status_exemplar(self):
        with db_cursor() as cur:
            cur.execute("SELECT status FROM exemplar WHERE id = ?",
                        (self.ex_id,))
            return cur.fetchone()["status"]

    def reserva(self, reserva_id):
        with db_cursor() as cur:
            cur.execute("SELECT * FROM reserva WHERE id = ?", (reserva_id,))
            return dict(cur.fetchone())

    def vencer_prazo(self, reserva_id):
        """Simula prazo de retirada estourado (ontem)."""
        with db_cursor() as cur:
            cur.execute(
                "UPDATE reserva SET disponivel_ate = "
                "date('now','localtime','-1 day') WHERE id = ?",
                (reserva_id,))


class TestCriarReserva(ReservasTestCase):
    def test_reserva_entra_na_fila_em_ordem(self):
        r1 = reservas.criar_reserva(self.livro_id, self.ub["id"])
        r2 = reservas.criar_reserva(self.livro_id, self.uc["id"])
        self.assertEqual(r1["posicao"], 1)
        self.assertEqual(r2["posicao"], 2)
        self.assertEqual(r1["titulo"], "Único Exemplar")

    def test_livro_com_exemplar_disponivel_nao_reserva(self):
        outro = self.criar_livro(titulo="Sobrando", exemplares=2)
        with self.assertRaises(RegraNegocioError):
            reservas.criar_reserva(outro["livro_id"], self.ub["id"])

    def test_reserva_duplicada_do_mesmo_livro(self):
        reservas.criar_reserva(self.livro_id, self.ub["id"])
        with self.assertRaises(RegraNegocioError):
            reservas.criar_reserva(self.livro_id, self.ub["id"])

    def test_limite_de_reservas_ativas(self):
        # 3 livros esgotados + 1 extra: a 4ª reserva estoura o limite.
        # Um professor (limite 5 empréstimos) esgota os exemplares.
        self.criar_usuario(matricula="prof1", perfil="PROFESSOR",
                           nome="Prof Fila")
        esgotados = []
        for i in range(4):
            liv = self.criar_livro(titulo=f"Esgotado {i}", exemplares=1)
            servicos.realizar_emprestimo(
                codigo_exemplar=liv["exemplares"][0][1],
                matricula_usuario="prof1")
            esgotados.append(liv["livro_id"])
        for lid in esgotados[:3]:
            reservas.criar_reserva(lid, self.ub["id"])
        with self.assertRaises(RegraNegocioError):
            reservas.criar_reserva(esgotados[3], self.ub["id"])

    def test_livro_inexistente(self):
        with self.assertRaises(RegraNegocioError):
            reservas.criar_reserva(99999, self.ub["id"])


class TestDevolucaoPromoveFila(ReservasTestCase):
    def test_devolucao_separa_exemplar_pro_primeiro_da_fila(self):
        r = reservas.criar_reserva(self.livro_id, self.ub["id"])
        res = servicos.realizar_devolucao(codigo_exemplar=self.codigo)
        self.assertEqual(res["reservado_para"], "Beto B")
        self.assertIsNotNone(res["reserva_ate"])
        self.assertEqual(self.status_exemplar(), "RESERVADO")
        dados = self.reserva(r["id"])
        self.assertEqual(dados["exemplar_id"], self.ex_id)
        self.assertIsNotNone(dados["disponivel_ate"])

    def test_devolucao_sem_fila_libera_exemplar(self):
        res = servicos.realizar_devolucao(codigo_exemplar=self.codigo)
        self.assertIsNone(res["reservado_para"])
        self.assertEqual(self.status_exemplar(), "DISPONIVEL")

    def test_exemplar_reservado_nao_conta_como_disponivel(self):
        reservas.criar_reserva(self.livro_id, self.ub["id"])
        servicos.realizar_devolucao(codigo_exemplar=self.codigo)
        liv = servicos.listar_livros("Único Exemplar")[0]
        self.assertEqual(liv["disponiveis"], 0)


class TestEmprestimoRespeitaReserva(ReservasTestCase):
    def setUp(self):
        super().setUp()
        self.r = reservas.criar_reserva(self.livro_id, self.ub["id"])
        servicos.realizar_devolucao(codigo_exemplar=self.codigo)

    def test_dono_da_vez_leva_e_reserva_e_atendida(self):
        res = servicos.realizar_emprestimo(codigo_exemplar=self.codigo,
                                           matricula_usuario="ub")
        self.assertEqual(res["usuario_nome"], "Beto B")
        self.assertEqual(self.reserva(self.r["id"])["status"], "ATENDIDA")
        self.assertEqual(self.status_exemplar(), "EMPRESTADO")

    def test_outro_usuario_nao_leva_exemplar_reservado(self):
        with self.assertRaises(RegraNegocioError):
            servicos.realizar_emprestimo(codigo_exemplar=self.codigo,
                                         matricula_usuario="uc")
        self.assertEqual(self.status_exemplar(), "RESERVADO")

    def test_prazo_vencido_passa_a_vez_pro_proximo(self):
        r2 = reservas.criar_reserva(self.livro_id, self.uc["id"])
        self.vencer_prazo(self.r["id"])
        # Caio (2º da fila) agora consegue levar; a do Beto expirou
        servicos.realizar_emprestimo(codigo_exemplar=self.codigo,
                                     matricula_usuario="uc")
        self.assertEqual(self.reserva(self.r["id"])["status"], "EXPIRADA")
        self.assertEqual(self.reserva(r2["id"])["status"], "ATENDIDA")

    def test_prazo_vencido_sem_fila_libera_geral(self):
        self.vencer_prazo(self.r["id"])
        servicos.realizar_emprestimo(codigo_exemplar=self.codigo,
                                     matricula_usuario="uc")
        self.assertEqual(self.reserva(self.r["id"])["status"], "EXPIRADA")


class TestCancelamento(ReservasTestCase):
    def test_cancelar_propria_reserva(self):
        r = reservas.criar_reserva(self.livro_id, self.ub["id"])
        reservas.cancelar_reserva(r["id"], usuario_id=self.ub["id"])
        self.assertEqual(self.reserva(r["id"])["status"], "CANCELADA")

    def test_nao_cancela_reserva_alheia(self):
        r = reservas.criar_reserva(self.livro_id, self.ub["id"])
        with self.assertRaises(RegraNegocioError):
            reservas.cancelar_reserva(r["id"], usuario_id=self.uc["id"])

    def test_cancelar_com_exemplar_separado_promove_proximo(self):
        r1 = reservas.criar_reserva(self.livro_id, self.ub["id"])
        r2 = reservas.criar_reserva(self.livro_id, self.uc["id"])
        servicos.realizar_devolucao(codigo_exemplar=self.codigo)
        reservas.cancelar_reserva(r1["id"], usuario_id=self.ub["id"])
        dados2 = self.reserva(r2["id"])
        self.assertEqual(dados2["exemplar_id"], self.ex_id)
        self.assertEqual(self.status_exemplar(), "RESERVADO")

    def test_cancelar_ultimo_da_fila_libera_exemplar(self):
        r = reservas.criar_reserva(self.livro_id, self.ub["id"])
        servicos.realizar_devolucao(codigo_exemplar=self.codigo)
        reservas.cancelar_reserva(r["id"], usuario_id=self.ub["id"])
        self.assertEqual(self.status_exemplar(), "DISPONIVEL")


class TestConsultas(ReservasTestCase):
    def test_listar_reservas_do_usuario(self):
        reservas.criar_reserva(self.livro_id, self.ub["id"])
        minhas = reservas.listar_reservas_usuario(self.ub["id"])
        self.assertEqual(len(minhas), 1)
        self.assertEqual(minhas[0]["titulo"], "Único Exemplar")
        self.assertEqual(minhas[0]["posicao"], 1)

    def test_fila_do_livro_em_ordem(self):
        reservas.criar_reserva(self.livro_id, self.ub["id"])
        reservas.criar_reserva(self.livro_id, self.uc["id"])
        fila = reservas.fila_do_livro(self.livro_id)
        self.assertEqual([f["nome"] for f in fila], ["Beto B", "Caio C"])


class TestExemplarNovoAtendeFila(ReservasTestCase):
    def test_adicionar_exemplar_separa_pra_fila(self):
        r = reservas.criar_reserva(self.livro_id, self.ub["id"])
        novos = servicos.adicionar_exemplares(self.livro_id, 1)
        novo_id = novos[0][0]
        dados = self.reserva(r["id"])
        self.assertEqual(dados["exemplar_id"], novo_id)
        with db_cursor() as cur:
            cur.execute("SELECT status FROM exemplar WHERE id = ?",
                        (novo_id,))
            self.assertEqual(cur.fetchone()["status"], "RESERVADO")


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
