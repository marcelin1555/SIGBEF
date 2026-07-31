"""Testes dos avisos de vencimento por e-mail (sigbef/notificacoes.py)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.base import SigbefTestCase

from sigbef import notificacoes, servicos
from sigbef.database import db_cursor, set_config
from sigbef.servicos import RegraNegocioError


class NotificacoesTestCase(SigbefTestCase):
    def setUp(self):
        super().setUp()
        notificacoes.definir_avisos(True)
        # Prazo de aluno é 7 dias; janela de 10 pega o empréstimo de hoje
        set_config("EMAIL_DIAS_ANTES", "10")
        self.u = self.criar_usuario(matricula="a1", nome="Ana Mail",
                                    email="ana@escola.br")
        liv = self.criar_livro(titulo="Com Prazo", exemplares=2)
        self.codigo = liv["exemplares"][0][1]
        self.codigo2 = liv["exemplares"][1][1]
        servicos.realizar_emprestimo(codigo_exemplar=self.codigo,
                                     matricula_usuario="a1")

    def transporte_fake(self):
        caixa = []
        return caixa, lambda msgs: caixa.extend(msgs)


class TestPendentes(NotificacoesTestCase):
    def test_emprestimo_na_janela_aparece(self):
        pend = notificacoes.emails_pendentes()
        self.assertEqual(len(pend), 1)
        self.assertEqual(pend[0]["email"], "ana@escola.br")
        self.assertEqual(pend[0]["titulo"], "Com Prazo")

    def test_usuario_sem_email_fica_de_fora(self):
        self.criar_usuario(matricula="semmail", nome="Sem Mail")
        servicos.realizar_emprestimo(codigo_exemplar=self.codigo2,
                                     matricula_usuario="semmail")
        pend = notificacoes.emails_pendentes()
        self.assertEqual(len(pend), 1)  # só a Ana

    def test_fora_da_janela_fica_de_fora(self):
        set_config("EMAIL_DIAS_ANTES", "1")  # vence em 7, janela de 1
        self.assertEqual(notificacoes.emails_pendentes(), [])

    def test_devolvido_fica_de_fora(self):
        servicos.realizar_devolucao(codigo_exemplar=self.codigo)
        self.assertEqual(notificacoes.emails_pendentes(), [])


class TestEnvio(NotificacoesTestCase):
    def test_envia_e_registra(self):
        caixa, transporte = self.transporte_fake()
        res = notificacoes.enviar_avisos(transporte=transporte)
        self.assertEqual(res["enviados"], 1)
        self.assertEqual(len(caixa), 1)
        self.assertEqual(caixa[0]["To"], "ana@escola.br")
        self.assertIn("Com Prazo", caixa[0]["Subject"])
        self.assertIn("Ana Mail", caixa[0].get_content())

    def test_nao_reenvia_o_mesmo_aviso(self):
        caixa, transporte = self.transporte_fake()
        notificacoes.enviar_avisos(transporte=transporte)
        res2 = notificacoes.enviar_avisos(transporte=transporte)
        self.assertEqual(res2["enviados"], 0)
        self.assertEqual(len(caixa), 1)

    def test_falha_no_envio_nao_registra(self):
        def transporte_quebrado(msgs):
            raise RegraNegocioError("sem rede")
        with self.assertRaises(RegraNegocioError):
            notificacoes.enviar_avisos(transporte=transporte_quebrado)
        # Nada registrado: o aviso continua pendente pra nova tentativa
        self.assertEqual(len(notificacoes.emails_pendentes()), 1)

    def test_desligado_recusa(self):
        notificacoes.definir_avisos(False)
        with self.assertRaises(RegraNegocioError):
            notificacoes.enviar_avisos(transporte=lambda m: None)

    def test_auditoria_do_envio(self):
        _, transporte = self.transporte_fake()
        notificacoes.enviar_avisos(transporte=transporte, executor_id=self.u["id"])
        with db_cursor() as cur:
            cur.execute("SELECT detalhes FROM auditoria WHERE acao = 'EMAIL_AVISOS'")
            row = cur.fetchone()
        self.assertIn("enviados=1", row["detalhes"])


class TestTransporteReal(NotificacoesTestCase):
    def test_sem_host_orienta_configurar(self):
        set_config("SMTP_HOST", "")
        with self.assertRaises(RegraNegocioError):
            notificacoes.enviar_avisos()  # transporte real, sem host

    def test_queda_no_meio_do_lote_nao_reenvia_quem_ja_recebeu(self):
        """Bug: uma conexão SMTP que cai no meio do lote não podia fazer
        quem já recebeu o aviso ser avisado de novo na próxima tentativa
        — antes, o registro só acontecia depois do lote inteiro dar
        certo, então uma falha parcial apagava o progresso já feito."""
        set_config("SMTP_HOST", "smtp.escola.br")
        self.criar_usuario(matricula="a2", nome="Bia Mail",
                           email="bia@escola.br")
        liv = self.criar_livro(titulo="Segundo Prazo", exemplares=1)
        servicos.realizar_emprestimo(codigo_exemplar=liv["exemplares"][0][1],
                                     matricula_usuario="a2")
        self.assertEqual(len(notificacoes.emails_pendentes()), 2)

        fake_smtp = MagicMock()
        fake_smtp.has_extn.return_value = False
        fake_smtp.send_message.side_effect = [None, OSError("conexão caiu")]

        with patch("sigbef.notificacoes.smtplib.SMTP", return_value=fake_smtp):
            with self.assertRaises(RegraNegocioError):
                notificacoes.enviar_avisos()

        self.assertEqual(fake_smtp.send_message.call_count, 2)
        # O primeiro já saiu antes da queda: não pode voltar a aparecer
        # como pendente, senão a próxima tentativa manda de novo.
        self.assertEqual(len(notificacoes.emails_pendentes()), 1)


class TestAvisoReserva(NotificacoesTestCase):
    """Aviso de reserva disponível (livro reservado ficou separado)."""

    def setUp(self):
        super().setUp()
        from sigbef import reservas
        self.reservas = reservas
        # Beto tem e-mail e reserva um livro esgotado; ao devolver, o
        # exemplar fica separado pra ele (vira pendente de aviso).
        self.beto = self.criar_usuario(matricula="beto", nome="Beto B",
                                       email="beto@escola.br")
        liv = self.criar_livro(titulo="Reservadão", exemplares=1)
        self.codigo_res = liv["exemplares"][0][1]
        servicos.realizar_emprestimo(codigo_exemplar=self.codigo_res,
                                     matricula_usuario="a1")
        reservas.criar_reserva(liv["livro_id"], self.beto["id"])
        servicos.realizar_devolucao(codigo_exemplar=self.codigo_res)

    def test_reserva_separada_entra_em_pendentes(self):
        pend = notificacoes.reservas_pendentes()
        self.assertEqual(len(pend), 1)
        self.assertEqual(pend[0]["email"], "beto@escola.br")
        self.assertEqual(pend[0]["titulo"], "Reservadão")

    def test_reserva_de_usuario_sem_email_fica_de_fora(self):
        semmail = self.criar_usuario(matricula="semmail", nome="Sem Mail")
        liv = self.criar_livro(titulo="Outro Esgotado", exemplares=1)
        cod = liv["exemplares"][0][1]
        servicos.realizar_emprestimo(codigo_exemplar=cod,
                                     matricula_usuario="a1")
        self.reservas.criar_reserva(liv["livro_id"], semmail["id"])
        servicos.realizar_devolucao(codigo_exemplar=cod)
        titulos = [p["titulo"] for p in notificacoes.reservas_pendentes()]
        self.assertNotIn("Outro Esgotado", titulos)

    def test_envio_combinado_conta_os_dois_tipos(self):
        caixa, transporte = self.transporte_fake()
        res = notificacoes.enviar_avisos(transporte=transporte)
        # 1 de vencimento (Ana, do setUp base) + 1 de reserva (Beto)
        self.assertEqual(res["vencimento"], 1)
        self.assertEqual(res["reserva"], 1)
        self.assertEqual(res["enviados"], 2)
        destinatarios = {m["To"] for m in caixa}
        self.assertIn("beto@escola.br", destinatarios)
        assunto_reserva = [m["Subject"] for m in caixa
                           if m["To"] == "beto@escola.br"][0]
        self.assertIn("Reservadão", assunto_reserva)

    def test_nao_reenvia_aviso_de_reserva(self):
        _, transporte = self.transporte_fake()
        notificacoes.enviar_avisos(transporte=transporte)
        res2 = notificacoes.enviar_avisos(transporte=transporte)
        self.assertEqual(res2["reserva"], 0)


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
