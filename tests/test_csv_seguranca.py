"""Testes de segurança: neutralização de injeção de fórmula em CSV
(CWE-1236) nos relatórios exportáveis do painel."""
from __future__ import annotations

import unittest

from sigbef.ui_painel import _neutralizar_celula_csv


class TestNeutralizarCelulaCsv(unittest.TestCase):
    def test_formula_igual_e_neutralizada(self):
        self.assertEqual(_neutralizar_celula_csv("=HYPERLINK(\"http://x\")"),
                         "'=HYPERLINK(\"http://x\")")

    def test_formula_mais_e_neutralizada(self):
        self.assertEqual(_neutralizar_celula_csv("+cmd|'/c calc'!A1"),
                         "'+cmd|'/c calc'!A1")

    def test_formula_menos_e_neutralizada(self):
        self.assertEqual(_neutralizar_celula_csv("-2+3"), "'-2+3")

    def test_formula_arroba_e_neutralizada(self):
        self.assertEqual(_neutralizar_celula_csv("@SUM(A1:A9)"), "'@SUM(A1:A9)")

    def test_tab_e_neutralizado(self):
        self.assertEqual(_neutralizar_celula_csv("\tmalicioso"),
                         "'\tmalicioso")

    def test_titulo_normal_passa_intacto(self):
        self.assertEqual(_neutralizar_celula_csv("Dom Casmurro"),
                         "Dom Casmurro")

    def test_numero_passa_intacto(self):
        self.assertEqual(_neutralizar_celula_csv(42), 42)

    def test_vazio_passa_intacto(self):
        self.assertEqual(_neutralizar_celula_csv(""), "")

    def test_sinal_negativo_no_meio_nao_afeta(self):
        # só o PRIMEIRO caractere importa para o Excel interpretar como fórmula
        self.assertEqual(_neutralizar_celula_csv("Livro-teste"), "Livro-teste")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
