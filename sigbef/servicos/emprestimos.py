"""Empréstimo, devolução, renovação e multas."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from .. import reservas
from ..database import db_cursor, get_config_int, registrar_auditoria
from ..erros import RegraNegocioError

from .regras import (
    _atraso_e_multa, _limite_para_perfil, _prazo_colecao, _prazo_para_perfil,
)


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
            "SELECT IFNULL(SUM(multa - multa_paga - multa_isenta),0) AS m "
            "FROM emprestimo WHERE usuario_id = ? "
            "AND multa - multa_paga - multa_isenta > 0",
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
    with db_cursor(imediato=True) as cur:
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

        # O limite é conferido DE NOVO aqui dentro, e não só lá em cima.
        #
        # `status_usuario` roda numa transação própria, antes desta. Entre
        # uma e outra cabe um segundo empréstimo: duas bibliotecárias
        # atendendo ao mesmo tempo, ou o balcão e a API do aplicativo.
        # As duas passavam pela verificação com o mesmo número e as duas
        # gravavam — o aluno terminava com um livro a mais que o limite,
        # sem nada no sistema indicando como. A conferência só vale
        # porque a transação é `imediato`: sem isso este SELECT rodaria
        # fora dela e a corrida continuaria aberta.
        limite = _limite_para_perfil(u["perfil"])
        cur.execute(
            "SELECT COUNT(*) AS qt FROM emprestimo "
            "WHERE usuario_id = ? AND data_devolucao IS NULL", (u["id"],))
        if cur.fetchone()["qt"] >= limite:
            raise RegraNegocioError(
                f"Limite de {limite} empréstimos simultâneos atingido "
                "para este usuário.")
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
    with db_cursor() as cur:
        cur.execute(
            """SELECT e.id, e.usuario_id, e.data_prevista,
                       ex.id AS exemplar_id, l.id AS livro_id, l.titulo,
                       u.nome AS usuario, u.matricula
               FROM emprestimo e
               JOIN exemplar ex ON ex.id = e.exemplar_id
               JOIN livro l ON l.id = ex.livro_id
               JOIN usuario u ON u.id = e.usuario_id
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
        # Quem estava com o livro. Numa devolução avulsa a bibliotecária
        # tem o aluno na frente; numa pilha de trinta, não — e é ela que
        # precisa saber de quem era cada um.
        "usuario": emp["usuario"],
        "matricula": emp["matricula"],
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

    limite = get_config_int("LIMITE_RENOVACOES", 2)
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
                       e.renovacoes, e.colecao_id, u.perfil
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

        # Conta a partir do prazo atual, ou de hoje se já venceu. Contar
        # sempre de hoje encurtava o prazo: o aluno que renovava no
        # segundo dia gastava uma renovação sem ganhar nada, e um
        # exemplar de coleção (60 dias) renovado voltava para 14.
        prazo = (_prazo_colecao() if emp["colecao_id"]
                 else _prazo_para_perfil(emp["perfil"]))
        base = max(date.today(),
                   datetime.strptime(emp["data_prevista"], "%Y-%m-%d").date())
        nova_data = (base + timedelta(days=prazo)).isoformat()
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
                       -- Vem junto para a tela poder mostrar uma colecao
                       -- de trinta livros como UMA linha. O relatorio e o
                       -- aviso de vencimento continuam vendo os trinta,
                       -- que e o certo: sao trinta exemplares fora.
                       e.colecao_id, e.colecao_turma,
                       (date(e.data_prevista) < date('now','localtime')) AS atrasado
                FROM emprestimo e
                JOIN exemplar ex ON ex.id = e.exemplar_id
                JOIN livro l ON l.id = ex.livro_id
                JOIN usuario u ON u.id = e.usuario_id
                WHERE e.data_devolucao IS NULL
                ORDER BY e.data_prevista""")
        return [dict(r) for r in cur.fetchall()]


def saldo_multa(emprestimo_id: int) -> float:
    """Quanto ainda falta receber deste emprestimo."""
    with db_cursor() as cur:
        cur.execute(
            "SELECT multa - multa_paga - multa_isenta AS saldo "
            "FROM emprestimo WHERE id = ?", (emprestimo_id,))
        row = cur.fetchone()
    if row is None:
        raise RegraNegocioError("Emprestimo nao encontrado.")
    return round(float(row["saldo"] or 0), 2)


def quitar_multa(emprestimo_id: int, operador_id: Optional[int] = None,
                 valor: Optional[float] = None) -> float:
    """Registra o recebimento da multa. Devolve o saldo que sobrou.

    Antes desta versao isto fazia `UPDATE emprestimo SET multa = 0`, o que
    apagava o valor lancado junto com a divida: depois de quitar, nao havia
    mais como saber que a multa existiu, e o relatorio da direcao — que
    somava a mesma coluna sob o rotulo "Multas lancadas" — passava a
    contar so o que **nao** tinha sido pago.

    `multa` agora nunca muda depois do lancamento. O recebimento vai para
    `multa_paga`. Sem `valor`, quita o saldo inteiro; com `valor`, aceita
    pagamento parcial.
    """
    saldo = saldo_multa(emprestimo_id)
    if saldo <= 0:
        raise RegraNegocioError("Este emprestimo nao tem multa em aberto.")
    pago = saldo if valor is None else round(float(valor), 2)
    if pago <= 0:
        raise RegraNegocioError("O valor recebido precisa ser maior que zero.")
    if pago > saldo:
        raise RegraNegocioError(
            f"O valor recebido (R$ {pago:.2f}) passa do saldo devedor "
            f"(R$ {saldo:.2f}).")

    quitou = abs(pago - saldo) < 0.005
    with db_cursor() as cur:
        cur.execute(
            "UPDATE emprestimo SET multa_paga = ROUND(multa_paga + ?, 2), "
            "multa_quitada_em = CASE WHEN ? THEN datetime('now','localtime') "
            "ELSE multa_quitada_em END WHERE id = ?",
            (pago, 1 if quitou else 0, emprestimo_id))
    registrar_auditoria(
        operador_id, "QUITAR_MULTA",
        f"emp_id={emprestimo_id}; recebido={pago:.2f}; "
        f"saldo_restante={saldo - pago:.2f}")
    return round(saldo - pago, 2)


def isentar_multa(emprestimo_id: int, motivo: str,
                  operador_id: Optional[int] = None) -> None:
    """Perdoa o saldo da multa, com motivo obrigatorio.

    Existe porque perdoar acontece de verdade — livro danificado por
    problema da propria escola, aluno em situacao dificil, atraso causado
    por feriado nao previsto. Antes so dava para fingir que a multa nunca
    existiu, usando o mesmo botao de quitar. Isentar e receber sao coisas
    diferentes e agora aparecem diferentes no relatorio.

    O motivo e obrigatorio de proposito: isencao sem justificativa
    escrita e exatamente o registro que ninguem consegue defender depois.
    """
    motivo = (motivo or "").strip()
    if not motivo:
        raise RegraNegocioError(
            "Informe o motivo da isencao. Multa perdoada sem justificativa "
            "nao tem como ser explicada depois.")
    saldo = saldo_multa(emprestimo_id)
    if saldo <= 0:
        raise RegraNegocioError("Este emprestimo nao tem multa em aberto.")
    with db_cursor() as cur:
        cur.execute(
            "UPDATE emprestimo SET multa_isenta = ROUND(multa_isenta + ?, 2), "
            "multa_motivo_isencao = ?, "
            "multa_quitada_em = datetime('now','localtime') WHERE id = ?",
            (saldo, motivo, emprestimo_id))
    registrar_auditoria(
        operador_id, "ISENTAR_MULTA",
        f"emp_id={emprestimo_id}; isentado={saldo:.2f}; motivo={motivo}")


def dono_do_emprestimo_aberto(emprestimo_id: int) -> Optional[int]:
    """Quem está com o empréstimo; None se ele não existe ou já foi devolvido."""
    with db_cursor() as cur:
        cur.execute(
            "SELECT usuario_id FROM emprestimo "
            "WHERE id = ? AND data_devolucao IS NULL",
            (emprestimo_id,),
        )
        row = cur.fetchone()
    return row["usuario_id"] if row else None
