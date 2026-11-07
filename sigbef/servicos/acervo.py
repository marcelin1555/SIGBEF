"""Livros: cadastro, edição, busca, exclusão e metadados por ISBN."""
from __future__ import annotations

import re
from typing import Optional

from .. import database, reservas
from ..barcode_util import gerar_codigo_exemplar
from ..database import db_cursor, get_config, registrar_auditoria, set_config
from ..erros import RegraNegocioError
from ..reservas import cancelar_reservas_do_livro_cur

from .comum import _codigo_barras_unico


def _validar_titulo_autores(titulo: str,
                             autores: list[str]) -> tuple[str, list[str]]:
    """Regra comum ao cadastro e à edição: título e ao menos um autor.

    Compartilhada pra não deixar a mensagem de erro divergir entre os
    dois caminhos com o tempo.
    """
    titulo = (titulo or "").strip()
    if not titulo:
        raise RegraNegocioError("Título é obrigatório.")
    autores_limpos = [a.strip() for a in (autores or []) if a and a.strip()]
    if not autores_limpos:
        raise RegraNegocioError("Informe pelo menos um autor.")
    return titulo, autores_limpos


#: Faixa aceita para o ano de publicação. A mesma que a importação por
#: planilha já usava — aqui ela vira regra única, em vez de existir só
#: num dos dois caminhos.
ANO_MINIMO, ANO_MAXIMO = 1000, 2100


def _validar_ano(ano) -> None:
    if ano in (None, ""):
        return
    try:
        n = int(ano)
    except (TypeError, ValueError):
        raise RegraNegocioError(
            f"Ano de publicação inválido: “{ano}”. Informe só o ano, "
            "com quatro dígitos.")
    if not ANO_MINIMO <= n <= ANO_MAXIMO:
        raise RegraNegocioError(
            f"Ano de publicação fora da faixa aceita "
            f"({ANO_MINIMO}–{ANO_MAXIMO}): {n}.")


def _validar_isbn_inedito(cur, isbn: str,
                          ignorar_livro_id: Optional[int] = None) -> None:
    """Recusa ISBN que já está em outro livro ativo do acervo.

    ISBN identifica uma edição. Dois registros com o mesmo ISBN são o
    mesmo livro cadastrado duas vezes — e é assim que o acervo ganha
    títulos duplicados que ninguém consegue conciliar depois.
    """
    isbn = (isbn or "").strip()
    if not isbn:
        return
    sql = "SELECT id, titulo FROM livro WHERE ativo = 1 AND isbn = ?"
    params: list = [isbn]
    if ignorar_livro_id is not None:
        sql += " AND id != ?"
        params.append(ignorar_livro_id)
    cur.execute(sql, params)
    ja = cur.fetchone()
    if ja:
        raise RegraNegocioError(
            f"O ISBN {isbn} já está cadastrado em “{ja['titulo']}”. "
            "Se for outro exemplar do mesmo livro, acrescente exemplares "
            "ao registro existente em vez de cadastrar de novo.")


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
    tombos: Optional[list[str]] = None,
    usuario_id: Optional[int] = None,
) -> dict:
    """Cadastra um livro com seus autores e exemplares iniciais.

    `tombos`, quando informado, dá a cada exemplar o número que já está
    escrito no livro físico, na ordem, em vez do tombo gerado pelo
    sistema. Precisa ter exatamente `quantidade_exemplares` itens, e
    nenhum deles pode já estar em uso.

    Retorna um dict com `livro_id` e `exemplares` (lista de tuplas
    (id, codigo_barras)).
    """
    with db_cursor() as cur:
        # A importação por planilha já recusava ano fora de faixa e ISBN
        # repetido; o cadastro pela tela aceitava os dois calado. O mesmo
        # acervo ficava com regra diferente conforme a porta de entrada,
        # e a porta mais usada era a mais permissiva.
        #
        # A conferência mora aqui, na camada de serviço e dentro da
        # transação, e não na tela: assim vale para o balcão, para a
        # planilha e para qualquer caminho novo.
        _validar_ano(ano)
        _validar_isbn_inedito(cur, isbn)
        res = _inserir_livro_cur(
            cur, titulo=titulo, autores=autores, isbn=isbn, editora=editora,
            categoria=categoria, ano=ano, edicao=edicao, sinopse=sinopse,
            quantidade_exemplares=quantidade_exemplares,
            localizacao=localizacao, tombos=tombos,
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


def _tombo_em_uso(cur, tombo: str) -> bool:
    cur.execute("SELECT 1 FROM exemplar WHERE numero_tombo = ? LIMIT 1",
                (tombo,))
    return cur.fetchone() is not None


def _validar_tombos_ineditos(cur, tombos_limpos: list[str]) -> None:
    """Recusa tombo repetido no lote ou já em uso por outro exemplar.

    Mesmo motivo de `alterar_tombo_exemplar`: o balcão procura por
    `codigo_barras OR numero_tombo` com LIMIT 1, então dois exemplares
    com o mesmo tombo fazem o empréstimo pegar a cópia errada em
    silêncio. A coluna tem índice, mas não tem UNIQUE. Compartilhada
    pelo cadastro de livro e por acrescentar exemplares a um já
    existente — os dois caminhos escrevem tombo escolhido pela pessoa.
    """
    if not tombos_limpos:
        return
    repetido_no_lote = next(
        (t for t in tombos_limpos if tombos_limpos.count(t) > 1), None)
    if repetido_no_lote:
        raise RegraNegocioError(
            f"O tombo {repetido_no_lote} foi informado mais de uma vez. "
            "Cada exemplar precisa do seu próprio número.")
    marcadores = ", ".join("?" * len(tombos_limpos))
    cur.execute(
        f"""SELECT l.titulo, ex.numero_tombo
               FROM exemplar ex JOIN livro l ON l.id = ex.livro_id
               WHERE ex.numero_tombo IN ({marcadores}) LIMIT 1""",
        tombos_limpos)
    em_uso = cur.fetchone()
    if em_uso:
        raise RegraNegocioError(
            f"O tombo {em_uso['numero_tombo']} já está com "
            f"\"{em_uso['titulo']}\". Cada exemplar precisa do seu "
            "próprio número.")


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
    titulo, autores_limpos = _validar_titulo_autores(titulo, autores)
    if quantidade_exemplares < 1:
        raise RegraNegocioError("Cadastre pelo menos um exemplar.")
    tombos_limpos = [t.strip() for t in (tombos or []) if t and t.strip()]
    if tombos_limpos and len(tombos_limpos) != quantidade_exemplares:
        raise RegraNegocioError(
            f"Número de tombos ({len(tombos_limpos)}) diferente da "
            f"quantidade de exemplares ({quantidade_exemplares}).")
    _validar_tombos_ineditos(cur, tombos_limpos)

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
                         usuario_id: Optional[int] = None,
                         tombos: Optional[list[str]] = None
                         ) -> list[tuple[int, str]]:
    """Acrescenta exemplares a um livro que já está no acervo.

    É o caminho para a segunda leva do mesmo título — a escola recebe
    mais cópias de um livro-texto que já foi catalogado. Cadastrar de
    novo criaria um título duplicado, com a busca mostrando o mesmo
    livro duas vezes e a contagem do acervo errada.

    `tombos`, quando informado, dá a cada exemplar novo o número que já
    está escrito na cópia física, na ordem. Em branco, o sistema
    continua gerando `{livro_id}-{sequência}`.
    """
    if quantidade < 1:
        raise RegraNegocioError("Quantidade deve ser >= 1.")
    tombos_limpos = [t.strip() for t in (tombos or []) if t and t.strip()]
    if tombos_limpos and len(tombos_limpos) != quantidade:
        raise RegraNegocioError(
            f"Número de tombos ({len(tombos_limpos)}) diferente da "
            f"quantidade de exemplares ({quantidade}).")
    exemplares: list[tuple[int, str]] = []
    with db_cursor() as cur:
        cur.execute("SELECT id FROM livro WHERE id = ? AND ativo = 1", (livro_id,))
        if not cur.fetchone():
            raise RegraNegocioError("Livro não encontrado.")
        _validar_tombos_ineditos(cur, tombos_limpos)
        cur.execute("SELECT COUNT(*) AS qtd FROM exemplar WHERE livro_id = ?", (livro_id,))
        existente = cur.fetchone()["qtd"]
        seq = existente
        for i in range(1, quantidade + 1):
            codigo = _codigo_barras_unico(cur, "exemplar", gerar_codigo_exemplar)
            if tombos_limpos:
                tombo = tombos_limpos[i - 1]
            else:
                # A sequência é contagem de exemplares, não o maior
                # número já usado: um tombo corrigido na mão para
                # `00012-004` fazia a próxima leva gerar `00012-004` de
                # novo, e o balcão passa a achar a cópia errada pelo
                # tombo. Aqui o número é pulado até sobrar um livre.
                seq += 1
                tombo = f"{livro_id:05d}-{seq:03d}"
                while _tombo_em_uso(cur, tombo):
                    seq += 1
                    tombo = f"{livro_id:05d}-{seq:03d}"
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


def editar_livro(
    livro_id: int,
    *,
    titulo: str,
    autores: list[str],
    isbn: str = "",
    editora: str = "",
    categoria: str = "",
    ano: Optional[int] = None,
    edicao: str = "",
    sinopse: str = "",
    usuario_id: Optional[int] = None,
) -> None:
    """Corrige os dados de um livro já cadastrado.

    Só os campos do livro (título, autores, ISBN, editora, categoria,
    ano, edição, sinopse). Exemplares, quantidade, tombo e localização
    têm fluxo próprio (`adicionar_exemplares`, baixa) e não são tocados
    aqui — misturar os dois numa tela só faria a bibliotecária mudar o
    acervo por engano ao só corrigir um título digitado errado.
    """
    titulo, autores_limpos = _validar_titulo_autores(titulo, autores)
    with db_cursor() as cur:
        cur.execute("SELECT id FROM livro WHERE id = ? AND ativo = 1",
                    (livro_id,))
        if not cur.fetchone():
            raise RegraNegocioError("Livro não encontrado.")

        # As mesmas regras do cadastro. `ignorar_livro_id` deixa o
        # próprio livro manter o ISBN que já é dele — sem isso, salvar a
        # edição sem mexer no ISBN acusaria conflito consigo mesmo.
        _validar_ano(ano)
        _validar_isbn_inedito(cur, isbn, ignorar_livro_id=livro_id)

        editora = (editora or "").strip()
        categoria = (categoria or "").strip()
        editora_id = _upsert_nome(cur, "editora", editora) if editora else None
        categoria_id = (_upsert_nome(cur, "categoria", categoria)
                         if categoria else None)

        cur.execute(
            """UPDATE livro
                  SET titulo = ?, isbn = ?, editora_id = ?, categoria_id = ?,
                      ano_publicacao = ?, edicao = ?, sinopse = ?
                WHERE id = ?""",
            (titulo, isbn or None, editora_id, categoria_id, ano,
             edicao or None, sinopse or None, livro_id),
        )

        # Autor não é dado do livro, é associação (N:N) — refaz do zero é
        # mais simples e seguro que calcular a diferença entre a lista
        # antiga e a nova. Um autor que ficou sem nenhum livro associado
        # continua no catálogo (mesmo comportamento de sempre: `autor`
        # nunca é limpo de órfãos em nenhum outro fluxo do sistema).
        cur.execute("DELETE FROM livro_autor WHERE livro_id = ?", (livro_id,))
        for nome_autor in autores_limpos:
            autor_id = _upsert_nome(cur, "autor", nome_autor)
            cur.execute(
                "INSERT OR IGNORE INTO livro_autor(livro_id, autor_id) "
                "VALUES (?, ?)",
                (livro_id, autor_id),
            )

    registrar_auditoria(usuario_id, "EDICAO_LIVRO", f"livro_id={livro_id}")


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


_PALAVRA = re.compile(r"\w+", re.UNICODE)


def consulta_de_busca(termo: str) -> Optional[str]:
    """Traduz o que a pessoa digitou numa consulta FTS5 segura.

    Cada palavra vira um prefixo ("casm" acha "Casmurro") e todas
    precisam aparecer, em qualquer ordem e em qualquer campo: "machado
    casmurro" acha o livro pelo autor e pelo título ao mesmo tempo.

    A entrada nunca chega crua ao MATCH. Aspas, parênteses, dois-pontos,
    asterisco e hífen são operadores do FTS5, e "Dom Casmurro: edição
    crítica" ou "C++" digitados como vieram derrubariam a busca com erro
    de sintaxe. Só as sequências de letras e números passam, e sempre
    entre aspas -- o que também desarma AND, OR e NOT digitados como
    palavra.

    Um código com separador ("978-85-359-1066-3", "00012-004") vira duas
    alternativas: as partes em sequência, que acham o tombo; e tudo
    junto, que acha o ISBN guardado sem hífen.

    Prefixo só a partir de duas letras. "C++" vira "C", e "C" como
    prefixo acharia toda palavra que começa com C -- no acervo do CEFE,
    1.422 dos 2.867 livros. Com uma letra, a palavra tem de ser
    exatamente ela.

    Devolve None quando não sobra nada pesquisável.
    """
    blocos = []
    for pedaco in (termo or "").split():
        partes = _PALAVRA.findall(pedaco)
        if not partes:
            continue
        prefixo = "*" if len(partes[-1]) >= 2 else ""
        frase = '"%s"%s' % (" ".join(partes), prefixo)
        if len(partes) > 1 and any(ch.isdigit() for ch in pedaco):
            frase = '(%s OR "%s"*)' % (frase, "".join(partes))
        blocos.append(frase)
    return " ".join(blocos) or None


def _filtro_de_livros(termo: str, apenas_disponiveis: bool,
                      categoria: Optional[str], autor: Optional[str]):
    """Monta a junção e o WHERE compartilhados entre listar e contar.

    Existe para os dois nunca discordarem: um total que não bate com a
    lista é pior que total nenhum, porque a pessoa fica procurando o
    livro que o contador prometeu. Por isso a busca textual entra como
    JUNÇÃO, e não só no WHERE: listar precisa da relevância para ordenar,
    e contar tem de passar exatamente pelas mesmas linhas.

    Devolve (juncao, onde, params), com os parâmetros da junção antes
    dos do WHERE, na ordem em que aparecem no SQL.
    """
    juncao = ""
    params: list = []
    onde = "l.ativo = 1"
    termo = (termo or "").strip()

    if termo and database.BUSCA_FTS:
        consulta = consulta_de_busca(termo)
        if consulta is None:
            # Só pontuação: nada a procurar, e nada a mostrar -- o LIKE
            # antigo também não achava título nenhum com "***".
            onde += " AND 0"
        else:
            # Pesos do bm25 por coluna: acertar no título vale mais que
            # no autor, que vale mais que na categoria. Um tombo ou ISBN
            # costuma achar um livro só, então o peso ali pouco importa.
            juncao = """JOIN (
                SELECT rowid AS livro_id,
                       bm25(livro_busca, 10.0, 5.0, 2.0, 1.0) AS relevancia
                  FROM livro_busca
                 WHERE livro_busca MATCH ?
            ) busca ON busca.livro_id = l.id"""
            params.append(consulta)
    elif termo:
        # SQLite sem FTS5: a busca de antes, que ainda tropeça em acento,
        # mas mantém o sistema de pé.
        termo_like = f"%{termo}%"
        params += [termo_like, termo_like, termo_like, termo_like]
        onde += """
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
    return juncao, onde, params


def contar_livros(termo: str = "", apenas_disponiveis: bool = False,
                  categoria: Optional[str] = None,
                  autor: Optional[str] = None) -> int:
    """Quantos livros a busca encontra, sem trazer nenhum.

    Barato porque não monta os agregados de exemplar nem os autores:
    é a contagem que a tela mostra ao lado da página exibida.
    """
    juncao, onde, params = _filtro_de_livros(termo, apenas_disponiveis,
                                              categoria, autor)
    with db_cursor() as cur:
        cur.execute(f"""SELECT COUNT(*) FROM livro l
                        {juncao}
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
    juncao, onde, params = _filtro_de_livros(termo, apenas_disponiveis,
                                              categoria, autor)
    # Com busca, o mais relevante primeiro: quem digita "1984" quer o
    # livro "1984" no topo, não enterrado entre os títulos que começam
    # com "19". Sem busca, a ordem alfabética de sempre. O título e o id
    # desempatam, para "Carregar mais" nunca repetir nem pular um livro.
    ordem = ("busca.relevancia, l.titulo, l.id" if juncao
             else "l.titulo, l.id")
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
        {juncao}
        LEFT JOIN categoria c ON c.id = l.categoria_id
        LEFT JOIN editora e ON e.id = l.editora_id
        WHERE {onde}
        ORDER BY {ordem}{paginacao}
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


def excluir_livro(livro_id: int, usuario_id: Optional[int] = None,
                  liberar_tombos: bool = False) -> None:
    """Exclusão lógica do livro (e de seus exemplares).

    @param liberar_tombos devolve os números de tombo ao uso, para que
        possam ser escritos em outros exemplares.

        Nasceu de um beco real. O tombo de um exemplar excluído
        continuava ocupado — a checagem de duplicidade não olha status
        nem se o livro está ativo — e o livro sumia de todas as telas.
        Resultado: números presos por um título que ninguém consegue
        mais abrir, sem caminho nenhum para soltá-los.

        Nasce **desligado**, como a caixa equivalente na baixa: enquanto
        dois exemplares puderem ter o mesmo tombo, mesmo que por um
        instante, o balcão pode emprestar a cópia errada. Liberar é
        escolha explícita de quem sabe que aquela numeração vai ser
        reaproveitada.
    """
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
        # `status != 'BAIXADO'`, e não `= 'DISPONIVEL'`: o exemplar
        # separado para uma reserva (RESERVADO) escapava da baixa. Quando
        # a reserva vencia, a expiração o devolvia para DISPONIVEL — e
        # como `localizar_exemplar` não filtra livro ativo, o livro
        # excluído voltava a ser emprestável no balcão.
        cur.execute(
            "UPDATE exemplar SET status = 'BAIXADO' "
            "WHERE livro_id = ? AND status != 'BAIXADO'",
            (livro_id,),
        )
        canceladas = cancelar_reservas_do_livro_cur(cur, livro_id)

        tombos_soltos = 0
        if liberar_tombos:
            cur.execute(
                "SELECT COUNT(*) AS n FROM exemplar "
                "WHERE livro_id = ? AND numero_tombo IS NOT NULL",
                (livro_id,))
            tombos_soltos = cur.fetchone()["n"]
            cur.execute(
                "UPDATE exemplar SET numero_tombo = NULL WHERE livro_id = ?",
                (livro_id,))

    registrar_auditoria(
        usuario_id, "EXCLUSAO_LIVRO",
        f"livro_id={livro_id}"
        + (f" reservas_canceladas={canceladas}" if canceladas else "")
        + (f" tombos_liberados={tombos_soltos}" if tombos_soltos else ""))


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
    from .. import isbn_lookup
    try:
        return isbn_lookup.buscar(isbn)
    except isbn_lookup.ISBNLookupError as e:
        raise RegraNegocioError(str(e))
