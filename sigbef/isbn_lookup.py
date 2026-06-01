# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marcello
"""
SIGBEF — Busca opcional de metadados de livro por ISBN (online).

Desligada por padrão (config ISBN_LOOKUP=0) para o sistema continuar
funcionando 100% offline. Quando ligada em Configurações, o cadastro de
livro ganha um botão "Buscar online" que consulta a Open Library e, como
fallback, o Google Books. Usa só a biblioteca padrão (urllib + json),
sem dependência externa.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request

TIMEOUT = 6  # segundos por requisição
_UA = {"User-Agent": "SIGBEF/1.2 (biblioteca escolar)"}


class ISBNLookupError(Exception):
    """Falha ao consultar (rede indisponível, timeout, etc.)."""


def _limpar_isbn(isbn: str) -> str:
    return re.sub(r"[^0-9Xx]", "", isbn or "").upper()


def _ano(texto) -> int | None:
    m = re.search(r"(\d{4})", str(texto or ""))
    return int(m.group(1)) if m else None


def _http_json(url: str, _retry: bool = True) -> dict:
    req = urllib.request.Request(url, headers=_UA)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 429 = limite de requisições; espera um pouco e tenta uma vez mais
        if e.code == 429 and _retry:
            time.sleep(1.5)
            return _http_json(url, _retry=False)
        raise


def _via_openlibrary(isbn: str) -> dict | None:
    url = (f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}"
           f"&format=json&jscmd=data")
    item = _http_json(url).get(f"ISBN:{isbn}")
    if not item:
        return None
    autores = [a.get("name") for a in item.get("authors", []) if a.get("name")]
    pubs = item.get("publishers", [])
    editora = ""
    if pubs:
        editora = pubs[0].get("name", "") if isinstance(pubs[0], dict) else str(pubs[0])
    return {
        "titulo": item.get("title", "") or "",
        "autores": autores,
        "editora": editora,
        "ano": _ano(item.get("publish_date")),
        "isbn": isbn,
        "fonte": "Open Library",
    }


def _via_openlibrary_edition(isbn: str) -> dict | None:
    """Endpoint de edição da Open Library (/isbn/<isbn>.json).

    Cobre livros que a API de 'books' (jscmd=data) não retorna. Os autores
    vêm como chaves (/authors/OLxxxx), resolvidas em chamadas extras de
    melhor esforço (se falhar, deixa autores vazio pro usuário preencher).
    """
    try:
        ed = _http_json(f"https://openlibrary.org/isbn/{isbn}.json")
    except urllib.error.HTTPError as e:
        if e.code == 404:  # ISBN não existe nessa base = não encontrado
            return None
        raise
    if not ed or not ed.get("title"):
        return None
    autores = []
    for a in ed.get("authors", []) or []:
        chave = a.get("key") if isinstance(a, dict) else None
        if not chave:
            continue
        try:
            nome = _http_json(f"https://openlibrary.org{chave}.json").get("name")
            if nome:
                autores.append(nome)
        except Exception:
            pass
    pubs = ed.get("publishers", []) or []
    return {
        "titulo": ed.get("title", "") or "",
        "autores": autores,
        "editora": pubs[0] if pubs else "",
        "ano": _ano(ed.get("publish_date")),
        "isbn": isbn,
        "fonte": "Open Library",
    }


def _via_googlebooks(isbn: str) -> dict | None:
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    items = _http_json(url).get("items") or []
    if not items:
        return None
    vi = items[0].get("volumeInfo", {})
    return {
        "titulo": vi.get("title", "") or "",
        "autores": vi.get("authors", []) or [],
        "editora": vi.get("publisher", "") or "",
        "ano": _ano(vi.get("publishedDate")),
        "isbn": isbn,
        "fonte": "Google Books",
    }


def buscar(isbn: str) -> dict | None:
    """Busca metadados por ISBN.

    Retorna um dict (titulo, autores, editora, ano, isbn, fonte) ou None se
    nenhuma fonte encontrar o livro. Lança ISBNLookupError se não conseguir
    consultar nenhuma fonte (ex.: sem internet).
    """
    isbn = _limpar_isbn(isbn)
    if len(isbn) not in (10, 13):
        raise ISBNLookupError("ISBN inválido: informe 10 ou 13 dígitos.")

    erros = []
    for fonte in (_via_openlibrary, _via_openlibrary_edition, _via_googlebooks):
        try:
            res = fonte(isbn)
            if res and res.get("titulo"):
                return res
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue  # não encontrado nessa fonte, tenta a próxima
            erros.append("limite de requisições (HTTP 429)"
                         if e.code == 429 else "HTTP %d" % e.code)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            erros.append(str(getattr(e, "reason", e)))
        except (ValueError, KeyError):
            pass

    # Se alguma fonte FALHOU (rede/429), não foi um "não encontrado" limpo:
    # avisa que pode ser temporário, em vez de dizer que o livro não existe.
    if erros:
        raise ISBNLookupError(
            "Não foi possível confirmar o ISBN agora (" + erros[0] + "). "
            "Tente de novo em alguns segundos ou preencha manualmente.")
    return None
