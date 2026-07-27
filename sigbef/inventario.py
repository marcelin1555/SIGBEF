"""
SIGBEF — Conferência do acervo (inventário).

Toda biblioteca escolar bate estante contra cadastro pelo menos uma vez
por ano, normalmente no fim do ano letivo. Até aqui isso era feito no
papel, e o resultado nunca voltava para o sistema.

O fluxo é simples de propósito, porque acontece de pé, no meio da
estante, com o leitor na mão: abre a conferência, passa o leitor em cada
exemplar, encerra. O relatório sai da diferença entre o que o cadastro
diz e o que apareceu.

Módulo separado (como `reservas`) porque é um ciclo com estado próprio —
aberto, em andamento, encerrado — e misturá-lo em `servicos` só faria
aquele arquivo crescer.
"""
from __future__ import annotations

from typing import Optional

from .database import db_cursor, registrar_auditoria
from .servicos import RegraNegocioError, localizar_exemplar


def abrir(descricao: str = "", usuario_id: Optional[int] = None) -> dict:
    """Começa uma conferência. Só uma pode estar aberta por vez.

    Duas conferências simultâneas dividiriam as leituras entre elas, e
    as duas terminariam apontando livros sumidos que estão na estante.
    """
    aberta = em_andamento()
    if aberta:
        raise RegraNegocioError(
            f"Já existe uma conferência em andamento, iniciada em "
            f"{aberta['iniciado_em']}. Encerre-a antes de começar outra.")

    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO inventario (descricao, usuario_id) VALUES (?, ?)",
            ((descricao or "").strip(), usuario_id))
        inv_id = cur.lastrowid
    registrar_auditoria(usuario_id, "INVENTARIO_ABERTO", f"id={inv_id}")
    return obter(inv_id)


def em_andamento() -> Optional[dict]:
    with db_cursor() as cur:
        cur.execute("""SELECT * FROM inventario WHERE encerrado_em IS NULL
                        ORDER BY id DESC LIMIT 1""")
        row = cur.fetchone()
        return dict(row) if row else None


def obter(inventario_id: int) -> Optional[dict]:
    with db_cursor() as cur:
        cur.execute("SELECT * FROM inventario WHERE id = ?", (inventario_id,))
        row = cur.fetchone()
        if not row:
            return None
        inv = dict(row)
        cur.execute("SELECT COUNT(*) FROM inventario_item WHERE inventario_id = ?",
                    (inventario_id,))
        inv["lidos"] = cur.fetchone()[0]
        return inv


def registrar_leitura(inventario_id: int, codigo: str) -> dict:
    """Anota que um exemplar foi visto na estante.

    Idempotente: passar o mesmo livro de novo devolve `repetido=True` em
    vez de erro. Na prática isso acontece o tempo todo — a pessoa perde
    a conta de onde parou na prateleira — e transformar em erro só
    ensinaria a ignorar o aviso.
    """
    inv = obter(inventario_id)
    if not inv:
        raise RegraNegocioError("Conferência não encontrada.")
    if inv["encerrado_em"]:
        raise RegraNegocioError(
            "Esta conferência já foi encerrada. Abra uma nova para "
            "continuar contando.")

    ex = localizar_exemplar(codigo)
    if not ex:
        raise RegraNegocioError(
            f"Exemplar '{codigo}' não está no cadastro. Anote o código: "
            "pode ser um livro que nunca foi cadastrado.")

    with db_cursor() as cur:
        cur.execute("""SELECT 1 FROM inventario_item
                        WHERE inventario_id = ? AND exemplar_id = ?""",
                    (inventario_id, ex["id"]))
        repetido = cur.fetchone() is not None
        if not repetido:
            cur.execute("""INSERT INTO inventario_item
                              (inventario_id, exemplar_id) VALUES (?, ?)""",
                        (inventario_id, ex["id"]))

    return {
        "titulo": ex["titulo"],
        "codigo_barras": ex["codigo_barras"],
        "status": ex["status"],
        "repetido": repetido,
        # Chamar a atenção na hora: o exemplar que o sistema dava como
        # emprestado ou baixado, e apareceu na prateleira, é a descoberta
        # que a conferência existe para fazer.
        "inesperado": ex["status"] in ("EMPRESTADO", "BAIXADO"),
    }


def encerrar(inventario_id: int, usuario_id: Optional[int] = None) -> dict:
    inv = obter(inventario_id)
    if not inv:
        raise RegraNegocioError("Conferência não encontrada.")
    if inv["encerrado_em"]:
        raise RegraNegocioError("Esta conferência já foi encerrada.")
    with db_cursor() as cur:
        cur.execute("""UPDATE inventario
                          SET encerrado_em = datetime('now','localtime')
                        WHERE id = ?""", (inventario_id,))
    registrar_auditoria(usuario_id, "INVENTARIO_ENCERRADO",
                        f"id={inventario_id}; lidos={inv['lidos']}")
    return resultado(inventario_id)


def resultado(inventario_id: int) -> dict:
    """O que a conferência descobriu, em três listas.

    As três respondem perguntas diferentes, e por isso não viram uma
    lista só com um campo "situação": a primeira gera busca na estante,
    a segunda é só conferência, a terceira gera correção no cadastro.
    """
    with db_cursor() as cur:
        # 1. O cadastro diz que está na estante, mas ninguém passou o
        #    leitor. É a lista que interessa: são os que sumiram.
        cur.execute("""SELECT ex.codigo_barras, ex.numero_tombo,
                              ex.localizacao, l.titulo
                         FROM exemplar ex
                         JOIN livro l ON l.id = ex.livro_id
                        WHERE ex.status = 'DISPONIVEL'
                          AND ex.id NOT IN (SELECT exemplar_id
                                              FROM inventario_item
                                             WHERE inventario_id = ?)
                        ORDER BY ex.localizacao, l.titulo""",
                    (inventario_id,))
        nao_encontrados = [dict(r) for r in cur.fetchall()]

        # 2. Emprestados e não vistos: era exatamente o esperado.
        cur.execute("""SELECT ex.codigo_barras, ex.numero_tombo, l.titulo,
                              u.nome AS com_quem, e.data_prevista
                         FROM exemplar ex
                         JOIN livro l ON l.id = ex.livro_id
                         LEFT JOIN emprestimo e
                                ON e.exemplar_id = ex.id
                               AND e.data_devolucao IS NULL
                         LEFT JOIN usuario u ON u.id = e.usuario_id
                        WHERE ex.status = 'EMPRESTADO'
                          AND ex.id NOT IN (SELECT exemplar_id
                                              FROM inventario_item
                                             WHERE inventario_id = ?)
                        ORDER BY l.titulo""", (inventario_id,))
        fora_como_esperado = [dict(r) for r in cur.fetchall()]

        # 3. Apareceu na estante, mas o cadastro dizia outra coisa.
        cur.execute("""SELECT ex.codigo_barras, ex.numero_tombo, l.titulo,
                              ex.status, ex.motivo_baixa
                         FROM inventario_item it
                         JOIN exemplar ex ON ex.id = it.exemplar_id
                         JOIN livro l ON l.id = ex.livro_id
                        WHERE it.inventario_id = ?
                          AND ex.status IN ('EMPRESTADO', 'BAIXADO')
                        ORDER BY l.titulo""", (inventario_id,))
        apareceram = [dict(r) for r in cur.fetchall()]

        cur.execute("""SELECT COUNT(*) FROM exemplar
                        WHERE status != 'BAIXADO'""")
        no_acervo = cur.fetchone()[0]

    inv = obter(inventario_id) or {}
    return {
        "inventario_id": inventario_id,
        "descricao": inv.get("descricao") or "",
        "iniciado_em": inv.get("iniciado_em"),
        "encerrado_em": inv.get("encerrado_em"),
        "no_acervo": no_acervo,
        "lidos": inv.get("lidos", 0),
        "nao_encontrados": nao_encontrados,
        "fora_como_esperado": fora_como_esperado,
        "apareceram": apareceram,
    }


def listar(limite: int = 20) -> list[dict]:
    """Conferências anteriores, da mais recente para a mais antiga."""
    with db_cursor() as cur:
        cur.execute("""SELECT i.*,
                              (SELECT COUNT(*) FROM inventario_item it
                                WHERE it.inventario_id = i.id) AS lidos
                         FROM inventario i
                        ORDER BY i.id DESC LIMIT ?""", (limite,))
        return [dict(r) for r in cur.fetchall()]
