"""
SIGBEF — Empréstimo de coleção: o livro-texto da turma inteira.

Trinta exemplares do mesmo título saem no começo do bimestre e voltam
no fim. Pelo caminho comum isso são trinta empréstimos digitados, trinta
linhas iguais na tela de empréstimos abertos e trinta devoluções — e é
exatamente por isso que esse tipo de saída acabava virando papel, fora
do sistema.

A dúvida que segurava a função era em nome de quem fica o exemplar. A
resposta implementada: **no nome do professor, com a turma anotada**,
porque é ele quem responde pelos trinta livros, e porque o mesmo
professor pode levar coleções para turmas diferentes no mesmo bimestre.

Uso:
    python -m unittest tests.test_colecao -v
"""
from __future__ import annotations

from tests.base import SigbefTestCase

from sigbef import reservas, servicos
from sigbef.database import db_cursor
from sigbef.servicos import RegraNegocioError


class BaseColecao(SigbefTestCase):

    def setUp(self):
        super().setUp()
        self.prof = self.criar_usuario(matricula="prof1", perfil="PROFESSOR",
                                       nome="Professora de História")
        self.livro = self.criar_livro(titulo="História do Brasil",
                                      exemplares=35)

    def emprestar(self, quantidade=30, turma="3º ano B", **kw):
        kw.setdefault("livro_id", self.livro["livro_id"])
        kw.setdefault("matricula_professor", "prof1")
        return servicos.emprestar_colecao(quantidade=quantidade, turma=turma,
                                          **kw)


class TestEmprestarColecao(BaseColecao):

    def test_sai_tudo_num_registro_so(self):
        col = self.emprestar(quantidade=30)

        self.assertEqual(col["quantidade"], 30)
        self.assertEqual(len(servicos.listar_colecoes_em_aberto()), 1,
                         "trinta livros têm que ser UMA linha na tela")

    def test_cada_exemplar_continua_marcado_como_emprestado(self):
        """A linha única é só apresentação: a estante tem que saber que
        os trinta exemplares não estão lá."""
        self.emprestar(quantidade=30)
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS q FROM exemplar "
                        "WHERE livro_id = ? AND status = 'EMPRESTADO'",
                        (self.livro["livro_id"],))
            self.assertEqual(cur.fetchone()["q"], 30)

    def test_a_turma_fica_registrada(self):
        """Sem a turma, ninguém sabe qual pilha é de quem no fim do
        bimestre — e o professor pode ter levado duas."""
        self.emprestar(quantidade=10, turma="1º ano A")
        self.emprestar(quantidade=10, turma="2º ano C")

        turmas = sorted(c["turma"]
                        for c in servicos.listar_colecoes_em_aberto())
        self.assertEqual(turmas, ["1º ano A", "2º ano C"])

    def test_turma_em_branco_e_recusada(self):
        with self.assertRaises(RegraNegocioError) as ctx:
            self.emprestar(quantidade=5, turma="   ")
        self.assertIn("turma", str(ctx.exception).lower())

    def test_prazo_e_o_do_bimestre_nao_o_de_duas_semanas(self):
        col = self.emprestar(quantidade=5)
        self.assertEqual(col["prazo_dias"],
                         servicos._config_int("PRAZO_COLECAO_DIAS", 60))
        self.assertGreater(col["prazo_dias"],
                           servicos._prazo_para_perfil("PROFESSOR"))

    def test_nao_esbarra_no_limite_de_emprestimos(self):
        """É o ponto da funcionalidade: o limite do professor é 5, e a
        turma tem 30 alunos."""
        limite = servicos._limite_para_perfil("PROFESSOR")
        self.assertLess(limite, 30, "o teste depende de um limite baixo")
        col = self.emprestar(quantidade=30)
        self.assertEqual(col["quantidade"], 30)

    def test_multa_em_aberto_continua_bloqueando(self):
        """O limite a coleção dispensa; a multa, não. Essa regra é sobre
        responsabilidade, e trinta livros pesam mais, não menos."""
        with db_cursor() as cur:
            cur.execute(
                "INSERT INTO emprestimo (exemplar_id, usuario_id, "
                "data_prevista, data_devolucao, multa) "
                "VALUES (?, ?, date('now'), datetime('now'), 12.0)",
                (self.livro["exemplares"][0][0], self.prof["id"]))

        with self.assertRaises(RegraNegocioError) as ctx:
            self.emprestar(quantidade=5)
        self.assertIn("multa", str(ctx.exception).lower())

    def test_aluno_nao_leva_colecao(self):
        self.criar_usuario(matricula="a1", perfil="ALUNO")
        with self.assertRaises(RegraNegocioError) as ctx:
            self.emprestar(quantidade=5, matricula_professor="a1")
        self.assertIn("professor", str(ctx.exception).lower())

    def test_pede_mais_do_que_existe(self):
        with self.assertRaises(RegraNegocioError) as ctx:
            self.emprestar(quantidade=100)
        self.assertIn("40", str(ctx.exception),
                      "acima do teto tem que falar do teto")

    def test_pede_mais_do_que_esta_disponivel(self):
        """Dentro do teto, mas o acervo não tem tantos livres."""
        self.emprestar(quantidade=30)
        with self.assertRaises(RegraNegocioError) as ctx:
            self.emprestar(quantidade=10, turma="outra")
        self.assertIn("5 exemplar", str(ctx.exception))

    def test_nada_sai_quando_a_colecao_e_recusada(self):
        """Recusa parcial seria o pior resultado: sete livros fora do
        acervo e nenhum registro de coleção."""
        with self.assertRaises(RegraNegocioError):
            self.emprestar(quantidade=100)
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS q FROM exemplar "
                        "WHERE status = 'EMPRESTADO'")
            self.assertEqual(cur.fetchone()["q"], 0)

    def test_nao_fura_a_fila_de_reserva(self):
        """Exemplar separado para alguém da fila não entra na coleção.

        Reservar só é permitido quando não há exemplar livre, então os
        três saem emprestados primeiro. Um volta e fica RESERVADO para
        quem esperou; os outros dois seguem fora. Uma coleção de um só
        exemplar passaria se o reservado fosse contado como livre —
        furando a fila sem ninguém ver.
        """
        pequeno = self.criar_livro(titulo="Disputado", exemplares=3)
        self.criar_usuario(matricula="a1")
        for i in (0, 1, 2):
            servicos.realizar_emprestimo(
                codigo_exemplar=pequeno["exemplares"][i][1],
                matricula_usuario="a1")
        aluno = self.criar_usuario(matricula="a2", nome="Quem espera")
        reservas.criar_reserva(pequeno["livro_id"], aluno["id"])
        servicos.realizar_devolucao(
            codigo_exemplar=pequeno["exemplares"][0][1])

        with db_cursor() as cur:
            cur.execute("SELECT status, COUNT(*) AS q FROM exemplar "
                        "WHERE livro_id = ? GROUP BY status",
                        (pequeno["livro_id"],))
            por_status = {r["status"]: r["q"] for r in cur.fetchall()}
        self.assertEqual(por_status.get("RESERVADO"), 1,
                         "o teste precisa de um exemplar reservado")

        with self.assertRaises(RegraNegocioError) as ctx:
            servicos.emprestar_colecao(livro_id=pequeno["livro_id"],
                                       matricula_professor="prof1",
                                       quantidade=1, turma="3º B")
        self.assertIn("0 exemplar", str(ctx.exception))

    def test_fica_na_auditoria(self):
        col = self.emprestar(quantidade=5, turma="3º ano B")
        with db_cursor() as cur:
            cur.execute("SELECT detalhes FROM auditoria "
                        "WHERE acao = 'EMPRESTIMO_COLECAO'")
            detalhes = cur.fetchone()["detalhes"]
        self.assertIn(col["colecao_id"], detalhes)
        self.assertIn("3º ano B", detalhes)


class TestDevolverColecao(BaseColecao):

    def test_devolve_tudo_de_uma_vez(self):
        col = self.emprestar(quantidade=30)

        res = servicos.devolver_colecao(col["colecao_id"])

        self.assertEqual(res["devolvidos"], 30)
        self.assertEqual(servicos.listar_colecoes_em_aberto(), [])
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS q FROM exemplar "
                        "WHERE livro_id = ? AND status = 'DISPONIVEL'",
                        (self.livro["livro_id"],))
            self.assertEqual(cur.fetchone()["q"], 35)

    def test_aceita_colecao_parcialmente_devolvida(self):
        """Um exemplar pode ter voltado sozinho pelo balcão. Isso não
        pode travar a devolução dos outros vinte e nove."""
        col = self.emprestar(quantidade=30)
        servicos.realizar_devolucao(codigo_exemplar=col["codigos"][0])

        res = servicos.devolver_colecao(col["colecao_id"])

        self.assertEqual(res["devolvidos"], 29)
        self.assertEqual(servicos.listar_colecoes_em_aberto(), [])

    def test_devolver_duas_vezes_avisa(self):
        col = self.emprestar(quantidade=5)
        servicos.devolver_colecao(col["colecao_id"])
        with self.assertRaises(RegraNegocioError):
            servicos.devolver_colecao(col["colecao_id"])

    def test_a_fila_de_espera_e_atendida_na_devolucao(self):
        """Trinta livros voltando com gente esperando não podem ir
        direto para a estante."""
        col = self.emprestar(quantidade=35)
        aluno = self.criar_usuario(matricula="a9", nome="Quem espera")
        reserva = reservas.criar_reserva(self.livro["livro_id"], aluno["id"])

        servicos.devolver_colecao(col["colecao_id"])

        minhas = reservas.listar_reservas_usuario(aluno["id"])
        atual = next(r for r in minhas if r["id"] == reserva["id"])
        self.assertIsNotNone(
            atual.get("exemplar_id"),
            "a devolução da coleção não separou exemplar para a fila")

    def test_a_colecao_devolvida_sai_da_lista(self):
        col = self.emprestar(quantidade=5, turma="A")
        outra = self.emprestar(quantidade=5, turma="B")
        servicos.devolver_colecao(col["colecao_id"])
        restantes = servicos.listar_colecoes_em_aberto()
        self.assertEqual([c["colecao_id"] for c in restantes],
                         [outra["colecao_id"]])


class TestColecaoNasOutrasTelas(BaseColecao):

    def test_relatorio_continua_vendo_os_trinta(self):
        """Na lista de empréstimos abertos a coleção é UMA linha para a
        bibliotecária; para o relatório e para o aviso de vencimento são
        trinta exemplares fora do acervo, e têm que continuar sendo."""
        self.emprestar(quantidade=30)
        abertos = servicos.listar_emprestimos_em_aberto()
        self.assertEqual(len(abertos), 30)
        self.assertTrue(all(e["colecao_id"] for e in abertos),
                        "a tela precisa saber quais linhas são de coleção")

    def test_o_acervo_nao_muda_de_tamanho(self):
        antes = servicos.estatisticas()["exemplares"]
        col = self.emprestar(quantidade=30)
        self.assertEqual(servicos.estatisticas()["exemplares"], antes)
        servicos.devolver_colecao(col["colecao_id"])
        self.assertEqual(servicos.estatisticas()["exemplares"], antes)

    def test_migracao_devolve_a_coluna_num_banco_antigo(self):
        """Um banco anterior a esta versão não tem as colunas, e a
        migração leve tem que criá-las."""
        from sigbef.database import init_database
        with db_cursor() as cur:
            cur.execute("ALTER TABLE emprestimo DROP COLUMN colecao_turma")
            cur.execute("PRAGMA table_info(emprestimo)")
            self.assertNotIn("colecao_turma",
                             {r["name"] for r in cur.fetchall()})

        init_database()

        with db_cursor() as cur:
            cur.execute("PRAGMA table_info(emprestimo)")
            self.assertIn("colecao_turma",
                          {r["name"] for r in cur.fetchall()})


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
