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


def listar_livros(termo: str = "", apenas_disponiveis: bool = False,
                  categoria: Optional[str] = None,
                  autor: Optional[str] = None) -> list[dict]:
    """Lista livros com agregados de exemplares (total e disponíveis).

    `termo` faz busca livre (título, ISBN, autor, categoria). `categoria`
    e `autor` são filtros exatos e opcionais (busca avançada); omitidos,
    o resultado é idêntico à busca simples.
    """
    termo_like = f"%{termo.strip()}%" if termo else "%"
    params: list = [termo_like, termo_like, termo_like, termo_like]
    filtros = ""
    if categoria:
        filtros += " AND c.nome = ?"
        params.append(categoria)
    if autor:
        filtros += (" AND EXISTS (SELECT 1 FROM livro_autor la2 "
                    "JOIN autor a2 ON a2.id = la2.autor_id "
                    "WHERE la2.livro_id = l.id AND a2.nome = ?)")
        params.append(autor)
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
            (SELECT COUNT(*) FROM exemplar ex WHERE ex.livro_id = l.id) AS total_exemplares,
            (SELECT COUNT(*) FROM exemplar ex
                WHERE ex.livro_id = l.id AND ex.status = 'DISPONIVEL') AS disponiveis
        FROM livro l
        LEFT JOIN categoria c ON c.id = l.categoria_id
        LEFT JOIN editora e ON e.id = l.editora_id
        WHERE l.ativo = 1
          AND (
                l.titulo LIKE ?
                OR IFNULL(l.isbn, '') LIKE ?
                OR EXISTS (
                    SELECT 1 FROM livro_autor la
                    JOIN autor a ON a.id = la.autor_id
                    WHERE la.livro_id = l.id AND a.nome LIKE ?
                )
                OR IFNULL(c.nome, '') LIKE ?
              )
          {filtros}
        ORDER BY l.titulo
    """
    with db_cursor() as cur:
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
    if apenas_disponiveis:
        rows = [r for r in rows if (r["disponiveis"] or 0) > 0]
    return rows


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
            """SELECT id, codigo_barras, numero_tombo, localizacao, status
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

    Retorna {"livros", "exemplares", "pulados": [(linha, motivo)],
    "erros": [(linha, motivo)]}.
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
    validas, erros, pulados = [], [], []
    for num, linha in enumerate(leitor, start=2):
        dados = {mapa[k]: (v or "").strip()
                 for k, v in linha.items() if k in mapa}
        if not any(dados.values()):
            continue  # linha totalmente em branco
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
            "pulados": pulados, "erros": erros}


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
                              f"Há {atrasados} exemplar(es) em atraso.")
    if multa_aberta > 0:
        return StatusUsuario(em_aberto, multa_aberta, False,
                              f"Há multas em aberto: R$ {multa_aberta:.2f}.")
    if em_aberto >= limite:
        return StatusUsuario(em_aberto, multa_aberta, False,
                              f"Limite de {limite} empréstimos atingido.")
    return StatusUsuario(em_aberto, multa_aberta, True,
                          f"OK: {em_aberto} de {limite} empréstimos em uso.")


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

    multa_dia = _config_float("MULTA_POR_DIA", 1.5)
    multa_teto = _config_float("MULTA_TETO", 60.0)

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

        prevista = datetime.strptime(emp["data_prevista"], "%Y-%m-%d").date()
        hoje = date.today()
        dias_atraso = max((hoje - prevista).days, 0)
        multa = round(min(multa_dia * dias_atraso, multa_teto), 2) if dias_atraso else 0.0

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


def renovar_emprestimo(emprestimo_id: int,
                       operador_id: Optional[int] = None) -> dict:
    with db_cursor() as cur:
        cur.execute(
            """SELECT e.id, e.usuario_id, e.exemplar_id, e.data_prevista,
                       u.perfil
               FROM emprestimo e JOIN usuario u ON u.id = e.usuario_id
               WHERE e.id = ? AND e.data_devolucao IS NULL""",
            (emprestimo_id,),
        )
        emp = cur.fetchone()
        if not emp:
            raise RegraNegocioError("Empréstimo não encontrado.")

        prazo = _prazo_para_perfil(emp["perfil"])
        nova_data = (date.today() + timedelta(days=prazo)).isoformat()
        cur.execute(
            "UPDATE emprestimo SET data_prevista = ? WHERE id = ?",
            (nova_data, emprestimo_id),
        )
    registrar_auditoria(operador_id or emp["usuario_id"], "RENOVACAO",
                         f"emp_id={emprestimo_id}; nova_prevista={nova_data}")
    return {"data_prevista": nova_data}


def listar_emprestimos_usuario(usuario_id: int,
                                somente_abertos: bool = False) -> list[dict]:
    sql = """
        SELECT e.id, l.titulo, ex.codigo_barras, e.data_emprestimo,
               e.data_prevista, e.data_devolucao, e.multa, e.origem
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


def relatorio_circulacao(top: int = 10) -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            """SELECT l.titulo, COUNT(*) AS emprestimos
                FROM emprestimo e
                JOIN exemplar ex ON ex.id = e.exemplar_id
                JOIN livro l ON l.id = ex.livro_id
                GROUP BY l.id
                ORDER BY emprestimos DESC
                LIMIT ?""", (top,))
        return [dict(r) for r in cur.fetchall()]


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
