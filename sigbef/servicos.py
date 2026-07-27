"""
SIGBEF — Camada de serviços (regras de negócio).

Concentra as operações de negócio (cadastros, empréstimos, devoluções e
consultas) em funções puras, separadas da camada de UI.
"""
from __future__ import annotations

import base64
import csv
import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from .auth import gerar_hash
from .barcode_util import gerar_codigo_exemplar, gerar_codigo_usuario
from .database import db_cursor, get_config, set_config, registrar_auditoria


class RegraNegocioError(Exception):
    """Erro tratado de regra de negócio (mensagens amigáveis ao usuário)."""


def _codigo_barras_unico(cur, tabela: str, gerador) -> str:
    """Gera um código de barras garantidamente único na tabela.

    Os geradores usam timestamp por segundo + sufixo aleatório de 4
    dígitos; em cadastros em lote (muitos códigos no mesmo segundo)
    colisões são possíveis — aqui a unicidade é conferida no banco
    antes de usar, com novo sorteio em caso de choque.
    """
    for _ in range(1000):
        codigo = gerador()
        cur.execute(f"SELECT 1 FROM {tabela} WHERE codigo_barras = ?",
                    (codigo,))
        if not cur.fetchone():
            return codigo
    raise RegraNegocioError(
        "Não foi possível gerar um código de barras único. Tente novamente.")


# ---------------------------------------------------------------------------
# Livros e Exemplares
# ---------------------------------------------------------------------------
def cadastrar_livro(
    *,
    titulo: str,
    autores: list[str],
    isbn: str = "",
    editora: str = "",
    categoria: str = "",
    ano: Optional[int] = None,
    edicao: str = "",
    sinopse: str = "",
    quantidade_exemplares: int = 1,
    localizacao: str = "",
    usuario_id: Optional[int] = None,
) -> dict:
    """Cadastra um livro com seus autores e exemplares iniciais.

    Retorna um dict com `livro_id` e `exemplares` (lista de tuplas
    (id, codigo_barras)).
    """
    with db_cursor() as cur:
        res = _inserir_livro_cur(
            cur, titulo=titulo, autores=autores, isbn=isbn, editora=editora,
            categoria=categoria, ano=ano, edicao=edicao, sinopse=sinopse,
            quantidade_exemplares=quantidade_exemplares,
            localizacao=localizacao,
        )
    registrar_auditoria(usuario_id, "CADASTRO_LIVRO",
                         f"livro_id={res['livro_id']}; "
                         f"exemplares={len(res['exemplares'])}")
    return res


def _upsert_nome(cur, tabela: str, nome: str) -> int:
    """INSERT OR IGNORE + SELECT id dentro da transação corrente (usado
    pelo cadastro unitário e pela importação em massa)."""
    cur.execute(f"INSERT OR IGNORE INTO {tabela}(nome) VALUES (?)", (nome,))
    cur.execute(f"SELECT id FROM {tabela} WHERE nome = ?", (nome,))
    return cur.fetchone()["id"]


def _inserir_livro_cur(
    cur,
    *,
    titulo: str,
    autores: list[str],
    isbn: str = "",
    editora: str = "",
    categoria: str = "",
    ano: Optional[int] = None,
    edicao: str = "",
    sinopse: str = "",
    quantidade_exemplares: int = 1,
    localizacao: str = "",
    tombos: Optional[list[str]] = None,
) -> dict:
    """Núcleo do cadastro de livro dentro de uma transação já aberta.

    Compartilhado entre o cadastro unitário e a importação CSV — na
    importação, milhares de livros entram numa transação única (um
    commit por livro limitava a ~35 livros/s no teste de estresse).

    `tombos`, quando informado, atribui um número de tombo próprio a
    cada exemplar (na ordem), em vez do tombo gerado automaticamente.
    Deve ter exatamente `quantidade_exemplares` itens.
    """
    titulo = (titulo or "").strip()
    if not titulo:
        raise RegraNegocioError("Título é obrigatório.")
    autores_limpos = [a.strip() for a in (autores or []) if a and a.strip()]
    if not autores_limpos:
        raise RegraNegocioError("Informe pelo menos um autor.")
    if quantidade_exemplares < 1:
        raise RegraNegocioError("Cadastre pelo menos um exemplar.")
    tombos_limpos = [t.strip() for t in (tombos or []) if t and t.strip()]
    if tombos_limpos and len(tombos_limpos) != quantidade_exemplares:
        raise RegraNegocioError(
            f"Número de tombos ({len(tombos_limpos)}) diferente da "
            f"quantidade de exemplares ({quantidade_exemplares}).")

    editora = (editora or "").strip()
    categoria = (categoria or "").strip()
    editora_id = _upsert_nome(cur, "editora", editora) if editora else None
    categoria_id = _upsert_nome(cur, "categoria", categoria) if categoria else None
    autor_ids = [_upsert_nome(cur, "autor", a) for a in autores_limpos]

    cur.execute(
        """INSERT INTO livro
            (titulo, isbn, editora_id, categoria_id, ano_publicacao, edicao, sinopse)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (titulo, isbn or None, editora_id, categoria_id, ano, edicao or None, sinopse or None),
    )
    livro_id = cur.lastrowid
    for autor_id in autor_ids:
        cur.execute(
            "INSERT OR IGNORE INTO livro_autor(livro_id, autor_id) VALUES (?, ?)",
            (livro_id, autor_id),
        )

    exemplares: list[tuple[int, str]] = []
    for i in range(1, quantidade_exemplares + 1):
        codigo = _codigo_barras_unico(cur, "exemplar", gerar_codigo_exemplar)
        if tombos_limpos:
            tombo = tombos_limpos[i - 1]
        else:
            tombo = f"{livro_id:05d}-{i:03d}"
        cur.execute(
            """INSERT INTO exemplar(livro_id, codigo_barras, numero_tombo, localizacao)
                   VALUES (?, ?, ?, ?)""",
            (livro_id, codigo, tombo, localizacao or None),
        )
        exemplares.append((cur.lastrowid, codigo))

    return {"livro_id": livro_id, "exemplares": exemplares}


def adicionar_exemplares(livro_id: int, quantidade: int, localizacao: str = "",
                         usuario_id: Optional[int] = None) -> list[tuple[int, str]]:
    if quantidade < 1:
        raise RegraNegocioError("Quantidade deve ser >= 1.")
    exemplares: list[tuple[int, str]] = []
    from . import reservas
    with db_cursor() as cur:
        cur.execute("SELECT id FROM livro WHERE id = ? AND ativo = 1", (livro_id,))
        if not cur.fetchone():
            raise RegraNegocioError("Livro não encontrado.")
        cur.execute("SELECT COUNT(*) AS qtd FROM exemplar WHERE livro_id = ?", (livro_id,))
        existente = cur.fetchone()["qtd"]
        for i in range(1, quantidade + 1):
            codigo = _codigo_barras_unico(cur, "exemplar", gerar_codigo_exemplar)
            tombo = f"{livro_id:05d}-{(existente + i):03d}"
            cur.execute(
                """INSERT INTO exemplar(livro_id, codigo_barras, numero_tombo, localizacao)
                       VALUES (?, ?, ?, ?)""",
                (livro_id, codigo, tombo, localizacao or None),
            )
            exemplares.append((cur.lastrowid, codigo))
            # Exemplar novo de livro com fila já sai separado pra ela
            reservas._promover_fila_cur(cur, livro_id, cur.lastrowid)

    registrar_auditoria(usuario_id, "ADD_EXEMPLARES",
                         f"livro_id={livro_id}; novos={len(exemplares)}")
    return exemplares


def listar_categorias() -> list[str]:
    """Nomes de categorias em uso no acervo, ordenados (para filtros de busca)."""
    with db_cursor() as cur:
        cur.execute("SELECT nome FROM categoria ORDER BY nome")
        return [r["nome"] for r in cur.fetchall()]


def listar_autores() -> list[str]:
    """Nomes de autores em uso no acervo, ordenados (para filtros de busca)."""
    with db_cursor() as cur:
        cur.execute("SELECT nome FROM autor ORDER BY nome")
        return [r["nome"] for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Brasão da instituição (imagem opcional, exibida no login e no cabeçalho)
# ---------------------------------------------------------------------------
# Guardado em base64 na tabela de configuração: o backup do banco (1
# arquivo) continua levando tudo junto, sem caminho de arquivo frágil.
# PNG e GIF apenas: são os formatos que o tk.PhotoImage lê nativamente
# no Tk 8.6, mantendo a regra de zero dependência externa.
BRASAO_CHAVE = "BRASAO_INSTITUICAO"
BRASAO_LIMITE_BYTES = 512 * 1024

_MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
_MAGIC_GIF = (b"GIF87a", b"GIF89a")


def salvar_brasao(caminho: str, usuario_id: Optional[int] = None) -> None:
    """Valida e grava a imagem do brasão da instituição.

    Levanta RegraNegocioError com mensagem amigável se o arquivo não
    for PNG/GIF ou passar do limite de tamanho.
    """
    dados = Path(caminho).read_bytes()
    eh_png = dados[:8] == _MAGIC_PNG
    eh_gif = dados[:6] in _MAGIC_GIF
    if not (eh_png or eh_gif):
        raise RegraNegocioError(
            "Formato não suportado. Use uma imagem PNG ou GIF "
            "(JPEG não é aceito).")
    if len(dados) > BRASAO_LIMITE_BYTES:
        kb = BRASAO_LIMITE_BYTES // 1024
        raise RegraNegocioError(
            f"Imagem muito grande ({len(dados) // 1024} KB). "
            f"O limite é {kb} KB; reduza a imagem e tente de novo.")
    set_config(BRASAO_CHAVE, base64.b64encode(dados).decode("ascii"))
    registrar_auditoria(usuario_id, "BRASAO_DEFINIDO",
                         f"{len(dados)} bytes")


def obter_brasao() -> Optional[str]:
    """Base64 do brasão configurado, ou None se não houver."""
    valor = get_config(BRASAO_CHAVE, "")
    return valor or None


def remover_brasao(usuario_id: Optional[int] = None) -> None:
    set_config(BRASAO_CHAVE, "")
    registrar_auditoria(usuario_id, "BRASAO_REMOVIDO", "")


def _filtro_de_livros(termo: str, apenas_disponiveis: bool,
                      categoria: Optional[str], autor: Optional[str]):
    """Monta o WHERE compartilhado entre listar e contar.

    Existe para os dois nunca discordarem: um total que não bate com a
    lista é pior que total nenhum, porque a pessoa fica procurando o
    livro que o contador prometeu.
    """
    termo_like = f"%{termo.strip()}%" if termo else "%"
    params: list = [termo_like, termo_like, termo_like, termo_like]
    onde = """l.ativo = 1
          AND (
                l.titulo LIKE ?
                OR IFNULL(l.isbn, '') LIKE ?
                OR EXISTS (
                    SELECT 1 FROM livro_autor la
                    JOIN autor a ON a.id = la.autor_id
                    WHERE la.livro_id = l.id AND a.nome LIKE ?
                )
                OR IFNULL(c.nome, '') LIKE ?
              )"""
    if categoria:
        onde += " AND c.nome = ?"
        params.append(categoria)
    if autor:
        onde += (" AND EXISTS (SELECT 1 FROM livro_autor la2 "
                 "JOIN autor a2 ON a2.id = la2.autor_id "
                 "WHERE la2.livro_id = l.id AND a2.nome = ?)")
        params.append(autor)
    if apenas_disponiveis:
        # No SQL, não em Python: com LIMIT, filtrar depois cortaria o
        # bloco antes de saber quais linhas sobrevivem, e a página viria
        # com menos livros do que cabia nela.
        onde += (" AND EXISTS (SELECT 1 FROM exemplar ex2 "
                 "WHERE ex2.livro_id = l.id AND ex2.status = 'DISPONIVEL')")
    return onde, params


def contar_livros(termo: str = "", apenas_disponiveis: bool = False,
                  categoria: Optional[str] = None,
                  autor: Optional[str] = None) -> int:
    """Quantos livros a busca encontra, sem trazer nenhum.

    Barato porque não monta os agregados de exemplar nem os autores:
    é a contagem que a tela mostra ao lado da página exibida.
    """
    onde, params = _filtro_de_livros(termo, apenas_disponiveis,
                                      categoria, autor)
    with db_cursor() as cur:
        cur.execute(f"""SELECT COUNT(*) FROM livro l
                        LEFT JOIN categoria c ON c.id = l.categoria_id
                        WHERE {onde}""", params)
        return cur.fetchone()[0]


def listar_livros(termo: str = "", apenas_disponiveis: bool = False,
                  categoria: Optional[str] = None,
                  autor: Optional[str] = None,
                  limite: Optional[int] = None,
                  offset: int = 0) -> list[dict]:
    """Lista livros com agregados de exemplares (total e disponíveis).

    `termo` faz busca livre (título, ISBN, autor, categoria). `categoria`
    e `autor` são filtros exatos e opcionais (busca avançada); omitidos,
    o resultado é idêntico à busca simples.

    `limite` corta o resultado no banco. Cada linha carrega três
    subconsultas (autores, total de exemplares, disponíveis), então o
    custo é por linha devolvida: pedir 50 de um acervo de 250 mil custa
    50 vezes três, não 250 mil vezes três. Sem limite, o comportamento é
    o de antes — quem exporta CSV precisa mesmo de tudo.
    """
    onde, params = _filtro_de_livros(termo, apenas_disponiveis,
                                      categoria, autor)
    paginacao = ""
    if limite is not None:
        paginacao = " LIMIT ? OFFSET ?"
        params = params + [int(limite), int(offset)]
    sql = f"""
        SELECT
            l.id,
            l.titulo,
            l.isbn,
            l.ano_publicacao,
            l.edicao,
            COALESCE(c.nome, '') AS categoria,
            COALESCE(e.nome, '') AS editora,
            (
                SELECT GROUP_CONCAT(a.nome, ', ')
                FROM livro_autor la
                JOIN autor a ON a.id = la.autor_id
                WHERE la.livro_id = l.id
            ) AS autores,
            -- Baixado não conta: a pergunta da tela é quantos exemplares
            -- a biblioteca tem, e o que foi extraviado ou descartado não
            -- está mais lá. O histórico de empréstimo deles continua.
            (SELECT COUNT(*) FROM exemplar ex
                WHERE ex.livro_id = l.id AND ex.status != 'BAIXADO') AS total_exemplares,
            (SELECT COUNT(*) FROM exemplar ex
                WHERE ex.livro_id = l.id AND ex.status = 'DISPONIVEL') AS disponiveis
        FROM livro l
        LEFT JOIN categoria c ON c.id = l.categoria_id
        LEFT JOIN editora e ON e.id = l.editora_id
        WHERE {onde}
        ORDER BY l.titulo, l.id{paginacao}
    """
    with db_cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def detalhes_livro(livro_id: int) -> Optional[dict]:
    with db_cursor() as cur:
        cur.execute(
            """SELECT l.*, c.nome AS categoria_nome, e.nome AS editora_nome
               FROM livro l
               LEFT JOIN categoria c ON c.id = l.categoria_id
               LEFT JOIN editora e ON e.id = l.editora_id
               WHERE l.id = ? AND l.ativo = 1""",
            (livro_id,),
        )
        livro = cur.fetchone()
        if not livro:
            return None
        livro = dict(livro)
        cur.execute(
            """SELECT a.nome FROM livro_autor la
               JOIN autor a ON a.id = la.autor_id
               WHERE la.livro_id = ? ORDER BY a.nome""",
            (livro_id,),
        )
        livro["autores"] = [r["nome"] for r in cur.fetchall()]
        cur.execute(
            """SELECT id, codigo_barras, numero_tombo, localizacao, status,
                      motivo_baixa, data_baixa
               FROM exemplar WHERE livro_id = ? ORDER BY numero_tombo""",
            (livro_id,),
        )
        livro["exemplares"] = [dict(r) for r in cur.fetchall()]
    return livro


def listar_exemplares_disponiveis(termo: str = "") -> list[dict]:
    """Lista todos os exemplares disponíveis para empréstimo (com info do livro).

    Útil para alimentar o diálogo "Selecionar exemplar..." na tela de
    empréstimo. Aceita termo de busca opcional para filtrar por título,
    autor ou tombo.
    """
    termo_like = f"%{termo.strip()}%" if termo else "%"
    with db_cursor() as cur:
        cur.execute(
            """SELECT ex.id, ex.codigo_barras, ex.numero_tombo,
                       ex.localizacao, l.titulo,
                       (SELECT GROUP_CONCAT(a.nome, ', ')
                          FROM livro_autor la JOIN autor a ON a.id = la.autor_id
                          WHERE la.livro_id = l.id) AS autores
               FROM exemplar ex
               JOIN livro l ON l.id = ex.livro_id
               WHERE ex.status = 'DISPONIVEL' AND l.ativo = 1
                 AND (
                       l.titulo LIKE ?
                       OR ex.numero_tombo LIKE ?
                       OR ex.codigo_barras LIKE ?
                       OR EXISTS (
                            SELECT 1 FROM livro_autor la
                            JOIN autor a ON a.id = la.autor_id
                            WHERE la.livro_id = l.id AND a.nome LIKE ?)
                     )
               ORDER BY l.titulo, ex.numero_tombo""",
            (termo_like, termo_like, termo_like, termo_like),
        )
        return [dict(r) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Importação de acervo via CSV
# ---------------------------------------------------------------------------
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


def listar_exemplares_para_etiquetas(termo: str = "") -> list[dict]:
    """Exemplares ativos (não baixados) com o título do livro, para a
    impressão de etiquetas em massa. O filtro segue a mesma semântica
    da busca do acervo (título, ISBN ou autor); termo vazio = tudo."""
    termo_like = f"%{termo.strip()}%" if termo else "%"
    with db_cursor() as cur:
        cur.execute(
            """SELECT l.titulo, ex.codigo_barras, ex.numero_tombo
               FROM exemplar ex
               JOIN livro l ON l.id = ex.livro_id
               WHERE l.ativo = 1 AND ex.status != 'BAIXADO'
                 AND (
                       l.titulo LIKE ?
                       OR IFNULL(l.isbn, '') LIKE ?
                       OR EXISTS (
                            SELECT 1 FROM livro_autor la
                            JOIN autor a ON a.id = la.autor_id
                            WHERE la.livro_id = l.id AND a.nome LIKE ?)
                     )
               ORDER BY l.titulo, ex.numero_tombo""",
            (termo_like, termo_like, termo_like),
        )
        return [dict(r) for r in cur.fetchall()]


def excluir_livro(livro_id: int, usuario_id: Optional[int] = None) -> None:
    """Exclusão lógica do livro (e de seus exemplares)."""
    with db_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS abertos FROM emprestimo e "
            "JOIN exemplar ex ON ex.id = e.exemplar_id "
            "WHERE ex.livro_id = ? AND e.data_devolucao IS NULL",
            (livro_id,),
        )
        if cur.fetchone()["abertos"]:
            raise RegraNegocioError(
                "Existem empréstimos em aberto para este livro. Devolva-os primeiro."
            )
        cur.execute("UPDATE livro SET ativo = 0 WHERE id = ?", (livro_id,))
        cur.execute(
            "UPDATE exemplar SET status = 'BAIXADO' "
            "WHERE livro_id = ? AND status = 'DISPONIVEL'",
            (livro_id,),
        )
    registrar_auditoria(usuario_id, "EXCLUSAO_LIVRO", f"livro_id={livro_id}")


def _atraso_e_multa(data_prevista: str,
                     ate: Optional[date] = None) -> tuple[int, float]:
    """Dias de atraso e multa correspondente, na regra da escola.

    Uma função só porque agora há dois caminhos que encerram um
    empréstimo — a devolução no balcão e a baixa de um exemplar perdido —
    e a conta precisa ser a mesma nos dois. O teto (`MULTA_TETO`) existe
    para o esquecimento de um ano não virar uma dívida impagável.
    """
    prevista = datetime.strptime(data_prevista, "%Y-%m-%d").date()
    dias = max(((ate or date.today()) - prevista).days, 0)
    if not dias:
        return 0, 0.0
    multa = min(_config_float("MULTA_POR_DIA", 1.5) * dias,
                _config_float("MULTA_TETO", 60.0))
    return dias, round(multa, 2)


# Por que o exemplar saiu do acervo. A diferença importa na hora de
# repor: extraviado costuma virar cobrança, danificado vira compra,
# descartado foi decisão da escola.
MOTIVOS_BAIXA = {
    "EXTRAVIADO": "Extraviado (não foi encontrado)",
    "DANIFICADO": "Danificado sem conserto",
    "DESCARTADO": "Descartado (desatualizado ou fora de uso)",
    "DOADO": "Doado ou transferido",
}


def baixar_exemplar(codigo: str, motivo: str,
                     usuario_id: Optional[int] = None) -> dict:
    """Tira um exemplar do acervo, sem mexer nos outros do mesmo título.

    Antes só existia `excluir_livro`, que baixa o título inteiro: um
    exemplar rasgado obrigava a escolher entre sumir com o livro todo ou
    deixar o sistema dizendo que ele está na estante.

    Exemplar **emprestado também pode ser baixado**, e esse é o caso que
    mais acontece: o aluno perdeu o livro. Exigir a devolução primeiro
    seria exigir o impossível, então o empréstimo é encerrado aqui, com
    a data de hoje, e a multa de atraso é calculada se houver — o que a
    escola faz depois com a cobrança é decisão dela, fora do sistema.
    """
    motivo = (motivo or "").strip().upper()
    if motivo not in MOTIVOS_BAIXA:
        raise RegraNegocioError(
            "Informe por que o exemplar está saindo do acervo: "
            + ", ".join(MOTIVOS_BAIXA))

    ex = localizar_exemplar(codigo)
    if not ex:
        raise RegraNegocioError(
            "Exemplar não encontrado. Confira o código de barras ou o tombo.")
    if ex["status"] == "BAIXADO":
        raise RegraNegocioError(
            f"Este exemplar já foi baixado do acervo.")

    hoje = date.today().isoformat()
    multa = 0.0
    with db_cursor() as cur:
        cur.execute("""SELECT id, usuario_id, data_prevista FROM emprestimo
                        WHERE exemplar_id = ? AND data_devolucao IS NULL
                        LIMIT 1""", (ex["id"],))
        emp = cur.fetchone()
        if emp:
            _, multa = _atraso_e_multa(emp["data_prevista"])
            cur.execute("""UPDATE emprestimo
                              SET data_devolucao = ?, multa = ?
                            WHERE id = ?""",
                        (hoje, multa, emp["id"]))

        cur.execute("""UPDATE exemplar
                          SET status = 'BAIXADO', motivo_baixa = ?,
                              data_baixa = ?
                        WHERE id = ?""", (motivo, hoje, ex["id"]))

    registrar_auditoria(
        usuario_id, "BAIXA_EXEMPLAR",
        f"exemplar={ex['codigo_barras']} livro={ex['titulo']} motivo={motivo}"
        + (f" emprestimo_encerrado={emp['id']}" if emp else ""))

    return {
        "exemplar_id": ex["id"],
        "codigo_barras": ex["codigo_barras"],
        "titulo": ex["titulo"],
        "motivo": motivo,
        "estava_emprestado": bool(emp),
        "multa": multa,
    }


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------
def cadastrar_usuario(
    *,
    nome: str,
    matricula: str,
    perfil: str,
    senha: str,
    email: str = "",
    telefone: str = "",
    turma: str = "",
    gerar_cartao: bool = True,
    usuario_id_executor: Optional[int] = None,
) -> dict:
    nome = (nome or "").strip()
    matricula = (matricula or "").strip()
    turma = (turma or "").strip()
    if not nome or not matricula:
        raise RegraNegocioError("Nome e matrícula são obrigatórios.")
    if perfil not in ("ALUNO", "PROFESSOR", "BIBLIOTECARIO", "ADMINISTRADOR"):
        raise RegraNegocioError("Perfil inválido.")
    if not senha or len(senha) < 4:
        raise RegraNegocioError("Senha deve ter pelo menos 4 caracteres.")

    senha_hash = gerar_hash(senha)
    with db_cursor() as cur:
        cur.execute("SELECT 1 FROM usuario WHERE matricula = ?", (matricula,))
        if cur.fetchone():
            raise RegraNegocioError("Já existe um usuário com esta matrícula.")
        cartao = (_codigo_barras_unico(cur, "usuario", gerar_codigo_usuario)
                  if gerar_cartao else None)
        cur.execute(
            """INSERT INTO usuario(nome, matricula, email, telefone, turma,
                                   perfil, senha_hash, codigo_barras)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (nome, matricula, email or None, telefone or None,
             turma or None, perfil, senha_hash, cartao),
        )
        novo_id = cur.lastrowid
    registrar_auditoria(usuario_id_executor, "CADASTRO_USUARIO",
                         f"id={novo_id}; perfil={perfil}")
    return {"id": novo_id, "matricula": matricula, "codigo_barras": cartao}


def listar_usuarios(termo: str = "") -> list[dict]:
    termo_like = f"%{termo.strip()}%" if termo else "%"
    with db_cursor() as cur:
        cur.execute(
            """SELECT id, nome, matricula, email, turma, perfil,
                      codigo_barras, ativo
               FROM usuario
               WHERE nome LIKE ? OR matricula LIKE ? OR IFNULL(email,'') LIKE ?
                  OR IFNULL(turma,'') LIKE ?
               ORDER BY nome""",
            (termo_like, termo_like, termo_like, termo_like),
        )
        return [dict(r) for r in cur.fetchall()]


def alterar_senha(usuario_id: int, nova_senha: str) -> None:
    if not nova_senha or len(nova_senha) < 4:
        raise RegraNegocioError("Senha deve ter pelo menos 4 caracteres.")
    with db_cursor() as cur:
        cur.execute(
            "UPDATE usuario SET senha_hash = ? WHERE id = ?",
            (gerar_hash(nova_senha), usuario_id),
        )
    registrar_auditoria(usuario_id, "TROCA_SENHA", "")


def alternar_status_usuario(usuario_id: int, ativo: bool,
                            executor_id: Optional[int] = None) -> None:
    with db_cursor() as cur:
        cur.execute("UPDATE usuario SET ativo = ? WHERE id = ?",
                    (1 if ativo else 0, usuario_id))
    # Auditoria registra QUEM executou; o usuário afetado vai no detalhe
    registrar_auditoria(executor_id, "STATUS_USUARIO",
                         f"alvo={usuario_id}; ativo={'sim' if ativo else 'nao'}")


def obter_usuario(usuario_id: int) -> dict:
    with db_cursor() as cur:
        cur.execute(
            """SELECT id, nome, matricula, email, telefone, turma, perfil,
                      codigo_barras, ativo
               FROM usuario WHERE id = ?""",
            (usuario_id,),
        )
        row = cur.fetchone()
    if not row:
        raise RegraNegocioError("Usuário não encontrado.")
    return dict(row)


def atualizar_usuario(
    usuario_id: int,
    *,
    nome: str,
    perfil: str,
    email: str = "",
    telefone: str = "",
    turma: str = "",
    executor_id: Optional[int] = None,
) -> None:
    """Atualiza os dados cadastrais de um usuário (nome, contato, turma
    e perfil). A matrícula é fixa; senha tem fluxo próprio."""
    nome = (nome or "").strip()
    if not nome:
        raise RegraNegocioError("Nome é obrigatório.")
    if perfil not in ("ALUNO", "PROFESSOR", "BIBLIOTECARIO", "ADMINISTRADOR"):
        raise RegraNegocioError("Perfil inválido.")
    with db_cursor() as cur:
        cur.execute("SELECT perfil FROM usuario WHERE id = ?", (usuario_id,))
        row = cur.fetchone()
        if not row:
            raise RegraNegocioError("Usuário não encontrado.")
        if (executor_id is not None and usuario_id == executor_id
                and row["perfil"] != perfil):
            raise RegraNegocioError(
                "Você não pode alterar o próprio perfil de acesso.")
        cur.execute(
            """UPDATE usuario SET nome = ?, email = ?, telefone = ?,
                                  turma = ?, perfil = ?
               WHERE id = ?""",
            (nome, (email or "").strip() or None,
             (telefone or "").strip() or None,
             (turma or "").strip() or None, perfil, usuario_id),
        )
    registrar_auditoria(executor_id, "EDICAO_USUARIO",
                         f"id={usuario_id}; perfil={perfil}")


def excluir_usuario(usuario_id: int, executor_id: Optional[int] = None) -> None:
    """Exclui definitivamente um usuário sem histórico de empréstimos.

    Quem já emprestou algum dia não pode ser excluído (o histórico seria
    perdido) — nesse caso use `alternar_status_usuario` para bloquear o
    acesso preservando os registros.
    """
    if executor_id is not None and usuario_id == executor_id:
        raise RegraNegocioError("Você não pode excluir o próprio usuário logado.")
    with db_cursor() as cur:
        cur.execute("SELECT matricula FROM usuario WHERE id = ?", (usuario_id,))
        row = cur.fetchone()
        if not row:
            raise RegraNegocioError("Usuário não encontrado.")
        cur.execute(
            "SELECT COUNT(*) AS n FROM emprestimo WHERE usuario_id = ?",
            (usuario_id,),
        )
        if cur.fetchone()["n"]:
            raise RegraNegocioError(
                "Este usuário possui histórico de empréstimos e não pode ser "
                "excluído. Use 'Ativar/Desativar' para bloquear o acesso "
                "preservando o histórico."
            )
        # Desvincula as entradas de auditoria (o log em si é preservado)
        cur.execute("UPDATE auditoria SET usuario_id = NULL WHERE usuario_id = ?",
                    (usuario_id,))
        cur.execute("DELETE FROM usuario WHERE id = ?", (usuario_id,))
    registrar_auditoria(executor_id, "EXCLUSAO_USUARIO",
                         f"id={usuario_id}; matricula={row['matricula']}")


def gerar_cartao_usuario(usuario_id: int,
                          executor_id: Optional[int] = None) -> str:
    """Garante que o usuário tenha código de barras de cartão e o retorna."""
    with db_cursor() as cur:
        cur.execute("SELECT codigo_barras FROM usuario WHERE id = ?",
                    (usuario_id,))
        row = cur.fetchone()
        if not row:
            raise RegraNegocioError("Usuário não encontrado.")
        if row["codigo_barras"]:
            return row["codigo_barras"]
        codigo = _codigo_barras_unico(cur, "usuario", gerar_codigo_usuario)
        cur.execute("UPDATE usuario SET codigo_barras = ? WHERE id = ?",
                    (codigo, usuario_id))
    registrar_auditoria(executor_id, "CARTAO_GERADO", f"usuario_id={usuario_id}")
    return codigo


# ---------------------------------------------------------------------------
# Empréstimos
# ---------------------------------------------------------------------------
def _config_int(chave: str, default: int) -> int:
    try:
        return int(get_config(chave) or default)
    except (TypeError, ValueError):
        return default


def _config_float(chave: str, default: float) -> float:
    try:
        return float(get_config(chave) or default)
    except (TypeError, ValueError):
        return default


def _prazo_para_perfil(perfil: str) -> int:
    if perfil == "PROFESSOR":
        return _config_int("PRAZO_PROFESSOR_DIAS", 14)
    return _config_int("PRAZO_ALUNO_DIAS", 7)


def _limite_para_perfil(perfil: str) -> int:
    if perfil == "PROFESSOR":
        return _config_int("LIMITE_PROFESSOR", 5)
    return _config_int("LIMITE_ALUNO", 3)


@dataclass
class StatusUsuario:
    em_aberto: int
    multas_em_aberto: float
    pode_pegar: bool
    motivo: str = ""
    limite: int = 0  # quantos empréstimos simultâneos o perfil permite


def status_usuario(usuario_id: int) -> StatusUsuario:
    """Verifica se o usuário pode realizar novos empréstimos."""
    with db_cursor() as cur:
        cur.execute(
            "SELECT perfil, ativo FROM usuario WHERE id = ?",
            (usuario_id,),
        )
        u = cur.fetchone()
        if not u:
            return StatusUsuario(0, 0.0, False, "Usuário não encontrado.")
        if not u["ativo"]:
            return StatusUsuario(0, 0.0, False, "Conta desativada.")

        cur.execute(
            "SELECT COUNT(*) AS qt FROM emprestimo "
            "WHERE usuario_id = ? AND data_devolucao IS NULL",
            (usuario_id,),
        )
        em_aberto = cur.fetchone()["qt"]
        cur.execute(
            "SELECT IFNULL(SUM(multa),0) AS m FROM emprestimo "
            "WHERE usuario_id = ? AND multa > 0",
            (usuario_id,),
        )
        multa_aberta = float(cur.fetchone()["m"] or 0)
        cur.execute(
            """SELECT COUNT(*) AS qt FROM emprestimo
               WHERE usuario_id = ? AND data_devolucao IS NULL
               AND date(data_prevista) < date('now','localtime')""",
            (usuario_id,),
        )
        atrasados = cur.fetchone()["qt"]

    limite = _limite_para_perfil(u["perfil"])
    if atrasados:
        return StatusUsuario(em_aberto, multa_aberta, False,
                              f"Há {atrasados} exemplar(es) em atraso.", limite)
    if multa_aberta > 0:
        return StatusUsuario(em_aberto, multa_aberta, False,
                              f"Há multas em aberto: R$ {multa_aberta:.2f}.", limite)
    if em_aberto >= limite:
        return StatusUsuario(em_aberto, multa_aberta, False,
                              f"Limite de {limite} empréstimos atingido.", limite)
    return StatusUsuario(em_aberto, multa_aberta, True,
                          f"OK: {em_aberto} de {limite} empréstimos em uso.", limite)


def localizar_exemplar(termo: str) -> Optional[dict]:
    """Busca um exemplar por código de barras OU número de tombo.

    Aceita os dois formatos para deixar o sistema mais tolerante a
    digitação manual (o código de barras é longo).
    """
    termo = (termo or "").strip()
    if not termo:
        return None
    with db_cursor() as cur:
        cur.execute(
            """SELECT ex.id, ex.status, ex.codigo_barras, ex.numero_tombo,
                       l.titulo, l.id AS livro_id
               FROM exemplar ex JOIN livro l ON l.id = ex.livro_id
               WHERE ex.codigo_barras = ? OR ex.numero_tombo = ?
               LIMIT 1""",
            (termo, termo),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def localizar_usuario(termo: str) -> Optional[dict]:
    """Busca usuário por matrícula OU código de barras do cartão."""
    termo = (termo or "").strip()
    if not termo:
        return None
    with db_cursor() as cur:
        cur.execute(
            """SELECT id, nome, matricula, perfil, ativo, codigo_barras
               FROM usuario
               WHERE matricula = ? OR codigo_barras = ?
               LIMIT 1""",
            (termo, termo),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def realizar_emprestimo(*, codigo_exemplar: str, matricula_usuario: str,
                         origem: str = "BALCAO",
                         operador_id: Optional[int] = None) -> dict:
    """Registra um empréstimo. Aceita código de barras OU tombo do exemplar
    e matrícula OU código de barras do cartão do usuário."""
    if origem not in ("BALCAO", "AUTOATENDIMENTO"):
        raise RegraNegocioError("Origem inválida.")
    codigo = (codigo_exemplar or "").strip()
    matr = (matricula_usuario or "").strip()
    if not codigo or not matr:
        raise RegraNegocioError("Informe o código do exemplar e a matrícula.")

    u = localizar_usuario(matr)
    if not u or not u["ativo"]:
        raise RegraNegocioError("Usuário não encontrado ou inativo.")

    ex = localizar_exemplar(codigo)
    if not ex:
        raise RegraNegocioError(
            "Exemplar não encontrado. Confira o código de barras ou o tombo "
            "(use o botão 'Selecionar...' para escolher na lista)."
        )
    if ex["status"] not in ("DISPONIVEL", "RESERVADO"):
        raise RegraNegocioError(
            f"Exemplar '{ex['titulo']}' não está disponível "
            f"(status: {ex['status']})."
        )

    st = status_usuario(u["id"])
    if not st.pode_pegar:
        raise RegraNegocioError(st.motivo)

    prazo = _prazo_para_perfil(u["perfil"])
    data_prevista = (date.today() + timedelta(days=prazo)).isoformat()

    from . import reservas
    with db_cursor() as cur:
        reservas._expirar_vencidas_cur(cur)
        # Exemplar separado por reserva só sai com o dono da vez
        cur.execute(
            "SELECT id, usuario_id FROM reserva "
            "WHERE exemplar_id = ? AND status = 'ATIVA'",
            (ex["id"],),
        )
        res_ativa = cur.fetchone()
        if res_ativa and res_ativa["usuario_id"] != u["id"]:
            raise RegraNegocioError(
                f"Exemplar '{ex['titulo']}' está reservado para outro "
                "usuário da fila de espera."
            )
        # Trava atômica contra corrida (balcão e kiosk simultâneos): só a
        # primeira transação consegue mudar o status pra EMPRESTADO; as
        # demais não afetam linha nenhuma e são rejeitadas aqui.
        cur.execute(
            "UPDATE exemplar SET status = 'EMPRESTADO' "
            "WHERE id = ? AND status IN ('DISPONIVEL', 'RESERVADO')",
            (ex["id"],),
        )
        if cur.rowcount != 1:
            raise RegraNegocioError(
                f"Exemplar '{ex['titulo']}' não está disponível "
                "(pode ter acabado de ser emprestado em outro terminal)."
            )
        if res_ativa:
            cur.execute("UPDATE reserva SET status = 'ATENDIDA' WHERE id = ?",
                        (res_ativa["id"],))
        cur.execute(
            """INSERT INTO emprestimo(exemplar_id, usuario_id, data_prevista, origem)
               VALUES (?, ?, ?, ?)""",
            (ex["id"], u["id"], data_prevista, origem),
        )
        emp_id = cur.lastrowid

    registrar_auditoria(operador_id or u["id"], "EMPRESTIMO",
                         f"emp_id={emp_id}; exemplar={ex['codigo_barras']}; usuario={u['matricula']}")
    return {
        "id": emp_id,
        "titulo": ex["titulo"],
        "codigo": ex["codigo_barras"],
        "tombo": ex["numero_tombo"],
        "data_prevista": data_prevista,
        "prazo_dias": prazo,
        "usuario_nome": u["nome"],
    }


def realizar_devolucao(*, codigo_exemplar: str,
                        operador_id: Optional[int] = None) -> dict:
    """Devolve um exemplar e calcula multa (se houver atraso).
    Aceita código de barras OU número de tombo."""
    codigo = (codigo_exemplar or "").strip()
    if not codigo:
        raise RegraNegocioError("Informe o código do exemplar.")

    ex_localizado = localizar_exemplar(codigo)
    if not ex_localizado:
        raise RegraNegocioError(
            "Exemplar não encontrado. Confira o código de barras ou o tombo."
        )

    from . import reservas
    with db_cursor() as cur:
        cur.execute(
            """SELECT e.id, e.usuario_id, e.data_prevista,
                       ex.id AS exemplar_id, l.id AS livro_id, l.titulo
               FROM emprestimo e
               JOIN exemplar ex ON ex.id = e.exemplar_id
               JOIN livro l ON l.id = ex.livro_id
               WHERE ex.id = ? AND e.data_devolucao IS NULL""",
            (ex_localizado["id"],),
        )
        emp = cur.fetchone()
        if not emp:
            raise RegraNegocioError(
                f"O exemplar '{ex_localizado['titulo']}' não está emprestado "
                "no momento."
            )

        dias_atraso, multa = _atraso_e_multa(emp["data_prevista"])

        cur.execute(
            "UPDATE emprestimo SET data_devolucao = datetime('now','localtime'), multa = ? "
            "WHERE id = ? AND data_devolucao IS NULL",
            (multa, emp["id"]),
        )
        if cur.rowcount != 1:
            raise RegraNegocioError(
                "Este exemplar acabou de ser devolvido em outro terminal."
            )
        cur.execute("UPDATE exemplar SET status = 'DISPONIVEL' WHERE id = ?",
                    (emp["exemplar_id"],))
        # Se o livro tem fila de espera, o exemplar já sai separado
        # pro primeiro da fila em vez de voltar pra prateleira
        reservas._expirar_vencidas_cur(cur)
        promovida = reservas._promover_fila_cur(
            cur, emp["livro_id"], emp["exemplar_id"])

    registrar_auditoria(operador_id or emp["usuario_id"], "DEVOLUCAO",
                         f"emp_id={emp['id']}; multa={multa:.2f}; atraso={dias_atraso}d")
    return {
        "titulo": emp["titulo"],
        "dias_atraso": dias_atraso,
        "multa": multa,
        "reservado_para": promovida["usuario_nome"] if promovida else None,
        "reserva_ate": promovida["disponivel_ate"] if promovida else None,
    }


def _motivo_para_nao_renovar(cur, emp) -> Optional[str]:
    """Regras de renovação, ou None quando pode renovar.

    Existe porque a renovação passou a ser feita também pelo aluno, no
    celular, sem ninguém no balcão para julgar o caso. Recebe o cursor
    já aberto para rodar dentro da mesma transação de quem chama.
    """
    if emp["data_prevista"] < date.today().isoformat():
        return ("O prazo deste livro já venceu. Passe na biblioteca "
                "para devolver ou renovar.")

    limite = _config_int("LIMITE_RENOVACOES", 2)
    if emp["renovacoes"] >= limite:
        return (f"Você já renovou este livro {emp['renovacoes']}x. "
                "Para continuar com ele, fale com a biblioteca.")

    cur.execute(
        """SELECT COUNT(*) AS n
             FROM reserva r JOIN exemplar ex ON ex.livro_id = r.livro_id
            WHERE ex.id = ? AND r.status = 'ATIVA'""",
        (emp["exemplar_id"],),
    )
    if cur.fetchone()["n"]:
        return ("Outro leitor está esperando por este livro na fila de "
                "reservas, então ele não pode ser renovado.")
    return None


def pode_renovar(emprestimo_id: int) -> tuple[bool, str]:
    """Diz se um empréstimo pode ser renovado e, se não, por quê.

    Usada pelo app para desabilitar o botão antes de tentar, e pela API
    para recusar com uma frase que o aluno entenda.
    """
    with db_cursor() as cur:
        cur.execute(
            """SELECT e.data_prevista, e.exemplar_id, e.renovacoes
                 FROM emprestimo e
                WHERE e.id = ? AND e.data_devolucao IS NULL""",
            (emprestimo_id,),
        )
        emp = cur.fetchone()
        if not emp:
            return False, "Empréstimo não encontrado."
        motivo = _motivo_para_nao_renovar(cur, emp)
    return (motivo is None), (motivo or "")


def renovar_emprestimo(emprestimo_id: int,
                       operador_id: Optional[int] = None,
                       *, validar_regras: bool = False) -> dict:
    """Estende o prazo de um empréstimo em aberto.

    No balcão (`validar_regras=False`) a bibliotecária continua podendo
    renovar em qualquer situação: ela tem o aluno na frente e o contexto
    que o sistema não tem. Pelo app o aluno decide sozinho, então ali as
    regras de `pode_renovar` são obrigatórias.
    """
    with db_cursor() as cur:
        cur.execute(
            """SELECT e.id, e.usuario_id, e.exemplar_id, e.data_prevista,
                       e.renovacoes, u.perfil
               FROM emprestimo e JOIN usuario u ON u.id = e.usuario_id
               WHERE e.id = ? AND e.data_devolucao IS NULL""",
            (emprestimo_id,),
        )
        emp = cur.fetchone()
        if not emp:
            raise RegraNegocioError("Empréstimo não encontrado.")

        if validar_regras:
            motivo = _motivo_para_nao_renovar(cur, emp)
            if motivo:
                raise RegraNegocioError(motivo)

        prazo = _prazo_para_perfil(emp["perfil"])
        nova_data = (date.today() + timedelta(days=prazo)).isoformat()
        cur.execute(
            "UPDATE emprestimo SET data_prevista = ?, "
            "renovacoes = renovacoes + 1 WHERE id = ?",
            (nova_data, emprestimo_id),
        )
    registrar_auditoria(operador_id or emp["usuario_id"], "RENOVACAO",
                         f"emp_id={emprestimo_id}; nova_prevista={nova_data}")
    return {"data_prevista": nova_data}


def listar_emprestimos_usuario(usuario_id: int,
                                somente_abertos: bool = False) -> list[dict]:
    sql = """
        SELECT e.id, l.titulo, ex.codigo_barras, e.data_emprestimo,
               e.data_prevista, e.data_devolucao, e.multa, e.origem,
               e.renovacoes
        FROM emprestimo e
        JOIN exemplar ex ON ex.id = e.exemplar_id
        JOIN livro l ON l.id = ex.livro_id
        WHERE e.usuario_id = ?
    """
    if somente_abertos:
        sql += " AND e.data_devolucao IS NULL"
    sql += " ORDER BY e.data_emprestimo DESC"
    with db_cursor() as cur:
        cur.execute(sql, (usuario_id,))
        return [dict(r) for r in cur.fetchall()]


def listar_emprestimos_em_aberto() -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            """SELECT e.id, u.nome AS usuario, u.matricula, u.turma,
                       l.titulo, ex.codigo_barras, e.data_emprestimo,
                       e.data_prevista,
                       (date(e.data_prevista) < date('now','localtime')) AS atrasado
                FROM emprestimo e
                JOIN exemplar ex ON ex.id = e.exemplar_id
                JOIN livro l ON l.id = ex.livro_id
                JOIN usuario u ON u.id = e.usuario_id
                WHERE e.data_devolucao IS NULL
                ORDER BY e.data_prevista""")
        return [dict(r) for r in cur.fetchall()]


def quitar_multa(emprestimo_id: int, operador_id: Optional[int] = None) -> None:
    with db_cursor() as cur:
        cur.execute("UPDATE emprestimo SET multa = 0 WHERE id = ?", (emprestimo_id,))
    registrar_auditoria(operador_id, "QUITAR_MULTA", f"emp_id={emprestimo_id}")


# ---------------------------------------------------------------------------
# Estatísticas / relatórios
# ---------------------------------------------------------------------------
def estatisticas() -> dict:
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS qt FROM livro WHERE ativo = 1")
        livros = cur.fetchone()["qt"]
        cur.execute("SELECT COUNT(*) AS qt FROM exemplar")
        exemplares = cur.fetchone()["qt"]
        cur.execute(
            "SELECT COUNT(*) AS qt FROM exemplar WHERE status = 'DISPONIVEL'")
        disponiveis = cur.fetchone()["qt"]
        cur.execute(
            "SELECT COUNT(*) AS qt FROM emprestimo WHERE data_devolucao IS NULL")
        emp_abertos = cur.fetchone()["qt"]
        cur.execute(
            """SELECT COUNT(*) AS qt FROM emprestimo
               WHERE data_devolucao IS NULL
               AND date(data_prevista) < date('now','localtime')""")
        atrasados = cur.fetchone()["qt"]
        cur.execute("SELECT COUNT(*) AS qt FROM usuario WHERE ativo = 1")
        usuarios = cur.fetchone()["qt"]
    return {
        "livros": livros,
        "exemplares": exemplares,
        "disponiveis": disponiveis,
        "emp_abertos": emp_abertos,
        "atrasados": atrasados,
        "usuarios": usuarios,
    }


def relatorio_inadimplentes() -> list[dict]:
    """Quem está impedido de pegar livro, e por quê (RF-052).

    Cobre as duas causas de bloqueio, não só a multa: `status_usuario`
    barra tanto quem deve dinheiro quanto quem está com exemplar
    atrasado, e uma lista que mostrasse só a primeira deixaria de fora
    justamente quem ainda está com o livro da escola em casa.

    Ordena pelo atraso mais antigo primeiro — é quem a bibliotecária
    precisa procurar primeiro.
    """
    with db_cursor() as cur:
        cur.execute(
            """SELECT u.id, u.nome, u.matricula,
                       COALESCE(NULLIF(TRIM(u.turma), ''), '') AS turma,
                       COALESCE(u.email, '') AS email,
                       IFNULL(SUM(CASE WHEN e.multa > 0 THEN e.multa END), 0)
                           AS multa,
                       SUM(CASE WHEN e.data_devolucao IS NULL
                                 AND date(e.data_prevista) < date('now','localtime')
                                THEN 1 ELSE 0 END) AS em_atraso,
                       MIN(CASE WHEN e.data_devolucao IS NULL
                                 AND date(e.data_prevista) < date('now','localtime')
                                THEN date(e.data_prevista) END) AS vencimento_antigo
                 FROM usuario u
                 JOIN emprestimo e ON e.usuario_id = u.id
                WHERE u.ativo = 1
                GROUP BY u.id
               HAVING multa > 0 OR em_atraso > 0
                ORDER BY vencimento_antigo IS NULL, vencimento_antigo,
                         multa DESC, u.nome""",
        )
        linhas = [dict(r) for r in cur.fetchall()]

    hoje = date.today()
    for linha in linhas:
        venc = linha.pop("vencimento_antigo", None)
        # Dias do atraso mais antigo: é o número que dá urgência à lista.
        if venc:
            try:
                linha["dias_atraso"] = (hoje - date.fromisoformat(venc)).days
            except ValueError:
                linha["dias_atraso"] = 0
        else:
            linha["dias_atraso"] = 0
        linha["multa"] = round(float(linha["multa"] or 0), 2)
    return linhas


def _recorte_de_periodo(inicio: Optional[str], fim: Optional[str],
                        coluna: str = "e.data_emprestimo"):
    """Cláusula de período para os relatórios, e seus parâmetros.

    As datas chegam como 'AAAA-MM-DD' e o intervalo é fechado dos dois
    lados: quem pede 01/05 a 31/05 espera o dia 31 dentro da conta.
    `date()` na coluna porque `data_emprestimo` guarda data e hora, e
    comparar o texto cru deixaria o último dia de fora.

    Período invertido (fim antes do início) não é erro: devolve vazio,
    que é a resposta honesta para um intervalo que não existe.
    """
    onde, params = "", []
    if inicio:
        onde += f" AND date({coluna}) >= date(?)"
        params.append(inicio)
    if fim:
        onde += f" AND date({coluna}) <= date(?)"
        params.append(fim)
    return onde, params


def relatorio_circulacao(top: int = 10, inicio: Optional[str] = None,
                          fim: Optional[str] = None) -> list[dict]:
    """Livros mais emprestados, opcionalmente num intervalo de datas.

    Sem período, o resultado é o de sempre: o acumulado desde a
    implantação.
    """
    onde, params = _recorte_de_periodo(inicio, fim)
    with db_cursor() as cur:
        cur.execute(
            f"""SELECT l.titulo, COUNT(*) AS emprestimos
                FROM emprestimo e
                JOIN exemplar ex ON ex.id = e.exemplar_id
                JOIN livro l ON l.id = ex.livro_id
                WHERE 1 = 1 {onde}
                GROUP BY l.id
                ORDER BY emprestimos DESC
                LIMIT ?""", params + [top])
        return [dict(r) for r in cur.fetchall()]


def relatorio_movimentacao(inicio: Optional[str] = None,
                            fim: Optional[str] = None) -> dict:
    """O que aconteceu na biblioteca num período.

    Existe para a pergunta que a direção faz no fim do ano e que o
    sistema não sabia responder: quanto a biblioteca circulou entre
    tais datas. Devolve os totais, o movimento mês a mês e a divisão
    por turma, tudo já recortado.

    Empréstimo e devolução são contados por datas diferentes de
    propósito: um livro emprestado em novembro e devolvido em fevereiro
    aparece no empréstimo de novembro e na devolução de fevereiro, que
    é como a bibliotecária conta.
    """
    onde_emp, p_emp = _recorte_de_periodo(inicio, fim)
    onde_dev, p_dev = _recorte_de_periodo(inicio, fim, "e.data_devolucao")

    with db_cursor() as cur:
        cur.execute(f"""SELECT COUNT(*) FROM emprestimo e
                         WHERE 1 = 1 {onde_emp}""", p_emp)
        emprestimos = cur.fetchone()[0]

        cur.execute(f"""SELECT COUNT(*) FROM emprestimo e
                         WHERE e.data_devolucao IS NOT NULL {onde_dev}""",
                    p_dev)
        devolucoes = cur.fetchone()[0]

        # Atraso e multa se contam na devolução: é quando o atraso
        # termina de existir e a multa é lançada.
        cur.execute(f"""SELECT
                          SUM(CASE WHEN date(e.data_devolucao)
                                      > date(e.data_prevista)
                                   THEN 1 ELSE 0 END),
                          IFNULL(SUM(e.multa), 0)
                        FROM emprestimo e
                       WHERE e.data_devolucao IS NOT NULL {onde_dev}""",
                    p_dev)
        linha = cur.fetchone()
        com_atraso, multa_total = (linha[0] or 0), (linha[1] or 0.0)

        cur.execute(f"""SELECT strftime('%Y-%m', e.data_emprestimo) AS mes,
                               COUNT(*) AS total
                          FROM emprestimo e
                         WHERE 1 = 1 {onde_emp}
                         GROUP BY mes ORDER BY mes""", p_emp)
        por_mes = [dict(r) for r in cur.fetchall()]

        cur.execute(f"""SELECT IFNULL(NULLIF(u.turma, ''), 'Sem turma') AS turma,
                               COUNT(*) AS total,
                               COUNT(DISTINCT u.id) AS leitores
                          FROM emprestimo e
                          JOIN usuario u ON u.id = e.usuario_id
                         WHERE 1 = 1 {onde_emp}
                         GROUP BY turma
                         ORDER BY total DESC""", p_emp)
        por_turma = [dict(r) for r in cur.fetchall()]

        cur.execute(f"""SELECT COUNT(DISTINCT e.usuario_id) FROM emprestimo e
                         WHERE 1 = 1 {onde_emp}""", p_emp)
        leitores = cur.fetchone()[0]

    return {
        "inicio": inicio, "fim": fim,
        "emprestimos": emprestimos,
        "devolucoes": devolucoes,
        "com_atraso": com_atraso,
        "multa_total": round(multa_total, 2),
        "leitores": leitores,
        "taxa_atraso": round(com_atraso * 100 / devolucoes, 1) if devolucoes
                       else 0.0,
        "por_mes": por_mes,
        "por_turma": por_turma,
    }


# ---------------------------------------------------------------------------
# Estatísticas de uso — o que a escola precisa enxergar
#
# Os relatórios em CSV respondem "o que aconteceu". Estas consultas
# respondem "o que fazer": qual turma parou de ler, qual categoria está
# encalhada, quais livros nunca saíram da estante. Todas devolvem lista
# de dicts prontos para desenhar, sem cálculo do lado da tela.
# ---------------------------------------------------------------------------
def emprestimos_por_mes(meses: int = 12) -> list[dict]:
    """Movimento mês a mês, do mais antigo ao mais recente.

    Meses sem empréstimo nenhum entram com zero: um buraco no gráfico
    conta uma história (férias, greve, biblioteca fechada) que a linha
    pulando o mês esconderia.
    """
    with db_cursor() as cur:
        cur.execute(
            """SELECT strftime('%Y-%m', data_emprestimo) AS mes,
                       COUNT(*) AS emprestimos
                 FROM emprestimo
                WHERE data_emprestimo >= date('now','localtime',?)
                GROUP BY mes ORDER BY mes""",
            (f"-{int(meses)} months",),
        )
        achados = {r["mes"]: r["emprestimos"] for r in cur.fetchall()}

        # Série completa, para o eixo não ter furo.
        cur.execute(
            """WITH RECURSIVE seq(n) AS (
                   SELECT 0 UNION ALL SELECT n + 1 FROM seq WHERE n < ?
               )
               SELECT strftime('%Y-%m',
                               date('now','localtime', '-' || (? - n) || ' months')
                      ) AS mes FROM seq""",
            (int(meses) - 1, int(meses) - 1),
        )
        return [{"mes": r["mes"], "emprestimos": achados.get(r["mes"], 0)}
                for r in cur.fetchall()]


def emprestimos_por_turma(top: int = 10) -> list[dict]:
    """Quais turmas leem mais. Só alunos: professor não tem turma."""
    with db_cursor() as cur:
        cur.execute(
            """SELECT COALESCE(NULLIF(TRIM(u.turma), ''), 'Sem turma') AS turma,
                       COUNT(*) AS emprestimos,
                       COUNT(DISTINCT u.id) AS leitores
                 FROM emprestimo e JOIN usuario u ON u.id = e.usuario_id
                WHERE u.perfil = 'ALUNO'
                GROUP BY turma
                ORDER BY emprestimos DESC LIMIT ?""",
            (int(top),),
        )
        return [dict(r) for r in cur.fetchall()]


def emprestimos_por_categoria(top: int = 8) -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            """SELECT COALESCE(NULLIF(TRIM(c.nome), ''), 'Sem categoria')
                         AS categoria,
                       COUNT(*) AS emprestimos
                 FROM emprestimo e
                 JOIN exemplar ex ON ex.id = e.exemplar_id
                 JOIN livro l ON l.id = ex.livro_id
                 LEFT JOIN categoria c ON c.id = l.categoria_id
                GROUP BY categoria
                ORDER BY emprestimos DESC LIMIT ?""",
            (int(top),),
        )
        return [dict(r) for r in cur.fetchall()]


def livros_nunca_emprestados(limite: int = 200) -> list[dict]:
    """Acervo parado: livro ativo que nunca saiu.

    É a consulta mais acionável do painel — dá para levar esses títulos
    para a sala de aula, montar exposição ou concluir que a compra não
    acertou o gosto de ninguém.
    """
    with db_cursor() as cur:
        cur.execute(
            """SELECT l.id, l.titulo,
                       COALESCE(NULLIF(TRIM(c.nome), ''), '') AS categoria,
                       l.ano_publicacao,
                       COUNT(ex.id) AS exemplares
                 FROM livro l
                 LEFT JOIN categoria c ON c.id = l.categoria_id
                 LEFT JOIN exemplar ex ON ex.livro_id = l.id
                WHERE l.ativo = 1
                  AND NOT EXISTS (
                      SELECT 1 FROM emprestimo e
                       JOIN exemplar e2 ON e2.id = e.exemplar_id
                      WHERE e2.livro_id = l.id)
                GROUP BY l.id
                ORDER BY l.titulo LIMIT ?""",
            (int(limite),),
        )
        return [dict(r) for r in cur.fetchall()]


def resumo_de_uso() -> dict:
    """Números que o painel mostra em destaque.

    `taxa_atraso` considera só o que já foi devolvido: empréstimo em
    aberto ainda pode voltar no prazo, e contá-lo como atraso inflaria
    o número — a bibliotecária perceberia e pararia de confiar na tela.
    """
    with db_cursor() as cur:
        cur.execute(
            """SELECT COUNT(*) AS devolvidos,
                       SUM(CASE WHEN date(data_devolucao) > date(data_prevista)
                                THEN 1 ELSE 0 END) AS com_atraso
                 FROM emprestimo WHERE data_devolucao IS NOT NULL""")
        r = cur.fetchone()
        devolvidos = r["devolvidos"] or 0
        com_atraso = r["com_atraso"] or 0

        cur.execute("SELECT COUNT(*) AS n FROM livro WHERE ativo = 1")
        acervo = cur.fetchone()["n"] or 0

        cur.execute(
            """SELECT COUNT(DISTINCT l.id) AS n
                 FROM livro l
                 JOIN exemplar ex ON ex.livro_id = l.id
                 JOIN emprestimo e ON e.exemplar_id = ex.id
                WHERE l.ativo = 1""")
        ja_sairam = cur.fetchone()["n"] or 0

        cur.execute(
            """SELECT COUNT(DISTINCT usuario_id) AS n FROM emprestimo
                WHERE data_emprestimo >= date('now','localtime','-30 days')""")
        leitores_mes = cur.fetchone()["n"] or 0

    return {
        "acervo": acervo,
        "ja_sairam": ja_sairam,
        "nunca_sairam": max(acervo - ja_sairam, 0),
        "cobertura": round(100 * ja_sairam / acervo, 1) if acervo else 0.0,
        "devolvidos": devolvidos,
        "taxa_atraso": round(100 * com_atraso / devolvidos, 1) if devolvidos else 0.0,
        "leitores_30_dias": leitores_mes,
    }


# ---------------------------------------------------------------------------
# Leitura do aluno — o que o app mostra para ele sobre ele mesmo
# ---------------------------------------------------------------------------
def estatisticas_do_leitor(usuario_id: int) -> dict:
    """Retrato da leitura de uma pessoa, contando só o que ela devolveu.

    Livro em mãos ainda não foi lido — contá-lo faria o número subir no
    empréstimo e não na leitura, que é o oposto do que a tela promete.
    """
    with db_cursor() as cur:
        cur.execute(
            """SELECT COUNT(*) AS total,
                       SUM(CASE WHEN strftime('%Y', e.data_devolucao)
                                     = strftime('%Y','now','localtime')
                                THEN 1 ELSE 0 END) AS no_ano,
                       AVG(julianday(e.data_devolucao)
                           - julianday(e.data_emprestimo)) AS dias_medios,
                       MIN(date(e.data_emprestimo)) AS desde
                 FROM emprestimo e
                WHERE e.usuario_id = ? AND e.data_devolucao IS NOT NULL""",
            (usuario_id,),
        )
        r = cur.fetchone()

        # Dois livros no mínimo para chamar de gosto. Com um só não há
        # padrão nenhum: quem leu quatro livros de quatro categorias
        # diferentes veria "você lê mais X · 1 livro", que é uma
        # conclusão tirada do nada.
        cur.execute(
            """SELECT COALESCE(NULLIF(TRIM(c.nome), ''), '') AS categoria,
                       COUNT(*) AS lidos
                 FROM emprestimo e
                 JOIN exemplar ex ON ex.id = e.exemplar_id
                 JOIN livro l ON l.id = ex.livro_id
                 LEFT JOIN categoria c ON c.id = l.categoria_id
                WHERE e.usuario_id = ? AND e.data_devolucao IS NOT NULL
                  AND TRIM(COALESCE(c.nome, '')) <> ''
                GROUP BY categoria
               HAVING lidos >= 2
                ORDER BY lidos DESC, categoria LIMIT 1""",
            (usuario_id,),
        )
        favorita = cur.fetchone()

    total = r["total"] or 0
    return {
        "total_lidos": total,
        "lidos_no_ano": r["no_ano"] or 0,
        "dias_medios": round(r["dias_medios"], 1) if r["dias_medios"] else 0.0,
        "leitor_desde": r["desde"] or "",
        "categoria_favorita": favorita["categoria"] if favorita else "",
        "lidos_na_favorita": favorita["lidos"] if favorita else 0,
    }


def recomendacoes_para(usuario_id: int, limite: int = 6) -> list[dict]:
    """Livros para sugerir a um leitor, com o motivo de cada sugestão.

    Em cascata, porque biblioteca de escola tem pouco dado e um
    algoritmo colaborativo puro devolveria lista vazia na maior parte
    dos casos:

    1. quem leu os mesmos livros que você também leu estes;
    2. os mais procurados da sua categoria favorita;
    3. os mais procurados da biblioteca;
    4. o que ninguém pegou ainda.

    O passo 4 fecha um ciclo com o painel de uso: o acervo parado que a
    bibliotecária vê no relatório é o mesmo que aparece aqui para o
    aluno como convite. Livro que ninguém pega não é livro ruim — na
    maioria das vezes é livro que ninguém viu.

    O passo 1 usa o histórico de outros leitores **em agregado** — o
    resultado nunca diz quem leu o quê, e o app só recebe o título.

    Cada item traz `motivo` ("porque você leu X") para a tela explicar a
    sugestão: lista sem explicação parece anúncio.
    """
    limite = max(1, int(limite))
    with db_cursor() as cur:
        cur.execute(
            """SELECT DISTINCT l.id, l.titulo
                 FROM emprestimo e
                 JOIN exemplar ex ON ex.id = e.exemplar_id
                 JOIN livro l ON l.id = ex.livro_id
                WHERE e.usuario_id = ?""",
            (usuario_id,),
        )
        meus = {r["id"]: r["titulo"] for r in cur.fetchall()}

        recomendados: list[dict] = []
        vistos = set(meus)

        def juntar(linhas, motivo_de) -> None:
            for row in linhas:
                if len(recomendados) >= limite:
                    return
                if row["id"] in vistos:
                    continue
                vistos.add(row["id"])
                recomendados.append({
                    "id": row["id"],
                    "titulo": row["titulo"],
                    "categoria": row["categoria"] or "",
                    "motivo": motivo_de(row),
                })

        # 1. Colaborativo: o que leram quem leu o mesmo que eu.
        if meus:
            marcadores = ",".join("?" * len(meus))
            cur.execute(
                f"""SELECT l2.id, l2.titulo,
                            COALESCE(NULLIF(TRIM(c.nome), ''), '') AS categoria,
                            COUNT(*) AS forca,
                            (SELECT l3.titulo
                               FROM emprestimo e3
                               JOIN exemplar x3 ON x3.id = e3.exemplar_id
                               JOIN livro l3 ON l3.id = x3.livro_id
                              WHERE e3.usuario_id = outros.usuario_id
                                AND l3.id IN ({marcadores})
                              LIMIT 1) AS ponte
                       FROM (SELECT DISTINCT e1.usuario_id
                               FROM emprestimo e1
                               JOIN exemplar x1 ON x1.id = e1.exemplar_id
                              WHERE x1.livro_id IN ({marcadores})
                                AND e1.usuario_id <> ?) AS outros
                       JOIN emprestimo e2 ON e2.usuario_id = outros.usuario_id
                       JOIN exemplar x2 ON x2.id = e2.exemplar_id
                       JOIN livro l2 ON l2.id = x2.livro_id
                       LEFT JOIN categoria c ON c.id = l2.categoria_id
                      WHERE l2.ativo = 1
                      GROUP BY l2.id
                      ORDER BY forca DESC, l2.titulo
                      LIMIT ?""",
                (*meus, *meus, usuario_id, limite * 3),
            )
            juntar(cur.fetchall(),
                   lambda r: (f"Quem leu \"{r['ponte']}\" também leu"
                              if r["ponte"] else "Quem lê como você também leu"))

        # 2. Mais procurados da categoria favorita.
        if len(recomendados) < limite:
            favorita = estatisticas_do_leitor(usuario_id)["categoria_favorita"]
            if favorita:
                cur.execute(
                    """SELECT l.id, l.titulo, c.nome AS categoria,
                               COUNT(e.id) AS forca
                         FROM livro l
                         JOIN categoria c ON c.id = l.categoria_id
                         LEFT JOIN exemplar ex ON ex.livro_id = l.id
                         LEFT JOIN emprestimo e ON e.exemplar_id = ex.id
                        WHERE l.ativo = 1 AND c.nome = ?
                        GROUP BY l.id ORDER BY forca DESC, l.titulo LIMIT ?""",
                    (favorita, limite * 3),
                )
                juntar(cur.fetchall(),
                       lambda r, f=favorita: f"Você lê muito {f}")

        # 3. Os mais procurados da biblioteca — vale para quem nunca
        #    pegou nada, que é justamente quem mais precisa de sugestão.
        if len(recomendados) < limite:
            cur.execute(
                """SELECT l.id, l.titulo,
                           COALESCE(NULLIF(TRIM(c.nome), ''), '') AS categoria,
                           COUNT(e.id) AS forca
                     FROM livro l
                     LEFT JOIN categoria c ON c.id = l.categoria_id
                     LEFT JOIN exemplar ex ON ex.livro_id = l.id
                     LEFT JOIN emprestimo e ON e.exemplar_id = ex.id
                    WHERE l.ativo = 1
                    GROUP BY l.id
                   HAVING forca > 0
                    ORDER BY forca DESC, l.titulo LIMIT ?""",
                (limite * 3,),
            )
            juntar(cur.fetchall(), lambda r: "Um dos mais lidos da escola")

        # 4. Acervo parado: dá visibilidade a quem nunca teve, e garante
        #    que a lista não volte vazia numa biblioteca pequena.
        if len(recomendados) < limite:
            cur.execute(
                """SELECT l.id, l.titulo,
                           COALESCE(NULLIF(TRIM(c.nome), ''), '') AS categoria
                     FROM livro l
                     LEFT JOIN categoria c ON c.id = l.categoria_id
                    WHERE l.ativo = 1
                      AND NOT EXISTS (
                          SELECT 1 FROM emprestimo e
                           JOIN exemplar x ON x.id = e.exemplar_id
                          WHERE x.livro_id = l.id)
                    ORDER BY l.titulo LIMIT ?""",
                (limite * 3,),
            )
            juntar(cur.fetchall(),
                   lambda r: "Ninguém pegou ainda — seja o primeiro")

    return recomendados


# ---------------------------------------------------------------------------
# Integração opcional: busca de metadados por ISBN (online, opt-in)
# ---------------------------------------------------------------------------
def isbn_lookup_ativo() -> bool:
    """True se a busca por ISBN estiver ligada nas configurações."""
    return (get_config("ISBN_LOOKUP", "0") or "0").strip() == "1"


def definir_isbn_lookup(ativo: bool) -> None:
    set_config("ISBN_LOOKUP", "1" if ativo else "0")


def buscar_metadados_isbn(isbn: str) -> Optional[dict]:
    """Busca título/autores/editora/ano por ISBN (Open Library + Google Books).

    Só funciona com a integração ligada (Configurações → Integrações). Retorna
    um dict com os campos ou None se nada for encontrado. Lança
    RegraNegocioError se a busca estiver desligada ou falhar (ex.: offline).
    """
    if not isbn_lookup_ativo():
        raise RegraNegocioError(
            "A busca por ISBN está desligada. "
            "Ative em Configurações → Integrações.")
    from . import isbn_lookup
    try:
        return isbn_lookup.buscar(isbn)
    except isbn_lookup.ISBNLookupError as e:
        raise RegraNegocioError(str(e))
