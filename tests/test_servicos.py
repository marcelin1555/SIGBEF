"""
SIGBEF — Testes da camada de serviços (regras de negócio).

Cobre cadastro de livros/exemplares, usuários, empréstimos, devoluções,
multas, importação CSV e relatórios, sempre contra um banco SQLite
temporário zerado a cada teste (ver tests.base).

Uso:
    python -m unittest tests.test_servicos -v
"""
# O import de tests.base precisa vir antes de qualquer import de sigbef
# (ele aponta SIGBEF_DB_PATH para um banco temporário).
from tests.base import SigbefTestCase

import os
import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from sigbef import servicos
from sigbef.database import db_cursor, get_config, set_config
from sigbef.servicos import RegraNegocioError


class ServicosTestCase(SigbefTestCase):
    """Base com helpers específicos dos testes de serviços."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def emprestar(self, codigo, matricula, **kw):
        return servicos.realizar_emprestimo(
            codigo_exemplar=codigo, matricula_usuario=matricula, **kw)

    def atrasar_emprestimo(self, emprestimo_id, dias=3):
        """Simula atraso movendo a data prevista para o passado."""
        passada = (date.today() - timedelta(days=dias)).isoformat()
        with db_cursor() as cur:
            cur.execute("UPDATE emprestimo SET data_prevista = ? WHERE id = ?",
                        (passada, emprestimo_id))

    def status_exemplar(self, exemplar_id):
        with db_cursor() as cur:
            cur.execute("SELECT status FROM exemplar WHERE id = ?",
                        (exemplar_id,))
            return cur.fetchone()["status"]

    def csv_temporario(self, conteudo, encoding="utf-8-sig"):
        """Grava um CSV num diretório temporário e retorna o caminho."""
        pasta = tempfile.mkdtemp(prefix="sigbef-csv-")
        self.addCleanup(shutil.rmtree, pasta, ignore_errors=True)
        caminho = os.path.join(pasta, "acervo.csv")
        if isinstance(conteudo, bytes):
            Path(caminho).write_bytes(conteudo)
        else:
            Path(caminho).write_text(conteudo, encoding=encoding)
        return caminho


# ---------------------------------------------------------------------------
# Livros e exemplares
# ---------------------------------------------------------------------------
class TestCadastroLivro(ServicosTestCase):
    """Cadastro de livro com autores e exemplares iniciais."""

    def test_cadastro_com_multiplos_exemplares(self):
        """Cadastra com 3 exemplares e confere os tombos sequenciais."""
        res = self.criar_livro(titulo="Dom Casmurro", exemplares=3,
                               autores=["Machado de Assis"])
        self.assertEqual(len(res["exemplares"]), 3)
        detalhes = servicos.detalhes_livro(res["livro_id"])
        tombos = [ex["numero_tombo"] for ex in detalhes["exemplares"]]
        esperados = [f"{res['livro_id']:05d}-{i:03d}" for i in (1, 2, 3)]
        self.assertEqual(tombos, esperados)

    def test_erro_sem_titulo(self):
        """Título em branco é rejeitado."""
        with self.assertRaises(RegraNegocioError):
            servicos.cadastrar_livro(titulo="   ", autores=["Fulano"])

    def test_erro_sem_autores(self):
        """Lista de autores vazia (ou só espaços) é rejeitada."""
        with self.assertRaises(RegraNegocioError):
            servicos.cadastrar_livro(titulo="Sem Autor", autores=["  ", ""])

    def test_erro_quantidade_menor_que_um(self):
        """Quantidade de exemplares abaixo de 1 é rejeitada."""
        with self.assertRaises(RegraNegocioError):
            servicos.cadastrar_livro(titulo="Zero Exemplares",
                                     autores=["Fulano"],
                                     quantidade_exemplares=0)


class TestAdicionarExemplares(ServicosTestCase):
    """Acréscimo de exemplares a um livro já cadastrado."""

    def test_continua_numeracao_do_tombo(self):
        """Novos exemplares continuam a sequência de tombos existente."""
        res = self.criar_livro(exemplares=2)
        novos = servicos.adicionar_exemplares(res["livro_id"], 2)
        self.assertEqual(len(novos), 2)
        detalhes = servicos.detalhes_livro(res["livro_id"])
        tombos = [ex["numero_tombo"] for ex in detalhes["exemplares"]]
        esperados = [f"{res['livro_id']:05d}-{i:03d}" for i in (1, 2, 3, 4)]
        self.assertEqual(tombos, esperados)

    def test_erro_livro_inexistente(self):
        """Adicionar exemplares a livro que não existe falha."""
        with self.assertRaises(RegraNegocioError):
            servicos.adicionar_exemplares(9999, 1)


class TestListarLivros(ServicosTestCase):
    """Busca no acervo por título, autor e categoria."""

    def setUp(self):
        super().setUp()
        self.criar_livro(titulo="Dom Casmurro",
                         autores=["Machado de Assis"],
                         categoria="Romance")
        self.criar_livro(titulo="Python para Todos",
                         autores=["Guido Docente"],
                         categoria="Informatica")

    def test_busca_por_titulo(self):
        rows = servicos.listar_livros("Casmurro")
        self.assertEqual([r["titulo"] for r in rows], ["Dom Casmurro"])

    def test_busca_por_autor(self):
        rows = servicos.listar_livros("Machado")
        self.assertEqual([r["titulo"] for r in rows], ["Dom Casmurro"])

    def test_busca_por_categoria(self):
        rows = servicos.listar_livros("Informatica")
        self.assertEqual([r["titulo"] for r in rows], ["Python para Todos"])

    def test_apenas_disponiveis_filtra_emprestados(self):
        """Livro com o único exemplar emprestado some do filtro."""
        u = self.criar_usuario()
        detalhes = servicos.listar_livros("Casmurro")[0]
        info = servicos.detalhes_livro(detalhes["id"])
        self.emprestar(info["exemplares"][0]["codigo_barras"], u["matricula"])
        titulos = [r["titulo"]
                   for r in servicos.listar_livros(apenas_disponiveis=True)]
        self.assertNotIn("Dom Casmurro", titulos)
        self.assertIn("Python para Todos", titulos)


class TestDetalhesLivro(ServicosTestCase):
    """Ficha completa do livro."""

    def test_campos_completos(self):
        res = self.criar_livro(
            titulo="Grande Sertão: Veredas",
            autores=["Guimarães Rosa"],
            isbn="9788520923252", editora="Nova Fronteira",
            categoria="Romance", ano=1956, edicao="1ª",
            sinopse="A travessia de Riobaldo.", exemplares=2,
            localizacao="Estante A1",
        )
        livro = servicos.detalhes_livro(res["livro_id"])
        self.assertEqual(livro["titulo"], "Grande Sertão: Veredas")
        self.assertEqual(livro["isbn"], "9788520923252")
        self.assertEqual(livro["editora_nome"], "Nova Fronteira")
        self.assertEqual(livro["categoria_nome"], "Romance")
        self.assertEqual(livro["ano_publicacao"], 1956)
        self.assertEqual(livro["edicao"], "1ª")
        self.assertEqual(livro["sinopse"], "A travessia de Riobaldo.")
        self.assertEqual(livro["autores"], ["Guimarães Rosa"])
        self.assertEqual(len(livro["exemplares"]), 2)
        self.assertEqual(livro["exemplares"][0]["status"], "DISPONIVEL")
        self.assertEqual(livro["exemplares"][0]["localizacao"], "Estante A1")

    def test_none_para_id_inexistente(self):
        self.assertIsNone(servicos.detalhes_livro(9999))


class TestExcluirLivro(ServicosTestCase):
    """Exclusão lógica do livro."""

    def test_exclusao_logica(self):
        """Livro excluído some da listagem e exemplares viram BAIXADO."""
        res = self.criar_livro(exemplares=2)
        servicos.excluir_livro(res["livro_id"])
        self.assertEqual(servicos.listar_livros(), [])
        self.assertIsNone(servicos.detalhes_livro(res["livro_id"]))
        for ex_id, _codigo in res["exemplares"]:
            self.assertEqual(self.status_exemplar(ex_id), "BAIXADO")

    def test_erro_com_emprestimo_em_aberto(self):
        res = self.criar_livro()
        u = self.criar_usuario()
        self.emprestar(res["exemplares"][0][1], u["matricula"])
        with self.assertRaises(RegraNegocioError):
            servicos.excluir_livro(res["livro_id"])


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------
class TestUsuarios(ServicosTestCase):
    """Cadastro, edição, exclusão e status de usuários."""

    def test_erro_matricula_duplicada(self):
        self.criar_usuario(matricula="2024001")
        with self.assertRaises(RegraNegocioError):
            self.criar_usuario(matricula="2024001", nome="Outro Nome")

    def test_erro_perfil_invalido(self):
        with self.assertRaises(RegraNegocioError):
            self.criar_usuario(perfil="MONITOR")

    def test_erro_senha_curta(self):
        with self.assertRaises(RegraNegocioError):
            self.criar_usuario(senha="123")

    def test_atualizar_nao_permite_mudar_o_proprio_perfil(self):
        u = self.criar_usuario(perfil="BIBLIOTECARIO")
        with self.assertRaises(RegraNegocioError):
            servicos.atualizar_usuario(
                u["id"], nome="Nome Novo", perfil="ADMINISTRADOR",
                executor_id=u["id"])
        # Mudar outros dados mantendo o perfil continua permitido
        servicos.atualizar_usuario(
            u["id"], nome="Nome Novo", perfil="BIBLIOTECARIO",
            executor_id=u["id"])
        self.assertEqual(servicos.obter_usuario(u["id"])["nome"], "Nome Novo")

    def test_excluir_erro_com_historico_de_emprestimo(self):
        """Mesmo com o empréstimo já devolvido, o histórico impede a exclusão."""
        u = self.criar_usuario()
        livro = self.criar_livro()
        codigo = livro["exemplares"][0][1]
        self.emprestar(codigo, u["matricula"])
        servicos.realizar_devolucao(codigo_exemplar=codigo)
        with self.assertRaises(RegraNegocioError):
            servicos.excluir_usuario(u["id"])

    def test_excluir_sucesso_sem_historico(self):
        u = self.criar_usuario()
        servicos.excluir_usuario(u["id"])
        with self.assertRaises(RegraNegocioError):
            servicos.obter_usuario(u["id"])

    def test_excluir_erro_a_si_mesmo(self):
        u = self.criar_usuario()
        with self.assertRaises(RegraNegocioError):
            servicos.excluir_usuario(u["id"], executor_id=u["id"])

    def test_alternar_status_usuario(self):
        u = self.criar_usuario()
        servicos.alternar_status_usuario(u["id"], False)
        self.assertEqual(servicos.obter_usuario(u["id"])["ativo"], 0)
        servicos.alternar_status_usuario(u["id"], True)
        self.assertEqual(servicos.obter_usuario(u["id"])["ativo"], 1)

    def test_alternar_status_audita_o_executor(self):
        """A auditoria registra QUEM desativou; o afetado vai no detalhe."""
        from sigbef.database import db_cursor
        admin = self.criar_usuario(matricula="chefe", perfil="ADMINISTRADOR")
        alvo = self.criar_usuario(matricula="alvo1")
        servicos.alternar_status_usuario(alvo["id"], False,
                                         executor_id=admin["id"])
        with db_cursor() as cur:
            cur.execute("SELECT usuario_id, detalhes FROM auditoria "
                        "WHERE acao = 'STATUS_USUARIO'")
            row = cur.fetchone()
        self.assertEqual(row["usuario_id"], admin["id"])
        self.assertIn(f"alvo={alvo['id']}", row["detalhes"])


# ---------------------------------------------------------------------------
# Empréstimos
# ---------------------------------------------------------------------------
class TestEmprestimo(ServicosTestCase):
    """Regras de empréstimo (prazos, limites e bloqueios)."""

    def test_sucesso_aluno_prazo_7_dias(self):
        u = self.criar_usuario(perfil="ALUNO")
        livro = self.criar_livro()
        ex_id, codigo = livro["exemplares"][0]
        res = self.emprestar(codigo, u["matricula"])
        self.assertEqual(self.status_exemplar(ex_id), "EMPRESTADO")
        esperada = (date.today() + timedelta(days=7)).isoformat()
        self.assertEqual(res["data_prevista"], esperada)
        self.assertEqual(res["prazo_dias"], 7)

    def test_sucesso_professor_prazo_14_dias(self):
        u = self.criar_usuario(matricula="prof1", perfil="PROFESSOR")
        livro = self.criar_livro()
        res = self.emprestar(livro["exemplares"][0][1], u["matricula"])
        esperada = (date.today() + timedelta(days=14)).isoformat()
        self.assertEqual(res["data_prevista"], esperada)

    def test_erro_usuario_inativo(self):
        u = self.criar_usuario()
        servicos.alternar_status_usuario(u["id"], False)
        livro = self.criar_livro()
        with self.assertRaises(RegraNegocioError):
            self.emprestar(livro["exemplares"][0][1], u["matricula"])

    def test_erro_exemplar_ja_emprestado(self):
        u1 = self.criar_usuario(matricula="aluno1")
        u2 = self.criar_usuario(matricula="aluno2")
        livro = self.criar_livro()
        codigo = livro["exemplares"][0][1]
        self.emprestar(codigo, u1["matricula"])
        with self.assertRaises(RegraNegocioError):
            self.emprestar(codigo, u2["matricula"])

    def test_limite_de_emprestimos_simultaneos_aluno(self):
        """ALUNO pode 3 empréstimos; o 4º é bloqueado."""
        u = self.criar_usuario(perfil="ALUNO")
        livro = self.criar_livro(exemplares=4)
        codigos = [c for _id, c in livro["exemplares"]]
        for codigo in codigos[:3]:
            self.emprestar(codigo, u["matricula"])
        with self.assertRaises(RegraNegocioError) as ctx:
            self.emprestar(codigos[3], u["matricula"])
        self.assertIn("Limite", str(ctx.exception))

    def test_bloqueio_por_atraso(self):
        u = self.criar_usuario()
        livro = self.criar_livro(exemplares=2)
        res = self.emprestar(livro["exemplares"][0][1], u["matricula"])
        self.atrasar_emprestimo(res["id"])
        with self.assertRaises(RegraNegocioError) as ctx:
            self.emprestar(livro["exemplares"][1][1], u["matricula"])
        self.assertIn("atraso", str(ctx.exception))

    def test_bloqueio_por_multa_em_aberto(self):
        u = self.criar_usuario()
        livro = self.criar_livro(exemplares=2)
        codigo = livro["exemplares"][0][1]
        res = self.emprestar(codigo, u["matricula"])
        self.atrasar_emprestimo(res["id"], dias=2)
        dev = servicos.realizar_devolucao(codigo_exemplar=codigo)
        self.assertGreater(dev["multa"], 0)
        with self.assertRaises(RegraNegocioError) as ctx:
            self.emprestar(livro["exemplares"][1][1], u["matricula"])
        self.assertIn("multas", str(ctx.exception))

    def test_trava_atomica_exemplar_marcado_emprestado_no_banco(self):
        """Exemplar já EMPRESTADO direto no banco não pode ser emprestado."""
        u = self.criar_usuario()
        livro = self.criar_livro()
        ex_id, codigo = livro["exemplares"][0]
        with db_cursor() as cur:
            cur.execute(
                "UPDATE exemplar SET status = 'EMPRESTADO' WHERE id = ?",
                (ex_id,))
        with self.assertRaises(RegraNegocioError):
            self.emprestar(codigo, u["matricula"])
        # Nenhum empréstimo pode ter sido registrado
        self.assertEqual(servicos.listar_emprestimos_em_aberto(), [])


class TestDevolucao(ServicosTestCase):
    """Devolução e cálculo de multa."""

    def test_sem_atraso_multa_zero(self):
        u = self.criar_usuario()
        livro = self.criar_livro()
        ex_id, codigo = livro["exemplares"][0]
        self.emprestar(codigo, u["matricula"])
        res = servicos.realizar_devolucao(codigo_exemplar=codigo)
        self.assertEqual(res["dias_atraso"], 0)
        self.assertEqual(res["multa"], 0.0)
        self.assertEqual(self.status_exemplar(ex_id), "DISPONIVEL")

    def test_com_atraso_multa_por_dia(self):
        u = self.criar_usuario()
        livro = self.criar_livro()
        codigo = livro["exemplares"][0][1]
        emp = self.emprestar(codigo, u["matricula"])
        self.atrasar_emprestimo(emp["id"], dias=3)
        multa_dia = float(get_config("MULTA_POR_DIA"))
        res = servicos.realizar_devolucao(codigo_exemplar=codigo)
        self.assertEqual(res["dias_atraso"], 3)
        self.assertEqual(res["multa"], round(3 * multa_dia, 2))

    def test_multa_respeita_teto(self):
        u = self.criar_usuario()
        livro = self.criar_livro()
        codigo = livro["exemplares"][0][1]
        emp = self.emprestar(codigo, u["matricula"])
        self.atrasar_emprestimo(emp["id"], dias=100)  # 100 * 1,50 > teto
        teto = float(get_config("MULTA_TETO"))
        res = servicos.realizar_devolucao(codigo_exemplar=codigo)
        self.assertEqual(res["multa"], teto)

    def test_erro_devolver_exemplar_nao_emprestado(self):
        livro = self.criar_livro()
        with self.assertRaises(RegraNegocioError):
            servicos.realizar_devolucao(
                codigo_exemplar=livro["exemplares"][0][1])


class TestRenovacao(ServicosTestCase):
    """Renovação de empréstimo."""

    def test_nova_data_prevista_hoje_mais_prazo(self):
        u = self.criar_usuario(perfil="ALUNO")
        livro = self.criar_livro()
        emp = self.emprestar(livro["exemplares"][0][1], u["matricula"])
        # Move a data para trás para garantir que a renovação recalcula
        self.atrasar_emprestimo(emp["id"], dias=1)
        res = servicos.renovar_emprestimo(emp["id"])
        esperada = (date.today() + timedelta(days=7)).isoformat()
        self.assertEqual(res["data_prevista"], esperada)


class TestQuitarMulta(ServicosTestCase):
    """Quitação de multa."""

    def test_quitar_zera_multa(self):
        u = self.criar_usuario()
        livro = self.criar_livro()
        codigo = livro["exemplares"][0][1]
        emp = self.emprestar(codigo, u["matricula"])
        self.atrasar_emprestimo(emp["id"], dias=2)
        servicos.realizar_devolucao(codigo_exemplar=codigo)
        self.assertGreater(servicos.status_usuario(u["id"]).multas_em_aberto, 0)
        servicos.quitar_multa(emp["id"])
        st = servicos.status_usuario(u["id"])
        self.assertEqual(st.multas_em_aberto, 0.0)
        self.assertTrue(st.pode_pegar)


class TestStatusUsuario(ServicosTestCase):
    """Semáforo do usuário nos quatro cenários."""

    def test_cenario_ok(self):
        u = self.criar_usuario()
        st = servicos.status_usuario(u["id"])
        self.assertTrue(st.pode_pegar)
        self.assertEqual(st.em_aberto, 0)
        self.assertIn("OK", st.motivo)

    def test_cenario_limite_atingido(self):
        u = self.criar_usuario(perfil="ALUNO")
        livro = self.criar_livro(exemplares=3)
        for _id, codigo in livro["exemplares"]:
            self.emprestar(codigo, u["matricula"])
        st = servicos.status_usuario(u["id"])
        self.assertFalse(st.pode_pegar)
        self.assertEqual(st.em_aberto, 3)
        self.assertIn("Limite", st.motivo)

    def test_cenario_multa_em_aberto(self):
        u = self.criar_usuario()
        livro = self.criar_livro()
        codigo = livro["exemplares"][0][1]
        emp = self.emprestar(codigo, u["matricula"])
        self.atrasar_emprestimo(emp["id"], dias=2)
        servicos.realizar_devolucao(codigo_exemplar=codigo)
        st = servicos.status_usuario(u["id"])
        self.assertFalse(st.pode_pegar)
        self.assertGreater(st.multas_em_aberto, 0)
        self.assertIn("multas", st.motivo)

    def test_cenario_atraso(self):
        u = self.criar_usuario()
        livro = self.criar_livro()
        emp = self.emprestar(livro["exemplares"][0][1], u["matricula"])
        self.atrasar_emprestimo(emp["id"])
        st = servicos.status_usuario(u["id"])
        self.assertFalse(st.pode_pegar)
        self.assertIn("atraso", st.motivo)


# ---------------------------------------------------------------------------
# Importação de acervo via CSV
# ---------------------------------------------------------------------------
class TestImportacaoCSV(ServicosTestCase):
    """Importação em massa de acervo."""

    def test_separador_ponto_e_virgula(self):
        caminho = self.csv_temporario(
            "titulo;autores;quantidade\n"
            "Dom Casmurro;Machado de Assis;2\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 1)
        self.assertEqual(res["exemplares"], 2)
        self.assertEqual(res["erros"], [])
        self.assertEqual(res["pulados"], [])

    def test_separador_virgula(self):
        caminho = self.csv_temporario(
            "titulo,autores,quantidade\n"
            "Iracema,Jose de Alencar,1\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 1)
        self.assertEqual(res["exemplares"], 1)

    def test_encoding_utf8_sig(self):
        caminho = self.csv_temporario(
            "titulo;autores\nAção e Reação;José do Ó\n",
            encoding="utf-8-sig")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 1)
        rows = servicos.listar_livros("Ação e Reação")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["autores"], "José do Ó")

    def test_encoding_cp1252(self):
        """Bytes com acento em Windows-1252 (inválidos em UTF-8)."""
        conteudo = ("titulo;autores\n"
                    "Coração Selvagem;João Câmara\n").encode("cp1252")
        caminho = self.csv_temporario(conteudo)
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 1)
        rows = servicos.listar_livros("Coração Selvagem")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["autores"], "João Câmara")

    def test_erro_sem_coluna_titulo(self):
        caminho = self.csv_temporario(
            "autores;isbn\nMachado de Assis;123\n")
        with self.assertRaises(RegraNegocioError):
            servicos.importar_acervo_csv(caminho)

    def test_linha_sem_autores_vai_para_erros(self):
        caminho = self.csv_temporario(
            "titulo;autores\nLivro Sem Autor;\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 0)
        self.assertEqual(len(res["erros"]), 1)
        self.assertEqual(res["erros"][0][0], 2)  # linha 2 do arquivo
        self.assertIn("autores", res["erros"][0][1])

    def test_ano_invalido_vai_para_erros(self):
        caminho = self.csv_temporario(
            "titulo;autores;ano\n"
            "Livro Futurista;Fulano;3050\n"
            "Livro Sem Numero;Beltrano;abc\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 0)
        self.assertEqual(len(res["erros"]), 2)
        self.assertTrue(all("ano" in motivo for _n, motivo in res["erros"]))

    def test_isbn_ja_no_banco_vai_para_pulados(self):
        self.criar_livro(titulo="Já Cadastrado", isbn="9780000000001")
        caminho = self.csv_temporario(
            "titulo;autores;isbn\n"
            "Duplicado;Fulano;9780000000001\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 0)
        self.assertEqual(len(res["pulados"]), 1)
        self.assertIn("9780000000001", res["pulados"][0][1])

    def test_isbn_repetido_dentro_do_arquivo_vai_para_pulados(self):
        caminho = self.csv_temporario(
            "titulo;autores;isbn\n"
            "Primeiro;Fulano;9780000000002\n"
            "Repetido;Beltrano;9780000000002\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 1)
        self.assertEqual(len(res["pulados"]), 1)
        self.assertEqual(res["pulados"][0][0], 3)  # linha 3 do arquivo

    def test_quantidade_de_exemplares_respeitada(self):
        caminho = self.csv_temporario(
            "titulo;autores;quantidade\n"
            "Cinco Copias;Fulano;5\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["exemplares"], 5)
        livro = servicos.listar_livros("Cinco Copias")[0]
        self.assertEqual(livro["total_exemplares"], 5)

    def test_gerar_modelo_csv(self):
        pasta = tempfile.mkdtemp(prefix="sigbef-modelo-")
        self.addCleanup(shutil.rmtree, pasta, ignore_errors=True)
        destino = os.path.join(pasta, "modelo.csv")
        servicos.gerar_modelo_csv(destino)
        texto = Path(destino).read_text(encoding="utf-8-sig")
        self.assertTrue(texto.startswith("titulo;autores;"))
        # O modelo gerado precisa ser importável de volta
        res = servicos.importar_acervo_csv(destino)
        self.assertEqual(res["livros"], 2)
        self.assertEqual(res["erros"], [])


# ---------------------------------------------------------------------------
# Listagens de exemplares
# ---------------------------------------------------------------------------
class TestListagensExemplares(ServicosTestCase):
    """Listas para etiquetas e para seleção de empréstimo."""

    def setUp(self):
        super().setUp()
        self.livro_a = self.criar_livro(titulo="Dom Casmurro",
                                        autores=["Machado de Assis"],
                                        exemplares=2)
        self.livro_b = self.criar_livro(titulo="Python para Todos",
                                        autores=["Guido Docente"])

    def test_etiquetas_filtro_por_termo(self):
        todos = servicos.listar_exemplares_para_etiquetas()
        self.assertEqual(len(todos), 3)
        filtrados = servicos.listar_exemplares_para_etiquetas("Casmurro")
        self.assertEqual(len(filtrados), 2)
        self.assertTrue(all(r["titulo"] == "Dom Casmurro" for r in filtrados))

    def test_disponiveis_filtro_por_termo_e_status(self):
        u = self.criar_usuario()
        self.emprestar(self.livro_a["exemplares"][0][1], u["matricula"])
        disponiveis = servicos.listar_exemplares_disponiveis()
        self.assertEqual(len(disponiveis), 2)  # 1 de cada livro
        filtrados = servicos.listar_exemplares_disponiveis("Python")
        self.assertEqual(len(filtrados), 1)
        self.assertEqual(filtrados[0]["titulo"], "Python para Todos")


# ---------------------------------------------------------------------------
# Estatísticas e relatórios
# ---------------------------------------------------------------------------
class TestRelatorios(ServicosTestCase):
    """Painel de estatísticas e circulação."""

    def test_estatisticas_apos_operacoes_conhecidas(self):
        u = self.criar_usuario()
        livro_a = self.criar_livro(titulo="Livro A", exemplares=2)
        self.criar_livro(titulo="Livro B")
        emp = self.emprestar(livro_a["exemplares"][0][1], u["matricula"])
        self.atrasar_emprestimo(emp["id"])
        est = servicos.estatisticas()
        self.assertEqual(est["livros"], 2)
        self.assertEqual(est["exemplares"], 3)
        self.assertEqual(est["disponiveis"], 2)
        self.assertEqual(est["emp_abertos"], 1)
        self.assertEqual(est["atrasados"], 1)
        self.assertEqual(est["usuarios"], 1)

    def test_relatorio_circulacao(self):
        u = self.criar_usuario(perfil="PROFESSOR")  # limite maior
        livro_a = self.criar_livro(titulo="Mais Emprestado")
        livro_b = self.criar_livro(titulo="Menos Emprestado")
        codigo_a = livro_a["exemplares"][0][1]
        # Livro A circula 2x; livro B, 1x
        self.emprestar(codigo_a, u["matricula"])
        servicos.realizar_devolucao(codigo_exemplar=codigo_a)
        self.emprestar(codigo_a, u["matricula"])
        self.emprestar(livro_b["exemplares"][0][1], u["matricula"])
        rel = servicos.relatorio_circulacao()
        self.assertEqual(rel[0], {"titulo": "Mais Emprestado", "emprestimos": 2})
        self.assertEqual(rel[1], {"titulo": "Menos Emprestado", "emprestimos": 1})


if __name__ == "__main__":
    unittest.main()
