"""
SIGBEF — Contagens que mentiam e um limite que dava para furar.

Três defeitos de correção, sem relação de código entre si, mas com o
mesmo efeito: o sistema afirmava um número que não correspondia ao que
existia.

1. **O limite de empréstimos era conferido fora da transação.** Entre a
   verificação e a gravação cabia um segundo empréstimo — duas
   bibliotecárias atendendo ao mesmo tempo, ou o balcão e o aplicativo.
   As duas passavam com o mesmo número e as duas gravavam.

2. **`estatisticas()` contava exemplar baixado.** Baixar um livro
   perdido *aumentava* o total de exemplares mostrado no painel, porque
   a contagem não filtrava nada.

3. **A posição na fila divergia entre o balcão e o aplicativo.** A
   consulta do balcão somava também as reservas que já tinham exemplar
   separado; a do aplicativo não. O mesmo aluno era o 2º da fila para a
   bibliotecária e o 1º no celular.
"""
from __future__ import annotations

from tests.base import SigbefTestCase

from sigbef import reservas, servicos
from sigbef.database import db_cursor
from sigbef.servicos import RegraNegocioError


class TestLimiteNaTransacao(SigbefTestCase):

    def test_limite_e_respeitado_no_caminho_normal(self):
        """Confere a regra antes de testar como ela era furada."""
        self.criar_usuario(matricula="a1")
        limite = servicos._limite_para_perfil("ALUNO")
        livro = self.criar_livro(exemplares=limite + 1)
        for i in range(limite):
            servicos.realizar_emprestimo(
                codigo_exemplar=livro["exemplares"][i][1],
                matricula_usuario="a1")
        with self.assertRaises(RegraNegocioError):
            servicos.realizar_emprestimo(
                codigo_exemplar=livro["exemplares"][limite][1],
                matricula_usuario="a1")

    def test_limite_nao_e_furado_por_emprestimo_gravado_no_meio(self):
        """Simula o segundo atendimento que entrava entre a checagem e a
        gravação.

        `status_usuario` roda numa transação própria. Aqui o teste faz
        exatamente o que a concorrência fazia: deixa o usuário passar na
        checagem e grava um empréstimo direto no banco antes que o
        `realizar_emprestimo` chegue ao INSERT.
        """
        usuario = self.criar_usuario(matricula="a1")
        limite = servicos._limite_para_perfil("ALUNO")
        livro = self.criar_livro(exemplares=limite + 2)

        # Chega a um a menos que o limite pelo caminho normal.
        for i in range(limite - 1):
            servicos.realizar_emprestimo(
                codigo_exemplar=livro["exemplares"][i][1],
                matricula_usuario="a1")

        # O "outro atendimento": grava direto, sem passar pelo serviço.
        outro = servicos.localizar_exemplar(livro["exemplares"][limite][1])
        with db_cursor() as cur:
            cur.execute(
                "INSERT INTO emprestimo (exemplar_id, usuario_id, "
                "data_prevista) VALUES (?, ?, date('now','+7 days'))",
                (outro["id"], usuario["id"]))
            cur.execute("UPDATE exemplar SET status = 'EMPRESTADO' "
                        "WHERE id = ?", (outro["id"],))

        # Agora o usuário já está no limite. O empréstimo tem que ser
        # recusado, mesmo que a checagem de fora tenha passado.
        with self.assertRaises(RegraNegocioError) as ctx:
            servicos.realizar_emprestimo(
                codigo_exemplar=livro["exemplares"][limite - 1][1],
                matricula_usuario="a1")
        self.assertIn("imite", str(ctx.exception))

        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS q FROM emprestimo "
                        "WHERE usuario_id = ? AND data_devolucao IS NULL",
                        (usuario["id"],))
            self.assertLessEqual(
                cur.fetchone()["q"], limite,
                "o usuário passou do limite de empréstimos simultâneos")


class TestEstatisticasNaoContamBaixado(SigbefTestCase):

    def test_baixar_exemplar_diminui_o_acervo(self):
        """Baixar um livro perdido aumentava o total. É o defeito."""
        self.criar_usuario(matricula="a1")
        livro = self.criar_livro(exemplares=3)
        antes = servicos.estatisticas()["exemplares"]

        servicos.baixar_exemplar(livro["exemplares"][0][1], "EXTRAVIADO")

        depois = servicos.estatisticas()["exemplares"]
        self.assertEqual(depois, antes - 1,
                         "exemplar baixado saiu do acervo e não pode "
                         "continuar sendo contado")

    def test_total_bate_com_a_soma_dos_status(self):
        """O total tem que ser a soma do que está em cada situação."""
        self.criar_usuario(matricula="a1")
        livro = self.criar_livro(exemplares=4)
        servicos.realizar_emprestimo(
            codigo_exemplar=livro["exemplares"][0][1],
            matricula_usuario="a1")
        servicos.baixar_exemplar(livro["exemplares"][1][1], "DANIFICADO")

        est = servicos.estatisticas()
        with db_cursor() as cur:
            cur.execute("SELECT status, COUNT(*) AS q FROM exemplar "
                        "GROUP BY status")
            por_status = {r["status"]: r["q"] for r in cur.fetchall()}
        em_acervo = sum(q for s, q in por_status.items() if s != "BAIXADO")
        self.assertEqual(est["exemplares"], em_acervo)


class TestPosicaoNaFilaNaoDiverge(SigbefTestCase):

    def montar_fila(self, quantos_esperando=2):
        """Um livro com todos os exemplares emprestados e uma fila."""
        livro = self.criar_livro(titulo="Disputado", exemplares=1)
        codigo = livro["exemplares"][0][1]
        self.criar_usuario(matricula="leitor", nome="Quem pegou")
        servicos.realizar_emprestimo(codigo_exemplar=codigo,
                                     matricula_usuario="leitor")
        fila = []
        for i in range(quantos_esperando):
            u = self.criar_usuario(matricula="fila%d" % i,
                                   nome="Da fila %d" % i)
            fila.append((u, reservas.criar_reserva(livro["livro_id"], u["id"])))
        return livro, codigo, fila

    def test_balcao_e_aplicativo_dizem_a_mesma_posicao(self):
        """É o defeito de origem, medido dos dois lados."""
        livro, codigo, fila = self.montar_fila(quantos_esperando=3)
        # Devolve: o primeiro da fila ganha exemplar separado e sai da
        # disputa. Os outros dois continuam esperando.
        servicos.realizar_devolucao(codigo_exemplar=codigo)

        for usuario, reserva in fila:
            do_app = next(r for r in reservas.listar_reservas_usuario(
                usuario["id"]) if r["id"] == reserva["id"])
            do_balcao = next(r for r in reservas.listar_reservas_ativas()
                             if r["id"] == reserva["id"])
            self.assertEqual(
                do_balcao["posicao"], do_app["posicao"],
                "balcão diz %s e o app diz %s para a reserva de %s"
                % (do_balcao["posicao"], do_app["posicao"], usuario["id"]))

    def test_quem_ja_tem_exemplar_nao_ocupa_lugar_na_fila(self):
        """Quem já tem o livro separado saiu da disputa pela próxima
        devolução, e não pode inflar a posição de quem ainda espera."""
        livro, codigo, fila = self.montar_fila(quantos_esperando=2)
        servicos.realizar_devolucao(codigo_exemplar=codigo)

        segundo = fila[1][1]
        do_balcao = next(r for r in reservas.listar_reservas_ativas()
                         if r["id"] == segundo["id"])
        self.assertEqual(
            do_balcao["posicao"], 1,
            "o segundo da fila virou o primeiro a esperar quando o "
            "primeiro recebeu o exemplar separado")


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
