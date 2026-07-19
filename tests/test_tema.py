"""Lógica de cores do tema (funções puras, sem abrir Tk)."""
import unittest

from sigbef import ui_tema as tema


class TestContraste(unittest.TestCase):
    def test_contraste_extremos(self):
        # Preto x branco é o contraste máximo da WCAG (21:1)
        self.assertAlmostEqual(tema.contraste("#000000", "#FFFFFF"), 21, delta=0.1)
        # Mesma cor não tem contraste (1:1)
        self.assertAlmostEqual(tema.contraste("#1F4E79", "#1F4E79"), 1, delta=0.01)

    def test_contraste_e_simetrico(self):
        a = tema.contraste("#1F4E79", "#FFFFFF")
        b = tema.contraste("#FFFFFF", "#1F4E79")
        self.assertAlmostEqual(a, b, delta=0.001)


class TestPrimariaClaraDemais(unittest.TestCase):
    def test_presets_todos_passam(self):
        """As 5 paletas prontas têm primária escura o suficiente."""
        for chave, preset in tema.PRESETS.items():
            self.assertFalse(
                tema.primaria_clara_demais(preset["primaria"]),
                f"preset {chave} reprovado no contraste")

    def test_cor_clara_e_reprovada(self):
        for clara in ("#FFFFFF", "#FFEB3B", "#8AD1FF", "#E0E0E0"):
            self.assertTrue(tema.primaria_clara_demais(clara),
                            f"{clara} deveria ser reprovada")

    def test_cor_escura_e_aprovada(self):
        for escura in ("#000000", "#1F4E79", "#4E342E", "#4527A0"):
            self.assertFalse(tema.primaria_clara_demais(escura),
                             f"{escura} deveria ser aprovada")


class TestDerivadasDaPrimaria(unittest.TestCase):
    def test_suave_e_mais_clara_que_a_primaria(self):
        suave = tema._mesclar_branco("#1F4E79", 0.65)
        self.assertGreater(tema._luminancia(suave),
                           tema._luminancia("#1F4E79"))

    def test_escura_e_mais_escura_que_a_primaria(self):
        escura = tema._ajustar_cor("#1F4E79", 0.72)
        self.assertLess(tema._luminancia(escura),
                        tema._luminancia("#1F4E79"))


if __name__ == "__main__":
    unittest.main()
