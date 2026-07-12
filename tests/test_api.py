"""Testes da API REST somente leitura (sigbef/api.py).

Sobe o servidor HTTP real numa porta efêmera e consome com http.client,
sem tocar a rede externa.
"""
from __future__ import annotations

import http.client
import json
import threading

from tests.base import SigbefTestCase

from sigbef import api, reservas, servicos
from sigbef.database import db_cursor


class ApiTestCase(SigbefTestCase):
    def setUp(self):
        super().setUp()
        api.definir_api(True)          # gera o token na primeira ativação
        self.token = api.obter_token()
        self.servidor = api.criar_servidor(porta=0, bind="127.0.0.1")
        self.porta = self.servidor.server_address[1]
        self._th = threading.Thread(target=self.servidor.serve_forever,
                                    daemon=True)
        self._th.start()

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()

    def get(self, caminho, token="CERTO"):
        """GET na API. token: 'CERTO' usa o válido; None omite; outro envia cru."""
        conn = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        headers = {}
        if token == "CERTO":
            headers["Authorization"] = f"Bearer {self.token}"
        elif token is not None:
            headers["Authorization"] = f"Bearer {token}"
        conn.request("GET", caminho, headers=headers)
        resp = conn.getresponse()
        corpo = json.loads(resp.read().decode("utf-8") or "{}")
        conn.close()
        return resp.status, corpo


class TestAutenticacao(ApiTestCase):
    def test_ping_sem_token(self):
        status, corpo = self.get("/api/v1/ping", token=None)
        self.assertEqual(status, 200)
        self.assertTrue(corpo["ok"])
        self.assertEqual(corpo["servico"], "SIGBEF")

    def test_sem_token_401(self):
        status, corpo = self.get("/api/v1/estatisticas", token=None)
        self.assertEqual(status, 401)
        self.assertIn("erro", corpo)

    def test_token_errado_401(self):
        status, _ = self.get("/api/v1/estatisticas", token="token-falso")
        self.assertEqual(status, 401)

    def test_api_desligada_403(self):
        api.definir_api(False)
        status, corpo = self.get("/api/v1/estatisticas")
        self.assertEqual(status, 403)
        self.assertIn("desligada", corpo["erro"])

    def test_post_405(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        conn.request("POST", "/api/v1/livros",
                     headers={"Authorization": f"Bearer {self.token}"})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 405)
        conn.close()

    def test_novo_token_invalida_o_antigo(self):
        antigo = self.token
        api.gerar_novo_token()
        status, _ = self.get("/api/v1/estatisticas", token=antigo)
        self.assertEqual(status, 401)
        status, _ = self.get("/api/v1/estatisticas",
                             token=api.obter_token())
        self.assertEqual(status, 200)


class TestRotas(ApiTestCase):
    def test_estatisticas(self):
        self.criar_livro(titulo="Estatistico", exemplares=3)
        status, corpo = self.get("/api/v1/estatisticas")
        self.assertEqual(status, 200)
        self.assertEqual(corpo["livros"], 1)
        self.assertEqual(corpo["exemplares"], 3)

    def test_listar_livros_com_busca(self):
        self.criar_livro(titulo="Dom Casmurro")
        self.criar_livro(titulo="Vidas Secas")
        status, corpo = self.get("/api/v1/livros?q=Casmurro")
        self.assertEqual(status, 200)
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["livros"][0]["titulo"], "Dom Casmurro")

    def test_detalhes_do_livro(self):
        liv = self.criar_livro(titulo="Detalhado", exemplares=2,
                               isbn="9788500000001")
        status, corpo = self.get(f"/api/v1/livros/{liv['livro_id']}")
        self.assertEqual(status, 200)
        self.assertEqual(corpo["titulo"], "Detalhado")
        self.assertEqual(corpo["isbn"], "9788500000001")
        self.assertEqual(len(corpo["exemplares"]), 2)
        self.assertEqual(corpo["exemplares"][0]["status"], "DISPONIVEL")

    def test_livro_inexistente_404(self):
        status, _ = self.get("/api/v1/livros/99999")
        self.assertEqual(status, 404)

    def test_rota_desconhecida_404(self):
        status, corpo = self.get("/api/v1/naoexiste")
        self.assertEqual(status, 404)
        self.assertIn("Rotas:", corpo["erro"])

    def test_emprestimos_abertos(self):
        u = self.criar_usuario(matricula="ap1")
        liv = self.criar_livro(titulo="Circulando")
        servicos.realizar_emprestimo(
            codigo_exemplar=liv["exemplares"][0][1], matricula_usuario="ap1")
        status, corpo = self.get("/api/v1/emprestimos/abertos")
        self.assertEqual(status, 200)
        self.assertEqual(corpo["total"], 1)
        self.assertEqual(corpo["emprestimos"][0]["titulo"], "Circulando")


class TestSituacaoUsuario(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.u = self.criar_usuario(matricula="alu1", nome="Aluna Api",
                                    turma="3A")
        self.outro = self.criar_usuario(matricula="alu2")
        liv1 = self.criar_livro(titulo="Nas Maos Dela")
        servicos.realizar_emprestimo(
            codigo_exemplar=liv1["exemplares"][0][1], matricula_usuario="alu1")
        # livro esgotado por outro usuário, pra ela ter uma reserva na fila
        liv2 = self.criar_livro(titulo="Esgotadinho")
        servicos.realizar_emprestimo(
            codigo_exemplar=liv2["exemplares"][0][1], matricula_usuario="alu2")
        reservas.criar_reserva(liv2["livro_id"], self.u["id"])

    def test_situacao_completa(self):
        status, corpo = self.get("/api/v1/usuarios/alu1/emprestimos")
        self.assertEqual(status, 200)
        self.assertEqual(corpo["nome"], "Aluna Api")
        self.assertEqual(corpo["turma"], "3A")
        self.assertTrue(corpo["pode_pegar"])
        self.assertEqual(len(corpo["emprestimos_abertos"]), 1)
        self.assertEqual(corpo["emprestimos_abertos"][0]["titulo"],
                         "Nas Maos Dela")
        self.assertEqual(len(corpo["reservas_ativas"]), 1)
        self.assertEqual(corpo["reservas_ativas"][0]["titulo"], "Esgotadinho")
        self.assertEqual(corpo["reservas_ativas"][0]["posicao"], 1)

    def test_nao_vaza_dados_sensiveis(self):
        _, corpo = self.get("/api/v1/usuarios/alu1/emprestimos")
        despejo = json.dumps(corpo)
        self.assertNotIn("senha", despejo)
        self.assertNotIn("email", despejo)
        self.assertNotIn("telefone", despejo)

    def test_matricula_inexistente_404(self):
        status, _ = self.get("/api/v1/usuarios/fantasma/emprestimos")
        self.assertEqual(status, 404)


class TestEscopoDoToken(ApiTestCase):
    """Token de consulta acessa só o acervo público; dados de leitores
    exigem o token completo (princípio do menor privilégio)."""

    def token_consulta(self):
        return api.obter_token_consulta()

    def test_consulta_acessa_acervo(self):
        self.criar_livro(titulo="Publico")
        for rota in ("/api/v1/estatisticas", "/api/v1/livros",
                     "/api/v1/livros/1"):
            status, _ = self.get(rota, token=self.token_consulta())
            self.assertEqual(status, 200, rota)

    def test_consulta_barrado_em_dados_de_leitor(self):
        self.criar_usuario(matricula="alu9")
        status, corpo = self.get("/api/v1/usuarios/alu9/emprestimos",
                                 token=self.token_consulta())
        self.assertEqual(status, 403)
        self.assertIn("consulta", corpo["erro"])

    def test_consulta_barrado_em_circulacao(self):
        status, _ = self.get("/api/v1/emprestimos/abertos",
                             token=self.token_consulta())
        self.assertEqual(status, 403)

    def test_completo_acessa_tudo(self):
        self.criar_usuario(matricula="alu8")
        status, _ = self.get("/api/v1/usuarios/alu8/emprestimos")  # token completo
        self.assertEqual(status, 200)
        status, _ = self.get("/api/v1/emprestimos/abertos")
        self.assertEqual(status, 200)

    def test_tokens_sao_distintos(self):
        self.assertNotEqual(api.obter_token(), api.obter_token_consulta())
        self.assertTrue(api.obter_token_consulta())


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
