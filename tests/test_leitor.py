"""
SIGBEF — Estatística pessoal e recomendação para o leitor.

O que o aplicativo mostra ao aluno sobre a própria leitura, e como as
sugestões são montadas quando há pouco dado — que é a regra numa
biblioteca escolar, não a exceção.

Uso:
    python -m unittest tests.test_leitor -v
"""
from tests.base import SigbefTestCase

import unittest

from sigbef import servicos
from sigbef.database import db_cursor


class LeitorTestCase(SigbefTestCase):

    def setUp(self):
        super().setUp()
        self.livros = {}

    def livro(self, titulo, categoria="Literatura"):
        if titulo not in self.livros:
            self.livros[titulo] = self.criar_livro(titulo=titulo,
                                                    categoria=categoria)
        return self.livros[titulo]

    def ler(self, matricula, titulo, categoria="Literatura"):
        """Empresta e devolve — só assim conta como lido."""
        codigo = self.livro(titulo, categoria)["exemplares"][0][1]
        servicos.realizar_emprestimo(codigo_exemplar=codigo,
                                      matricula_usuario=matricula)
        servicos.realizar_devolucao(codigo_exemplar=codigo)

    def pegar(self, matricula, titulo, categoria="Literatura"):
        """Empresta e NÃO devolve."""
        codigo = self.livro(titulo, categoria)["exemplares"][0][1]
        return servicos.realizar_emprestimo(codigo_exemplar=codigo,
                                             matricula_usuario=matricula)


class TestEstatisticasDoLeitor(LeitorTestCase):

    def test_conta_so_o_que_foi_devolvido(self):
        """Livro em mãos ainda não foi lido."""
        u = self.criar_usuario(matricula="ana")
        self.ler("ana", "Lido")
        self.pegar("ana", "Ainda Comigo")

        e = servicos.estatisticas_do_leitor(u["id"])
        self.assertEqual(e["total_lidos"], 1)

    def test_categoria_favorita_e_a_mais_lida(self):
        u = self.criar_usuario(matricula="ana")
        self.ler("ana", "Romance 1", "Literatura")
        self.ler("ana", "Romance 2", "Literatura")
        self.ler("ana", "Álgebra", "Didáticos")

        e = servicos.estatisticas_do_leitor(u["id"])
        self.assertEqual(e["categoria_favorita"], "Literatura")
        self.assertEqual(e["lidos_na_favorita"], 2)

    def test_leitor_novo_nao_quebra(self):
        u = self.criar_usuario(matricula="novo")
        e = servicos.estatisticas_do_leitor(u["id"])
        self.assertEqual(e["total_lidos"], 0)
        self.assertEqual(e["categoria_favorita"], "")
        self.assertEqual(e["dias_medios"], 0.0)
        self.assertEqual(e["leitor_desde"], "")

    def test_um_livro_so_nao_faz_uma_favorita(self):
        """Quatro livros de quatro categorias não revelam gosto nenhum.

        Visto em dados reais: a tela dizia "você lê mais X · 1 livro",
        uma conclusão tirada do nada.
        """
        u = self.criar_usuario(matricula="ana")
        self.ler("ana", "Um", "Literatura")
        self.ler("ana", "Dois", "Didáticos")
        self.ler("ana", "Três", "História")

        e = servicos.estatisticas_do_leitor(u["id"])
        self.assertEqual(e["total_lidos"], 3)
        self.assertEqual(e["categoria_favorita"], "")

    def test_livro_sem_categoria_nao_vira_favorita(self):
        """'Sem categoria' não é gosto de ninguém."""
        u = self.criar_usuario(matricula="ana")
        self.ler("ana", "Solto", "")
        self.assertEqual(
            servicos.estatisticas_do_leitor(u["id"])["categoria_favorita"], "")


class TestRecomendacoes(LeitorTestCase):

    def test_colaborativo_sugere_o_que_o_parecido_leu(self):
        ana = self.criar_usuario(matricula="ana")
        self.criar_usuario(matricula="bru", nome="Bruno")
        self.ler("ana", "Vidas Secas")
        self.ler("bru", "Vidas Secas")
        self.ler("bru", "O Cortiço")

        rec = servicos.recomendacoes_para(ana["id"], 3)
        cortico = [r for r in rec if r["titulo"] == "O Cortiço"]
        self.assertTrue(cortico, "deveria sugerir o que o leitor parecido leu")
        self.assertIn("Vidas Secas", cortico[0]["motivo"])

    def test_nunca_sugere_o_que_ja_li(self):
        ana = self.criar_usuario(matricula="ana")
        self.criar_usuario(matricula="bru", nome="Bruno")
        self.ler("ana", "Vidas Secas")
        self.ler("ana", "Dom Casmurro")
        self.ler("bru", "Vidas Secas")
        self.ler("bru", "Dom Casmurro")

        titulos = [r["titulo"] for r in servicos.recomendacoes_para(ana["id"])]
        self.assertNotIn("Vidas Secas", titulos)
        self.assertNotIn("Dom Casmurro", titulos)

    def test_livro_em_maos_tambem_nao_e_sugerido(self):
        ana = self.criar_usuario(matricula="ana")
        self.pegar("ana", "Comigo Agora")
        titulos = [r["titulo"] for r in servicos.recomendacoes_para(ana["id"])]
        self.assertNotIn("Comigo Agora", titulos)

    def test_leitor_sem_historico_recebe_os_mais_lidos(self):
        """Quem nunca pegou nada é quem mais precisa de sugestão."""
        self.criar_usuario(matricula="bru", nome="Bruno")
        novo = self.criar_usuario(matricula="novo", nome="Novo")
        self.ler("bru", "Popular")

        rec = servicos.recomendacoes_para(novo["id"], 3)
        self.assertTrue(rec)
        self.assertEqual(rec[0]["titulo"], "Popular")
        self.assertIn("mais lidos", rec[0]["motivo"])

    def test_completa_com_acervo_parado(self):
        """O livro que ninguém pegou vira convite, não fica invisível.

        Categoria de propósito diferente da favorita: se fosse a mesma,
        a etapa 2 o pegaria antes — o que também estaria certo, e com
        explicação melhor ("você lê muito Literatura").
        """
        ana = self.criar_usuario(matricula="ana")
        self.ler("ana", "Já Li", "Literatura")
        self.livro("Ninguém Pegou", "Astronomia")

        rec = servicos.recomendacoes_para(ana["id"], 5)
        parado = [r for r in rec if r["titulo"] == "Ninguém Pegou"]
        self.assertTrue(parado)
        self.assertIn("primeiro", parado[0]["motivo"])

    def test_categoria_favorita_tem_prioridade_sobre_o_parado(self):
        """Explicação boa antes de explicação genérica.

        Dois livros na categoria porque um só não configura favorita —
        ver `test_um_livro_so_nao_faz_uma_favorita`.
        """
        ana = self.criar_usuario(matricula="ana")
        self.ler("ana", "Já Li", "Literatura")
        self.ler("ana", "Já Li Também", "Literatura")
        self.livro("Outro de Literatura", "Literatura")

        rec = servicos.recomendacoes_para(ana["id"], 5)
        item = [r for r in rec if r["titulo"] == "Outro de Literatura"][0]
        self.assertIn("Literatura", item["motivo"])

    def test_respeita_o_limite(self):
        self.criar_usuario(matricula="ana")
        ana = servicos.localizar_usuario("ana")
        for i in range(12):
            self.livro(f"Livro {i:02d}")
        self.assertEqual(len(servicos.recomendacoes_para(ana["id"], 4)), 4)

    def test_nao_repete_titulo_entre_as_etapas(self):
        ana = self.criar_usuario(matricula="ana")
        self.criar_usuario(matricula="bru", nome="Bruno")
        self.ler("ana", "Vidas Secas")
        self.ler("bru", "Vidas Secas")
        self.ler("bru", "O Cortiço")
        for i in range(6):
            self.livro(f"Extra {i}")

        titulos = [r["titulo"] for r in servicos.recomendacoes_para(ana["id"], 8)]
        self.assertEqual(len(titulos), len(set(titulos)))

    def test_livro_inativo_nunca_e_sugerido(self):
        ana = self.criar_usuario(matricula="ana")
        morto = self.livro("Descartado")
        with db_cursor() as cur:
            cur.execute("UPDATE livro SET ativo = 0 WHERE id = ?",
                        (morto["livro_id"],))
        titulos = [r["titulo"] for r in servicos.recomendacoes_para(ana["id"])]
        self.assertNotIn("Descartado", titulos)

    def test_biblioteca_vazia_devolve_lista_vazia(self):
        ana = self.criar_usuario(matricula="ana")
        self.assertEqual(servicos.recomendacoes_para(ana["id"]), [])

    def test_todo_item_traz_motivo(self):
        """Sugestão sem explicação parece anúncio."""
        ana = self.criar_usuario(matricula="ana")
        for i in range(4):
            self.livro(f"Livro {i}")
        for r in servicos.recomendacoes_para(ana["id"]):
            self.assertTrue(r["motivo"].strip())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
