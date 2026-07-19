"""Integridade dos ícones embutidos da interface.

Valida só os dados (base64/PNG), sem abrir Tk — assim roda em qualquer
ambiente de CI, inclusive Linux sem display.
"""
import base64
import unittest

from sigbef.icones_data import ICONES

# Combinações que a UI realmente usa (sidebar, cabeçalho e cards do
# painel). Se tools/gerar_icones.js deixar de gerar alguma, este teste
# quebra antes de o app quebrar em produção.
CHAVES_USADAS = [
    # Ícone de janela (barra de título / alt-tab)
    "logo_original_32", "logo_original_64",
    # Logo em plaqueta (sobre a cor primária de qualquer paleta)
    "logoplaca_original_28", "logoplaca_original_36",
    "logoplaca_original_48", "logoplaca_original_56",
    # Sidebar e cabeçalho
    "home_branco_16", "livro_branco_16", "usuarios_branco_16",
    "troca_branco_16", "grafico_branco_16", "engrenagem_branco_16",
    "busca_branco_16", "leitor_branco_16", "sair_branco_16",
    # Cards do painel
    "livro_cinza_20", "barcode_cinza_20", "check_verde_20",
    "troca_cinza_20", "alerta_vermelho_20", "usuarios_cinza_20",
    # Botões de ação, aviso do kiosk e tela final do setup
    "mais_branco_14", "confirmar_branco_14", "desfazer_branco_14",
    "relogio_branco_16", "check_verde_28",
]

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class TestIconesEmbutidos(unittest.TestCase):
    def test_chaves_usadas_pela_ui_existem(self):
        for chave in CHAVES_USADAS:
            self.assertIn(chave, ICONES)

    def test_todos_sao_png_validos(self):
        for chave, b64 in ICONES.items():
            raw = base64.b64decode(b64, validate=True)
            self.assertEqual(raw[:8], PNG_MAGIC, f"{chave} não é PNG")

    def test_tamanho_total_modesto(self):
        """Os dados embutidos devem seguir minúsculos (< 64 KB)."""
        total = sum(len(v) for v in ICONES.values())
        self.assertLess(total, 64 * 1024)


if __name__ == "__main__":
    unittest.main()
