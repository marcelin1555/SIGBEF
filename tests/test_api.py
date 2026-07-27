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

    def test_acervo_vem_em_paginas(self):
        """A rota deixou de despejar o acervo inteiro num JSON só.

        Antes, `total` era o tamanho da lista devolvida — os dois viviam
        colados. Agora são coisas diferentes: `total` é o que a busca
        encontrou, `livros` é o pedaço que coube nesta página, e o app
        precisa dos dois para saber se ainda falta baixar.
        """
        for i in range(12):
            self.criar_livro(titulo=f"Paginado {i:02d}")

        status, corpo = self.get("/api/v1/livros?limite=5")
        self.assertEqual(status, 200)
        self.assertEqual(corpo["total"], 12)
        self.assertEqual(len(corpo["livros"]), 5)
        self.assertEqual(corpo["pagina"], 1)
        self.assertEqual(corpo["paginas"], 3)

        _, p2 = self.get("/api/v1/livros?limite=5&pagina=2")
        self.assertEqual(len(p2["livros"]), 5)
        _, p3 = self.get("/api/v1/livros?limite=5&pagina=3")
        self.assertEqual(len(p3["livros"]), 2)

        ids = ([l["id"] for l in corpo["livros"]]
               + [l["id"] for l in p2["livros"]]
               + [l["id"] for l in p3["livros"]])
        self.assertEqual(len(set(ids)), 12, "página repetiu ou perdeu livro")

    def test_pagina_alem_do_fim_vem_vazia_sem_erro(self):
        self.criar_livro(titulo="Só um")
        status, corpo = self.get("/api/v1/livros?pagina=99")
        self.assertEqual(status, 200)
        self.assertEqual(corpo["livros"], [])
        self.assertEqual(corpo["total"], 1)

    def test_limite_absurdo_vira_o_teto_em_vez_de_erro(self):
        """Quem integra outro sistema pode pedir demais sem querer."""
        self.criar_livro(titulo="Um")
        _, corpo = self.get("/api/v1/livros?limite=999999")
        self.assertEqual(corpo["limite"], api.LIVROS_MAX_POR_PAGINA)

    def test_parametro_de_pagina_sujo_nao_derruba(self):
        self.criar_livro(titulo="Um")
        for sujeira in ("pagina=abc", "pagina=-5", "limite=zero", "limite=0"):
            with self.subTest(q=sujeira):
                status, _ = self.get(f"/api/v1/livros?{sujeira}")
                self.assertEqual(status, 200)

    def test_busca_com_pagina_conta_o_total_da_busca(self):
        for i in range(8):
            self.criar_livro(titulo=f"Sertao {i}")
        self.criar_livro(titulo="Outro assunto")
        _, corpo = self.get("/api/v1/livros?q=Sertao&limite=3")
        self.assertEqual(corpo["total"], 8)       # o que a busca achou
        self.assertEqual(len(corpo["livros"]), 3)  # o que coube na página

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


class TestLoginDoApp(ApiTestCase):
    """Login por aluno e isolamento entre leitores (R2)."""

    def post(self, caminho, corpo, token=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        dados = json.dumps(corpo).encode("utf-8")
        conn.request("POST", caminho, body=dados, headers=headers)
        resp = conn.getresponse()
        texto = resp.read().decode("utf-8") or "{}"
        conn.close()
        return resp.status, json.loads(texto)

    def _aluno(self, matricula="alu100", senha="senha123"):
        servicos.cadastrar_usuario(nome="Aluno de Teste",
                                   matricula=matricula, perfil="ALUNO",
                                   senha=senha, gerar_cartao=False)
        return matricula, senha

    def test_login_devolve_token_e_dados(self):
        matricula, senha = self._aluno()
        status, corpo = self.post("/api/v1/login",
                                  {"matricula": matricula, "senha": senha})
        self.assertEqual(status, 200)
        self.assertTrue(corpo.get("token"))
        self.assertEqual(corpo["usuario"]["matricula"], matricula)
        self.assertNotIn("senha", json.dumps(corpo))

    def test_senha_errada_401(self):
        matricula, _ = self._aluno()
        status, _ = self.post("/api/v1/login",
                              {"matricula": matricula, "senha": "errada"})
        self.assertEqual(status, 401)

    def test_matricula_inexistente_401(self):
        status, _ = self.post("/api/v1/login",
                              {"matricula": "naoexiste", "senha": "x"})
        self.assertEqual(status, 401)

    def test_corpo_invalido_400(self):
        status, _ = self.post("/api/v1/login", {"matricula": "so-isso"})
        self.assertEqual(status, 400)

    def test_token_de_sessao_le_os_proprios_emprestimos(self):
        matricula, senha = self._aluno()
        _, corpo = self.post("/api/v1/login",
                             {"matricula": matricula, "senha": senha})
        status, _ = self.get(f"/api/v1/usuarios/{matricula}/emprestimos",
                             token=corpo["token"])
        self.assertEqual(status, 200)

    def test_aluno_NAO_le_emprestimos_de_outro(self):
        """O furo de privacidade que motivou o R2."""
        matricula, senha = self._aluno("alu100")
        self._aluno("alu200", "outra123")
        _, corpo = self.post("/api/v1/login",
                             {"matricula": matricula, "senha": senha})
        status, _ = self.get("/api/v1/usuarios/alu200/emprestimos",
                             token=corpo["token"])
        self.assertEqual(status, 403)

    def test_aluno_nao_ve_circulacao_da_escola(self):
        matricula, senha = self._aluno()
        _, corpo = self.post("/api/v1/login",
                             {"matricula": matricula, "senha": senha})
        status, _ = self.get("/api/v1/emprestimos/abertos",
                             token=corpo["token"])
        self.assertEqual(status, 403)

    def test_aluno_consulta_o_acervo(self):
        matricula, senha = self._aluno()
        _, corpo = self.post("/api/v1/login",
                             {"matricula": matricula, "senha": senha})
        status, _ = self.get("/api/v1/livros", token=corpo["token"])
        self.assertEqual(status, 200)

    def test_sessao_revogada_perde_acesso(self):
        from sigbef import auth
        matricula, senha = self._aluno()
        _, corpo = self.post("/api/v1/login",
                             {"matricula": matricula, "senha": senha})
        token = corpo["token"]
        self.assertEqual(
            self.get(f"/api/v1/usuarios/{matricula}/emprestimos",
                     token=token)[0], 200)
        auth.revogar_sessoes_app()
        self.assertEqual(
            self.get(f"/api/v1/usuarios/{matricula}/emprestimos",
                     token=token)[0], 401)

    def test_sessao_expirada_perde_acesso(self):
        from sigbef import auth
        matricula, senha = self._aluno()
        with db_cursor() as cur:
            cur.execute("SELECT id FROM usuario WHERE matricula = ?",
                        (matricula,))
            uid = cur.fetchone()["id"]
        token = auth.criar_sessao_app(uid, dias=-1)   # já nasce vencida
        status, _ = self.get(f"/api/v1/usuarios/{matricula}/emprestimos",
                             token=token)
        self.assertEqual(status, 401)

    def test_token_nao_fica_em_claro_no_banco(self):
        matricula, senha = self._aluno()
        _, corpo = self.post("/api/v1/login",
                             {"matricula": matricula, "senha": senha})
        with db_cursor() as cur:
            cur.execute("SELECT token_hash FROM sessao_app")
            guardados = [r["token_hash"] for r in cur.fetchall()]
        self.assertTrue(guardados)
        self.assertNotIn(corpo["token"], guardados)

    def test_post_em_outra_rota_continua_405(self):
        status, _ = self.post("/api/v1/livros", {"titulo": "x"})
        self.assertEqual(status, 405)

    def test_contador_de_aparelhos_pareados(self):
        from sigbef import auth
        matricula, senha = self._aluno()
        self.assertEqual(auth.sessoes_app_ativas(), 0)
        self.post("/api/v1/login", {"matricula": matricula, "senha": senha})
        self.assertEqual(auth.sessoes_app_ativas(), 1)
        auth.revogar_sessoes_app()
        self.assertEqual(auth.sessoes_app_ativas(), 0)


class TestPareamento(SigbefTestCase):
    """Endereço que vai dentro do QR code lido pelo aplicativo (R1)."""

    def test_ip_local_nao_e_loopback(self):
        ip = api.ip_local()
        # Sem rede a função devolve None de propósito; com rede, nunca 127.x
        if ip is not None:
            self.assertFalse(ip.startswith("127."))
            self.assertRegex(ip, r"^\d+\.\d+\.\d+\.\d+$")

    def test_endereco_tem_esquema_ip_e_porta(self):
        endereco = api.endereco_pareamento()
        if endereco is None:
            self.skipTest("máquina sem rede")
        self.assertTrue(endereco.startswith("sigbef://"))
        self.assertTrue(endereco.endswith(f":{api.porta_configurada()}"))

    def test_endereco_nao_carrega_token(self):
        """O QR fica exposto na tela: não pode levar credencial nenhuma."""
        api.definir_api(True)
        endereco = api.endereco_pareamento()
        if endereco is None:
            self.skipTest("máquina sem rede")
        self.assertNotIn(api.obter_token(), endereco)
        self.assertNotIn(api.obter_token_consulta(), endereco)
        for suspeito in ("token", "t=", "senha", "?"):
            self.assertNotIn(suspeito, endereco)

    def test_endereco_vira_qr_legivel(self):
        endereco = api.endereco_pareamento() or "sigbef://192.168.0.1:8765"
        from sigbef import qr_util
        matriz = qr_util.matriz(endereco)
        self.assertGreaterEqual(len(matriz), 21)


class TestEscritaPeloApp(ApiTestCase):
    """As três gravações que a API aceita (R3).

    A regra que orienta todos estes testes: só o aluno logado, só nos
    dados dele. Token de sistema não escreve nada.
    """

    def post(self, caminho, corpo=None, token=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        dados = json.dumps(corpo if corpo is not None else {}).encode("utf-8")
        conn.request("POST", caminho, body=dados, headers=headers)
        resp = conn.getresponse()
        texto = resp.read().decode("utf-8") or "{}"
        conn.close()
        return resp.status, json.loads(texto)

    def _logar(self, matricula="alu100", senha="senha123", perfil="ALUNO"):
        servicos.cadastrar_usuario(nome="Aluno de Teste",
                                   matricula=matricula, perfil=perfil,
                                   senha=senha, gerar_cartao=False)
        _, corpo = self.post("/api/v1/login",
                             {"matricula": matricula, "senha": senha})
        return corpo["token"]

    def _livro_emprestado_para_outro(self):
        """Livro sem exemplar livre — condição para poder reservar."""
        outro = servicos.cadastrar_usuario(
            nome="Quem Pegou", matricula="pegou1", perfil="ALUNO",
            senha="senha123", gerar_cartao=False)
        livro = servicos.cadastrar_livro(titulo="Livro Disputado",
                                          autores=["Autora"],
                                          quantidade_exemplares=1)
        servicos.realizar_emprestimo(
            codigo_exemplar=livro["exemplares"][0][1],
            matricula_usuario=outro["matricula"])
        return livro["livro_id"]

    # ---------------- reserva ----------------
    def test_aluno_reserva_livro_indisponivel(self):
        livro_id = self._livro_emprestado_para_outro()
        token = self._logar()
        status, corpo = self.post("/api/v1/reservas", {"livro_id": livro_id},
                                  token=token)
        self.assertEqual(status, 201)
        self.assertEqual(corpo["reserva"]["posicao"], 1)

    def test_reservar_livro_disponivel_recusado_com_motivo(self):
        livro = servicos.cadastrar_livro(titulo="Tem na Estante",
                                          autores=["Autora"],
                                          quantidade_exemplares=1)
        token = self._logar()
        status, corpo = self.post("/api/v1/reservas",
                                  {"livro_id": livro["livro_id"]},
                                  token=token)
        self.assertEqual(status, 409)
        self.assertIn("disponível", corpo["erro"])

    def test_token_de_sistema_nao_reserva(self):
        """O token completo é da escola, não de uma pessoa."""
        livro_id = self._livro_emprestado_para_outro()
        status, _ = self.post("/api/v1/reservas", {"livro_id": livro_id},
                              token=self.token)
        self.assertEqual(status, 403)

    def test_sem_token_nao_reserva(self):
        livro_id = self._livro_emprestado_para_outro()
        status, _ = self.post("/api/v1/reservas", {"livro_id": livro_id})
        self.assertEqual(status, 403)

    def test_livro_id_ausente_400(self):
        token = self._logar()
        status, _ = self.post("/api/v1/reservas", {}, token=token)
        self.assertEqual(status, 400)

    # ---------------- cancelamento ----------------
    def test_aluno_cancela_a_propria_reserva(self):
        livro_id = self._livro_emprestado_para_outro()
        token = self._logar()
        _, corpo = self.post("/api/v1/reservas", {"livro_id": livro_id},
                             token=token)
        reserva_id = corpo["reserva"]["id"]
        status, _ = self.post(f"/api/v1/reservas/{reserva_id}/cancelar",
                              token=token)
        self.assertEqual(status, 200)

    def test_aluno_NAO_cancela_reserva_de_outro(self):
        from sigbef import reservas
        livro_id = self._livro_emprestado_para_outro()
        vitima = servicos.cadastrar_usuario(
            nome="Dono da Fila", matricula="alu200", perfil="ALUNO",
            senha="outra123", gerar_cartao=False)
        r = reservas.criar_reserva(livro_id, vitima["id"])

        token = self._logar()
        status, _ = self.post(f"/api/v1/reservas/{r['id']}/cancelar",
                              token=token)
        self.assertEqual(status, 409)
        # E a reserva da vítima continua de pé.
        self.assertEqual(len(reservas.listar_reservas_usuario(vitima["id"])), 1)

    # ---------------- renovação ----------------
    def _emprestimo_do_aluno(self, matricula="alu100"):
        livro = servicos.cadastrar_livro(titulo="Livro do Aluno",
                                          autores=["Autora"],
                                          quantidade_exemplares=1)
        return servicos.realizar_emprestimo(
            codigo_exemplar=livro["exemplares"][0][1],
            matricula_usuario=matricula)

    def test_aluno_renova_o_proprio_emprestimo(self):
        token = self._logar()
        emp = self._emprestimo_do_aluno()
        status, corpo = self.post(f"/api/v1/emprestimos/{emp['id']}/renovar",
                                  token=token)
        self.assertEqual(status, 200)
        self.assertTrue(corpo["data_prevista"])

    def test_aluno_NAO_renova_emprestimo_de_outro(self):
        token = self._logar()
        outro = servicos.cadastrar_usuario(
            nome="Outro", matricula="alu200", perfil="ALUNO",
            senha="outra123", gerar_cartao=False)
        emp = self._emprestimo_do_aluno(outro["matricula"])
        status, _ = self.post(f"/api/v1/emprestimos/{emp['id']}/renovar",
                              token=token)
        self.assertEqual(status, 403)

    def test_renovar_atrasado_recusado_com_frase_do_aluno(self):
        from sigbef.database import db_cursor
        from datetime import date, timedelta
        token = self._logar()
        emp = self._emprestimo_do_aluno()
        passada = (date.today() - timedelta(days=3)).isoformat()
        with db_cursor() as cur:
            cur.execute("UPDATE emprestimo SET data_prevista = ? WHERE id = ?",
                        (passada, emp["id"]))
        status, corpo = self.post(f"/api/v1/emprestimos/{emp['id']}/renovar",
                                  token=token)
        self.assertEqual(status, 409)
        self.assertIn("prazo", corpo["erro"].lower())

    def test_emprestimo_inexistente_404(self):
        token = self._logar()
        status, _ = self.post("/api/v1/emprestimos/99999/renovar", token=token)
        self.assertEqual(status, 404)

    # ---------------- superfície de escrita ----------------
    def test_rota_de_escrita_desconhecida_405(self):
        token = self._logar()
        status, _ = self.post("/api/v1/livros", {"titulo": "Hackeado"},
                              token=token)
        self.assertEqual(status, 405)

    def test_put_e_delete_continuam_recusados(self):
        token = self._logar()
        for metodo in ("PUT", "DELETE", "PATCH"):
            conn = http.client.HTTPConnection("127.0.0.1", self.porta,
                                              timeout=5)
            conn.request(metodo, "/api/v1/reservas", body=b"{}",
                         headers={"Authorization": f"Bearer {token}"})
            resp = conn.getresponse()
            resp.read()
            conn.close()
            self.assertEqual(resp.status, 405, metodo)

    def test_leitura_traz_estatistica_e_recomendacao(self):
        token = self._logar()
        emp = self._emprestimo_do_aluno()
        with __import__("sigbef").database.db_cursor() as cur:
            cur.execute("SELECT ex.codigo_barras FROM emprestimo e "
                        "JOIN exemplar ex ON ex.id = e.exemplar_id "
                        "WHERE e.id = ?", (emp["id"],))
            codigo = cur.fetchone()["codigo_barras"]
        servicos.realizar_devolucao(codigo_exemplar=codigo)
        # Um segundo livro, para haver o que recomendar.
        servicos.cadastrar_livro(titulo="Outro Livro", autores=["Autora"],
                                  quantidade_exemplares=1)

        status, corpo = self.get("/api/v1/usuarios/alu100/leitura",
                                 token=token)
        self.assertEqual(status, 200)
        self.assertEqual(corpo["estatisticas"]["total_lidos"], 1)
        self.assertTrue(corpo["recomendacoes"])
        self.assertTrue(corpo["recomendacoes"][0]["motivo"])

    def test_aluno_NAO_le_a_leitura_de_outro(self):
        """Mesmo isolamento das outras rotas de dados pessoais."""
        token = self._logar()
        servicos.cadastrar_usuario(nome="Outro", matricula="alu200",
                                   perfil="ALUNO", senha="outra123",
                                   gerar_cartao=False)
        status, _ = self.get("/api/v1/usuarios/alu200/leitura", token=token)
        self.assertEqual(status, 403)

    def test_leitura_exige_token(self):
        status, _ = self.get("/api/v1/usuarios/alu100/leitura", token=None)
        self.assertEqual(status, 401)

    def test_limite_da_recomendacao_fica_na_faixa(self):
        """Pedido absurdo recebe o teto, não um erro."""
        token = self._logar()
        for i in range(9):
            servicos.cadastrar_livro(titulo=f"Livro {i}", autores=["A"],
                                      quantidade_exemplares=1)
        _, corpo = self.get(
            "/api/v1/usuarios/alu100/leitura?limite=3", token=token)
        self.assertEqual(len(corpo["recomendacoes"]), 3)

        _, corpo = self.get(
            "/api/v1/usuarios/alu100/leitura?limite=99999", token=token)
        self.assertLessEqual(len(corpo["recomendacoes"]), 20)

        _, corpo = self.get(
            "/api/v1/usuarios/alu100/leitura?limite=abc", token=token)
        self.assertLessEqual(len(corpo["recomendacoes"]), 6)

    def test_leitor_novo_recebe_estrutura_vazia_sem_erro(self):
        token = self._logar()
        status, corpo = self.get("/api/v1/usuarios/alu100/leitura",
                                 token=token)
        self.assertEqual(status, 200)
        self.assertEqual(corpo["estatisticas"]["total_lidos"], 0)
        self.assertEqual(corpo["recomendacoes"], [])

    def test_historico_traz_o_que_ja_foi_devolvido(self):
        """A tela do app tem a seção; faltava o dado vir."""
        token = self._logar()
        emp = self._emprestimo_do_aluno()
        _, antes = self.get("/api/v1/usuarios/alu100/emprestimos",
                            token=token)
        self.assertEqual(antes["historico"], [])

        with __import__("sigbef").database.db_cursor() as cur:
            cur.execute("SELECT ex.codigo_barras FROM emprestimo e "
                        "JOIN exemplar ex ON ex.id = e.exemplar_id "
                        "WHERE e.id = ?", (emp["id"],))
            codigo = cur.fetchone()["codigo_barras"]
        servicos.realizar_devolucao(codigo_exemplar=codigo)

        _, depois = self.get("/api/v1/usuarios/alu100/emprestimos",
                             token=token)
        self.assertEqual(depois["emprestimos_abertos"], [])
        self.assertEqual(len(depois["historico"]), 1)
        self.assertEqual(depois["historico"][0]["titulo"], "Livro do Aluno")
        self.assertTrue(depois["historico"][0]["data_devolucao"])

    def test_historico_vem_limitado(self):
        """Quem estuda há anos acumula centenas; a resposta não cresce."""
        from sigbef import api as api_mod
        token = self._logar()
        for i in range(api_mod.HISTORICO_MAX + 3):
            livro = servicos.cadastrar_livro(titulo=f"Livro {i}",
                                              autores=["Autora"],
                                              quantidade_exemplares=1)
            codigo = livro["exemplares"][0][1]
            servicos.realizar_emprestimo(codigo_exemplar=codigo,
                                         matricula_usuario="alu100")
            servicos.realizar_devolucao(codigo_exemplar=codigo)

        _, corpo = self.get("/api/v1/usuarios/alu100/emprestimos",
                            token=token)
        self.assertEqual(len(corpo["historico"]), api_mod.HISTORICO_MAX)

    def test_aluno_NAO_le_historico_de_outro(self):
        token = self._logar()
        servicos.cadastrar_usuario(nome="Outro", matricula="alu200",
                                   perfil="ALUNO", senha="outra123",
                                   gerar_cartao=False)
        status, _ = self.get("/api/v1/usuarios/alu200/emprestimos",
                             token=token)
        self.assertEqual(status, 403)

    def test_emprestimos_trazem_veredito_de_renovacao(self):
        """O app precisa saber se pode renovar antes de mostrar o botão."""
        token = self._logar()
        self._emprestimo_do_aluno()
        status, corpo = self.get("/api/v1/usuarios/alu100/emprestimos",
                                 token=token)
        self.assertEqual(status, 200)
        emp = corpo["emprestimos_abertos"][0]
        self.assertTrue(emp["pode_renovar"])
        self.assertEqual(emp["motivo_renovacao"], "")


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
