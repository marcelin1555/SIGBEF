"""Lógica de cores do tema e limite de janela ao tamanho da tela."""
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


class JanelaFalsa:
    """Dublê de janela Tk: registra o que `centralizar_janela` pediu.

    Evita abrir Tk de verdade — o teste roda no CI, que não tem tela.
    """

    def __init__(self, largura_tela, altura_tela):
        self._sw, self._sh = largura_tela, altura_tela
        self.geometria = None
        self.minimo = None

    def update_idletasks(self):
        pass

    def winfo_screenwidth(self):
        return self._sw

    def winfo_screenheight(self):
        return self._sh

    def geometry(self, valor):
        self.geometria = valor

    def minsize(self, largura, altura):
        self.minimo = (largura, altura)

    # ------------------------------------------------------------------
    @property
    def tamanho(self):
        return tuple(int(v) for v in self.geometria.split("+")[0].split("x"))


class TestCentralizarJanela(unittest.TestCase):
    """A janela não pode nascer maior que a tela, nem ficar presa acima dela.

    Defeito real que originou estes testes: as janelas principais faziam
    `centralizar_janela(...)` e logo abaixo `self.minsize(1180, 700)`. No
    laboratório da escola (1366x768 a 125% de escala, cerca de 1093x614
    úteis) a janela ficava travada em 1180x700, com a faixa de botões
    fora da tela e sem como redimensionar.
    """

    TELA_ESCOLA = (1093, 614)

    def test_janela_maior_que_a_tela_e_reduzida(self):
        j = JanelaFalsa(*self.TELA_ESCOLA)
        tema.centralizar_janela(j, 1280, 780)
        larg, alt = j.tamanho
        self.assertLessEqual(larg, self.TELA_ESCOLA[0])
        self.assertLessEqual(alt, self.TELA_ESCOLA[1])

    def test_minimo_nao_pode_aprisionar_a_janela(self):
        """O mínimo também é limitado pela tela — é o bug de origem."""
        j = JanelaFalsa(*self.TELA_ESCOLA)
        tema.centralizar_janela(j, 1280, 780, minimo=(1180, 700))
        self.assertIsNotNone(j.minimo)
        self.assertLessEqual(j.minimo[0], self.TELA_ESCOLA[0])
        self.assertLessEqual(j.minimo[1], self.TELA_ESCOLA[1])

    def test_minimo_nunca_maior_que_a_propria_janela(self):
        j = JanelaFalsa(*self.TELA_ESCOLA)
        tema.centralizar_janela(j, 1280, 780, minimo=(1180, 700))
        larg, alt = j.tamanho
        self.assertLessEqual(j.minimo[0], larg)
        self.assertLessEqual(j.minimo[1], alt)

    def test_tela_grande_respeita_o_tamanho_pedido(self):
        """Em monitor folgado, nada é reduzido."""
        j = JanelaFalsa(1920, 1080)
        tema.centralizar_janela(j, 1280, 780, minimo=(1180, 700))
        self.assertEqual(j.tamanho, (1280, 780))
        self.assertEqual(j.minimo, (1180, 700))

    def test_sem_minimo_nao_chama_minsize(self):
        j = JanelaFalsa(1920, 1080)
        tema.centralizar_janela(j, 600, 400)
        self.assertIsNone(j.minimo)

    def test_janela_nunca_nasce_fora_da_tela(self):
        j = JanelaFalsa(*self.TELA_ESCOLA)
        tema.centralizar_janela(j, 1280, 780)
        # geometria é "LARGxALT+X+Y"
        x, y = (int(v) for v in j.geometria.split("+")[1:])
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)

    def test_tela_minuscula_nao_gera_tamanho_negativo(self):
        """Guarda contra piso: tela absurda não pode virar largura < 0."""
        j = JanelaFalsa(200, 150)
        tema.centralizar_janela(j, 1280, 780, minimo=(1180, 700))
        larg, alt = j.tamanho
        self.assertGreater(larg, 0)
        self.assertGreater(alt, 0)


class TestJanelasDoSistemaUsamOLimite(unittest.TestCase):
    """Nenhuma janela pode chamar minsize por fora do helper.

    É exatamente assim que o limite foi desfeito da primeira vez.
    """

    def test_nenhum_modulo_de_ui_chama_minsize_direto(self):
        import ast
        from pathlib import Path

        pacote = Path(__file__).resolve().parent.parent / "sigbef"
        infratores = []
        for arquivo in pacote.glob("ui_*.py"):
            if arquivo.name == "ui_tema.py":
                continue  # é quem implementa o limite
            tree = ast.parse(arquivo.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "minsize"):
                    infratores.append(f"{arquivo.name}:{node.lineno}")
        self.assertEqual(
            infratores, [],
            "minsize() chamado fora de ui_tema.centralizar_janela — isso "
            "desfaz o limite de tamanho da tela. Use o parâmetro "
            "`minimo=` de centralizar_janela.")


if __name__ == "__main__":
    unittest.main()
