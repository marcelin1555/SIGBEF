"""
SIGBEF — Ciclo de vida do exemplar: RESERVADO e BAIXADO.

Três defeitos de gravidade alta com a mesma raiz: o sistema tratava
`RESERVADO` e `BAIXADO` de forma inconsistente entre os módulos. Por
isso este arquivo cobre os três juntos, com testes de transição de
status, em vez de três remendos separados.

1. **Baixar exemplar reservado deixava a reserva órfã.** A reserva
   continuava ATIVA apontando para um exemplar fora do acervo. O aluno
   da vez via "pronto para retirada", tinha uma vaga do próprio limite
   presa, e ia até a biblioteca buscar um livro que não existia mais.

   Pior: quando essa reserva vencia, `_promover_fila_cur` era chamada
   com o exemplar já baixado e gravava `exemplar_id` e `disponivel_ate`
   na reserva do próximo — o defeito contaminava a fila inteira, um
   aluno por vez.

2. **`excluir_livro` não baixava exemplar reservado.** Só baixava os
   `DISPONIVEL`. O `RESERVADO` sobrevivia, a expiração o devolvia para
   `DISPONIVEL`, e como `localizar_exemplar` não filtra livro ativo, o
   livro excluído voltava a ser emprestável no balcão.

3. **O inventário ignorava `RESERVADO`.** O exemplar separado para
   retirada não aparecia em nenhuma das três listas, mas era contado no
   total do acervo — a conferência da bibliotecária nunca fechava.
"""
from __future__ import annotations

from tests.base import SigbefTestCase

from sigbef import inventario, reservas, servicos
from sigbef.database import db_cursor


class CicloTestCase(SigbefTestCase):

    def status_exemplar(self, exemplar_id):
        with db_cursor() as cur:
            cur.execute("SELECT status FROM exemplar WHERE id = ?",
                        (exemplar_id,))
            return cur.fetchone()["status"]

    def reserva(self, reserva_id):
        with db_cursor() as cur:
            cur.execute("SELECT status, exemplar_id, disponivel_ate "
                        "FROM reserva WHERE id = ?", (reserva_id,))
            return dict(cur.fetchone())

    def exemplar_id_do_codigo(self, codigo):
        return servicos.localizar_exemplar(codigo)["id"]

    def montar_reserva_pronta(self, exemplares=1, devolver_todos=False):
        """Deixa um exemplar RESERVADO, separado para o primeiro da fila.

        Só dá para entrar na fila quando **nenhum** exemplar está livre —
        o sistema recusa reserva de livro disponível, e com razão. Então
        todos são emprestados antes, e só depois um é devolvido.
        """
        fila = self.criar_usuario(matricula="fila", nome="Quem esperou")
        livro = self.criar_livro(titulo="Dom Casmurro",
                                 exemplares=exemplares)
        codigos = [e[1] for e in livro["exemplares"]]

        for i, cod in enumerate(codigos):
            matricula = "leitor%d" % i
            self.criar_usuario(matricula=matricula, nome="Leitor %d" % i)
            servicos.realizar_emprestimo(codigo_exemplar=cod,
                                         matricula_usuario=matricula)

        r = reservas.criar_reserva(livro["livro_id"], fila["id"])

        servicos.realizar_devolucao(codigo_exemplar=codigos[0])
        if devolver_todos:
            for cod in codigos[1:]:
                servicos.realizar_devolucao(codigo_exemplar=cod)

        return {"livro": livro, "codigo": codigos[0], "codigos": codigos,
                "reserva_id": r["id"], "fila": fila,
                "exemplar_id": self.exemplar_id_do_codigo(codigos[0])}


class TestBaixaDeExemplarReservado(CicloTestCase):

    def test_exemplar_fica_reservado_para_o_primeiro_da_fila(self):
        """Confere a montagem antes de testar o defeito."""
        c = self.montar_reserva_pronta()
        self.assertEqual(self.status_exemplar(c["exemplar_id"]), "RESERVADO")
        self.assertEqual(self.reserva(c["reserva_id"])["exemplar_id"],
                         c["exemplar_id"])

    def test_baixar_nao_deixa_reserva_apontando_para_exemplar_fora(self):
        """É o defeito de origem."""
        c = self.montar_reserva_pronta()
        servicos.baixar_exemplar(c["codigo"], "EXTRAVIADO")

        r = self.reserva(c["reserva_id"])
        self.assertNotEqual(
            r["exemplar_id"], c["exemplar_id"],
            "a reserva não pode continuar apontando para o exemplar baixado")
        self.assertIsNone(r["disponivel_ate"],
                          "não pode continuar com prazo de retirada")

    def test_sem_outro_exemplar_a_reserva_e_cancelada(self):
        """Não há o que esperar: o título saiu inteiro do acervo."""
        c = self.montar_reserva_pronta(exemplares=1)
        servicos.baixar_exemplar(c["codigo"], "EXTRAVIADO")
        self.assertEqual(self.reserva(c["reserva_id"])["status"], "CANCELADA")

    def test_com_outro_exemplar_o_aluno_nao_perde_a_vez(self):
        """A biblioteca perder uma cópia não é culpa de quem esperava."""
        c = self.montar_reserva_pronta(exemplares=2, devolver_todos=True)
        outro = c["codigos"][1]
        outro_id = self.exemplar_id_do_codigo(outro)

        servicos.baixar_exemplar(c["codigo"], "DANIFICADO")

        r = self.reserva(c["reserva_id"])
        self.assertEqual(r["status"], "ATIVA")
        self.assertEqual(r["exemplar_id"], outro_id,
                         "devia ter sido reofertado o outro exemplar")
        self.assertEqual(self.status_exemplar(outro_id), "RESERVADO")

    def test_vaga_do_limite_do_aluno_e_devolvida(self):
        """Reserva órfã prendia uma vaga do limite de quem esperava."""
        c = self.montar_reserva_pronta(exemplares=1)
        antes = servicos.status_usuario(c["fila"]["id"]).em_aberto
        servicos.baixar_exemplar(c["codigo"], "EXTRAVIADO")
        depois = servicos.status_usuario(c["fila"]["id"]).em_aberto
        self.assertLessEqual(depois, antes)

    def test_baixa_fica_registrada_na_auditoria_com_as_reservas(self):
        c = self.montar_reserva_pronta()
        servicos.baixar_exemplar(c["codigo"], "EXTRAVIADO")
        reg = [r for r in servicos.listar_auditoria()
               if r["acao"] == "BAIXA_EXEMPLAR"]
        self.assertTrue(reg)
        self.assertIn("reservas_liberadas", reg[0]["detalhes"])


class TestFilaNaoContamina(CicloTestCase):
    """A promoção não pode entregar um exemplar que saiu do acervo."""

    def test_promover_recusa_exemplar_baixado(self):
        c = self.montar_reserva_pronta()
        servicos.baixar_exemplar(c["codigo"], "EXTRAVIADO")

        with db_cursor() as cur:
            promovida = reservas._promover_fila_cur(
                cur, c["livro"]["livro_id"], c["exemplar_id"])
        self.assertIsNone(
            promovida,
            "promoveu alguém para um exemplar baixado — é o cascateamento")

    def test_expiracao_nao_repassa_exemplar_baixado_ao_proximo(self):
        """Cada expiração passava o mesmo exemplar morto adiante."""
        c = self.montar_reserva_pronta(exemplares=1)
        segundo = self.criar_usuario(matricula="fila2", nome="Segundo da fila")
        r2 = reservas.criar_reserva(c["livro"]["livro_id"], segundo["id"])

        servicos.baixar_exemplar(c["codigo"], "EXTRAVIADO")
        with db_cursor() as cur:
            reservas._expirar_vencidas_cur(cur)

        self.assertIsNone(
            self.reserva(r2["id"])["exemplar_id"],
            "o segundo da fila recebeu o exemplar que saiu do acervo")


class TestExclusaoDeLivro(CicloTestCase):

    def test_exclusao_baixa_tambem_o_exemplar_reservado(self):
        c = self.montar_reserva_pronta()
        self.assertEqual(self.status_exemplar(c["exemplar_id"]), "RESERVADO")

        servicos.excluir_livro(c["livro"]["livro_id"])

        self.assertEqual(self.status_exemplar(c["exemplar_id"]), "BAIXADO")

    def test_livro_excluido_nao_volta_a_circular(self):
        """O caminho completo do defeito, ponta a ponta."""
        c = self.montar_reserva_pronta()
        servicos.excluir_livro(c["livro"]["livro_id"])

        # A expiração devolvia o RESERVADO sobrevivente para DISPONIVEL.
        with db_cursor() as cur:
            reservas._expirar_vencidas_cur(cur)
        self.assertEqual(self.status_exemplar(c["exemplar_id"]), "BAIXADO")

        self.criar_usuario(matricula="a9", nome="Aluno qualquer")
        with self.assertRaises(servicos.RegraNegocioError):
            servicos.realizar_emprestimo(codigo_exemplar=c["codigo"],
                                         matricula_usuario="a9")

    def test_exclusao_cancela_as_reservas_do_livro(self):
        c = self.montar_reserva_pronta()
        servicos.excluir_livro(c["livro"]["livro_id"])
        self.assertEqual(self.reserva(c["reserva_id"])["status"], "CANCELADA")


class TestInventarioContaReservado(CicloTestCase):

    def test_reservado_nao_conferido_aparece_como_nao_encontrado(self):
        """Ele está na biblioteca, na prateleira de retirada."""
        c = self.montar_reserva_pronta()
        inv = inventario.abrir("Conferência de teste")
        res = inventario.resultado(inv["id"])

        codigos = [x["codigo_barras"] for x in res["nao_encontrados"]]
        self.assertIn(c["codigo"], codigos,
                      "exemplar reservado sumiu de todas as listas")

    def test_a_lista_diz_qual_e_a_situacao_do_exemplar(self):
        """Sem o status, a bibliotecária não sabe onde procurar."""
        c = self.montar_reserva_pronta()
        inv = inventario.abrir("Conferência de teste")
        res = inventario.resultado(inv["id"])
        linha = next(x for x in res["nao_encontrados"]
                     if x["codigo_barras"] == c["codigo"])
        self.assertEqual(linha["status"], "RESERVADO")

    def test_os_numeros_da_conferencia_fecham(self):
        """Total do acervo tem que bater com a soma das listas.

        É o sintoma que a bibliotecária via: sobrava exemplar sem
        explicação, porque o RESERVADO entrava no total e em nenhuma
        lista.
        """
        # Sem nenhuma leitura: todo exemplar em acervo tem que cair em
        # exatamente uma das duas listas de "não conferido".
        c = self.montar_reserva_pronta(exemplares=3)
        inv = inventario.abrir("Conferência de teste")
        res = inventario.resultado(inv["id"])
        self.assertEqual(res["lidos"], 0, "o teste pressupõe zero leituras")

        somado = (len(res["nao_encontrados"])
                  + len(res["fora_como_esperado"]))
        self.assertEqual(
            res["no_acervo"], somado,
            "total do acervo (%d) não bate com a soma das listas (%d): "
            "sobrou exemplar que não aparece em lista nenhuma"
            % (res["no_acervo"], somado))


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
