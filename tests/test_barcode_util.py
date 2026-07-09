"""Testes de sigbef.barcode_util — geração de códigos e Code 128."""
import tests.base  # noqa: F401  # configura o ambiente de testes (deve ser o 1º import)

import unittest

from sigbef import barcode_util


class TestGerarCodigos(unittest.TestCase):
    """Geração de identificadores únicos EX.../US..."""

    def test_codigo_exemplar(self):
        """Prefixo EX + timestamp (12 dígitos) + sufixo aleatório (4 dígitos)."""
        cod = barcode_util.gerar_codigo_exemplar()
        self.assertTrue(cod.startswith("EX"))
        self.assertEqual(len(cod), 18)
        self.assertTrue(cod[2:].isdigit())

    def test_codigo_usuario(self):
        """Prefixo US + timestamp (12 dígitos) + sufixo aleatório (4 dígitos)."""
        cod = barcode_util.gerar_codigo_usuario()
        self.assertTrue(cod.startswith("US"))
        self.assertEqual(len(cod), 18)
        self.assertTrue(cod[2:].isdigit())


class TestCode128Valores(unittest.TestCase):
    """_code128b_valores: start + dados + checksum + stop."""

    def test_start_e_stop(self):
        valores = barcode_util._code128b_valores("AB")
        self.assertEqual(valores[0], 104)   # Start B
        self.assertEqual(valores[-1], 106)  # Stop

    def test_checksum_calculado_manualmente(self):
        """Para 'AB': dados são ord(ch)-32 e o checksum é a soma ponderada
        (start + 1*v1 + 2*v2 + ...) mod 103."""
        valores = barcode_util._code128b_valores("AB")
        v_a = ord("A") - 32  # 33
        v_b = ord("B") - 32  # 34
        checksum = (104 + 1 * v_a + 2 * v_b) % 103  # 205 % 103 = 102
        self.assertEqual(valores, [104, v_a, v_b, checksum, 106])

    def test_caractere_fora_da_faixa_vira_espaco(self):
        """COMPORTAMENTO REAL: caractere fora de 32..126 (ex.: 'ç') é
        codificado silenciosamente como espaço (valor 0)."""
        valores = barcode_util._code128b_valores("ç")
        self.assertEqual(valores[1], 0)


class TestCode128Barras(unittest.TestCase):
    """_code128b_barras: larguras em módulos e alternância barra/espaço."""

    def test_soma_de_modulos_por_simbolo(self):
        """Cada símbolo Code 128 soma 11 módulos, exceto o stop (13)."""
        valores = barcode_util._code128b_valores("AB")
        barras = barcode_util._code128b_barras("AB")
        # símbolos comuns têm 6 elementos; o stop tem 7
        self.assertEqual(len(barras), (len(valores) - 1) * 6 + 7)
        for i in range(len(valores) - 1):  # símbolos de 6 elementos
            grupo = barras[i * 6:(i + 1) * 6]
            self.assertEqual(sum(w for w, _ in grupo), 11,
                             f"símbolo {i} não soma 11 módulos")
        stop = barras[-7:]
        self.assertEqual(sum(w for w, _ in stop), 13)

    def test_alternancia_comeca_em_barra(self):
        """A sequência alterna barra/espaço, começando em barra."""
        barras = barcode_util._code128b_barras("AB")
        self.assertTrue(barras[0][1])  # primeiro elemento é barra
        for i, (_, eh_barra) in enumerate(barras):
            self.assertEqual(eh_barra, i % 2 == 0,
                             f"elemento {i} quebra a alternância")


class TestBarcodeSvg(unittest.TestCase):
    """barcode_svg: renderização SVG do código de barras."""

    def test_svg_basico(self):
        svg = barcode_util.barcode_svg("EX2401011200001234")
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("<rect", svg)
        self.assertIn("EX2401011200001234", svg)

    def test_escapa_texto_do_codigo(self):
        svg = barcode_util.barcode_svg("EX<1")
        self.assertIn("EX&lt;1", svg)
        self.assertNotIn(">EX<1<", svg)

    def test_sem_texto(self):
        svg = barcode_util.barcode_svg("EX123", mostrar_texto=False)
        self.assertNotIn("<text", svg)
        self.assertIn("<rect", svg)


class TestEtiquetasHtml(unittest.TestCase):
    """etiquetas_html: página de etiquetas de um livro."""

    EXEMPLARES = [
        {"codigo_barras": "EX0001", "numero_tombo": "T-1"},
        {"codigo_barras": "EX0002", "numero_tombo": "T-2"},
    ]

    def test_escapa_titulo(self):
        html_pag = barcode_util.etiquetas_html(
            "Dom Casmurro <script>alert(1)</script>", self.EXEMPLARES)
        self.assertIn("&lt;script&gt;", html_pag)
        self.assertNotIn("<script>alert(1)</script>", html_pag)

    def test_um_svg_por_exemplar(self):
        html_pag = barcode_util.etiquetas_html("Dom Casmurro", self.EXEMPLARES)
        self.assertEqual(html_pag.count("<svg"), len(self.EXEMPLARES))
        self.assertIn("T-1", html_pag)
        self.assertIn("T-2", html_pag)

    def test_botao_de_imprimir(self):
        html_pag = barcode_util.etiquetas_html("Dom Casmurro", self.EXEMPLARES)
        self.assertIn("window.print()", html_pag)
        self.assertIn("<button", html_pag)


class TestEtiquetasLoteHtml(unittest.TestCase):
    """etiquetas_lote_html: etiquetas de vários livros de uma vez."""

    def test_escapa_titulos_e_um_svg_por_exemplar(self):
        exemplares = [
            {"titulo": "Livro <script>x</script>", "codigo_barras": "EX0001",
             "numero_tombo": "T-1"},
            {"titulo": "Outro Livro", "codigo_barras": "EX0002",
             "numero_tombo": "T-2"},
        ]
        html_pag = barcode_util.etiquetas_lote_html(exemplares)
        self.assertIn("&lt;script&gt;", html_pag)
        self.assertNotIn("<script>x</script>", html_pag)
        self.assertEqual(html_pag.count("<svg"), len(exemplares))
        self.assertIn("window.print()", html_pag)


class TestCartoesHtml(unittest.TestCase):
    """cartoes_html: cartões de biblioteca dos usuários."""

    def test_escapa_nome_e_um_svg_por_usuario(self):
        usuarios = [
            {"nome": "Ana <script>x</script>", "matricula": "M-1",
             "perfil": "ALUNO", "turma": "9A", "codigo_barras": "US0001"},
            {"nome": "Beto", "matricula": "M-2",
             "perfil": "PROFESSOR", "turma": "", "codigo_barras": "US0002"},
        ]
        html_pag = barcode_util.cartoes_html(usuarios)
        self.assertIn("&lt;script&gt;", html_pag)
        self.assertNotIn("<script>x</script>", html_pag)
        self.assertEqual(html_pag.count("<svg"), len(usuarios))
        self.assertIn("M-1", html_pag)
        self.assertIn("Aluno", html_pag)  # perfil exibido com .title()
        self.assertIn("window.print()", html_pag)


if __name__ == "__main__":
    unittest.main()
