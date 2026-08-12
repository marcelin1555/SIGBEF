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

    def test_filtro_por_categoria_exato(self):
        rows = servicos.listar_livros(categoria="Romance")
        self.assertEqual([r["titulo"] for r in rows], ["Dom Casmurro"])

    def test_filtro_por_autor_exato(self):
        rows = servicos.listar_livros(autor="Guido Docente")
        self.assertEqual([r["titulo"] for r in rows], ["Python para Todos"])

    def test_texto_mais_categoria_combinados(self):
        self.criar_livro(titulo="Outro Romance", autores=["Autor X"],
                         categoria="Romance")
        rows = servicos.listar_livros("Casmurro", categoria="Romance")
        self.assertEqual([r["titulo"] for r in rows], ["Dom Casmurro"])

    def test_sem_filtro_devolve_tudo(self):
        rows = servicos.listar_livros()
        self.assertEqual(len(rows), 2)

    def test_listar_categorias_e_autores(self):
        self.assertIn("Romance", servicos.listar_categorias())
        self.assertIn("Informatica", servicos.listar_categorias())
        self.assertIn("Machado de Assis", servicos.listar_autores())


class TestPaginacaoDoAcervo(ServicosTestCase):
    """Listagem por blocos.

    Existe porque a tela e a API deixaram de trazer o acervo inteiro: com
    250 mil livros, cada linha carrega três subconsultas, e devolver
    tudo travava a janela por segundos e virava um JSON de dezenas de MB.
    """

    def setUp(self):
        super().setUp()
        # Títulos repetidos de propósito: é o caso que quebra paginação
        # ordenada só por título, porque a ordem entre iguais não é
        # estável e a mesma linha aparece em duas páginas (ou em nenhuma).
        for i in range(10):
            self.criar_livro(titulo="Livro Repetido",
                             autores=[f"Autor {i}"], categoria="Romance")
        for i in range(5):
            self.criar_livro(titulo=f"Único {i}", autores=["Solo"],
                             categoria="Poesia")

    def test_sem_limite_continua_trazendo_tudo(self):
        """Quem exporta CSV precisa mesmo do acervo inteiro."""
        self.assertEqual(len(servicos.listar_livros()), 15)

    def test_limite_corta_o_resultado(self):
        self.assertEqual(len(servicos.listar_livros(limite=4)), 4)

    def test_offset_anda_para_a_frente(self):
        p1 = servicos.listar_livros(limite=5, offset=0)
        p2 = servicos.listar_livros(limite=5, offset=5)
        self.assertEqual(len(p1), 5)
        self.assertEqual(len(p2), 5)
        self.assertFalse({r["id"] for r in p1} & {r["id"] for r in p2})

    def test_paginar_o_acervo_todo_nao_perde_nem_repete(self):
        """Com títulos iguais, a ordenação precisa ser estável."""
        vistos = []
        offset = 0
        while True:
            bloco = servicos.listar_livros(limite=4, offset=offset)
            if not bloco:
                break
            vistos.extend(r["id"] for r in bloco)
            offset += 4
        self.assertEqual(len(vistos), 15)
        self.assertEqual(len(set(vistos)), 15, "algum livro veio duas vezes")

    def test_pagina_alem_do_fim_vem_vazia(self):
        self.assertEqual(servicos.listar_livros(limite=5, offset=999), [])

    def test_contar_bate_com_o_tamanho_da_lista_sem_limite(self):
        for termo in ("", "Repetido", "Único", "nada disso"):
            with self.subTest(termo=termo):
                self.assertEqual(servicos.contar_livros(termo),
                                 len(servicos.listar_livros(termo)))

    def test_contar_respeita_categoria(self):
        self.assertEqual(servicos.contar_livros(categoria="Poesia"), 5)
        self.assertEqual(servicos.contar_livros(categoria="Romance"), 10)

    def test_contar_ignora_o_limite(self):
        """O total é do acervo, não da página; é o que a tela mostra."""
        self.assertEqual(servicos.contar_livros("Repetido"), 10)
        self.assertEqual(len(servicos.listar_livros("Repetido", limite=3)), 3)

    def test_apenas_disponiveis_filtra_antes_de_cortar(self):
        """O filtro migrou para o SQL justamente por causa do limite.

        Filtrando em Python depois do corte, uma página de 5 poderia
        chegar com 2 livros só porque os outros 3 estavam emprestados.
        """
        livro = self.criar_livro(titulo="Zzz Emprestado",
                                  autores=["Autor"], categoria="Romance")
        self.criar_usuario(matricula="p1")
        servicos.realizar_emprestimo(
            codigo_exemplar=livro["exemplares"][0][1],
            matricula_usuario="p1")

        total_disp = servicos.contar_livros(apenas_disponiveis=True)
        self.assertEqual(total_disp, 15)          # o emprestado saiu

        pagina = servicos.listar_livros(apenas_disponiveis=True, limite=15)
        self.assertEqual(len(pagina), 15)
        self.assertNotIn("Zzz Emprestado", [r["titulo"] for r in pagina])


class TestBaixaDeExemplar(ServicosTestCase):
    """Tirar um exemplar do acervo sem levar o título junto.

    Antes só existia `excluir_livro`, que baixa o livro inteiro: um
    exemplar rasgado obrigava a escolher entre sumir com o título todo
    ou deixar o sistema dizendo que ele está na estante.
    """

    def setUp(self):
        super().setUp()
        self.livro = self.criar_livro(titulo="Frágil", exemplares=3)
        self.criar_usuario(matricula="a1", nome="Ana")
        self.cod = [e[1] for e in self.livro["exemplares"]]

    def test_exemplar_sai_do_acervo_sem_levar_o_livro(self):
        servicos.baixar_exemplar(self.cod[0], "DANIFICADO")
        achados = servicos.listar_livros("Frágil")
        self.assertEqual(len(achados), 1, "o livro sumiu junto")
        self.assertEqual(achados[0]["total_exemplares"], 2)
        self.assertEqual(achados[0]["disponiveis"], 2)

    def test_exemplar_baixado_nao_pode_mais_ser_emprestado(self):
        servicos.baixar_exemplar(self.cod[0], "DESCARTADO")
        with self.assertRaises(RegraNegocioError):
            servicos.realizar_emprestimo(codigo_exemplar=self.cod[0],
                                          matricula_usuario="a1")

    def test_aluno_perdeu_o_livro_encerra_o_emprestimo(self):
        """O caso mais comum, e o que justifica permitir baixa de
        exemplar emprestado: exigir devolução seria exigir o impossível."""
        servicos.realizar_emprestimo(codigo_exemplar=self.cod[0],
                                      matricula_usuario="a1")
        r = servicos.baixar_exemplar(self.cod[0], "EXTRAVIADO")

        self.assertTrue(r["estava_emprestado"])
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM emprestimo "
                        "WHERE data_devolucao IS NULL")
            self.assertEqual(cur.fetchone()[0], 0)

    def test_perda_de_livro_atrasado_lanca_multa(self):
        emp = servicos.realizar_emprestimo(codigo_exemplar=self.cod[0],
                                            matricula_usuario="a1")
        with db_cursor() as cur:
            cur.execute("UPDATE emprestimo SET data_prevista = ? WHERE id = ?",
                        ((date.today() - timedelta(days=10)).isoformat(),
                         emp["id"]))
        r = servicos.baixar_exemplar(self.cod[0], "EXTRAVIADO")
        self.assertGreater(r["multa"], 0)

    def test_motivo_invalido_e_recusado(self):
        with self.assertRaises(RegraNegocioError):
            servicos.baixar_exemplar(self.cod[0], "SUMIU")

    def test_motivo_aceita_minusculas(self):
        """A interface manda maiúsculo, mas a API não deve ser chata."""
        r = servicos.baixar_exemplar(self.cod[0], "danificado")
        self.assertEqual(r["motivo"], "DANIFICADO")

    def test_baixar_duas_vezes_e_recusado(self):
        servicos.baixar_exemplar(self.cod[0], "DOADO")
        with self.assertRaises(RegraNegocioError):
            servicos.baixar_exemplar(self.cod[0], "DOADO")

    def test_exemplar_inexistente_e_recusado(self):
        with self.assertRaises(RegraNegocioError):
            servicos.baixar_exemplar("NAO-EXISTE", "DOADO")

    def test_motivo_e_data_ficam_registrados(self):
        """Meses depois, é o motivo que explica por que o livro sumiu."""
        servicos.baixar_exemplar(self.cod[0], "EXTRAVIADO")
        det = servicos.detalhes_livro(self.livro["livro_id"])
        baixado = [e for e in det["exemplares"] if e["status"] == "BAIXADO"][0]
        self.assertEqual(baixado["motivo_baixa"], "EXTRAVIADO")
        self.assertEqual(baixado["data_baixa"], date.today().isoformat())

    def test_fica_na_auditoria(self):
        servicos.baixar_exemplar(self.cod[0], "DANIFICADO")
        with db_cursor() as cur:
            cur.execute("SELECT detalhes FROM auditoria "
                        "WHERE acao = 'BAIXA_EXEMPLAR'")
            linha = cur.fetchone()
        self.assertIsNotNone(linha)
        self.assertIn("DANIFICADO", linha[0])

    def test_historico_de_emprestimo_do_exemplar_e_preservado(self):
        """O livro saiu do acervo, mas quem o leu continua registrado."""
        servicos.realizar_emprestimo(codigo_exemplar=self.cod[0],
                                      matricula_usuario="a1")
        servicos.realizar_devolucao(codigo_exemplar=self.cod[0])
        servicos.baixar_exemplar(self.cod[0], "DESCARTADO")
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM emprestimo")
            self.assertEqual(cur.fetchone()[0], 1)


class TestDevolucaoEmLote(ServicosTestCase):
    """A devolução em lote chama `realizar_devolucao` uma vez por leitura.

    O que se garante aqui é o contrato de que a tela depende: um erro no
    meio da pilha não pode derrubar as devoluções seguintes, e o retorno
    precisa dizer de quem era o livro — numa pilha de trinta, a
    bibliotecária não tem o aluno na frente.
    """

    def setUp(self):
        super().setUp()
        self.livro = self.criar_livro(titulo="Turma Toda", exemplares=4)
        self.criar_usuario(matricula="a1", nome="Ana")
        self.criar_usuario(matricula="a2", nome="Bruno")
        self.cod = [e[1] for e in self.livro["exemplares"]]

    def test_devolucao_diz_de_quem_era_o_livro(self):
        servicos.realizar_emprestimo(codigo_exemplar=self.cod[0],
                                      matricula_usuario="a1")
        r = servicos.realizar_devolucao(codigo_exemplar=self.cod[0])
        self.assertEqual(r["usuario"], "Ana")
        self.assertEqual(r["matricula"], "a1")

    def test_erro_no_meio_nao_impede_as_seguintes(self):
        for cod, mat in [(self.cod[0], "a1"), (self.cod[1], "a2")]:
            servicos.realizar_emprestimo(codigo_exemplar=cod,
                                          matricula_usuario=mat)

        devolvidos, recusados = [], 0
        for codigo in [self.cod[0], "CODIGO-INEXISTENTE",
                       self.cod[2], self.cod[1]]:
            try:
                devolvidos.append(
                    servicos.realizar_devolucao(codigo_exemplar=codigo))
            except RegraNegocioError:
                recusados += 1

        self.assertEqual(len(devolvidos), 2)
        self.assertEqual(recusados, 2)   # inexistente e não emprestado

    def test_multas_do_lote_somam(self):
        emp = servicos.realizar_emprestimo(codigo_exemplar=self.cod[0],
                                            matricula_usuario="a1")
        servicos.realizar_emprestimo(codigo_exemplar=self.cod[1],
                                      matricula_usuario="a2")
        with db_cursor() as cur:
            cur.execute("UPDATE emprestimo SET data_prevista = ? WHERE id = ?",
                        ((date.today() - timedelta(days=4)).isoformat(),
                         emp["id"]))

        total = sum((servicos.realizar_devolucao(codigo_exemplar=c)["multa"]
                     or 0) for c in self.cod[:2])
        self.assertGreater(total, 0)

    def test_livro_com_fila_avisa_para_separar(self):
        """Na pilha do fim de ano, é o que não pode voltar para a estante."""
        from sigbef import reservas
        for i in range(4):
            servicos.realizar_emprestimo(codigo_exemplar=self.cod[i],
                                          matricula_usuario="a1"
                                          if i < 3 else "a2")
        u = servicos.localizar_usuario("a2")
        reservas.criar_reserva(self.livro["livro_id"], u["id"])

        r = servicos.realizar_devolucao(codigo_exemplar=self.cod[0])
        self.assertEqual(r["reservado_para"], "Bruno")


class TestRelatoriosPorPeriodo(ServicosTestCase):
    """Recorte de datas nos relatórios.

    Existe para a pergunta que a direção faz no fim do ano e que o
    sistema não sabia responder: quanto a biblioteca circulou entre tais
    datas.
    """

    def setUp(self):
        super().setUp()
        self.livro = self.criar_livro(titulo="Circulante", exemplares=4)
        self.criar_usuario(matricula="a1", nome="Ana", turma="3A")
        self.cod = [e[1] for e in self.livro["exemplares"]]

    def emprestar_em(self, codigo, quando: date, devolver=True):
        """Empréstimo com data forjada, para montar o histórico."""
        emp = servicos.realizar_emprestimo(codigo_exemplar=codigo,
                                            matricula_usuario="a1")
        with db_cursor() as cur:
            cur.execute("UPDATE emprestimo SET data_emprestimo = ? "
                        "WHERE id = ?", (quando.isoformat(), emp["id"]))
        if devolver:
            servicos.realizar_devolucao(codigo_exemplar=codigo)
            with db_cursor() as cur:
                cur.execute("UPDATE emprestimo SET data_devolucao = ? "
                            "WHERE id = ?", (quando.isoformat(), emp["id"]))
        return emp

    def test_sem_periodo_conta_tudo(self):
        self.emprestar_em(self.cod[0], date.today() - timedelta(days=400))
        self.emprestar_em(self.cod[1], date.today())
        self.assertEqual(servicos.relatorio_movimentacao()["emprestimos"], 2)

    def test_periodo_recorta(self):
        self.emprestar_em(self.cod[0], date.today() - timedelta(days=400))
        self.emprestar_em(self.cod[1], date.today())
        r = servicos.relatorio_movimentacao(
            (date.today() - timedelta(days=30)).isoformat(),
            date.today().isoformat())
        self.assertEqual(r["emprestimos"], 1)

    def test_bordas_sao_inclusivas(self):
        """Quem pede 01/05 a 31/05 espera o dia 31 dentro da conta."""
        dia = date.today() - timedelta(days=10)
        self.emprestar_em(self.cod[0], dia)
        for inicio, fim in [(dia, dia),
                            (dia, date.today()),
                            (dia - timedelta(days=1), dia)]:
            with self.subTest(inicio=inicio, fim=fim):
                r = servicos.relatorio_movimentacao(inicio.isoformat(),
                                                     fim.isoformat())
                self.assertEqual(r["emprestimos"], 1)

    def test_periodo_invertido_devolve_vazio_sem_quebrar(self):
        self.emprestar_em(self.cod[0], date.today())
        r = servicos.relatorio_movimentacao(
            date.today().isoformat(),
            (date.today() - timedelta(days=30)).isoformat())
        self.assertEqual(r["emprestimos"], 0)

    def test_apenas_data_inicial(self):
        self.emprestar_em(self.cod[0], date.today() - timedelta(days=400))
        self.emprestar_em(self.cod[1], date.today())
        r = servicos.relatorio_movimentacao(
            (date.today() - timedelta(days=7)).isoformat(), None)
        self.assertEqual(r["emprestimos"], 1)

    def test_conta_por_turma(self):
        self.criar_usuario(matricula="a2", nome="Bruno", turma="2B")
        self.emprestar_em(self.cod[0], date.today())
        servicos.realizar_emprestimo(codigo_exemplar=self.cod[1],
                                      matricula_usuario="a2")
        turmas = {t["turma"]: t["total"]
                  for t in servicos.relatorio_movimentacao()["por_turma"]}
        self.assertEqual(turmas, {"3A": 1, "2B": 1})

    def test_circulacao_respeita_o_periodo(self):
        outro = self.criar_livro(titulo="Antigo", exemplares=1)
        self.emprestar_em(outro["exemplares"][0][1],
                          date.today() - timedelta(days=400))
        self.emprestar_em(self.cod[0], date.today())

        recente = servicos.relatorio_circulacao(
            10, (date.today() - timedelta(days=30)).isoformat(),
            date.today().isoformat())
        self.assertEqual([r["titulo"] for r in recente], ["Circulante"])
        self.assertEqual(len(servicos.relatorio_circulacao(10)), 2)

    def test_taxa_de_atraso_do_periodo(self):
        emp = servicos.realizar_emprestimo(codigo_exemplar=self.cod[0],
                                            matricula_usuario="a1")
        with db_cursor() as cur:
            cur.execute("UPDATE emprestimo SET data_prevista = ? WHERE id = ?",
                        ((date.today() - timedelta(days=5)).isoformat(),
                         emp["id"]))
        servicos.realizar_devolucao(codigo_exemplar=self.cod[0])

        r = servicos.relatorio_movimentacao()
        self.assertEqual(r["devolucoes"], 1)
        self.assertEqual(r["com_atraso"], 1)
        self.assertEqual(r["taxa_atraso"], 100.0)
        self.assertGreater(r["multa_total"], 0)

    def test_biblioteca_parada_nao_divide_por_zero(self):
        r = servicos.relatorio_movimentacao()
        self.assertEqual(r["emprestimos"], 0)
        self.assertEqual(r["taxa_atraso"], 0.0)


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

    def test_exclusao_em_lote_um_com_emprestimo_nao_trava_os_outros(self):
        """Como a tela faz: tenta cada um, um erro no meio não impede
        os demais de serem excluídos."""
        livre1 = self.criar_livro(titulo="Livre 1")
        preso = self.criar_livro(titulo="Com empréstimo")
        livre2 = self.criar_livro(titulo="Livre 2")
        u = self.criar_usuario()
        self.emprestar(preso["exemplares"][0][1], u["matricula"])

        excluidos, falhas = 0, []
        for res in (livre1, preso, livre2):
            try:
                servicos.excluir_livro(res["livro_id"])
                excluidos += 1
            except RegraNegocioError as e:
                falhas.append(str(e))

        self.assertEqual(excluidos, 2)
        self.assertEqual(len(falhas), 1)
        self.assertIsNone(servicos.detalhes_livro(livre1["livro_id"]))
        self.assertIsNone(servicos.detalhes_livro(livre2["livro_id"]))
        self.assertIsNotNone(servicos.detalhes_livro(preso["livro_id"]))


class TestEditarLivro(ServicosTestCase):
    """Corrigir os dados de um livro já cadastrado."""

    def test_edita_titulo_categoria_e_persiste(self):
        res = self.criar_livro(titulo="Titulo Errado", categoria="X")
        servicos.editar_livro(
            res["livro_id"], titulo="Título Certo",
            autores=["Autora de Teste"], categoria="Y")
        livro = servicos.detalhes_livro(res["livro_id"])
        self.assertEqual(livro["titulo"], "Título Certo")
        self.assertEqual(livro["categoria_nome"], "Y")

    def test_erro_sem_titulo(self):
        res = self.criar_livro()
        with self.assertRaises(RegraNegocioError):
            servicos.editar_livro(res["livro_id"], titulo="",
                                  autores=["Alguém"])

    def test_erro_sem_autor(self):
        res = self.criar_livro()
        with self.assertRaises(RegraNegocioError):
            servicos.editar_livro(res["livro_id"], titulo="Título",
                                  autores=[])

    def test_troca_de_autores_nao_deixa_duplicata(self):
        """Trocar a lista de autores limpa a associação antiga — não
        soma a nova com a velha."""
        res = self.criar_livro(autores=["Autora A", "Autora B"])
        servicos.editar_livro(res["livro_id"], titulo="Título",
                              autores=["Autora C"])
        livro = servicos.detalhes_livro(res["livro_id"])
        self.assertEqual(livro["autores"], ["Autora C"])

    def test_livro_inexistente(self):
        with self.assertRaises(RegraNegocioError):
            servicos.editar_livro(99999, titulo="Título",
                                  autores=["Alguém"])

    def test_livro_excluido(self):
        res = self.criar_livro()
        servicos.excluir_livro(res["livro_id"])
        with self.assertRaises(RegraNegocioError):
            servicos.editar_livro(res["livro_id"], titulo="Título",
                                  autores=["Alguém"])

    def test_nao_mexe_em_exemplares_nem_quantidade(self):
        res = self.criar_livro(exemplares=3)
        antes = servicos.detalhes_livro(res["livro_id"])["exemplares"]
        servicos.editar_livro(res["livro_id"], titulo="Outro Título",
                              autores=["Autora de Teste"])
        depois = servicos.detalhes_livro(res["livro_id"])["exemplares"]
        self.assertEqual(
            [e["id"] for e in antes], [e["id"] for e in depois])


class TestLocalizacaoExemplar(ServicosTestCase):
    """Mudar um exemplar de prateleira."""

    def localizacoes(self, livro_id):
        return [e.get("localizacao")
                for e in servicos.detalhes_livro(livro_id)["exemplares"]]

    def test_muda_a_prateleira(self):
        res = self.criar_livro(localizacao="Estante A")
        codigo = res["exemplares"][0][1]
        servicos.alterar_localizacao_exemplar(codigo, "Estante B, Prat. 3")
        self.assertEqual(self.localizacoes(res["livro_id"]),
                          ["Estante B, Prat. 3"])

    def test_so_mexe_no_exemplar_escolhido(self):
        """Volumes do mesmo título podem ficar em estantes diferentes."""
        res = self.criar_livro(exemplares=3, localizacao="Estante A")
        servicos.alterar_localizacao_exemplar(res["exemplares"][1][1],
                                              "Estante Z")
        self.assertEqual(sorted(self.localizacoes(res["livro_id"])),
                          ["Estante A", "Estante A", "Estante Z"])

    def test_em_branco_tira_a_localizacao(self):
        res = self.criar_livro(localizacao="Estante A")
        servicos.alterar_localizacao_exemplar(res["exemplares"][0][1], "   ")
        self.assertEqual(self.localizacoes(res["livro_id"]), [None])

    def test_aceita_o_tombo_alem_do_codigo_de_barras(self):
        res = self.criar_livro(localizacao="Estante A")
        tombo = servicos.detalhes_livro(
            res["livro_id"])["exemplares"][0]["numero_tombo"]
        servicos.alterar_localizacao_exemplar(tombo, "Estante C")
        self.assertEqual(self.localizacoes(res["livro_id"]), ["Estante C"])

    def test_exemplar_inexistente(self):
        with self.assertRaises(RegraNegocioError):
            servicos.alterar_localizacao_exemplar("NAO-EXISTE", "Estante A")

    def test_prateleira_nova_vai_para_a_etiqueta(self):
        res = self.criar_livro(titulo="Etiquetado", localizacao="Estante A")
        servicos.alterar_localizacao_exemplar(res["exemplares"][0][1],
                                              "Estante B, Prat. 7")
        etiquetas = servicos.listar_exemplares_para_etiquetas("Etiquetado")
        self.assertEqual(etiquetas[0]["localizacao"], "Estante B, Prat. 7")


class TestTomboDoExemplar(ServicosTestCase):
    """Corrigir o número de tombo escrito no livro físico."""

    def tombos(self, livro_id):
        return [ex["numero_tombo"]
                for ex in servicos.detalhes_livro(livro_id)["exemplares"]]

    def test_corrige_o_tombo(self):
        res = self.criar_livro()
        servicos.alterar_tombo_exemplar(res["exemplares"][0][1], "T-0042")
        self.assertEqual(self.tombos(res["livro_id"]), ["T-0042"])

    def test_so_mexe_no_exemplar_escolhido(self):
        res = self.criar_livro(exemplares=3)
        antes = self.tombos(res["livro_id"])
        servicos.alterar_tombo_exemplar(res["exemplares"][1][1], "T-999")
        depois = self.tombos(res["livro_id"])
        self.assertIn("T-999", depois)
        self.assertEqual(len([t for t in depois if t in antes]), 2)

    def test_em_branco_tira_o_tombo(self):
        res = self.criar_livro()
        servicos.alterar_tombo_exemplar(res["exemplares"][0][1], "   ")
        self.assertEqual(self.tombos(res["livro_id"]), [None])

    def test_recusa_tombo_ja_usado(self):
        """Tombo repetido faz o balcão emprestar o exemplar errado.

        `localizar_exemplar` casa por código de barras OU tombo e devolve
        o primeiro que achar, então a duplicata precisa ser barrada aqui:
        o banco não tem UNIQUE nessa coluna.
        """
        a = self.criar_livro(titulo="Livro A")
        b = self.criar_livro(titulo="Livro B")
        servicos.alterar_tombo_exemplar(a["exemplares"][0][1], "T-100")
        with self.assertRaises(RegraNegocioError):
            servicos.alterar_tombo_exemplar(b["exemplares"][0][1], "T-100")
        # o exemplar de B ficou como estava
        self.assertNotIn("T-100", self.tombos(b["livro_id"]))

    def test_pode_regravar_o_proprio_tombo(self):
        """Salvar sem mudar nada não pode ser lido como duplicata."""
        res = self.criar_livro()
        servicos.alterar_tombo_exemplar(res["exemplares"][0][1], "T-77")
        servicos.alterar_tombo_exemplar(res["exemplares"][0][1], "T-77")
        self.assertEqual(self.tombos(res["livro_id"]), ["T-77"])

    def test_tombo_novo_encontra_o_exemplar_no_balcao(self):
        res = self.criar_livro()
        servicos.alterar_tombo_exemplar(res["exemplares"][0][1], "T-555")
        achado = servicos.localizar_exemplar("T-555")
        self.assertIsNotNone(achado)
        self.assertEqual(achado["codigo_barras"], res["exemplares"][0][1])

    def test_exemplar_inexistente(self):
        with self.assertRaises(RegraNegocioError):
            servicos.alterar_tombo_exemplar("NAO-EXISTE", "T-1")

    def test_tombo_novo_vai_para_a_etiqueta(self):
        res = self.criar_livro(titulo="Tombado")
        servicos.alterar_tombo_exemplar(res["exemplares"][0][1], "T-321")
        etiquetas = servicos.listar_exemplares_para_etiquetas("Tombado")
        self.assertEqual(etiquetas[0]["numero_tombo"], "T-321")


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


class TestRegrasDeRenovacao(ServicosTestCase):
    """Regras que valem quando o aluno renova sozinho, pelo celular.

    No balcão a bibliotecária continua podendo renovar em qualquer caso
    — ela tem o contexto que o sistema não tem. Pelo app, não há ninguém
    para julgar, então `validar_regras=True` faz as regras valerem.
    """

    def _emprestimo(self, perfil="ALUNO"):
        u = self.criar_usuario(perfil=perfil)
        livro = self.criar_livro()
        emp = self.emprestar(livro["exemplares"][0][1], u["matricula"])
        return u, livro, emp

    def test_emprestimo_em_dia_pode_renovar(self):
        _, _, emp = self._emprestimo()
        pode, motivo = servicos.pode_renovar(emp["id"])
        self.assertTrue(pode)
        self.assertEqual(motivo, "")

    def test_atrasado_nao_renova(self):
        _, _, emp = self._emprestimo()
        self.atrasar_emprestimo(emp["id"], dias=2)
        pode, motivo = servicos.pode_renovar(emp["id"])
        self.assertFalse(pode)
        self.assertIn("prazo", motivo.lower())
        with self.assertRaises(RegraNegocioError):
            servicos.renovar_emprestimo(emp["id"], validar_regras=True)

    def test_balcao_ainda_renova_atrasado(self):
        """A bibliotecária não perde um poder que já tinha."""
        _, _, emp = self._emprestimo()
        self.atrasar_emprestimo(emp["id"], dias=2)
        res = servicos.renovar_emprestimo(emp["id"])
        self.assertEqual(res["data_prevista"],
                          (date.today() + timedelta(days=7)).isoformat())

    def test_livro_com_fila_de_reserva_nao_renova(self):
        from sigbef import reservas
        _, livro, emp = self._emprestimo()
        # O único exemplar está emprestado, então o outro aluno consegue
        # entrar na fila — e é isso que trava a renovação.
        outro = self.criar_usuario(matricula="esperando1")
        reservas.criar_reserva(livro["livro_id"], outro["id"])
        pode, motivo = servicos.pode_renovar(emp["id"])
        self.assertFalse(pode)
        self.assertIn("esperando", motivo.lower())

    def test_limite_de_renovacoes(self):
        set_config("LIMITE_RENOVACOES", "1")
        _, _, emp = self._emprestimo()
        servicos.renovar_emprestimo(emp["id"], validar_regras=True)
        pode, motivo = servicos.pode_renovar(emp["id"])
        self.assertFalse(pode)
        self.assertIn("renovou", motivo.lower())

    def test_renovacoes_sao_contadas(self):
        _, _, emp = self._emprestimo()
        servicos.renovar_emprestimo(emp["id"])
        servicos.renovar_emprestimo(emp["id"])
        with db_cursor() as cur:
            cur.execute("SELECT renovacoes FROM emprestimo WHERE id = ?",
                        (emp["id"],))
            self.assertEqual(cur.fetchone()["renovacoes"], 2)

    def test_emprestimo_inexistente(self):
        pode, motivo = servicos.pode_renovar(99999)
        self.assertFalse(pode)
        self.assertIn("não encontrado", motivo)


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
# Brasão da instituição
# ---------------------------------------------------------------------------
class TestBrasaoInstituicao(ServicosTestCase):
    """Imagem opcional da escola, guardada em base64 na configuração."""

    def _arquivo_imagem(self, dados: bytes) -> str:
        import shutil
        pasta = tempfile.mkdtemp(prefix="sigbef-brasao-")
        self.addCleanup(shutil.rmtree, pasta, ignore_errors=True)
        caminho = os.path.join(pasta, "brasao.png")
        Path(caminho).write_bytes(dados)
        return caminho

    def _png_valido(self) -> bytes:
        """Reusa um PNG real dos ícones embutidos como massa de teste."""
        import base64
        from sigbef.icones_data import ICONES
        return base64.b64decode(next(iter(ICONES.values())))

    def test_salvar_e_obter_brasao(self):
        caminho = self._arquivo_imagem(self._png_valido())
        servicos.salvar_brasao(caminho)
        self.assertIsNotNone(servicos.obter_brasao())

    def test_sem_brasao_por_padrao(self):
        self.assertIsNone(servicos.obter_brasao())

    def test_formato_invalido_rejeitado(self):
        jpeg_falso = b"\xff\xd8\xff\xe0" + b"\x00" * 64
        caminho = self._arquivo_imagem(jpeg_falso)
        with self.assertRaises(RegraNegocioError):
            servicos.salvar_brasao(caminho)
        self.assertIsNone(servicos.obter_brasao())

    def test_imagem_grande_demais_rejeitada(self):
        png = self._png_valido()
        inflado = png + b"\x00" * (servicos.BRASAO_LIMITE_BYTES + 1)
        caminho = self._arquivo_imagem(inflado)
        with self.assertRaises(RegraNegocioError):
            servicos.salvar_brasao(caminho)

    def test_remover_brasao(self):
        caminho = self._arquivo_imagem(self._png_valido())
        servicos.salvar_brasao(caminho)
        servicos.remover_brasao()
        self.assertIsNone(servicos.obter_brasao())


# ---------------------------------------------------------------------------
# Importação de acervo via CSV
# ---------------------------------------------------------------------------
class TestImportacaoEstragoDePlanilha(ServicosTestCase):
    """Campos que a planilha converteu em número.

    Encontrado no acervo real do CEFE: seis livros ("1808", "1889",
    "1984"…) tinham virado "1808.0" no banco. O Excel reconhece a célula
    como número e grava o ponto flutuante ao exportar; a importação
    aceitava o texto como veio.
    """

    def test_titulo_numerico_perde_o_ponto_zero(self):
        caminho = self.csv_temporario(
            "titulo;autores\n1984.0;George Orwell\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 1)
        self.assertEqual(servicos.listar_livros()[0]["titulo"], "1984")

    def test_a_correcao_e_avisada_nunca_silenciosa(self):
        caminho = self.csv_temporario(
            "titulo;autores\n1808.0;Laurentino Gomes\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(len(res["ajustes"]), 1)
        linha, texto = res["ajustes"][0]
        self.assertEqual(linha, 2)
        self.assertIn("1808.0", texto)
        self.assertIn("titulo", texto)

    def test_titulo_normal_com_ponto_nao_e_tocado(self):
        """'Web 2.0' é o título, não um número estragado."""
        caminho = self.csv_temporario(
            "titulo;autores\nWeb 2.0;Autor\nO Senhor dos Anéis;Tolkien\n")
        res = servicos.importar_acervo_csv(caminho)
        titulos = sorted(l["titulo"] for l in servicos.listar_livros())
        self.assertIn("Web 2.0", titulos)
        self.assertEqual(res["ajustes"], [])

    def test_isbn_em_notacao_cientifica_nao_entra(self):
        """Não dá para recuperar: os dígitos do meio se perderam.

        Guardar '9,78854E+12' como ISBN seria pior que deixar vazio —
        ninguém acharia o livro por esse código.
        """
        caminho = self.csv_temporario(
            "titulo;autores;isbn\nLivro;Autor;9,78854E+12\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 1)
        self.assertFalse(servicos.listar_livros()[0]["isbn"])
        self.assertIn("notação científica", res["ajustes"][0][1])

    def test_tombo_numerico_tambem_e_corrigido(self):
        caminho = self.csv_temporario(
            "titulo;autores;tombo\nLivro;Autor;04839.0\n")
        servicos.importar_acervo_csv(caminho)
        det = servicos.detalhes_livro(servicos.listar_livros()[0]["id"])
        self.assertEqual(det["exemplares"][0]["numero_tombo"], "04839")

    def test_importacao_limpa_nao_produz_ajuste(self):
        caminho = self.csv_temporario(
            "titulo;autores\nDom Casmurro;Machado de Assis\n")
        self.assertEqual(servicos.importar_acervo_csv(caminho)["ajustes"], [])


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

    def test_tombo_preservado_na_importacao(self):
        """Tombo do livro físico entra no exemplar, em vez do automático."""
        caminho = self.csv_temporario(
            "titulo;autores;tombo\n"
            "Meu Pé de Laranja Lima;José Mauro de Vasconcelos;8626\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["erros"], [])
        livro = servicos.listar_livros("Laranja Lima")[0]
        det = servicos.detalhes_livro(livro["id"])
        self.assertEqual(det["exemplares"][0]["numero_tombo"], "8626")

    def test_tombos_multiplos_um_por_exemplar(self):
        caminho = self.csv_temporario(
            "titulo;autores;quantidade;tombo\n"
            "Auto da Barca;Gil Vicente;3;101/102/103\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["exemplares"], 3)
        livro = servicos.listar_livros("Auto da Barca")[0]
        det = servicos.detalhes_livro(livro["id"])
        tombos = sorted(ex["numero_tombo"] for ex in det["exemplares"])
        self.assertEqual(tombos, ["101", "102", "103"])

    def test_tombo_divergente_da_quantidade_vai_para_erros(self):
        caminho = self.csv_temporario(
            "titulo;autores;quantidade;tombo\n"
            "Dois Sem Par;Fulano;2;só-um\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 0)
        self.assertEqual(len(res["erros"]), 1)
        self.assertIn("tombos", res["erros"][0][1])

    def test_tombo_repetido_no_arquivo_vai_para_erros(self):
        caminho = self.csv_temporario(
            "titulo;autores;tombo\n"
            "Primeiro;Fulano;777\n"
            "Segundo;Beltrano;777\n")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["livros"], 1)
        self.assertEqual(len(res["erros"]), 1)
        self.assertEqual(res["erros"][0][0], 3)  # linha 3 do arquivo
        self.assertIn("777", res["erros"][0][1])

    def test_tombo_ja_no_banco_vai_para_erros(self):
        caminho1 = self.csv_temporario(
            "titulo;autores;tombo\nOriginal;Fulano;555\n")
        servicos.importar_acervo_csv(caminho1)
        caminho2 = self.csv_temporario(
            "titulo;autores;tombo\nOutro Livro;Beltrano;555\n")
        res = servicos.importar_acervo_csv(caminho2)
        self.assertEqual(res["livros"], 0)
        self.assertEqual(len(res["erros"]), 1)
        self.assertIn("555", res["erros"][0][1])

    def test_cabecalho_n_de_registro_como_alias_de_tombo(self):
        """O cabeçalho do livro de tombo em papel (Nº de Registro) funciona."""
        caminho = self.csv_temporario(
            "titulo;autores;Nº de Registro\n"
            "Com Registro;Fulano;42\n", encoding="utf-8-sig")
        res = servicos.importar_acervo_csv(caminho)
        self.assertEqual(res["erros"], [])
        livro = servicos.listar_livros("Com Registro")[0]
        det = servicos.detalhes_livro(livro["id"])
        self.assertEqual(det["exemplares"][0]["numero_tombo"], "42")

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

    def test_etiquetas_dos_livros_selecionados(self):
        """Imprimir só o que foi marcado na lista, e não o acervo todo."""
        so_um = servicos.listar_exemplares_para_etiquetas(
            livro_ids=[self.livro_b["livro_id"]])
        self.assertEqual(len(so_um), 1)
        self.assertEqual(so_um[0]["titulo"], "Python para Todos")

        os_dois = servicos.listar_exemplares_para_etiquetas(
            livro_ids=[self.livro_a["livro_id"], self.livro_b["livro_id"]])
        self.assertEqual(len(os_dois), 3)

    def test_selecao_ignora_o_termo_de_busca(self):
        """A marcação na lista é mais específica que a caixa de busca."""
        etiquetas = servicos.listar_exemplares_para_etiquetas(
            "Casmurro", livro_ids=[self.livro_b["livro_id"]])
        self.assertEqual([e["titulo"] for e in etiquetas],
                          ["Python para Todos"])

    def test_selecao_vazia_nao_imprime_o_acervo_inteiro(self):
        """Lista vazia é lista vazia, e não 'sem filtro'."""
        self.assertEqual(servicos.listar_exemplares_para_etiquetas(
            livro_ids=[]), [])

    def test_selecao_ignora_exemplar_baixado(self):
        codigo = self.livro_a["exemplares"][0][1]
        servicos.baixar_exemplar(codigo, "EXTRAVIADO")
        etiquetas = servicos.listar_exemplares_para_etiquetas(
            livro_ids=[self.livro_a["livro_id"]])
        self.assertEqual(len(etiquetas), 1)
        self.assertNotIn(codigo, [e["codigo_barras"] for e in etiquetas])

    def test_selecao_repetida_nao_duplica_etiqueta(self):
        etiquetas = servicos.listar_exemplares_para_etiquetas(
            livro_ids=[self.livro_b["livro_id"], self.livro_b["livro_id"]])
        self.assertEqual(len(etiquetas), 1)

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
