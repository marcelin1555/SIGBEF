"""Testes do gerador de QR Code (sigbef/qr_util.py).

O critério de correção aqui é **decodificação**, não igualdade de matriz:
um QR válido pode ser desenhado com qualquer uma das 8 máscaras, e
bibliotecas diferentes fazem escolhas diferentes. O que importa é que um
leitor real recupere o texto original.

O decodificador (OpenCV) é usado **apenas no teste** — o SIGBEF em runtime
continua sem nenhuma dependência externa. Se o OpenCV não estiver
instalado, esses testes são pulados e os demais seguem valendo.
"""
import unittest

from sigbef import qr_util

try:  # decodificador opcional, só para teste
    import cv2
    import numpy as np
    TEM_DECODER = True
except ImportError:  # pragma: no cover
    TEM_DECODER = False


TEXTOS = [
    "A",
    "sigbef://192.168.0.42:8765",
    "sigbef://10.0.0.5:8765",
    "sigbef://192.168.100.200:8765",
    "https://sigbef.vercel.app",
    "Biblioteca do CEFE - pareamento do aplicativo movel 2026",
    "Acentuacao: coracao, biblioteca, matricula",
    "x" * 100,
]


def _para_imagem(matriz, borda=4, escala=8):
    """Converte a matriz num bitmap em tons de cinza para o decodificador."""
    n = len(matriz)
    lado = (n + borda * 2) * escala
    img = np.ones((lado, lado), dtype=np.uint8) * 255
    for i in range(n):
        for j in range(n):
            if matriz[i][j]:
                y, x = (i + borda) * escala, (j + borda) * escala
                img[y:y + escala, x:x + escala] = 0
    return img


class TestEstrutura(unittest.TestCase):
    def test_tamanho_segue_a_versao(self):
        """Lado = 17 + 4 * versão, e cresce conforme o texto."""
        for texto in TEXTOS:
            m = qr_util.matriz(texto)
            self.assertEqual(len(m), len(m[0]), "matriz deve ser quadrada")
            self.assertEqual((len(m) - 17) % 4, 0)

    def test_localizadores_nos_tres_cantos(self):
        m = qr_util.matriz("sigbef://192.168.0.42:8765")
        n = len(m)
        for linha, col in ((0, 0), (0, n - 7), (n - 7, 0)):
            # borda externa escura e miolo 3x3 escuro
            self.assertEqual(m[linha][col], 1)
            self.assertEqual(m[linha + 3][col + 3], 1)
            # anel claro em volta do miolo
            self.assertEqual(m[linha + 1][col + 1], 0)

    def test_modulo_escuro_fixo(self):
        m = qr_util.matriz("sigbef://192.168.0.42:8765")
        self.assertEqual(m[len(m) - 8][8], 1)

    def test_texto_vazio_recusado(self):
        with self.assertRaises(ValueError):
            qr_util.matriz("")

    def test_texto_longo_demais_recusado(self):
        with self.assertRaises(ValueError) as ctx:
            qr_util.matriz("z" * 500)
        self.assertIn("longo demais", str(ctx.exception))


class TestSVG(unittest.TestCase):
    def test_svg_bem_formado(self):
        svg = qr_util.gerar_svg("sigbef://192.168.0.42:8765")
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.endswith("</svg>"))
        self.assertIn("xmlns=", svg)
        self.assertGreater(svg.count("<rect"), 50)

    def test_svg_respeita_as_cores(self):
        svg = qr_util.gerar_svg("teste", cor="#1F4E79", fundo="#FFFFFF")
        self.assertIn("#1F4E79", svg)


@unittest.skipUnless(TEM_DECODER,
                     "OpenCV nao instalado (só é usado neste teste)")
class TestDecodificacao(unittest.TestCase):
    """O teste que de fato importa: um leitor consegue ler o que geramos?"""

    def test_todos_os_textos_voltam_iguais(self):
        detector = cv2.QRCodeDetector()
        for texto in TEXTOS:
            with self.subTest(texto=texto[:30]):
                img = _para_imagem(qr_util.matriz(texto))
                lido, _, _ = detector.detectAndDecode(img)
                self.assertEqual(lido, texto)

    def test_endereco_de_pareamento_real(self):
        """Formato exato que o app vai receber no pareamento."""
        detector = cv2.QRCodeDetector()
        alvo = "sigbef://192.168.1.100:8765"
        img = _para_imagem(qr_util.matriz(alvo))
        lido, _, _ = detector.detectAndDecode(img)
        self.assertEqual(lido, alvo)


if __name__ == "__main__":
    unittest.main()
