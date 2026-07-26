"""
SIGBEF — Estatísticas de uso do acervo.

Cobre as consultas que alimentam o painel: movimento por mês, turmas,
categorias, acervo parado e o resumo em destaque.

Uso:
    python -m unittest tests.test_estatisticas -v
"""
from tests.base import SigbefTestCase

import unittest
from datetime import date, timedelta

from sigbef import servicos
from sigbef.database import db_cursor


class EstatisticasTestCase(SigbefTestCase):

    def emprestar(self, codigo, matricula):
        return servicos.realizar_emprestimo(codigo_exemplar=codigo,
                                             matricula_usuario=matricula)

    def devolver(self, codigo):
        return servicos.realizar_devolucao(codigo_exemplar=codigo)

    def datar_emprestimo(self, emprestimo_id, quando: date):
        """Move um empréstimo no tempo, para simular meses anteriores."""
        with db_cursor() as cur:
            cur.execute("UPDATE emprestimo SET data_emprestimo = ? WHERE id = ?",
                        (quando.isoformat(), emprestimo_id))


class TestPorTurma(EstatisticasTestCase):

    def test_agrupa_e_ordena_pelo_maior(self):
        a = self.criar_usuario(matricula="a1", nome="Ana", turma="3º ano B")
        self.criar_usuario(matricula="a2", nome="Bia", turma="3º ano B")
        self.criar_usuario(matricula="a3", nome="Caio", turma="2º ano A")
        livro = self.criar_livro(titulo="Livro", exemplares=3)
        for codigo, matricula in zip([e[1] for e in livro["exemplares"]],
                                      ["a1", "a2", "a3"]):
            self.emprestar(codigo, matricula)

        turmas = servicos.emprestimos_por_turma()
        self.assertEqual(turmas[0]["turma"], "3º ano B")
        self.assertEqual(turmas[0]["emprestimos"], 2)
        self.assertEqual(turmas[0]["leitores"], 2)

    def test_professor_nao_entra(self):
        """Professor não tem turma; contá-lo sujaria o ranking das salas."""
        self.criar_usuario(matricula="p1", nome="Prof", perfil="PROFESSOR")
        livro = self.criar_livro(exemplares=1)
        self.emprestar(livro["exemplares"][0][1], "p1")
        self.assertEqual(servicos.emprestimos_por_turma(), [])

    def test_aluno_sem_turma_aparece_rotulado(self):
        self.criar_usuario(matricula="a1", nome="Ana", turma="")
        livro = self.criar_livro(exemplares=1)
        self.emprestar(livro["exemplares"][0][1], "a1")
        self.assertEqual(servicos.emprestimos_por_turma()[0]["turma"],
                          "Sem turma")


class TestPorCategoria(EstatisticasTestCase):

    def test_conta_por_categoria_do_livro(self):
        self.criar_usuario(matricula="a1")
        lit = self.criar_livro(titulo="Romance", categoria="Literatura")
        did = self.criar_livro(titulo="Álgebra", categoria="Didáticos")
        self.emprestar(lit["exemplares"][0][1], "a1")
        self.devolver(lit["exemplares"][0][1])
        self.emprestar(lit["exemplares"][0][1], "a1")
        self.devolver(lit["exemplares"][0][1])
        self.emprestar(did["exemplares"][0][1], "a1")

        cats = servicos.emprestimos_por_categoria()
        self.assertEqual(cats[0], {"categoria": "Literatura", "emprestimos": 2})

    def test_livro_sem_categoria_aparece_rotulado(self):
        self.criar_usuario(matricula="a1")
        livro = self.criar_livro(titulo="Solto", categoria="")
        self.emprestar(livro["exemplares"][0][1], "a1")
        self.assertEqual(servicos.emprestimos_por_categoria()[0]["categoria"],
                          "Sem categoria")


class TestAcervoParado(EstatisticasTestCase):

    def test_lista_so_o_que_nunca_saiu(self):
        self.criar_usuario(matricula="a1")
        lido = self.criar_livro(titulo="Já Lido")
        self.criar_livro(titulo="Nunca Lido")
        self.emprestar(lido["exemplares"][0][1], "a1")

        parados = [l["titulo"] for l in servicos.livros_nunca_emprestados()]
        self.assertEqual(parados, ["Nunca Lido"])

    def test_devolvido_nao_volta_para_a_lista(self):
        """Já saiu uma vez basta: o livro deixou de estar parado."""
        self.criar_usuario(matricula="a1")
        livro = self.criar_livro(titulo="Foi e Voltou")
        self.emprestar(livro["exemplares"][0][1], "a1")
        self.devolver(livro["exemplares"][0][1])
        self.assertEqual(servicos.livros_nunca_emprestados(), [])

    def test_livro_inativo_fica_de_fora(self):
        livro = self.criar_livro(titulo="Descartado")
        with db_cursor() as cur:
            cur.execute("UPDATE livro SET ativo = 0 WHERE id = ?",
                        (livro["livro_id"],))
        self.assertEqual(servicos.livros_nunca_emprestados(), [])


class TestPorMes(EstatisticasTestCase):

    def test_serie_completa_sem_buracos(self):
        """Mês vazio precisa aparecer: o buraco conta uma história."""
        serie = servicos.emprestimos_por_mes(6)
        self.assertEqual(len(serie), 6)
        self.assertEqual([s["emprestimos"] for s in serie], [0] * 6)
        # Em ordem cronológica, terminando no mês corrente.
        self.assertEqual([s["mes"] for s in serie],
                          sorted(s["mes"] for s in serie))
        self.assertEqual(serie[-1]["mes"], date.today().strftime("%Y-%m"))

    def test_conta_no_mes_certo(self):
        self.criar_usuario(matricula="a1")
        livro = self.criar_livro(exemplares=2)
        e1 = self.emprestar(livro["exemplares"][0][1], "a1")
        e2 = self.emprestar(livro["exemplares"][1][1], "a1")
        # Um fica no mês corrente, outro vai para ~2 meses atrás.
        self.datar_emprestimo(e2["id"], date.today() - timedelta(days=62))

        serie = servicos.emprestimos_por_mes(6)
        self.assertEqual(serie[-1]["emprestimos"], 1)
        self.assertEqual(sum(s["emprestimos"] for s in serie), 2)


class TestResumo(EstatisticasTestCase):

    def test_cobertura_e_acervo_parado(self):
        self.criar_usuario(matricula="a1")
        lido = self.criar_livro(titulo="Lido")
        self.criar_livro(titulo="Parado")
        self.emprestar(lido["exemplares"][0][1], "a1")

        r = servicos.resumo_de_uso()
        self.assertEqual(r["acervo"], 2)
        self.assertEqual(r["ja_sairam"], 1)
        self.assertEqual(r["nunca_sairam"], 1)
        self.assertEqual(r["cobertura"], 50.0)

    def test_taxa_de_atraso_olha_so_o_que_voltou(self):
        """Empréstimo em aberto ainda pode voltar no prazo."""
        self.criar_usuario(matricula="a1")
        # Segundo aluno de propósito: devolver atrasado gera multa, e
        # aluno multado não pega outro livro — a regra barraria o
        # cenário se os dois empréstimos fossem da mesma pessoa.
        self.criar_usuario(matricula="a2", nome="Bia")
        livro = self.criar_livro(exemplares=2)
        emp = self.emprestar(livro["exemplares"][0][1], "a1")
        with db_cursor() as cur:  # devolvido depois do prazo
            cur.execute("UPDATE emprestimo SET data_prevista = ? WHERE id = ?",
                        ((date.today() - timedelta(days=5)).isoformat(),
                         emp["id"]))
        self.devolver(livro["exemplares"][0][1])
        # Este fica em aberto e vencido: não deve entrar na conta.
        aberto = self.emprestar(livro["exemplares"][1][1], "a2")
        with db_cursor() as cur:
            cur.execute("UPDATE emprestimo SET data_prevista = ? WHERE id = ?",
                        ((date.today() - timedelta(days=9)).isoformat(),
                         aberto["id"]))

        r = servicos.resumo_de_uso()
        self.assertEqual(r["devolvidos"], 1)
        self.assertEqual(r["taxa_atraso"], 100.0)

    def test_biblioteca_zerada_nao_divide_por_zero(self):
        r = servicos.resumo_de_uso()
        self.assertEqual(r["cobertura"], 0.0)
        self.assertEqual(r["taxa_atraso"], 0.0)
        self.assertEqual(r["leitores_30_dias"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
