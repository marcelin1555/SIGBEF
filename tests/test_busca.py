"""
SIGBEF — Busca no acervo.

A busca era um LIKE, e o LIKE do SQLite só ignora maiúscula em ASCII.
Medido no acervo real do CEFE (2.867 títulos), antes desta mudança:

    "joao"       ->  0   contra "João"       -> 61
    "memorias"   ->  0   contra "Memórias"   -> 27
    "coracao"    ->  0   contra "Coração"    -> 14
    "matematica" ->  0   contra "Matemática" ->  6
    "machado casmurro"  -> 0
    tombo 4871          -> 0   (o README prometia busca por tombo)

Quem digita no celular quase nunca põe acento, então o aluno
praticamente não achava livro. E a planilha importada veio metade sem
acento: "portugues" achava 23 e "Português" só 2 -- quem escrevia
certo era punido.

A busca agora usa o FTS5 do próprio SQLite, com o tokenizador que tira
acento. Estes testes travam o comportamento novo e, principalmente, que
o índice acompanha cada caminho que mexe no acervo.

Uso:
    python -m unittest tests.test_busca -v
"""
from __future__ import annotations

import csv
import os
import tempfile

from tests.base import SigbefTestCase

from sigbef import database, servicos
from sigbef.database import db_cursor


class BaseBusca(SigbefTestCase):

    def livro(self, titulo, autores=("Autoria",), categoria="", isbn="",
              tombos=None, exemplares=1):
        return servicos.cadastrar_livro(
            titulo=titulo, autores=list(autores), categoria=categoria,
            isbn=isbn, quantidade_exemplares=exemplares, tombos=tombos)

    def titulos(self, termo, **kw):
        return [x["titulo"] for x in servicos.listar_livros(termo, **kw)]


class TestAcento(BaseBusca):
    """O defeito que motivou a mudança."""

    def test_sem_acento_acha_com_acento(self):
        self.livro("Memórias Póstumas de Brás Cubas")
        self.assertEqual(self.titulos("memorias postumas"),
                         ["Memórias Póstumas de Brás Cubas"])

    def test_com_acento_acha_sem_acento(self):
        """A planilha importada veio sem acento em metade dos registros:
        quem escreve certo não pode ser punido por isso."""
        self.livro("Gramatica da Lingua Portuguesa")
        self.assertEqual(self.titulos("Gramática"),
                         ["Gramatica da Lingua Portuguesa"])

    def test_nome_proprio_sem_acento(self):
        self.livro("O Auto da Compadecida", autores=["Ariano Suassuna"])
        self.livro("Vidas Secas", autores=["Graciliano Ramos"])
        self.livro("Coração de Tinta", autores=["Cornelia Funke"])
        self.assertEqual(self.titulos("coracao"), ["Coração de Tinta"])

    def test_maiuscula_acentuada(self):
        """O LIKE tratava Á e á como letras diferentes."""
        self.livro("A ÁRVORE GENEROSA")
        self.assertEqual(self.titulos("árvore"), ["A ÁRVORE GENEROSA"])
        self.assertEqual(self.titulos("ARVORE"), ["A ÁRVORE GENEROSA"])


class TestPalavras(BaseBusca):

    def test_palavras_em_qualquer_ordem(self):
        self.livro("Dom Casmurro", autores=["Machado de Assis"])
        self.assertEqual(self.titulos("casmurro dom"), ["Dom Casmurro"])

    def test_autor_e_titulo_na_mesma_busca(self):
        """Antes, a frase inteira precisava caber num campo só."""
        self.livro("Dom Casmurro", autores=["Machado de Assis"])
        self.livro("Dom Quixote", autores=["Miguel de Cervantes"])
        self.assertEqual(self.titulos("machado dom"), ["Dom Casmurro"])

    def test_todas_as_palavras_precisam_aparecer(self):
        self.livro("Dom Casmurro")
        self.livro("Dom Quixote")
        self.assertEqual(self.titulos("dom quixote"), ["Dom Quixote"])

    def test_prefixo_enquanto_digita(self):
        self.livro("Dom Casmurro")
        self.assertEqual(self.titulos("casm"), ["Dom Casmurro"])

    def test_nao_acha_pedaco_do_meio_da_palavra(self):
        """Mudança deliberada. O LIKE achava "ética" dentro de
        "Poética" e "Aritmética" -- no acervo do CEFE, 8 dos 9
        resultados eram ruído. Quem procura ética quer ética."""
        self.livro("Antologia Poética")
        self.livro("Aritmética da Emília")
        self.livro("Temas Transversais e Ética")
        self.assertEqual(self.titulos("ética"),
                         ["Temas Transversais e Ética"])

    def test_uma_letra_nao_vira_prefixo(self):
        """"C++" vira "C"; como prefixo, acharia toda palavra com C --
        1.422 dos 2.867 livros do CEFE."""
        self.livro("Linguagem C")
        self.livro("Crônicas Escolhidas")
        self.livro("Casa Grande e Senzala")
        self.assertEqual(self.titulos("C++"), ["Linguagem C"])


class TestCodigos(BaseBusca):
    """Tombo e ISBN: o que o README prometia e a busca não fazia."""

    def test_acha_pelo_tombo(self):
        self.livro("Vidas Secas", tombos=["4871"])
        self.assertEqual(self.titulos("4871"), ["Vidas Secas"])

    def test_tombo_com_hifen(self):
        self.livro("Vidas Secas", tombos=["00012-004"])
        self.assertEqual(self.titulos("00012-004"), ["Vidas Secas"])

    def test_isbn_sem_hifen(self):
        self.livro("Dom Casmurro", isbn="978-85-359-1066-3")
        self.assertEqual(self.titulos("9788535910663"), ["Dom Casmurro"])

    def test_isbn_com_hifen(self):
        self.livro("Dom Casmurro", isbn="9788535910663")
        self.assertEqual(self.titulos("978-85-359-1066-3"),
                         ["Dom Casmurro"])

    def test_tombo_de_cada_exemplar(self):
        self.livro("Vidas Secas", exemplares=3,
                   tombos=["T-100", "T-101", "T-102"])
        self.assertEqual(self.titulos("T-102"), ["Vidas Secas"])


class TestEntradaHostil(BaseBusca):
    """Aspas, parênteses, dois-pontos, asterisco e hífen são operadores
    do FTS5. Digitados crus, derrubariam a busca com erro de sintaxe."""

    ENTRADAS = ['"', "(", ")", "Dom Casmurro:", "C++", "a AND b", "NOT",
                "OR", "***", "título*", "'; DROP TABLE livro;--",
                "NEAR(dom casmurro)", "^dom", "dom -casmurro", "{}"]

    def test_nada_derruba_a_busca(self):
        self.livro("Dom Casmurro")
        for entrada in self.ENTRADAS:
            with self.subTest(entrada=entrada):
                servicos.listar_livros(entrada)
                servicos.contar_livros(entrada)

    def test_o_acervo_sobrevive(self):
        self.livro("Dom Casmurro")
        servicos.listar_livros("'; DROP TABLE livro;--")
        self.assertEqual(self.titulos(""), ["Dom Casmurro"])

    def test_so_pontuacao_nao_devolve_o_acervo_inteiro(self):
        """Não sobra nada para procurar; mostrar tudo seria dizer que
        todos os livros casam com "***"."""
        self.livro("Dom Casmurro")
        self.assertEqual(self.titulos("***"), [])

    def test_operadores_viram_palavras(self):
        self.livro("Ser OR Não Ser")
        self.assertEqual(self.titulos("OR"), ["Ser OR Não Ser"])


class TestResultado(BaseBusca):

    def test_termo_vazio_lista_o_acervo(self):
        self.livro("B")
        self.livro("A")
        self.assertEqual(self.titulos(""), ["A", "B"])

    def test_mais_relevante_primeiro(self):
        """Quem digita "1984" quer o livro "1984" no topo.

        O outro título começa com "0" para vir ANTES em ordem
        alfabética: se este teste passar, foi pela relevância, e não
        porque "1984" já seria o primeiro de qualquer jeito."""
        self.livro("0 Estudo sobre Orwell", categoria="1984 e outros")
        self.livro("1984", autores=["George Orwell"])
        self.assertEqual(self.titulos("1984")[0], "1984")

    def test_contagem_bate_com_a_lista(self):
        """Total que não bate com a lista é pior que total nenhum."""
        for t in ("Dom Casmurro", "Dom Quixote", "Memórias Póstumas",
                  "Vidas Secas", "Dom Pedro"):
            self.livro(t)
        for termo in ("", "dom", "memorias", "zzz", "***", "vid"):
            with self.subTest(termo=termo):
                self.assertEqual(servicos.contar_livros(termo),
                                 len(servicos.listar_livros(termo)))

    def test_paginas_nao_repetem_nem_pulam(self):
        for i in range(23):
            self.livro(f"Coleção Dom Volume {i:02d}")
        vistos = []
        for pagina in range(3):
            vistos += [x["id"] for x in servicos.listar_livros(
                "dom", limite=10, offset=pagina * 10)]
        self.assertEqual(len(vistos), 23)
        self.assertEqual(len(set(vistos)), 23)

    def test_combina_com_categoria(self):
        self.livro("Dom Casmurro", categoria="Romance")
        self.livro("Dom Pedro II", categoria="História")
        self.assertEqual(self.titulos("dom", categoria="Romance"),
                         ["Dom Casmurro"])

    def test_combina_com_apenas_disponiveis(self):
        liv = self.livro("Dom Casmurro")
        self.livro("Dom Quixote")
        aluno = self.criar_usuario(matricula="2024900")
        servicos.realizar_emprestimo(
            codigo_exemplar=liv["exemplares"][0][1],
            matricula_usuario=aluno["matricula"])
        self.assertEqual(self.titulos("dom", apenas_disponiveis=True),
                         ["Dom Quixote"])


class TestIndiceAcompanhaOAcervo(BaseBusca):
    """O índice é mantido por gatilhos. Cada caminho que mexe no acervo
    precisa aparecer aqui: um índice que depende de cada função lembrar
    de avisá-lo fica desatualizado no primeiro que esquecer."""

    def test_livro_novo_ja_aparece(self):
        self.livro("Vidas Secas")
        self.assertEqual(self.titulos("secas"), ["Vidas Secas"])

    def test_editar_titulo(self):
        liv = self.livro("Titulo Errado")
        servicos.editar_livro(liv["livro_id"], titulo="Vidas Secas",
                              autores=["Graciliano Ramos"])
        self.assertEqual(self.titulos("errado"), [])
        self.assertEqual(self.titulos("secas"), ["Vidas Secas"])

    def test_editar_autor(self):
        liv = self.livro("Vidas Secas", autores=["Autor Errado"])
        servicos.editar_livro(liv["livro_id"], titulo="Vidas Secas",
                              autores=["Graciliano Ramos"])
        self.assertEqual(self.titulos("graciliano"), ["Vidas Secas"])
        self.assertEqual(self.titulos("errado"), [])

    def test_editar_categoria(self):
        liv = self.livro("Vidas Secas", categoria="Errada")
        servicos.editar_livro(liv["livro_id"], titulo="Vidas Secas",
                              autores=["Autoria"], categoria="Romance")
        self.assertEqual(self.titulos("romance"), ["Vidas Secas"])

    def test_adicionar_exemplar_com_tombo(self):
        liv = self.livro("Vidas Secas")
        servicos.adicionar_exemplares(liv["livro_id"], 1, tombos=["T-900"])
        self.assertEqual(self.titulos("T-900"), ["Vidas Secas"])

    def test_corrigir_tombo(self):
        liv = self.livro("Vidas Secas", tombos=["T-100"])
        servicos.alterar_tombo_exemplar(liv["exemplares"][0][1], "T-555")
        self.assertEqual(self.titulos("T-555"), ["Vidas Secas"])
        self.assertEqual(self.titulos("T-100"), [])

    def test_liberar_tombo(self):
        liv = self.livro("Vidas Secas", tombos=["T-100"])
        servicos.alterar_tombo_exemplar(liv["exemplares"][0][1], "")
        self.assertEqual(self.titulos("T-100"), [])

    def test_livro_excluido_some(self):
        liv = self.livro("Vidas Secas")
        servicos.excluir_livro(liv["livro_id"])
        self.assertEqual(self.titulos("secas"), [])

    def test_emprestimo_nao_desindexa(self):
        """O gatilho de exemplar só olha tombo e livro: mudar o status
        num empréstimo não pode tirar o livro da busca."""
        liv = self.livro("Vidas Secas", tombos=["T-100"])
        aluno = self.criar_usuario(matricula="2024900")
        servicos.realizar_emprestimo(
            codigo_exemplar=liv["exemplares"][0][1],
            matricula_usuario=aluno["matricula"])
        self.assertEqual(self.titulos("T-100"), ["Vidas Secas"])

    def test_importacao_por_planilha(self):
        with tempfile.NamedTemporaryFile(
                "w", suffix=".csv", delete=False, encoding="utf-8",
                newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["titulo", "autores", "tombo"])
            w.writerow(["Memórias Póstumas", "Machado de Assis", "7001"])
            caminho = f.name
        try:
            servicos.importar_acervo_csv(caminho)
        finally:
            os.unlink(caminho)
        self.assertEqual(self.titulos("memorias"), ["Memórias Póstumas"])
        self.assertEqual(self.titulos("7001"), ["Memórias Póstumas"])


class TestMigracao(BaseBusca):
    """O banco da escola já existe, cheio, sem índice nenhum."""

    def _apagar_indice(self):
        with db_cursor() as cur:
            cur.execute("SELECT name FROM sqlite_master WHERE type='trigger'"
                        " AND name LIKE 'busca_%'")
            for (nome,) in cur.fetchall():
                cur.execute(f"DROP TRIGGER {nome}")
            cur.execute("DROP TABLE livro_busca")

    def test_banco_de_versao_anterior_ganha_indice(self):
        self.livro("Vidas Secas")
        self._apagar_indice()
        database.init_database()
        self.assertEqual(self.titulos("secas"), ["Vidas Secas"])

    def test_indice_incompleto_se_refaz_sozinho(self):
        """Subida interrompida no meio da primeira indexação."""
        self.livro("Vidas Secas")
        self.livro("Dom Casmurro")
        with db_cursor() as cur:
            cur.execute("DELETE FROM livro_busca WHERE rowid = "
                        "(SELECT MIN(id) FROM livro)")
        database.init_database()
        self.assertEqual(len(self.titulos("")), 2)
        self.assertEqual(servicos.contar_livros("secas"), 1)
        self.assertEqual(servicos.contar_livros("casmurro"), 1)

    def test_subir_de_novo_nao_duplica(self):
        self.livro("Vidas Secas")
        database.init_database()
        database.init_database()
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM livro_busca")
            self.assertEqual(cur.fetchone()[0], 1)


class TestSemFTS5(BaseBusca):
    """Um SQLite sem FTS5 não pode derrubar o sistema: volta a busca
    antiga, que tropeça em acento, mas mantém a biblioteca de pé."""

    def setUp(self):
        super().setUp()
        self._original = database.BUSCA_FTS
        database.BUSCA_FTS = False

    def tearDown(self):
        database.BUSCA_FTS = self._original
        super().tearDown() if hasattr(super(), "tearDown") else None

    def test_busca_continua_funcionando(self):
        self.livro("Dom Casmurro")
        self.assertEqual(self.titulos("casmurro"), ["Dom Casmurro"])

    def test_contagem_continua_batendo(self):
        self.livro("Dom Casmurro")
        self.livro("Dom Quixote")
        self.assertEqual(servicos.contar_livros("dom"),
                         len(servicos.listar_livros("dom")))


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
