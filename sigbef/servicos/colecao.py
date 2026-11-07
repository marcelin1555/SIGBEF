"""Empréstimo de coleção para a turma (vários exemplares de uma vez)."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Optional

from .. import reservas
from ..database import db_cursor, registrar_auditoria
from ..erros import RegraNegocioError

from .emprestimos import localizar_usuario, status_usuario
from .regras import _prazo_colecao, _teto_colecao


def emprestar_colecao(*, livro_id: int, matricula_professor: str,
                      quantidade: int, turma: str,
                      operador_id: Optional[int] = None) -> dict:
    """Empresta vários exemplares do mesmo livro de uma vez, para a turma.

    O caso é o livro-texto: trinta exemplares do mesmo título saem no
    começo do bimestre e voltam no fim. Registrar isso um por um dá
    trinta linhas iguais na tela de empréstimos abertos, e devolver dá
    trinta operações — foi por isso que esse tipo de saída acabou
    virando papel, fora do sistema.

    Três decisões que valem explicação:

    **Em nome do professor, com a turma anotada.** Era a dúvida que
    segurava a função: em nome de quem fica o exemplar. Fica com quem
    responde por ele. A turma vai junto porque o mesmo professor pode
    levar coleções para turmas diferentes no mesmo bimestre, e sem isso
    ninguém sabe, no fim, qual pilha é qual.

    **Não conta no limite de empréstimos simultâneos.** O limite existe
    para que uma pessoa não monopolize o acervo; trinta livros-texto da
    mesma obra são o oposto disso, são material didático com data para
    voltar. Multa em aberto continua bloqueando — essa regra é sobre
    responsabilidade, e vale mais aqui, não menos.

    **Uma linha por exemplar, amarradas por `colecao_id`.** O exemplar
    precisa aparecer como emprestado na conferência de estante e no
    próprio registro dele; o que muda é a apresentação.

    @return dados da coleção criada, incluindo o `colecao_id`.
    """
    matr = (matricula_professor or "").strip()
    turma = (turma or "").strip()
    if not matr:
        raise RegraNegocioError("Informe a matrícula do professor.")
    if not turma:
        raise RegraNegocioError(
            "Informe a turma. Sem ela não dá para saber, no fim do "
            "bimestre, qual pilha de livros é de quem.")
    try:
        quantidade = int(quantidade)
    except (TypeError, ValueError):
        raise RegraNegocioError("Quantidade inválida.")
    if quantidade < 1:
        raise RegraNegocioError("A quantidade tem que ser pelo menos 1.")
    teto = _teto_colecao()
    if quantidade > teto:
        raise RegraNegocioError(
            f"Quantidade acima do teto de {teto} exemplares por coleção. "
            "Se a turma for maior mesmo, aumente o teto em Configurações.")

    u = localizar_usuario(matr)
    if not u or not u["ativo"]:
        raise RegraNegocioError("Professor não encontrado ou inativo.")
    if u["perfil"] not in ("PROFESSOR", "BIBLIOTECARIO", "ADMINISTRADOR"):
        raise RegraNegocioError(
            "Coleção só sai no nome de um professor: é ele quem responde "
            "pelos exemplares da turma inteira.")

    st = status_usuario(u["id"])
    # Do bloqueio normal, só a parte de multa vale aqui: o limite de
    # empréstimos simultâneos é justamente o que a coleção dispensa.
    if st.multas_em_aberto > 0:
        raise RegraNegocioError(
            f"Há multa em aberto de {st.multas_em_aberto:.2f} no nome de "
            f"{u['nome']}. Resolva antes de levar a coleção.")

    prazo = _prazo_colecao()
    data_prevista = (date.today() + timedelta(days=prazo)).isoformat()
    colecao_id = uuid.uuid4().hex

    with db_cursor(imediato=True) as cur:
        cur.execute("SELECT titulo FROM livro WHERE id = ? AND ativo = 1",
                    (livro_id,))
        liv = cur.fetchone()
        if not liv:
            raise RegraNegocioError("Livro não encontrado.")

        # Só exemplares livres de verdade: RESERVADO fica de fora porque
        # já está separado para alguém da fila, e levar a coleção por
        # cima disso furaria a fila sem ninguém ver.
        cur.execute(
            "SELECT id, codigo_barras FROM exemplar "
            "WHERE livro_id = ? AND status = 'DISPONIVEL' "
            "ORDER BY id LIMIT ?", (livro_id, quantidade))
        livres = cur.fetchall()
        if len(livres) < quantidade:
            raise RegraNegocioError(
                f"Só há {len(livres)} exemplar(es) disponível(is) de "
                f"\u201c{liv['titulo']}\u201d, e a coleção pede {quantidade}.")

        codigos = []
        for ex in livres:
            # O mesmo UPDATE condicional do empréstimo comum: se outro
            # terminal pegou o exemplar entre a consulta e agora, a linha
            # não muda e a coleção inteira é desfeita pelo rollback.
            cur.execute(
                "UPDATE exemplar SET status = 'EMPRESTADO' "
                "WHERE id = ? AND status = 'DISPONIVEL'", (ex["id"],))
            if cur.rowcount != 1:
                raise RegraNegocioError(
                    "Um dos exemplares acabou de sair em outro terminal. "
                    "Nenhum livro foi emprestado; tente de novo.")
            cur.execute(
                "INSERT INTO emprestimo(exemplar_id, usuario_id, "
                "data_prevista, origem, colecao_id, colecao_turma) "
                "VALUES (?, ?, ?, 'BALCAO', ?, ?)",
                (ex["id"], u["id"], data_prevista, colecao_id, turma))
            codigos.append(ex["codigo_barras"])

    registrar_auditoria(
        operador_id or u["id"], "EMPRESTIMO_COLECAO",
        f"colecao={colecao_id}; livro={liv['titulo']}; turma={turma}; "
        f"professor={u['matricula']}; exemplares={len(codigos)}")
    return {
        "colecao_id": colecao_id,
        "titulo": liv["titulo"],
        "turma": turma,
        "professor": u["nome"],
        "quantidade": len(codigos),
        "codigos": codigos,
        "data_prevista": data_prevista,
        "prazo_dias": prazo,
    }


def listar_colecoes_em_aberto() -> list[dict]:
    """Uma linha por coleção, e não por exemplar.

    É a razão de a função existir: na tela de empréstimos abertos, uma
    coleção de trinta livros tem que ocupar uma linha, não trinta.
    """
    with db_cursor() as cur:
        cur.execute(
            """SELECT e.colecao_id, e.colecao_turma AS turma,
                      u.nome AS professor, u.matricula,
                      l.titulo, COUNT(*) AS quantidade,
                      MIN(e.data_emprestimo) AS data_emprestimo,
                      e.data_prevista,
                      (date(e.data_prevista) < date('now','localtime'))
                          AS atrasado
                 FROM emprestimo e
                 JOIN exemplar ex ON ex.id = e.exemplar_id
                 JOIN livro l ON l.id = ex.livro_id
                 JOIN usuario u ON u.id = e.usuario_id
                WHERE e.data_devolucao IS NULL AND e.colecao_id IS NOT NULL
                GROUP BY e.colecao_id
                ORDER BY e.data_prevista""")
        return [dict(r) for r in cur.fetchall()]


def devolver_colecao(colecao_id: str,
                     operador_id: Optional[int] = None) -> dict:
    """Devolve de uma vez o que ainda estiver fora numa coleção.

    Aceita coleção parcialmente devolvida: um exemplar pode ter voltado
    sozinho pelo balcão, e isso não pode impedir a devolução do resto.
    """
    colecao_id = (colecao_id or "").strip()
    if not colecao_id:
        raise RegraNegocioError("Coleção não informada.")
    with db_cursor() as cur:
        cur.execute(
            """SELECT e.id, e.exemplar_id, ex.livro_id, l.titulo
                 FROM emprestimo e
                 JOIN exemplar ex ON ex.id = e.exemplar_id
                 JOIN livro l ON l.id = ex.livro_id
                WHERE e.colecao_id = ? AND e.data_devolucao IS NULL""",
            (colecao_id,))
        pendentes = cur.fetchall()
        if not pendentes:
            raise RegraNegocioError(
                "Esta coleção já foi devolvida por inteiro.")

        titulo = pendentes[0]["titulo"]
        for emp in pendentes:
            cur.execute(
                "UPDATE emprestimo "
                "SET data_devolucao = datetime('now','localtime') "
                "WHERE id = ?", (emp["id"],))
            cur.execute("UPDATE exemplar SET status = 'DISPONIVEL' "
                        "WHERE id = ?", (emp["exemplar_id"],))
            # Cada exemplar que volta pode atender alguém da fila; sem
            # isto, trinta livros voltariam para a estante com gente
            # esperando por eles.
            reservas._promover_fila_cur(cur, emp["livro_id"],
                                        emp["exemplar_id"])

    registrar_auditoria(
        operador_id, "DEVOLUCAO_COLECAO",
        f"colecao={colecao_id}; livro={titulo}; exemplares={len(pendentes)}")
    return {"colecao_id": colecao_id, "titulo": titulo,
            "devolvidos": len(pendentes)}
