"""
SIGBEF — Liberar um número de tombo para reuso.

Veio de um beco real na biblioteca. A bibliotecária queria reaproveitar
um número de tombo, deu **baixa** no exemplar achando que era esse o
caminho, e o número continuou preso. Depois **excluiu o livro** do
acervo, e o número continuou preso — só que agora o livro tinha sumido
de todas as telas, então não havia mais como chegar naquele exemplar
nem para soltar o número.

Duas coisas estavam erradas, e uma estava certa mas escondida:

1. **Certa, mas escondida:** apagar o campo em "Corrigir tombo" sempre
   liberou o número, com o exemplar seguindo no acervo. Isso estava
   dito como "deixe em branco para tirar o tombo", em letra de apoio —
   e ninguém liga "tirar" a "usar em outro exemplar".
2. **Errada:** dar baixa não libera o tombo (é de propósito), mas a
   tela não oferecia alternativa nenhuma a quem só queria o número.
3. **Errada:** excluir o livro prendia os tombos para sempre, porque a
   checagem de duplicidade não olha status nem se o livro está ativo.

Uso:
    python -m unittest tests.test_liberar_tombo -v
"""
from __future__ import annotations

from tests.base import SigbefTestCase

from sigbef import servicos
from sigbef.database import db_cursor
from sigbef.servicos import RegraNegocioError


class BaseTombo(SigbefTestCase):

    def cadastrar_com_tombo(self, titulo, tombos):
        return servicos.cadastrar_livro(
            titulo=titulo, autores=["Autoria"],
            quantidade_exemplares=len(tombos), tombos=tombos)

    def tombo_esta_livre(self, tombo) -> bool:
        """Tenta usar o número num livro novo — a prova de fogo."""
        try:
            servicos.cadastrar_livro(
                titulo="Sonda %s" % tombo, autores=["Autoria"],
                quantidade_exemplares=1, tombos=[tombo])
            return True
        except RegraNegocioError:
            return False


class TestCorrigirTomboLibera(BaseTombo):
    """O caminho certo, e o que a bibliotecária procurava."""

    def test_apagar_o_numero_libera_para_outro_exemplar(self):
        liv = self.cadastrar_com_tombo("Antigo", ["T-100"])
        self.assertFalse(self.tombo_esta_livre("T-100"))

        servicos.alterar_tombo_exemplar(liv["exemplares"][0][1], "")

        self.assertTrue(self.tombo_esta_livre("T-100"))

    def test_o_exemplar_continua_no_acervo(self):
        """É a diferença para a baixa: o livro não sai da estante, só
        fica sem número até alguém dar outro a ele."""
        liv = self.cadastrar_com_tombo("Antigo", ["T-110"])
        codigo = liv["exemplares"][0][1]

        servicos.alterar_tombo_exemplar(codigo, "")

        ex = servicos.localizar_exemplar(codigo)
        self.assertEqual(ex["status"], "DISPONIVEL")
        self.assertIn(ex.get("numero_tombo"), (None, ""))

    def test_fica_na_auditoria(self):
        liv = self.cadastrar_com_tombo("Antigo", ["T-120"])
        servicos.alterar_tombo_exemplar(liv["exemplares"][0][1], "")
        with db_cursor() as cur:
            cur.execute("SELECT detalhes FROM auditoria "
                        "WHERE acao = 'TOMBO_EXEMPLAR'")
            self.assertIn("T-120", cur.fetchone()["detalhes"])


class TestBaixaNaoLiberaSozinha(BaseTombo):
    """O que ela tentou primeiro, e por que não funcionou."""

    def test_dar_baixa_mantem_o_tombo_ocupado(self):
        liv = self.cadastrar_com_tombo("Antigo", ["T-200"])
        servicos.baixar_exemplar(liv["exemplares"][0][1], "DESCARTADO")

        self.assertFalse(
            self.tombo_esta_livre("T-200"),
            "a baixa não pode soltar o número sozinha: por um instante "
            "dois exemplares teriam o mesmo tombo, e é essa dupla que "
            "faz o balcão emprestar a cópia errada")

    def test_baixa_mais_liberar_explicito_funciona(self):
        """O caminho que a caixinha da tela de baixa percorre."""
        liv = self.cadastrar_com_tombo("Antigo", ["T-210"])
        codigo = liv["exemplares"][0][1]
        servicos.baixar_exemplar(codigo, "DESCARTADO")
        servicos.alterar_tombo_exemplar(codigo, "")

        self.assertTrue(self.tombo_esta_livre("T-210"))


class TestExclusaoLiberaOsTombos(BaseTombo):
    """O beco: excluído, o livro some e os tombos ficam inalcançáveis."""

    def test_por_padrao_a_exclusao_guarda_a_numeracao(self):
        liv = self.cadastrar_com_tombo("Some", ["T-300", "T-301"])

        servicos.excluir_livro(liv["livro_id"])

        self.assertFalse(self.tombo_esta_livre("T-300"))

    def test_pedindo_para_liberar_os_numeros_voltam(self):
        liv = self.cadastrar_com_tombo("Some", ["T-310", "T-311"])

        servicos.excluir_livro(liv["livro_id"], liberar_tombos=True)

        self.assertTrue(self.tombo_esta_livre("T-310"))
        self.assertTrue(self.tombo_esta_livre("T-311"))

    def test_a_auditoria_registra_quantos_foram_soltos(self):
        liv = self.cadastrar_com_tombo("Some", ["T-320", "T-321"])
        servicos.excluir_livro(liv["livro_id"], liberar_tombos=True)
        with db_cursor() as cur:
            cur.execute("SELECT detalhes FROM auditoria "
                        "WHERE acao = 'EXCLUSAO_LIVRO'")
            self.assertIn("tombos_liberados=2", cur.fetchone()["detalhes"])

    def test_o_livro_continua_excluido_de_qualquer_jeito(self):
        """Liberar tombo é sobre o número, não sobre o acervo."""
        liv = self.cadastrar_com_tombo("Some", ["T-330"])
        servicos.excluir_livro(liv["livro_id"], liberar_tombos=True)
        titulos = [x["titulo"] for x in servicos.listar_livros("Some")]
        self.assertNotIn("Some", titulos)


class TestTomboContinuaUnico(BaseTombo):
    """Liberar não pode virar porta para tombo repetido."""

    def test_nao_da_para_repetir_tombo_de_exemplar_ativo(self):
        self.cadastrar_com_tombo("Um", ["T-400"])
        self.assertFalse(self.tombo_esta_livre("T-400"))

    def test_nao_da_para_repetir_tombo_de_exemplar_baixado(self):
        liv = self.cadastrar_com_tombo("Um", ["T-410"])
        servicos.baixar_exemplar(liv["exemplares"][0][1], "EXTRAVIADO")
        self.assertFalse(self.tombo_esta_livre("T-410"))

    def test_nao_da_para_repetir_tombo_de_livro_excluido(self):
        """Sem `liberar_tombos`, o número segue reservado — é o
        comportamento de sempre, e ele continua valendo."""
        liv = self.cadastrar_com_tombo("Um", ["T-420"])
        servicos.excluir_livro(liv["livro_id"])
        self.assertFalse(self.tombo_esta_livre("T-420"))

    def test_corrigir_tombo_recusa_numero_ja_em_uso(self):
        self.cadastrar_com_tombo("Um", ["T-430"])
        outro = self.cadastrar_com_tombo("Dois", ["T-431"])
        with self.assertRaises(RegraNegocioError):
            servicos.alterar_tombo_exemplar(outro["exemplares"][0][1],
                                            "T-430")


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
