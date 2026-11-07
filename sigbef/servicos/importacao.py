"""Importação do acervo a partir de planilha CSV."""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from pathlib import Path
from typing import Optional

from ..database import db_cursor, registrar_auditoria
from ..erros import RegraNegocioError

from .acervo import _inserir_livro_cur


_ALIASES_CSV = {
    "titulo": "titulo",
    "autores": "autores", "autor": "autores",
    "isbn": "isbn",
    "editora": "editora",
    "categoria": "categoria",
    "ano": "ano", "ano_publicacao": "ano",
    "edicao": "edicao",
    "sinopse": "sinopse",
    "quantidade": "quantidade", "quantidade_exemplares": "quantidade",
    "exemplares": "quantidade", "qtd": "quantidade",
    "localizacao": "localizacao", "estante": "localizacao",
    "tombo": "tombo", "tombos": "tombo", "numero_tombo": "tombo",
    "n_tombo": "tombo", "registro": "tombo", "n_de_registro": "tombo",
    "no_de_registro": "tombo", "numero_de_registro": "tombo",
}

MODELO_CSV = (
    "titulo;autores;isbn;editora;categoria;ano;edicao;quantidade;tombo;localizacao\n"
    "Dom Casmurro;Machado de Assis;9788535910663;Editora Exemplo;Romance;1899;1ª;3;101/102/103;Estante B2\n"
    'Contos Novos;"Mário de Andrade; Antonio Candido";;Outra Editora;Contos;1947;;2;;Estante C1\n'
)


def gerar_modelo_csv(destino: str) -> None:
    """Grava a planilha modelo de importação (UTF-8 com BOM, que o
    Excel abre com acentos corretos)."""
    Path(destino).write_text(MODELO_CSV, encoding="utf-8-sig")


def _normalizar_cabecalho(nome: str) -> str:
    s = unicodedata.normalize("NFKD", (nome or "").strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace(" ", "_")


# Texto que era número inteiro e a planilha transformou em decimal.
# Acontece com título ("1984" vira "1984.0"), tombo e ISBN: o Excel
# reconhece a célula como número e grava o ponto flutuante ao exportar.
_NUMERO_DE_PLANILHA = re.compile(r"^(\d+)\.0+$")

# ISBN de 13 dígitos que o Excel converteu para notação científica
# ("9788535914849" vira "9,78854E+12"). Aqui não há o que recuperar: os
# dígitos do meio se perderam de verdade.
_NOTACAO_CIENTIFICA = re.compile(r"^\d[.,]?\d*[Ee][+-]?\d+$")


def _corrigir_numero_de_planilha(valor: str) -> tuple[str, Optional[str]]:
    """Desfaz o estrago do Excel em campos que eram números inteiros.

    Devolve `(valor_corrigido, aviso)`. O aviso não é vazio quando algo
    mudou ou quando o dado é irrecuperável, para a importação mostrar à
    bibliotecária em vez de alterar o acervo em silêncio.
    """
    texto = (valor or "").strip()
    m = _NUMERO_DE_PLANILHA.match(texto)
    if m:
        return m.group(1), f"{texto!r} lido como número pela planilha"
    if _NOTACAO_CIENTIFICA.match(texto):
        # Não dá para reconstruir: "9,78854E+12" perdeu os dígitos do
        # meio. Melhor guardar vazio do que guardar um código falso que
        # ninguém vai conseguir usar na busca.
        return "", (f"{texto!r} está em notação científica e não pode ser "
                    "recuperado — formate a coluna como Texto na planilha")
    return texto, None


def importar_acervo_csv(caminho: str,
                        usuario_id: Optional[int] = None) -> dict:
    """Importa acervo em massa de um arquivo CSV, em transação única.

    Formato: primeira linha é o cabeçalho; `titulo` é obrigatório e as
    demais colunas (autores, isbn, editora, categoria, ano, edicao,
    sinopse, quantidade, tombo, localizacao) são opcionais. Aceita
    separador `;` ou `,` (Excel BR e internacional) e codificação UTF-8
    ou Windows-1252, detectados automaticamente. Vários autores na mesma
    célula separados por `;` ou `/`. Linhas com ISBN já cadastrado (ou
    repetido no arquivo) são puladas para não duplicar o acervo.

    A coluna `tombo` preserva o número de registro do livro físico (do
    livro de tombo em papel): um número por exemplar, separados por `/`
    quando a quantidade for maior que 1. Vazia, os tombos continuam
    sendo gerados automaticamente. Tombos repetidos (no arquivo ou já
    no banco) viram erro de linha, pois o empréstimo aceita o tombo
    como identificador do exemplar.

    Título, ISBN e tombo passam por uma correção antes de entrar: quando
    a planilha reconheceu a célula como número, "1984" chega como
    "1984.0" e o acervo ficaria com esse título. O que for corrigido vem
    em `ajustes`, para a bibliotecária ver o que mudou — nada é alterado
    em silêncio.

    Retorna {"livros", "exemplares", "pulados": [(linha, motivo)],
    "erros": [(linha, motivo)], "ajustes": [(linha, o que mudou)]}.
    """
    bruto = Path(caminho).read_bytes()
    try:
        texto = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = bruto.decode("cp1252")

    linhas_texto = texto.splitlines()
    if not linhas_texto:
        raise RegraNegocioError("O arquivo CSV está vazio.")
    cabecalho = linhas_texto[0]
    delim = ";" if cabecalho.count(";") >= cabecalho.count(",") else ","

    leitor = csv.DictReader(io.StringIO(texto), delimiter=delim)
    mapa = {}
    for original in (leitor.fieldnames or []):
        chave = _ALIASES_CSV.get(_normalizar_cabecalho(original))
        if chave and chave not in mapa.values():
            mapa[original] = chave
    if "titulo" not in mapa.values():
        raise RegraNegocioError(
            "O CSV precisa de uma coluna 'titulo'. Colunas aceitas: "
            "titulo, autores, isbn, editora, categoria, ano, edicao, "
            "sinopse, quantidade, tombo, localizacao.")

    with db_cursor() as cur:
        cur.execute("SELECT isbn FROM livro WHERE ativo = 1 AND isbn IS NOT NULL")
        isbns_existentes = {r["isbn"] for r in cur.fetchall()}
        cur.execute(
            "SELECT numero_tombo FROM exemplar WHERE numero_tombo IS NOT NULL")
        tombos_existentes = {r["numero_tombo"] for r in cur.fetchall()}

    # Fase 1 — validar todas as linhas (nada é gravado ainda)
    validas, erros, pulados, ajustes = [], [], [], []
    for num, linha in enumerate(leitor, start=2):
        dados = {mapa[k]: (v or "").strip()
                 for k, v in linha.items() if k in mapa}
        if not any(dados.values()):
            continue  # linha totalmente em branco

        # Campos que costumam sair estragados quando a planilha os
        # reconhece como número. Título "1984" chegando como "1984.0" é
        # o caso mais comum, e passava direto para o acervo.
        for campo in ("titulo", "isbn", "tombo"):
            if not dados.get(campo):
                continue
            corrigido, aviso = _corrigir_numero_de_planilha(dados[campo])
            if aviso:
                dados[campo] = corrigido
                ajustes.append((num, f"{campo}: {aviso}"))

        titulo = dados.get("titulo", "")
        if not titulo:
            erros.append((num, "título em branco"))
            continue
        autores = [a for a in re.split(r"[;/]", dados.get("autores", ""))
                   if a.strip()]
        if not autores:
            erros.append((num, "autores em branco"))
            continue
        ano = None
        if dados.get("ano"):
            try:
                ano = int(dados["ano"])
                if not 1000 <= ano <= 2100:
                    raise ValueError
            except ValueError:
                erros.append((num, f"ano inválido: {dados['ano']!r}"))
                continue
        quantidade = 1
        if dados.get("quantidade"):
            try:
                quantidade = int(dados["quantidade"])
                if not 1 <= quantidade <= 999:
                    raise ValueError
            except ValueError:
                erros.append((num,
                              f"quantidade inválida: {dados['quantidade']!r}"))
                continue
        tombos = [t.strip() for t in re.split(r"[;/]", dados.get("tombo", ""))
                  if t.strip()]
        if tombos:
            if len(tombos) != quantidade:
                erros.append((num,
                              f"tombos informados ({len(tombos)}) diferentes "
                              f"da quantidade de exemplares ({quantidade})"))
                continue
            repetido = next((t for t in tombos if t in tombos_existentes
                             or tombos.count(t) > 1), None)
            if repetido:
                erros.append((num, f"tombo {repetido} repetido ou já em uso"))
                continue
            tombos_existentes.update(tombos)  # deduplica dentro do arquivo
        isbn = dados.get("isbn", "")
        if isbn:
            if isbn in isbns_existentes:
                pulados.append((num, f"ISBN {isbn} já cadastrado"))
                continue
            isbns_existentes.add(isbn)  # também deduplica dentro do arquivo
        validas.append(dict(
            titulo=titulo, autores=autores, isbn=isbn,
            editora=dados.get("editora", ""),
            categoria=dados.get("categoria", ""), ano=ano,
            edicao=dados.get("edicao", ""), sinopse=dados.get("sinopse", ""),
            quantidade_exemplares=quantidade,
            localizacao=dados.get("localizacao", ""),
            tombos=tombos,
        ))

    # Fase 2 — inserir tudo em UMA transação (rápido e tudo-ou-nada)
    livros = exemplares = 0
    if validas:
        with db_cursor() as cur:
            for item in validas:
                res = _inserir_livro_cur(cur, **item)
                livros += 1
                exemplares += len(res["exemplares"])
    registrar_auditoria(usuario_id, "IMPORTACAO_CSV",
                         f"livros={livros}; exemplares={exemplares}; "
                         f"pulados={len(pulados)}; erros={len(erros)}")
    return {"livros": livros, "exemplares": exemplares,
            "pulados": pulados, "erros": erros, "ajustes": ajustes}
