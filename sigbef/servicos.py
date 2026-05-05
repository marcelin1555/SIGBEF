"""
SIGBEF — Camada de serviços (regras de negócio).

Concentra as operações de negócio (cadastros, empréstimos, devoluções e
consultas) em funções puras, separadas da camada de UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from .auth import gerar_hash
from .barcode_util import gerar_codigo_exemplar, gerar_codigo_usuario
from .database import db_cursor, get_config, registrar_auditoria


class RegraNegocioError(Exception):
    """Erro tratado de regra de negócio (mensagens amigáveis ao usuário)."""


# ---------------------------------------------------------------------------
# Editoras / Categorias / Autores (cadastros auxiliares)
# ---------------------------------------------------------------------------
def upsert_editora(nome: str) -> int:
    nome = (nome or "").strip()
    if not nome:
        raise RegraNegocioError("Nome da editora obrigatório.")
    with db_cursor() as cur:
        cur.execute("INSERT OR IGNORE INTO editora(nome) VALUES (?)", (nome,))
        cur.execute("SELECT id FROM editora WHERE nome = ?", (nome,))
        return cur.fetchone()["id"]


def upsert_categoria(nome: str) -> int:
    nome = (nome or "").strip()
    if not nome:
        raise RegraNegocioError("Nome da categoria obrigatório.")
    with db_cursor() as cur:
        cur.execute("INSERT OR IGNORE INTO categoria(nome) VALUES (?)", (nome,))
        cur.execute("SELECT id FROM categoria WHERE nome = ?", (nome,))
        return cur.fetchone()["id"]


def upsert_autor(nome: str) -> int:
    nome = (nome or "").strip()
    if not nome:
        raise RegraNegocioError("Nome do autor obrigatório.")
    with db_cursor() as cur:
        cur.execute("INSERT OR IGNORE INTO autor(nome) VALUES (?)", (nome,))
        cur.execute("SELECT id FROM autor WHERE nome = ?", (nome,))
        return cur.fetchone()["id"]


def listar_editoras() -> list[dict]:
    with db_cursor() as cur:
        cur.execute("SELECT id, nome FROM editora ORDER BY nome")
        return [dict(r) for r in cur.fetchall()]


def listar_categorias() -> list[dict]:
    with db_cursor() as cur:
        cur.execute("SELECT id, nome FROM categoria ORDER BY nome")
        return [dict(r) for r in cur.fetchall()]


def listar_autores() -> list[dict]:
    with db_cursor() as cur:
        cur.execute("SELECT id, nome FROM autor ORDER BY nome")
        return [dict(r) for r in cur.fetchall()]


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
    titulo = (titulo or "").strip()
    if not titulo:
        raise RegraNegocioError("Título é obrigatório.")
    if not autores:
        raise RegraNegocioError("Informe pelo menos um autor.")
    if quantidade_exemplares < 1:
        raise RegraNegocioError("Cadastre pelo menos um exemplar.")

    editora_id = upsert_editora(editora) if editora else None
    categoria_id = upsert_categoria(categoria) if categoria else None
    autor_ids = [upsert_autor(a) for a in autores if a.strip()]

    with db_cursor() as cur:
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
            codigo = gerar_codigo_exemplar()
            tombo = f"{livro_id:05d}-{i:03d}"
            cur.execute(
                """INSERT INTO exemplar(livro_id, codigo_barras, numero_tombo, localizacao)
                       VALUES (?, ?, ?, ?)""",
                (livro_id, codigo, tombo, localizacao or None),
            )
            exemplares.append((cur.lastrowid, codigo))

    registrar_auditoria(usuario_id, "CADASTRO_LIVRO",
                         f"livro_id={livro_id}; exemplares={len(exemplares)}")
    return {"livro_id": livro_id, "exemplares": exemplares}


def adicionar_exemplares(livro_id: int, quantidade: int, localizacao: str = "",
                         usuario_id: Optional[int] = None) -> list[tuple[int, str]]:
    if quantidade < 1:
        raise RegraNegocioError("Quantidade deve ser >= 1.")
    exemplares: list[tuple[int, str]] = []
    with db_cursor() as cur:
        cur.execute("SELECT id FROM livro WHERE id = ? AND ativo = 1", (livro_id,))
        if not cur.fetchone():
            raise RegraNegocioError("Livro não encontrado.")
        cur.execute("SELECT COUNT(*) AS qtd FROM exemplar WHERE livro_id = ?", (livro_id,))
        existente = cur.fetchone()["qtd"]
        for i in range(1, quantidade + 1):
            codigo = gerar_codigo_exemplar()
            tombo = f"{livro_id:05d}-{(existente + i):03d}"
            cur.execute(
                """INSERT INTO exemplar(livro_id, codigo_barras, numero_tombo, localizacao)
                       VALUES (?, ?, ?, ?)""",
                (livro_id, codigo, tombo, localizacao or None),
            )
            exemplares.append((cur.lastrowid, codigo))

    registrar_auditoria(usuario_id, "ADD_EXEMPLARES",
                         f"livro_id={livro_id}; novos={len(exemplares)}")
    return exemplares


def listar_livros(termo: str = "", apenas_disponiveis: bool = False) -> list[dict]:
    """Lista livros com agregados de exemplares (total e disponíveis)."""
    termo_like = f"%{termo.strip()}%" if termo else "%"
    sql = """
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
        ORDER BY l.titulo
    """
    with db_cursor() as cur:
        cur.execute(sql, (termo_like, termo_like, termo_like, termo_like))
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
    gerar_cartao: bool = True,
    usuario_id_executor: Optional[int] = None,
) -> dict:
    nome = (nome or "").strip()
    matricula = (matricula or "").strip()
    if not nome or not matricula:
        raise RegraNegocioError("Nome e matrícula são obrigatórios.")
    if perfil not in ("ALUNO", "PROFESSOR", "BIBLIOTECARIO", "ADMINISTRADOR"):
        raise RegraNegocioError("Perfil inválido.")
    if not senha or len(senha) < 4:
        raise RegraNegocioError("Senha deve ter pelo menos 4 caracteres.")

    cartao = gerar_codigo_usuario() if gerar_cartao else None
    senha_hash = gerar_hash(senha)
    with db_cursor() as cur:
        cur.execute("SELECT 1 FROM usuario WHERE matricula = ?", (matricula,))
        if cur.fetchone():
            raise RegraNegocioError("Já existe um usuário com esta matrícula.")
        cur.execute(
            """INSERT INTO usuario(nome, matricula, email, telefone,
                                   perfil, senha_hash, codigo_barras)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nome, matricula, email or None, telefone or None,
             perfil, senha_hash, cartao),
        )
        novo_id = cur.lastrowid
    registrar_auditoria(usuario_id_executor, "CADASTRO_USUARIO",
                         f"id={novo_id}; perfil={perfil}")
    return {"id": novo_id, "matricula": matricula, "codigo_barras": cartao}


def listar_usuarios(termo: str = "") -> list[dict]:
    termo_like = f"%{termo.strip()}%" if termo else "%"
    with db_cursor() as cur:
        cur.execute(
            """SELECT id, nome, matricula, email, perfil, codigo_barras, ativo
               FROM usuario
               WHERE nome LIKE ? OR matricula LIKE ? OR IFNULL(email,'') LIKE ?
               ORDER BY nome""",
            (termo_like, termo_like, termo_like),
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


def alternar_status_usuario(usuario_id: int, ativo: bool) -> None:
    with db_cursor() as cur:
        cur.execute("UPDATE usuario SET ativo = ? WHERE id = ?",
                    (1 if ativo else 0, usuario_id))
    registrar_auditoria(usuario_id, "STATUS_USUARIO",
                         f"ativo={'sim' if ativo else 'nao'}")


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
            "WHERE usuario_id = ? AND multa > 0 AND data_devolucao IS NULL",
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
                          f"OK — {em_aberto} de {limite} empréstimos em uso.")


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
    if ex["status"] != "DISPONIVEL":
        raise RegraNegocioError(
            f"Exemplar '{ex['titulo']}' não está disponível "
            f"(status: {ex['status']})."
        )

    st = status_usuario(u["id"])
    if not st.pode_pegar:
        raise RegraNegocioError(st.motivo)

    prazo = _prazo_para_perfil(u["perfil"])
    data_prevista = (date.today() + timedelta(days=prazo)).isoformat()

    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO emprestimo(exemplar_id, usuario_id, data_prevista, origem)
               VALUES (?, ?, ?, ?)""",
            (ex["id"], u["id"], data_prevista, origem),
        )
        emp_id = cur.lastrowid
        cur.execute("UPDATE exemplar SET status = 'EMPRESTADO' WHERE id = ?",
                    (ex["id"],))

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

    with db_cursor() as cur:
        cur.execute(
            """SELECT e.id, e.usuario_id, e.data_prevista, ex.id AS exemplar_id, l.titulo
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
            "UPDATE emprestimo SET data_devolucao = datetime('now','localtime'), multa = ? WHERE id = ?",
            (multa, emp["id"]),
        )
        cur.execute("UPDATE exemplar SET status = 'DISPONIVEL' WHERE id = ?",
                    (emp["exemplar_id"],))

    registrar_auditoria(operador_id or emp["usuario_id"], "DEVOLUCAO",
                         f"emp_id={emp['id']}; multa={multa:.2f}; atraso={dias_atraso}d")
    return {
        "titulo": emp["titulo"],
        "dias_atraso": dias_atraso,
        "multa": multa,
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
            """SELECT e.id, u.nome AS usuario, u.matricula, l.titulo,
                       ex.codigo_barras, e.data_emprestimo, e.data_prevista,
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
