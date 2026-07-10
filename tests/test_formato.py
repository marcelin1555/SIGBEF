"""Testes de sigbef.formato — formatação de datas, valores e status."""
import tests.base  # noqa: F401  # configura o ambiente de testes (deve ser o 1º import)

import unittest
from datetime import date, datetime

from sigbef import formato


class TestDataBr(unittest.TestCase):
    """data_br: conversão para o formato brasileiro dd/mm/yyyy."""

    def test_string_iso_data_pura(self):
        """'YYYY-MM-DD' vira 'dd/mm/yyyy' sem hora."""
        self.assertEqual(formato.data_br("2024-03-05"), "05/03/2024")

    def test_string_iso_com_hora(self):
        """'YYYY-MM-DD HH:MM:SS' vira 'dd/mm/yyyy HH:MM' (segundos descartados)."""
        self.assertEqual(formato.data_br("2024-03-05 14:30:45"),
                         "05/03/2024 14:30")

    def test_objeto_date(self):
        """Objeto date é aceito diretamente."""
        self.assertEqual(formato.data_br(date(2024, 12, 25)), "25/12/2024")

    def test_objeto_datetime_sem_com_hora_descarta_hora(self):
        """COMPORTAMENTO REAL: um datetime sem com_hora=True perde a hora
        (mostrar_hora só é automático para strings contendo espaço)."""
        self.assertEqual(formato.data_br(datetime(2024, 3, 5, 14, 30)),
                         "05/03/2024")

    def test_none_e_vazio_viram_vazio(self):
        self.assertEqual(formato.data_br(None), "")
        self.assertEqual(formato.data_br(""), "")

    def test_string_nao_reconhecida_volta_como_veio(self):
        self.assertEqual(formato.data_br("não é data"), "não é data")
        self.assertEqual(formato.data_br("2024-13-45"), "2024-13-45")

    def test_com_hora_forca_horario(self):
        """com_hora=True: data pura ganha 00:00; datetime mostra a hora real."""
        self.assertEqual(formato.data_br("2024-03-05", com_hora=True),
                         "05/03/2024 00:00")
        self.assertEqual(formato.data_br(date(2024, 3, 5), com_hora=True),
                         "05/03/2024 00:00")
        self.assertEqual(
            formato.data_br(datetime(2024, 3, 5, 14, 30), com_hora=True),
            "05/03/2024 14:30")


class TestDataHoraBr(unittest.TestCase):
    """data_hora_br: atalho para data_br(valor, com_hora=True)."""

    CASOS = [
        ("2024-03-05", "05/03/2024 00:00"),
        ("2024-03-05 14:30:45", "05/03/2024 14:30"),
        (date(2024, 3, 5), "05/03/2024 00:00"),
        (datetime(2024, 3, 5, 14, 30), "05/03/2024 14:30"),
        (None, ""),
        ("", ""),
        ("não é data", "não é data"),
    ]

    def test_equivale_a_data_br_com_hora(self):
        for valor, esperado in self.CASOS:
            with self.subTest(valor=valor):
                self.assertEqual(formato.data_hora_br(valor), esperado)
                self.assertEqual(formato.data_hora_br(valor),
                                 formato.data_br(valor, com_hora=True))


class TestReais(unittest.TestCase):
    """reais: formatação monetária 'R$ 0,00'."""

    def test_inteiro(self):
        self.assertEqual(formato.reais(10), "R$ 10,00")

    def test_decimal(self):
        self.assertEqual(formato.reais(1.5), "R$ 1,50")

    def test_valores_invalidos_viram_zero(self):
        self.assertEqual(formato.reais(None), "R$ 0,00")
        self.assertEqual(formato.reais("abc"), "R$ 0,00")

    def test_sem_separador_de_milhar(self):
        """COMPORTAMENTO REAL: valores grandes saem sem separador de milhar."""
        self.assertEqual(formato.reais(1234.5), "R$ 1234,50")


class TestStatusLegivel(unittest.TestCase):
    """status_legivel: rótulos legíveis para status de exemplar."""

    def test_status_mapeados(self):
        esperados = {
            "DISPONIVEL": "Disponível",
            "EMPRESTADO": "Emprestado",
            "RESERVADO": "Reservado",
            "MANUTENCAO": "Em manutenção",
            "BAIXADO": "Baixado",
        }
        for status, rotulo in esperados.items():
            with self.subTest(status=status):
                self.assertEqual(formato.status_legivel(status), rotulo)

    def test_status_desconhecido_volta_como_veio(self):
        self.assertEqual(formato.status_legivel("EXTRAVIADO"), "EXTRAVIADO")


if __name__ == "__main__":
    unittest.main()
