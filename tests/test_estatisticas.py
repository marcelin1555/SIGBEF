"""
SIGBEF — Estatísticas de uso do acervo.

Cobre as consultas que alimentam o painel: movimento por mês, turmas,
categorias, acervo parado e o resumo em destaque.

Uso:
    python -m unittest tests.test_estatisticas -v
"""
from tests.base import SigbefTestCase

import sqlite3
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


class TestSeriePorMesNosDiasDificeis(unittest.TestCase):
    """A técnica SQL de `emprestimos_por_mes`, testada nos dias em que ela
    quebrava: 29, 30 e 31.

    `date('now','-N months')` no SQLite não recua N meses no calendário —
    ele mantém o dia do mês e, se esse dia não existir no mês de destino,
    **rola para a frente** em vez de voltar. Em 31/07 menos 1 mês, o
    SQLite tenta "30/06", que não existe (junho tem 30 dias, mas o
    problema é achar o dia 31), e a rolagem devolve 01/07 — o mesmo mês
    de origem. Dois meses viravam o mesmo rótulo, e a soma dobrava.

    Como o teste roda em datas reais, ele não pode depender de "hoje"
    calhar de ser um desses dias. Por isso fixa a data com um literal em
    vez de `'now'` — é a mesma expressão SQL do código de produção
    (`servicos.emprestimos_por_mes`), só com a âncora sob controle.
    """

    def serie_para(self, ancora: str, meses: int) -> list[str]:
        con = sqlite3.connect(":memory:")
        try:
            rows = con.execute(
                """WITH RECURSIVE seq(n) AS (
                       SELECT 0 UNION ALL SELECT n + 1 FROM seq WHERE n < ?
                   )
                   SELECT strftime('%Y-%m',
                                   date(?, 'start of month',
                                        '-' || (? - n) || ' months')
                          ) AS mes FROM seq""",
                (meses - 1, ancora, meses - 1),
            ).fetchall()
            return [r[0] for r in rows]
        finally:
            con.close()

    def mes_esperado(self, ano: int, mes: int, voltar: int) -> str:
        """Calendário em Python puro, sem passar pelo SQLite: é o
        oráculo independente contra quem o SQL é conferido."""
        indice = (ano * 12 + (mes - 1)) - voltar
        return f"{indice // 12:04d}-{indice % 12 + 1:02d}"

    def test_dias_31_30_29_28_no_ano(self):
        casos = [
            ("2026-01-31", 2026, 1),   # janeiro -> dezembro (31 -> 31, ok)
            ("2026-03-31", 2026, 3),   # março -> fevereiro (31 -> 28)
            ("2026-05-31", 2026, 5),   # maio -> abril (31 -> 30)
            ("2026-07-31", 2026, 7),   # o caso que pegou o teste real
            ("2026-08-31", 2026, 8),   # agosto -> julho (31 -> 31, ok)
            ("2026-10-31", 2026, 10),  # outubro -> setembro (31 -> 30)
            ("2026-12-31", 2026, 12),  # dezembro -> novembro (31 -> 30)
            ("2028-02-29", 2028, 2),   # 29 de fevereiro, ano bissexto
            ("2026-04-30", 2026, 4),   # dia 30 também rola em fev
        ]
        for ancora, ano, mes in casos:
            with self.subTest(ancora=ancora):
                serie = self.serie_para(ancora, 6)
                esperado = [self.mes_esperado(ano, mes, v)
                            for v in range(5, -1, -1)]
                self.assertEqual(serie, esperado)
                self.assertEqual(len(set(serie)), 6,
                                 "mês duplicado: dois meses colapsaram "
                                 "no mesmo rótulo")

    def test_um_ano_inteiro_de_ancoras_dificeis(self):
        """Varre os 12 últimos dias de cada mês de um ano — não só os
        dias 31 — porque a rolagem também acontece a partir do 30 e do 29
        indo para fevereiro."""
        for mes in range(1, 13):
            ultimo_dia = (date(2026, mes % 12 + 1, 1) - timedelta(days=1)
                          if mes < 12 else date(2026, 12, 31))
            ancora = ultimo_dia.isoformat()
            with self.subTest(ancora=ancora):
                serie = self.serie_para(ancora, 12)
                self.assertEqual(len(serie), 12)
                self.assertEqual(len(set(serie)), 12,
                                 f"âncora {ancora} produziu mês duplicado")


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


class TestRelatorioInadimplentes(EstatisticasTestCase):
    """RF-052 — quem está impedido de pegar livro, e por quê.

    O bloqueio de `status_usuario` tem duas causas (multa em aberto e
    exemplar atrasado), e o relatório precisa cobrir as duas: uma lista
    só de devedores deixaria de fora quem ainda está com o livro da
    escola em casa.
    """

    def atrasar(self, emprestimo_id, dias):
        with db_cursor() as cur:
            cur.execute("UPDATE emprestimo SET data_prevista = ? WHERE id = ?",
                        ((date.today() - timedelta(days=dias)).isoformat(),
                         emprestimo_id))

    def test_biblioteca_em_dia_devolve_lista_vazia(self):
        self.criar_usuario(matricula="a1")
        livro = self.criar_livro()
        self.emprestar(livro["exemplares"][0][1], "a1")
        self.assertEqual(servicos.relatorio_inadimplentes(), [])

    def test_pega_quem_esta_com_livro_atrasado(self):
        """Ainda não devolveu: não há multa lançada, mas há pendência."""
        self.criar_usuario(matricula="a1", nome="Ana")
        livro = self.criar_livro()
        emp = self.emprestar(livro["exemplares"][0][1], "a1")
        self.atrasar(emp["id"], 12)

        r = servicos.relatorio_inadimplentes()
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["nome"], "Ana")
        self.assertEqual(r[0]["em_atraso"], 1)
        self.assertEqual(r[0]["dias_atraso"], 12)
        self.assertEqual(r[0]["multa"], 0)

    def test_pega_quem_devolveu_e_ficou_devendo(self):
        self.criar_usuario(matricula="a2", nome="Bruno")
        livro = self.criar_livro()
        emp = self.emprestar(livro["exemplares"][0][1], "a2")
        self.atrasar(emp["id"], 4)
        self.devolver(livro["exemplares"][0][1])

        r = servicos.relatorio_inadimplentes()
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["nome"], "Bruno")
        self.assertGreater(r[0]["multa"], 0)
        self.assertEqual(r[0]["em_atraso"], 0)

    def test_multa_quitada_sai_da_lista(self):
        u = self.criar_usuario(matricula="a2", nome="Bruno")
        livro = self.criar_livro()
        emp = self.emprestar(livro["exemplares"][0][1], "a2")
        self.atrasar(emp["id"], 4)
        self.devolver(livro["exemplares"][0][1])
        self.assertTrue(servicos.relatorio_inadimplentes())

        servicos.quitar_multa(emp["id"])
        self.assertEqual(servicos.relatorio_inadimplentes(), [])

    def test_atraso_mais_antigo_vem_primeiro(self):
        """É quem a bibliotecária precisa procurar primeiro."""
        self.criar_usuario(matricula="a1", nome="Recente")
        self.criar_usuario(matricula="a2", nome="Antigo")
        livro = self.criar_livro(exemplares=2)
        e1 = self.emprestar(livro["exemplares"][0][1], "a1")
        e2 = self.emprestar(livro["exemplares"][1][1], "a2")
        self.atrasar(e1["id"], 3)
        self.atrasar(e2["id"], 40)

        nomes = [r["nome"] for r in servicos.relatorio_inadimplentes()]
        self.assertEqual(nomes, ["Antigo", "Recente"])

    def test_usuario_inativo_fica_de_fora(self):
        u = self.criar_usuario(matricula="a1", nome="Saiu da escola")
        livro = self.criar_livro()
        emp = self.emprestar(livro["exemplares"][0][1], "a1")
        self.atrasar(emp["id"], 30)
        with db_cursor() as cur:
            cur.execute("UPDATE usuario SET ativo = 0 WHERE id = ?", (u["id"],))
        self.assertEqual(servicos.relatorio_inadimplentes(), [])

    def test_traz_contato_para_a_cobranca(self):
        self.criar_usuario(matricula="a1", nome="Ana", turma="3º ano B",
                            email="ana@escola.br")
        livro = self.criar_livro()
        emp = self.emprestar(livro["exemplares"][0][1], "a1")
        self.atrasar(emp["id"], 5)

        r = servicos.relatorio_inadimplentes()[0]
        self.assertEqual(r["turma"], "3º ano B")
        self.assertEqual(r["email"], "ana@escola.br")
        self.assertEqual(r["matricula"], "a1")

    def test_uma_linha_por_pessoa(self):
        """Dois livros atrasados não podem virar duas linhas."""
        self.criar_usuario(matricula="a1", nome="Ana")
        livro = self.criar_livro(exemplares=2)
        # Os dois empréstimos primeiro, o atraso depois: com um deles já
        # vencido, a regra de negócio recusaria o segundo.
        emps = [self.emprestar(livro["exemplares"][i][1], "a1") for i in (0, 1)]
        for emp in emps:
            self.atrasar(emp["id"], 7)

        r = servicos.relatorio_inadimplentes()
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["em_atraso"], 2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
