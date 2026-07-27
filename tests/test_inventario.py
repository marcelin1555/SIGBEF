"""
SIGBEF — Conferência do acervo.

A conferência acontece de pé, no meio da estante, com o leitor na mão.
Os testes aqui cobrem sobretudo o que dá errado nesse cenário: passar o
mesmo livro duas vezes, esquecer um pedaço da prateleira, achar na
estante o livro que o sistema dava como emprestado.

Uso:
    python -m unittest tests.test_inventario -v
"""
from __future__ import annotations

import unittest

from tests.base import SigbefTestCase

from sigbef import inventario, servicos
from sigbef.servicos import RegraNegocioError


class InventarioTestCase(SigbefTestCase):
    def setUp(self):
        super().setUp()
        self.livro = self.criar_livro(titulo="Acervo", exemplares=5)
        self.criar_usuario(matricula="a1", nome="Ana")
        self.cod = [e[1] for e in self.livro["exemplares"]]

    def abrir(self):
        return inventario.abrir("Conferência de teste")["id"]

    def emprestar(self, codigo, matricula):
        return servicos.realizar_emprestimo(codigo_exemplar=codigo,
                                             matricula_usuario=matricula)


class TestCicloDaConferencia(InventarioTestCase):

    def test_abre_e_aparece_como_em_andamento(self):
        self.assertIsNone(inventario.em_andamento())
        inv = self.abrir()
        self.assertEqual(inventario.em_andamento()["id"], inv)

    def test_duas_conferencias_ao_mesmo_tempo_sao_recusadas(self):
        """Divididas em duas, as leituras fariam as duas acusarem sumiço."""
        self.abrir()
        with self.assertRaises(RegraNegocioError):
            inventario.abrir("outra")

    def test_encerrar_libera_para_a_proxima(self):
        inv = self.abrir()
        inventario.encerrar(inv)
        self.assertIsNone(inventario.em_andamento())
        self.assertTrue(inventario.abrir("segunda"))

    def test_encerrar_duas_vezes_e_recusado(self):
        inv = self.abrir()
        inventario.encerrar(inv)
        with self.assertRaises(RegraNegocioError):
            inventario.encerrar(inv)

    def test_conferencia_encerrada_nao_aceita_leitura(self):
        inv = self.abrir()
        inventario.encerrar(inv)
        with self.assertRaises(RegraNegocioError):
            inventario.registrar_leitura(inv, self.cod[0])


class TestLeitura(InventarioTestCase):

    def test_leitura_conta_uma_vez(self):
        inv = self.abrir()
        inventario.registrar_leitura(inv, self.cod[0])
        self.assertEqual(inventario.obter(inv)["lidos"], 1)

    def test_mesmo_exemplar_duas_vezes_nao_duplica(self):
        """Acontece o tempo todo: a pessoa perde a conta na prateleira."""
        inv = self.abrir()
        primeira = inventario.registrar_leitura(inv, self.cod[0])
        segunda = inventario.registrar_leitura(inv, self.cod[0])
        self.assertFalse(primeira["repetido"])
        self.assertTrue(segunda["repetido"])
        self.assertEqual(inventario.obter(inv)["lidos"], 1)

    def test_aceita_tombo_alem_do_codigo_de_barras(self):
        inv = self.abrir()
        tombo = servicos.detalhes_livro(
            self.livro["livro_id"])["exemplares"][0]["numero_tombo"]
        r = inventario.registrar_leitura(inv, tombo)
        self.assertFalse(r["repetido"])

    def test_codigo_desconhecido_avisa_em_vez_de_ignorar(self):
        """Pode ser livro nunca cadastrado — a bibliotecária precisa saber."""
        inv = self.abrir()
        with self.assertRaises(RegraNegocioError):
            inventario.registrar_leitura(inv, "CODIGO-QUE-NAO-EXISTE")

    def test_emprestado_encontrado_na_estante_e_sinalizado(self):
        inv = self.abrir()
        self.emprestar(self.cod[0], "a1")
        r = inventario.registrar_leitura(inv, self.cod[0])
        self.assertTrue(r["inesperado"])

    def test_baixado_encontrado_na_estante_e_sinalizado(self):
        servicos.baixar_exemplar(self.cod[0], "EXTRAVIADO")
        inv = self.abrir()
        r = inventario.registrar_leitura(inv, self.cod[0])
        self.assertTrue(r["inesperado"])

    def test_exemplar_normal_nao_e_sinalizado(self):
        inv = self.abrir()
        r = inventario.registrar_leitura(inv, self.cod[0])
        self.assertFalse(r["inesperado"])


class TestResultado(InventarioTestCase):
    """As três listas respondem perguntas diferentes, e não podem se
    misturar: uma gera busca na estante, outra é só conferência, a
    terceira gera correção no cadastro."""

    def test_o_que_nao_foi_lido_aparece_como_nao_encontrado(self):
        inv = self.abrir()
        for c in self.cod[:3]:
            inventario.registrar_leitura(inv, c)
        res = inventario.encerrar(inv)
        faltando = {x["codigo_barras"] for x in res["nao_encontrados"]}
        self.assertEqual(faltando, set(self.cod[3:]))

    def test_emprestado_nao_conta_como_sumido(self):
        """O livro está com o aluno; a estante vazia ali é o esperado."""
        self.emprestar(self.cod[4], "a1")
        inv = self.abrir()
        for c in self.cod[:4]:
            inventario.registrar_leitura(inv, c)
        res = inventario.encerrar(inv)

        self.assertEqual(res["nao_encontrados"], [])
        self.assertEqual(len(res["fora_como_esperado"]), 1)
        self.assertEqual(res["fora_como_esperado"][0]["com_quem"], "Ana")

    def test_baixado_nao_conta_como_sumido(self):
        servicos.baixar_exemplar(self.cod[4], "DESCARTADO")
        inv = self.abrir()
        for c in self.cod[:4]:
            inventario.registrar_leitura(inv, c)
        res = inventario.encerrar(inv)
        self.assertEqual(res["nao_encontrados"], [])

    def test_apareceu_o_que_o_sistema_dava_como_fora(self):
        servicos.baixar_exemplar(self.cod[0], "EXTRAVIADO")
        inv = self.abrir()
        inventario.registrar_leitura(inv, self.cod[0])
        res = inventario.encerrar(inv)

        self.assertEqual(len(res["apareceram"]), 1)
        self.assertEqual(res["apareceram"][0]["status"], "BAIXADO")
        self.assertEqual(res["apareceram"][0]["motivo_baixa"], "EXTRAVIADO")

    def test_acervo_completo_conferido_nao_acusa_nada(self):
        inv = self.abrir()
        for c in self.cod:
            inventario.registrar_leitura(inv, c)
        res = inventario.encerrar(inv)
        self.assertEqual(res["nao_encontrados"], [])
        self.assertEqual(res["apareceram"], [])
        self.assertEqual(res["lidos"], 5)
        self.assertEqual(res["no_acervo"], 5)

    def test_resultado_parcial_antes_de_encerrar(self):
        """A bibliotecária confere o andamento sem fechar a conferência."""
        inv = self.abrir()
        inventario.registrar_leitura(inv, self.cod[0])
        res = inventario.resultado(inv)
        self.assertEqual(res["lidos"], 1)
        self.assertIsNone(res["encerrado_em"])
        self.assertIsNotNone(inventario.em_andamento())

    def test_baixado_sai_da_contagem_do_acervo(self):
        servicos.baixar_exemplar(self.cod[0], "DANIFICADO")
        inv = self.abrir()
        self.assertEqual(inventario.resultado(inv)["no_acervo"], 4)


class TestHistorico(InventarioTestCase):

    def test_listar_traz_da_mais_recente_para_a_mais_antiga(self):
        a = self.abrir()
        inventario.encerrar(a)
        b = inventario.abrir("segunda")["id"]
        historico = inventario.listar()
        self.assertEqual([i["id"] for i in historico], [b, a])

    def test_listar_conta_os_lidos_de_cada_uma(self):
        inv = self.abrir()
        inventario.registrar_leitura(inv, self.cod[0])
        inventario.registrar_leitura(inv, self.cod[1])
        inventario.encerrar(inv)
        self.assertEqual(inventario.listar()[0]["lidos"], 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
