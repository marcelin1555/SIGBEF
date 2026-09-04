"""
SIGBEF — Desfazer uma baixa dada por engano.

Aconteceu na biblioteca: na tela de detalhes do livro, "Dar baixa no
exemplar" fica ao lado de "Corrigir tombo" e "Mudar prateleira" — dois
botões inofensivos — e a bibliotecária clicou no errado. Até aqui não
havia volta.

E a baixa não é só o exemplar. Quando o livro está com alguém, ela
**encerra o empréstimo e lança a multa de atraso**. Um clique errado
cobrava de um aluno uma multa que não existia, e fechava um empréstimo
que continuava de pé — o livro segue na mochila dele.

O que estes testes fixam:

1. O exemplar volta ao acervo, com a situação certa: EMPRESTADO se o
   livro está com alguém, DISPONIVEL se estava na estante.
2. A multa lançada pela baixa é apagada. Ela nunca deveria ter existido.
3. A fila de espera **não** é desfeita: quem já recebeu outro exemplar
   legitimamente não pode perdê-lo por causa do erro de outra pessoa.
4. Baixas feitas antes desta versão também podem ser revertidas — a da
   bibliotecária é uma delas.

Uso:
    python -m unittest tests.test_reverter_baixa -v
"""
from __future__ import annotations

from tests.base import SigbefTestCase

from sigbef import reservas, servicos
from sigbef.database import db_cursor
from sigbef.servicos import RegraNegocioError


class BaseReversao(SigbefTestCase):

    def setUp(self):
        super().setUp()
        self.aluno = self.criar_usuario(matricula="a1", nome="Aluno da Vez")
        self.livro = self.criar_livro(titulo="Dom Casmurro", exemplares=3)
        self.codigo = self.livro["exemplares"][0][1]

    def status(self, codigo):
        return servicos.localizar_exemplar(codigo)["status"]


class TestReverterBaixaSimples(BaseReversao):

    def test_exemplar_volta_para_a_estante(self):
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")
        self.assertEqual(self.status(self.codigo), "BAIXADO")

        res = servicos.reverter_baixa(self.codigo, "clique errado no balcão")

        self.assertEqual(self.status(self.codigo), "DISPONIVEL")
        self.assertEqual(res["status"], "DISPONIVEL")

    def test_o_acervo_volta_ao_tamanho_de_antes(self):
        antes = servicos.estatisticas()["exemplares"]
        servicos.baixar_exemplar(self.codigo, "DANIFICADO")
        self.assertEqual(servicos.estatisticas()["exemplares"], antes - 1)

        servicos.reverter_baixa(self.codigo, "engano")

        self.assertEqual(servicos.estatisticas()["exemplares"], antes)

    def test_o_motivo_da_baixa_e_limpo(self):
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")
        servicos.reverter_baixa(self.codigo, "engano")
        with db_cursor() as cur:
            cur.execute("SELECT motivo_baixa, data_baixa FROM exemplar "
                        "WHERE codigo_barras = ?", (self.codigo,))
            linha = cur.fetchone()
        self.assertIsNone(linha["motivo_baixa"])
        self.assertIsNone(linha["data_baixa"])

    def test_justificativa_e_obrigatoria(self):
        """Corrigir o histórico do acervo sem dizer por quê é histórico
        em que ninguém confia depois."""
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")
        with self.assertRaises(RegraNegocioError):
            servicos.reverter_baixa(self.codigo, "   ")

    def test_nao_reverte_o_que_nao_foi_baixado(self):
        with self.assertRaises(RegraNegocioError) as ctx:
            servicos.reverter_baixa(self.codigo, "engano")
        self.assertIn("no acervo", str(ctx.exception))

    def test_fica_na_auditoria_com_a_justificativa(self):
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")
        servicos.reverter_baixa(self.codigo, "cliquei no botão errado")
        with db_cursor() as cur:
            cur.execute("SELECT detalhes FROM auditoria "
                        "WHERE acao = 'BAIXA_REVERTIDA'")
            detalhes = cur.fetchone()["detalhes"]
        self.assertIn("cliquei no botão errado", detalhes)
        self.assertIn("EXTRAVIADO", detalhes)


class TestReverterBaixaDeLivroEmprestado(BaseReversao):
    """O caso que dói: o livro está com um aluno."""

    def setUp(self):
        super().setUp()
        servicos.realizar_emprestimo(codigo_exemplar=self.codigo,
                                     matricula_usuario="a1")
        # Empréstimo vencido, para a baixa lançar multa de verdade.
        with db_cursor() as cur:
            cur.execute(
                "UPDATE emprestimo SET data_prevista = date('now','-10 days') "
                "WHERE data_devolucao IS NULL")

    def test_a_baixa_por_engano_cobrava_multa_do_aluno(self):
        """Confere o estrago antes de testar o conserto."""
        r = servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")
        self.assertTrue(r["estava_emprestado"])
        self.assertGreater(r["multa"], 0)

    def test_reverter_apaga_a_multa_que_a_baixa_lancou(self):
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")

        res = servicos.reverter_baixa(self.codigo, "não foi perdido, engano")

        self.assertGreater(res["multa_apagada"], 0)
        with db_cursor() as cur:
            cur.execute("SELECT multa FROM emprestimo WHERE id = ?",
                        (res["emprestimo_reaberto"],))
            self.assertEqual(cur.fetchone()["multa"], 0)

    def test_o_emprestimo_reabre(self):
        """O livro continua com o aluno — nunca voltou para a estante."""
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")

        res = servicos.reverter_baixa(self.codigo, "engano")

        self.assertIsNotNone(res["emprestimo_reaberto"])
        self.assertEqual(res["status"], "EMPRESTADO")
        self.assertEqual(self.status(self.codigo), "EMPRESTADO")
        abertos = servicos.listar_emprestimos_em_aberto()
        self.assertEqual(len(abertos), 1)
        self.assertEqual(abertos[0]["codigo_barras"], self.codigo)

    def test_o_aluno_volta_a_aparecer_com_o_livro(self):
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")
        servicos.reverter_baixa(self.codigo, "engano")
        st = servicos.status_usuario(self.aluno["id"])
        self.assertEqual(st.em_aberto, 1)
        self.assertEqual(st.multas_em_aberto, 0)

    def test_depois_de_reverter_da_para_devolver_normalmente(self):
        """A prova de que o empréstimo reaberto é um empréstimo de
        verdade, e não um remendo."""
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")
        servicos.reverter_baixa(self.codigo, "engano")

        dev = servicos.realizar_devolucao(codigo_exemplar=self.codigo)

        self.assertEqual(self.status(self.codigo), "DISPONIVEL")
        self.assertGreater(dev["multa"], 0,
                           "o atraso real continua valendo na devolução")

    def test_recusa_quando_a_multa_ja_foi_movimentada(self):
        """Se o dinheiro já entrou, quem resolve é gente, não o sistema."""
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")
        with db_cursor() as cur:
            cur.execute("SELECT id FROM emprestimo LIMIT 1")
            emp_id = cur.fetchone()["id"]
        servicos.quitar_multa(emp_id)

        with self.assertRaises(RegraNegocioError) as ctx:
            servicos.reverter_baixa(self.codigo, "engano")
        self.assertIn("quitada", str(ctx.exception).lower())
        self.assertEqual(self.status(self.codigo), "BAIXADO",
                         "recusou, então nada pode ter mudado")


class TestReversaoNaoDesfazAFila(BaseReversao):

    def test_quem_ja_recebeu_outro_exemplar_nao_perde(self):
        """A baixa devolve as reservas à fila e pode separar outra cópia.
        Reverter não pode tirar de alguém um livro já oferecido a ele.
        """
        pequeno = self.criar_livro(titulo="Disputado", exemplares=2)
        c0, c1 = (pequeno["exemplares"][0][1], pequeno["exemplares"][1][1])
        servicos.realizar_emprestimo(codigo_exemplar=c0,
                                     matricula_usuario="a1")
        servicos.realizar_emprestimo(codigo_exemplar=c1,
                                     matricula_usuario="a1")
        espera = self.criar_usuario(matricula="a2", nome="Quem espera")
        reserva = reservas.criar_reserva(pequeno["livro_id"], espera["id"])

        # Devolve um: a reserva ganha esse exemplar separado.
        servicos.realizar_devolucao(codigo_exemplar=c0)
        separado = next(r for r in reservas.listar_reservas_usuario(
            espera["id"]) if r["id"] == reserva["id"])
        self.assertIsNotNone(separado.get("exemplar_id"))

        # Baixa por engano o OUTRO exemplar, e reverte.
        servicos.baixar_exemplar(c1, "EXTRAVIADO")
        servicos.reverter_baixa(c1, "engano")

        ainda = next(r for r in reservas.listar_reservas_usuario(
            espera["id"]) if r["id"] == reserva["id"])
        self.assertEqual(ainda.get("exemplar_id"), separado.get("exemplar_id"),
                         "a reversão tirou da fila um exemplar já separado")

    def test_exemplar_que_volta_livre_atende_quem_espera(self):
        """O contrário também vale: se ninguém foi atendido no lugar
        dele, o exemplar que volta entra na fila pela porta da frente."""
        unico = self.criar_livro(titulo="So um", exemplares=1)
        codigo = unico["exemplares"][0][1]
        servicos.realizar_emprestimo(codigo_exemplar=codigo,
                                     matricula_usuario="a1")
        espera = self.criar_usuario(matricula="a3", nome="Na fila")
        reserva = reservas.criar_reserva(unico["livro_id"], espera["id"])
        servicos.realizar_devolucao(codigo_exemplar=codigo)
        # Agora o exemplar está RESERVADO para a3. A baixa o solta.
        servicos.baixar_exemplar(codigo, "EXTRAVIADO")

        res = servicos.reverter_baixa(codigo, "engano")

        self.assertIsNotNone(
            res["reserva_atendida"],
            "o exemplar voltou livre com gente na fila e não foi oferecido")
        atual = next(r for r in reservas.listar_reservas_usuario(
            espera["id"]) if r["id"] == reserva["id"])
        self.assertIsNotNone(atual.get("exemplar_id"))


class TestBaixaAntigaSemVinculo(BaseReversao):
    """A baixa da bibliotecária foi dada ANTES desta versão existir.

    Nos registros dela não há a marca `encerrado_por_baixa`, e o único
    indício de qual empréstimo a baixa fechou é a data. **Indício não é
    prova**: um livro devolvido normalmente e baixado no mesmo dia casa
    pela data do mesmo jeito. Por isso o sistema não decide sozinho —
    ele mostra o candidato e espera alguém confirmar.
    """

    def simular_baixa_antiga(self):
        servicos.realizar_emprestimo(codigo_exemplar=self.codigo,
                                     matricula_usuario="a1")
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")
        with db_cursor() as cur:      # o banco de antes não tinha a marca
            cur.execute("UPDATE emprestimo SET encerrado_por_baixa = 0")

    def test_sem_confirmacao_o_emprestimo_nao_reabre(self):
        """Silêncio não é autorização: reverte só o exemplar."""
        self.simular_baixa_antiga()

        res = servicos.reverter_baixa(self.codigo, "engano")

        self.assertIsNone(res["emprestimo_reaberto"])
        self.assertEqual(self.status(self.codigo), "DISPONIVEL")

    def test_o_candidato_e_oferecido_com_nome_e_data(self):
        """A bibliotecária precisa reconhecer o empréstimo para
        confirmar — só um id não diz nada a ninguém."""
        self.simular_baixa_antiga()

        cand = servicos.candidato_de_reabertura(self.codigo)

        self.assertIsNotNone(cand)
        self.assertEqual(cand["nome"], "Aluno da Vez")
        self.assertEqual(cand["matricula"], "a1")

    def test_confirmado_o_emprestimo_reabre(self):
        self.simular_baixa_antiga()
        cand = servicos.candidato_de_reabertura(self.codigo)

        res = servicos.reverter_baixa(self.codigo, "engano da bibliotecária",
                                      reabrir_emprestimo_id=cand["id"])

        self.assertEqual(res["emprestimo_reaberto"], cand["id"])
        self.assertTrue(res["reabertura_confirmada"])
        self.assertEqual(self.status(self.codigo), "EMPRESTADO")

    def test_nao_ha_candidato_quando_o_vinculo_esta_registrado(self):
        """Baixa desta versão em diante não gera pergunta nenhuma."""
        servicos.realizar_emprestimo(codigo_exemplar=self.codigo,
                                     matricula_usuario="a1")
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")
        self.assertIsNone(servicos.candidato_de_reabertura(self.codigo))

    def test_recusa_reabrir_emprestimo_de_outro_exemplar(self):
        """Confirmação de gente não dispensa conferência do sistema."""
        self.simular_baixa_antiga()
        outro = self.livro["exemplares"][1][1]
        servicos.realizar_emprestimo(codigo_exemplar=outro,
                                     matricula_usuario="a1")
        with db_cursor() as cur:
            cur.execute("SELECT id FROM emprestimo WHERE exemplar_id != "
                        "(SELECT id FROM exemplar WHERE codigo_barras = ?)",
                        (self.codigo,))
            alheio = cur.fetchone()["id"]

        with self.assertRaises(RegraNegocioError):
            servicos.reverter_baixa(self.codigo, "engano",
                                    reabrir_emprestimo_id=alheio)

    def test_nao_ressuscita_emprestimo_devolvido_de_verdade(self):
        """O defeito que este desenho evita.

        Livro devolvido normalmente e, depois, baixado no mesmo dia. A
        data casa, mas aquele empréstimo terminou de verdade — reabrir
        inventaria um livro na mão de quem já o entregou.
        """
        servicos.realizar_emprestimo(codigo_exemplar=self.codigo,
                                     matricula_usuario="a1")
        servicos.realizar_devolucao(codigo_exemplar=self.codigo)
        servicos.baixar_exemplar(self.codigo, "EXTRAVIADO")

        res = servicos.reverter_baixa(self.codigo, "engano")

        self.assertIsNone(res["emprestimo_reaberto"])
        self.assertEqual(self.status(self.codigo), "DISPONIVEL")
        self.assertEqual(servicos.listar_emprestimos_em_aberto(), [])


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
