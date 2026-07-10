"""Testes de sigbef.isbn_lookup — busca de metadados por ISBN (com stubs,
sem qualquer acesso à rede)."""
import tests.base  # noqa: F401  # configura o ambiente de testes (deve ser o 1º import)

import unittest
import urllib.error
from unittest import mock

from sigbef import isbn_lookup
from sigbef.isbn_lookup import ISBNLookupError

ISBN13 = "9788533302273"

# Prefixos de URL de cada fonte
_URL_BOOKS = "https://openlibrary.org/api/books"
_URL_EDICAO = "https://openlibrary.org/isbn/"
_URL_AUTOR = "https://openlibrary.org/authors/"
_URL_GOOGLE = "https://www.googleapis.com/books"


def _stub_http(mapa):
    """Cria um stub de _http_json que responde por prefixo de URL.

    Valores do mapa podem ser dicts (resposta JSON) ou exceções (levantadas).
    URLs não mapeadas respondem {} (fonte 'vazia').
    """
    def fake(url, _retry=True):
        for prefixo, resposta in mapa.items():
            if url.startswith(prefixo):
                if isinstance(resposta, Exception):
                    raise resposta
                return resposta
        return {}
    return fake


class TestLimparIsbn(unittest.TestCase):
    """_limpar_isbn: normalização do ISBN digitado."""

    def test_remove_hifens_e_espacos(self):
        self.assertEqual(isbn_lookup._limpar_isbn("978-85-333-0227-3"),
                         "9788533302273")
        self.assertEqual(isbn_lookup._limpar_isbn(" 85 333 0227 5 "),
                         "8533302275")

    def test_preserva_x_e_converte_para_maiusculo(self):
        self.assertEqual(isbn_lookup._limpar_isbn("85-333-0227-X"),
                         "853330227X")
        self.assertEqual(isbn_lookup._limpar_isbn("85-333-0227-x"),
                         "853330227X")

    def test_none_e_vazio(self):
        self.assertEqual(isbn_lookup._limpar_isbn(None), "")
        self.assertEqual(isbn_lookup._limpar_isbn(""), "")


class TestAno(unittest.TestCase):
    """_ano: extração de ano de textos de data variados."""

    def test_extrai_quatro_digitos(self):
        self.assertEqual(isbn_lookup._ano("1999"), 1999)
        self.assertEqual(isbn_lookup._ano("March 5, 2001"), 2001)
        self.assertEqual(isbn_lookup._ano("São Paulo, 1987"), 1987)
        self.assertEqual(isbn_lookup._ano("05/03/2010"), 2010)

    def test_sem_digitos_retorna_none(self):
        self.assertIsNone(isbn_lookup._ano("sem data"))
        self.assertIsNone(isbn_lookup._ano(None))
        self.assertIsNone(isbn_lookup._ano(""))

    def test_pega_os_primeiros_quatro_digitos_de_sequencias_longas(self):
        """COMPORTAMENTO REAL: numa sequência com mais de 4 dígitos, pega os
        4 primeiros (ex.: '123456' vira 1234) — pode extrair 'ano' errado."""
        self.assertEqual(isbn_lookup._ano("123456"), 1234)


class TestBuscarValidacao(unittest.TestCase):
    """buscar: validação do ISBN antes de qualquer consulta."""

    def test_isbn_invalido_levanta_erro(self):
        for invalido in ("123", "12345678901", "12345678901234", "", None):
            with self.subTest(isbn=invalido):
                with self.assertRaises(ISBNLookupError):
                    isbn_lookup.buscar(invalido)


class TestBuscarFontes(unittest.TestCase):
    """buscar: ordem das fontes e tratamento de falhas (tudo via stub)."""

    def _buscar_com_stub(self, mapa, isbn=ISBN13):
        with mock.patch.object(isbn_lookup, "_http_json", _stub_http(mapa)):
            return isbn_lookup.buscar(isbn)

    def test_openlibrary_books_completa(self):
        """(a) API 'books' retorna dado completo -> fonte 'Open Library'."""
        res = self._buscar_com_stub({
            _URL_BOOKS: {f"ISBN:{ISBN13}": {
                "title": "Dom Casmurro",
                "authors": [{"name": "Machado de Assis"}],
                "publishers": [{"name": "Editora Alfa"}],
                "publish_date": "1899",
            }},
        })
        self.assertEqual(res["titulo"], "Dom Casmurro")
        self.assertEqual(res["autores"], ["Machado de Assis"])
        self.assertEqual(res["editora"], "Editora Alfa")
        self.assertEqual(res["ano"], 1899)
        self.assertEqual(res["isbn"], ISBN13)
        self.assertEqual(res["fonte"], "Open Library")

    def test_openlibrary_via_edicao(self):
        """(b) 'books' vazia, endpoint de edição responde -> 'Open Library'."""
        res = self._buscar_com_stub({
            _URL_BOOKS: {},
            _URL_EDICAO: {
                "title": "Memórias Póstumas",
                "authors": [{"key": "/authors/OL123A"}],
                "publishers": ["Editora Beta"],
                "publish_date": "March 1881",
            },
            _URL_AUTOR: {"name": "Machado de Assis"},
        })
        self.assertEqual(res["titulo"], "Memórias Póstumas")
        self.assertEqual(res["autores"], ["Machado de Assis"])
        self.assertEqual(res["editora"], "Editora Beta")
        self.assertEqual(res["ano"], 1881)
        self.assertEqual(res["fonte"], "Open Library")

    def test_fallback_google_books(self):
        """(c) Open Library toda vazia, Google Books responde."""
        res = self._buscar_com_stub({
            _URL_BOOKS: {},
            _URL_EDICAO: {},
            _URL_GOOGLE: {"items": [{"volumeInfo": {
                "title": "Quincas Borba",
                "authors": ["Machado de Assis"],
                "publisher": "Editora Gama",
                "publishedDate": "1891-01-01",
            }}]},
        })
        self.assertEqual(res["titulo"], "Quincas Borba")
        self.assertEqual(res["autores"], ["Machado de Assis"])
        self.assertEqual(res["editora"], "Editora Gama")
        self.assertEqual(res["ano"], 1891)
        self.assertEqual(res["fonte"], "Google Books")

    def test_todas_vazias_sem_erro_retorna_none(self):
        """(d) Nenhuma fonte encontra e nenhuma falha -> None (não é erro)."""
        res = self._buscar_com_stub({
            _URL_BOOKS: {},
            _URL_EDICAO: {},
            _URL_GOOGLE: {},
        })
        self.assertIsNone(res)

    def test_erro_de_rede_levanta_isbnlookuperror(self):
        """(e) Falha de rede em todas as fontes -> ISBNLookupError com
        mensagem de tentar de novo (não confunde com 'não encontrado')."""
        mapa = {
            _URL_BOOKS: urllib.error.URLError("sem rede"),
            _URL_EDICAO: urllib.error.URLError("sem rede"),
            _URL_GOOGLE: urllib.error.URLError("sem rede"),
        }
        with mock.patch.object(isbn_lookup, "_http_json", _stub_http(mapa)):
            with self.assertRaises(ISBNLookupError) as ctx:
                isbn_lookup.buscar(ISBN13)
        self.assertIn("Tente de novo", str(ctx.exception))
        self.assertIn("sem rede", str(ctx.exception))

    def test_isbn10_com_x_e_aceito(self):
        """ISBN-10 terminando em X passa na validação e é consultado."""
        res = self._buscar_com_stub({
            _URL_BOOKS: {"ISBN:043942089X": {"title": "Livro X"}},
        }, isbn="0-439-42089-x")
        self.assertEqual(res["titulo"], "Livro X")
        self.assertEqual(res["isbn"], "043942089X")


class TestParsing(unittest.TestCase):
    """Parsing dos formatos de resposta de cada fonte."""

    def _buscar_com_stub(self, mapa):
        with mock.patch.object(isbn_lookup, "_http_json", _stub_http(mapa)):
            return isbn_lookup.buscar(ISBN13)

    def test_autores_como_lista_de_dicts_na_books_api(self):
        """Autores da API 'books' vêm como dicts; entradas sem 'name' são
        ignoradas."""
        res = self._buscar_com_stub({
            _URL_BOOKS: {f"ISBN:{ISBN13}": {
                "title": "Título",
                "authors": [{"name": "Autora Um"}, {}, {"name": "Autor Dois"}],
            }},
        })
        self.assertEqual(res["autores"], ["Autora Um", "Autor Dois"])

    def test_publishers_como_strings_no_endpoint_de_edicao(self):
        """No endpoint de edição os publishers são strings simples; a
        primeira vira a editora."""
        res = self._buscar_com_stub({
            _URL_BOOKS: {},
            _URL_EDICAO: {
                "title": "Título",
                "publishers": ["Editora Um", "Editora Dois"],
            },
        })
        self.assertEqual(res["editora"], "Editora Um")
        self.assertEqual(res["autores"], [])  # sem authors -> lista vazia

    def test_ano_extraido_de_publish_date(self):
        res = self._buscar_com_stub({
            _URL_BOOKS: {f"ISBN:{ISBN13}": {
                "title": "Título",
                "publish_date": "May 5, 2003",
            }},
        })
        self.assertEqual(res["ano"], 2003)

    def test_publish_date_sem_ano_vira_none(self):
        res = self._buscar_com_stub({
            _URL_BOOKS: {f"ISBN:{ISBN13}": {
                "title": "Título",
                "publish_date": "sem data",
            }},
        })
        self.assertIsNone(res["ano"])


if __name__ == "__main__":
    unittest.main()
