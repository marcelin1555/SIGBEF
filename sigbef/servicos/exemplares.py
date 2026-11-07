"""Exemplares: etiquetas, baixa, reabertura, localização e tombo."""
from __future__ import annotations

from datetime import date
from typing import Optional, Sequence

from ..database import db_cursor, registrar_auditoria
from ..erros import RegraNegocioError
from ..reservas import _promover_fila_cur, liberar_reservas_do_exemplar_cur

from .emprestimos import localizar_exemplar
from .regras import _atraso_e_multa


def listar_exemplares_para_etiquetas(
    termo: str = "", livro_ids: Optional[Sequence[int]] = None,
) -> list[dict]:
    """Exemplares ativos (não baixados) com o título do livro, para a
    impressão de etiquetas.

    Sem `livro_ids`, o filtro segue a busca do acervo (título, ISBN ou
    autor), e termo vazio significa o acervo inteiro.

    Com `livro_ids`, sai só o que a bibliotecária marcou na lista. É o
    caso comum na prática: chegaram seis livros novos, e reimprimir a
    etiqueta do acervo todo para colar seis é desperdício de papel.
    Nesse caso o termo da busca é ignorado, porque a seleção é mais
    específica do que ele.
    """
    if livro_ids is not None:
        ids = list(dict.fromkeys(int(i) for i in livro_ids))
        if not ids:
            return []
        marcadores = ", ".join("?" * len(ids))
        with db_cursor() as cur:
            cur.execute(
                f"""SELECT l.titulo, ex.codigo_barras, ex.numero_tombo,
                           ex.localizacao
                    FROM exemplar ex
                    JOIN livro l ON l.id = ex.livro_id
                    WHERE l.ativo = 1 AND ex.status != 'BAIXADO'
                      AND l.id IN ({marcadores})
                    ORDER BY l.titulo, ex.numero_tombo""",
                ids,
            )
            return [dict(r) for r in cur.fetchall()]

    termo_like = f"%{termo.strip()}%" if termo else "%"
    with db_cursor() as cur:
        cur.execute(
            """SELECT l.titulo, ex.codigo_barras, ex.numero_tombo,
                      ex.localizacao
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


def candidato_de_reabertura(codigo: str) -> Optional[dict]:
    """O empréstimo que *provavelmente* foi encerrado por uma baixa.

    Existe para o caso das baixas dadas antes de o vínculo
    `encerrado_por_baixa` existir — nelas não há registro de qual
    empréstimo a baixa fechou, e o único indício é a data.

    **Indício não é prova, e por isso isto não decide nada.** Um livro
    devolvido normalmente e baixado no mesmo dia casa pela data do mesmo
    jeito; reabrir por conta própria inventaria um empréstimo em aberto
    para um aluno que já entregou o livro. Quem confirma é a
    bibliotecária, olhando o nome e a data.

    @return None quando não há dúvida — ou porque não há candidato, ou
        porque o vínculo está registrado e `reverter_baixa` resolve
        sozinha.
    """
    ex = localizar_exemplar(codigo)
    if not ex or ex["status"] != "BAIXADO":
        return None
    with db_cursor() as cur:
        cur.execute("SELECT data_baixa FROM exemplar WHERE id = ?",
                    (ex["id"],))
        data_baixa = cur.fetchone()["data_baixa"]

        cur.execute("SELECT id FROM emprestimo WHERE exemplar_id = ? "
                    "AND encerrado_por_baixa = 1 LIMIT 1", (ex["id"],))
        if cur.fetchone() or not data_baixa:
            return None      # sem dúvida a resolver

        cur.execute(
            """SELECT e.id, e.data_emprestimo, e.data_prevista, e.multa,
                      u.nome, u.matricula
                 FROM emprestimo e JOIN usuario u ON u.id = e.usuario_id
                WHERE e.exemplar_id = ? AND date(e.data_devolucao) = date(?)
             ORDER BY e.id DESC LIMIT 1""", (ex["id"], data_baixa))
        linha = cur.fetchone()
    return dict(linha) if linha else None


def reverter_baixa(codigo: str, justificativa: str,
                   usuario_id: Optional[int] = None,
                   reabrir_emprestimo_id: Optional[int] = None) -> dict:
    """Desfaz uma baixa dada por engano, devolvendo o exemplar ao acervo.

    Existe por um caso real: na tela de detalhes do livro, "Dar baixa no
    exemplar" fica ao lado de "Corrigir tombo" e "Mudar prateleira" —
    dois botões inofensivos — e a bibliotecária clicou no errado. Até
    aqui não havia volta, e a baixa não é só o exemplar: ela **encerra
    o empréstimo e lança a multa** de quem estava com o livro. O engano
    de um clique cobrava de um aluno uma multa que não existia.

    O que é desfeito:

    · O exemplar volta ao acervo. Se havia um empréstimo encerrado pela
      baixa, ele reabre e o exemplar volta a EMPRESTADO — porque o livro
      continua com a pessoa; nada nunca esteve na estante.
    · A multa lançada pela baixa é apagada. Ela nunca deveria ter sido
      lançada: não houve atraso, houve um clique errado.
    · A reserva que a baixa **cancelou** — porque não sobrou exemplar
      nenhum do título — volta, na posição em que estava. Essa pessoa
      perdeu o lugar por causa do clique, não por decisão dela, e é um
      estrago que não aparece em tela nenhuma.

    O que não é desfeito: **a reserva que já ganhou outro exemplar.** A
    baixa devolveu as reservas à fila e pode ter separado outra cópia
    para o primeiro da vez; tirar isso dele seria trocar um erro por
    outro. O exemplar volta e, se estiver livre, entra na fila pela
    porta da frente.

    @param justificativa obrigatória: reverter uma baixa é corrigir o
        histórico do acervo, e histórico corrigido sem motivo escrito é
        histórico em que ninguém confia depois.
    @param reabrir_emprestimo_id só para baixas anteriores ao vínculo
        `encerrado_por_baixa`, em que o empréstimo a reabrir foi
        deduzido pela data e **confirmado por uma pessoa**. Ver
        `candidato_de_reabertura`.
    """
    justificativa = (justificativa or "").strip()
    if not justificativa:
        raise RegraNegocioError(
            "Explique por que a baixa está sendo revertida. Fica no "
            "histórico do exemplar.")

    ex = localizar_exemplar(codigo)
    if not ex:
        raise RegraNegocioError(
            "Exemplar não encontrado. Confira o código de barras ou o tombo.")
    if ex["status"] != "BAIXADO":
        raise RegraNegocioError(
            "Este exemplar está no acervo; não há baixa para reverter.")

    with db_cursor() as cur:
        cur.execute("SELECT data_baixa, motivo_baixa, numero_tombo "
                    "FROM exemplar WHERE id = ?", (ex["id"],))
        antes = cur.fetchone()

        # O empréstimo que a baixa encerrou, pelo vínculo registrado.
        cur.execute(
            "SELECT id, multa, multa_paga, multa_isenta FROM emprestimo "
            "WHERE exemplar_id = ? AND encerrado_por_baixa = 1 "
            "ORDER BY id DESC LIMIT 1", (ex["id"],))
        emp = cur.fetchone()
        confirmado = False

        if emp is None and reabrir_emprestimo_id is not None:
            # Baixa antiga, sem vínculo: só reabre o que uma pessoa
            # apontou, e mesmo assim conferindo que o empréstimo é deste
            # exemplar e foi encerrado no dia da baixa.
            cur.execute(
                "SELECT id, multa, multa_paga, multa_isenta FROM emprestimo "
                "WHERE id = ? AND exemplar_id = ? "
                "AND date(data_devolucao) = date(?)",
                (reabrir_emprestimo_id, ex["id"], antes["data_baixa"]))
            emp = cur.fetchone()
            if emp is None:
                raise RegraNegocioError(
                    "O empréstimo indicado não é deste exemplar ou não foi "
                    "encerrado na data da baixa.")
            confirmado = True

        multa_apagada = 0.0
        if emp is not None:
            movimentado = (float(emp["multa_paga"] or 0)
                           + float(emp["multa_isenta"] or 0))
            if movimentado > 0:
                # Dinheiro já entrou ou já foi perdoado. Reabrir o
                # empréstimo aqui bagunçaria o caixa; quem resolve isso é
                # gente, não o sistema.
                raise RegraNegocioError(
                    "A multa deste empréstimo já foi quitada ou isentada. "
                    "Reverter a baixa mexeria num valor já movimentado — "
                    "resolva a multa primeiro e tente de novo.")
            multa_apagada = float(emp["multa"] or 0)
            cur.execute(
                "UPDATE emprestimo SET data_devolucao = NULL, multa = 0, "
                "encerrado_por_baixa = 0 WHERE id = ?", (emp["id"],))

        # Emprestado se o livro voltou para a mão de alguém; disponível
        # se estava na estante quando a baixa aconteceu.
        novo_status = "EMPRESTADO" if emp is not None else "DISPONIVEL"
        cur.execute(
            "UPDATE exemplar SET status = ?, motivo_baixa = NULL, "
            "data_baixa = NULL WHERE id = ?", (novo_status, ex["id"]))

        # Quem foi cancelado por esta baixa volta para a fila, na
        # posição de antes: `criado_em` nunca foi tocado.
        cur.execute(
            "SELECT COUNT(*) AS n FROM reserva "
            "WHERE cancelada_por_baixa = ? AND status = 'CANCELADA'",
            (ex["id"],))
        reservas_restauradas = cur.fetchone()["n"]
        if reservas_restauradas:
            cur.execute(
                "UPDATE reserva SET status = 'ATIVA', "
                "cancelada_por_baixa = NULL "
                "WHERE cancelada_por_baixa = ? AND status = 'CANCELADA'",
                (ex["id"],))

        promovida = None
        if novo_status == "DISPONIVEL":
            promovida = _promover_fila_cur(cur, ex["livro_id"], ex["id"])

    registrar_auditoria(
        usuario_id, "BAIXA_REVERTIDA",
        f"exemplar={ex['codigo_barras']} livro={ex['titulo']} "
        f"motivo_original={antes['motivo_baixa'] or '?'} "
        f"justificativa={justificativa}"
        + (f" emprestimo_reaberto={emp['id']}" if emp is not None else "")
        + (" (reabertura confirmada por pessoa: baixa sem vinculo"
           " registrado)" if confirmado else "")
        + (f" reservas_restauradas={reservas_restauradas}"
           if reservas_restauradas else ""))

    return {
        "titulo": ex["titulo"],
        "codigo": ex["codigo_barras"],
        "status": novo_status,
        "emprestimo_reaberto": emp["id"] if emp is not None else None,
        "reabertura_confirmada": confirmado,
        "multa_apagada": round(multa_apagada, 2),
        "tombo": antes["numero_tombo"] or "",
        "reserva_atendida": promovida,
        "reservas_restauradas": reservas_restauradas,
    }


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
            # `encerrado_por_baixa` marca que este empréstimo não
            # terminou numa devolução de verdade. É o que permite
            # `reverter_baixa` reabrir exatamente este, sem adivinhar.
            cur.execute("""UPDATE emprestimo
                              SET data_devolucao = ?, multa = ?,
                                  encerrado_por_baixa = 1
                            WHERE id = ?""",
                        (hoje, multa, emp["id"]))

        cur.execute("""UPDATE exemplar
                          SET status = 'BAIXADO', motivo_baixa = ?,
                              data_baixa = ?
                        WHERE id = ?""", (motivo, hoje, ex["id"]))

        # Só depois de o exemplar estar BAIXADO: assim a reoferta dentro
        # de `liberar_reservas_do_exemplar_cur` nunca reoferece este
        # mesmo exemplar. Antes disto a reserva ficava ATIVA apontando
        # para um exemplar fora do acervo, e o aluno da vez ia até a
        # biblioteca buscar um livro que não existia mais.
        reservas_soltas = liberar_reservas_do_exemplar_cur(cur, ex["id"])

    registrar_auditoria(
        usuario_id, "BAIXA_EXEMPLAR",
        f"exemplar={ex['codigo_barras']} livro={ex['titulo']} motivo={motivo}"
        + (f" emprestimo_encerrado={emp['id']}" if emp else "")
        + (f" reservas_liberadas={len(reservas_soltas)}"
           if reservas_soltas else ""))

    return {
        "exemplar_id": ex["id"],
        "codigo_barras": ex["codigo_barras"],
        "titulo": ex["titulo"],
        "motivo": motivo,
        "estava_emprestado": bool(emp),
        "multa": multa,
    }


def alterar_localizacao_exemplar(codigo: str, localizacao: str,
                                  usuario_id: Optional[int] = None) -> dict:
    """Muda de prateleira um exemplar já cadastrado.

    A localização era definida uma vez no cadastro e não tinha como
    corrigir depois — mas estante muda: a biblioteca reorganiza, o livro
    volta para o lugar errado, ou a prateleira foi digitada errada na
    importação. Sem isto, o único caminho era excluir e recadastrar,
    perdendo o histórico de empréstimos do exemplar.

    Vale por exemplar, não pelo título: dois volumes do mesmo livro
    podem estar em estantes diferentes.
    """
    ex = localizar_exemplar(codigo)
    if not ex:
        raise RegraNegocioError(
            "Exemplar não encontrado. Confira o código de barras ou o tombo.")

    localizacao = (localizacao or "").strip()
    with db_cursor() as cur:
        cur.execute("UPDATE exemplar SET localizacao = ? WHERE id = ?",
                    (localizacao or None, ex["id"]))

    registrar_auditoria(
        usuario_id, "LOCALIZACAO_EXEMPLAR",
        f"exemplar={ex['codigo_barras']}; localizacao={localizacao or '(vazia)'}")
    return {
        "exemplar_id": ex["id"],
        "codigo_barras": ex["codigo_barras"],
        "titulo": ex["titulo"],
        "localizacao": localizacao,
    }


def alterar_tombo_exemplar(codigo: str, tombo: str,
                            usuario_id: Optional[int] = None) -> dict:
    """Corrige o número de tombo de um exemplar já cadastrado.

    O tombo é o número que está escrito no livro físico, e chegou errado
    em muito registro: a importação da planilha trouxe tombo trocado, e
    livro tombado à mão tem dígito ilegível. Sem isto, corrigir exigia
    excluir e recadastrar, perdendo o histórico de empréstimos.

    O tombo **não pode repetir**. Não é preciosismo: `localizar_exemplar`
    procura por `codigo_barras OR numero_tombo` e devolve o primeiro que
    achar, então dois exemplares com o mesmo tombo fazem o balcão
    emprestar ou devolver a cópia errada, sem avisar ninguém. O banco não
    tem UNIQUE nessa coluna (só índice), então a checagem é aqui.
    """
    ex = localizar_exemplar(codigo)
    if not ex:
        raise RegraNegocioError(
            "Exemplar não encontrado. Confira o código de barras ou o tombo.")

    tombo = (tombo or "").strip()
    if tombo:
        with db_cursor() as cur:
            cur.execute(
                """SELECT l.titulo
                   FROM exemplar ex JOIN livro l ON l.id = ex.livro_id
                   WHERE ex.numero_tombo = ? AND ex.id != ?
                   LIMIT 1""",
                (tombo, ex["id"]),
            )
            conflito = cur.fetchone()
        if conflito:
            raise RegraNegocioError(
                f'O tombo "{tombo}" já está em uso por outro exemplar '
                f'("{conflito["titulo"]}"). Dois exemplares com o mesmo '
                "tombo fazem o empréstimo pegar o livro errado.")

    with db_cursor() as cur:
        cur.execute("UPDATE exemplar SET numero_tombo = ? WHERE id = ?",
                    (tombo or None, ex["id"]))

    registrar_auditoria(
        usuario_id, "TOMBO_EXEMPLAR",
        f"exemplar={ex['codigo_barras']}; "
        f"tombo={ex.get('numero_tombo') or '(vazio)'} -> {tombo or '(vazio)'}")
    return {
        "exemplar_id": ex["id"],
        "codigo_barras": ex["codigo_barras"],
        "titulo": ex["titulo"],
        "numero_tombo": tombo,
    }
