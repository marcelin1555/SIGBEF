"""Estatísticas do painel e relatórios de uso."""
from __future__ import annotations

from datetime import date
from typing import Optional

from ..database import db_cursor


def estatisticas() -> dict:
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS qt FROM livro WHERE ativo = 1")
        livros = cur.fetchone()["qt"]
        # `!= 'BAIXADO'`: exemplar baixado saiu do acervo. Contá-lo aqui
        # fazia o painel anunciar um acervo maior do que a biblioteca
        # tem, e o número só crescia — baixar um livro perdido aumentava
        # a contagem de exemplares em vez de diminuir.
        cur.execute(
            "SELECT COUNT(*) AS qt FROM exemplar WHERE status != 'BAIXADO'")
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
                       -- Alias `multa_aberta`, e não `multa`: dentro de
                       -- HAVING o SQLite resolve o nome `multa` para a
                       -- COLUNA da tabela, não para o alias. Com a coluna
                       -- passando a sobreviver à quitação, quem já pagou
                       -- continuaria aparecendo como inadimplente.
                       IFNULL(SUM(CASE
                           WHEN e.multa - e.multa_paga - e.multa_isenta > 0
                           THEN e.multa - e.multa_paga - e.multa_isenta
                       END), 0) AS multa_aberta,
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
               HAVING multa_aberta > 0 OR em_atraso > 0
                ORDER BY vencimento_antigo IS NULL, vencimento_antigo,
                         multa_aberta DESC, u.nome""",
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
        # Volta a se chamar `multa` para fora: quem consome a lista quer
        # saber quanto a pessoa deve, e o alias interno só existe para
        # desfazer a ambiguidade com a coluna dentro do HAVING.
        linha["multa"] = round(float(linha.pop("multa_aberta") or 0), 2)
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
                          IFNULL(SUM(e.multa), 0),
                          IFNULL(SUM(e.multa_paga), 0),
                          IFNULL(SUM(e.multa_isenta), 0)
                        FROM emprestimo e
                       WHERE e.data_devolucao IS NOT NULL {onde_dev}""",
                    p_dev)
        linha = cur.fetchone()
        com_atraso, multa_total = (linha[0] or 0), (linha[1] or 0.0)
        # Lancado, recebido e isento sao tres numeros diferentes. Ate a
        # v1.10.4 existia so um, e ele mudava de significado dependendo de
        # alguem ter clicado em "quitar" -- o rotulo dizia "Multas
        # lancadas" e o valor era "multas que ninguem pagou".
        multa_recebida, multa_isenta = (linha[2] or 0.0), (linha[3] or 0.0)

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
        "multa_recebida": round(multa_recebida, 2),
        "multa_isenta": round(multa_isenta, 2),
        "multa_em_aberto": round(
            multa_total - multa_recebida - multa_isenta, 2),
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

    O deslocamento de meses sempre parte do primeiro dia do mês
    (`'start of month'`), nunca do dia de hoje direto. Sem isso, no dia
    31 de um mês, `date('now', '-1 months')` cai num mês sem dia 31 (ex.:
    30/06) e o SQLite **rola para a frente**, não para trás — devolvendo
    01/07 em vez de 30/06. O resultado: dois meses diferentes colapsavam
    no mesmo rótulo (e um terceiro sumia), dobrando a contagem exibida.
    Só acontece nos dias 29, 30 ou 31, o que fez o defeito passar
    despercebido em meses de teste mais curtos.
    """
    offset = f"-{int(meses) - 1} months"
    with db_cursor() as cur:
        cur.execute(
            """SELECT strftime('%Y-%m', data_emprestimo) AS mes,
                       COUNT(*) AS emprestimos
                 FROM emprestimo
                WHERE data_emprestimo >= date('now','localtime','start of month',?)
                GROUP BY mes ORDER BY mes""",
            (offset,),
        )
        achados = {r["mes"]: r["emprestimos"] for r in cur.fetchall()}

        # Série completa, para o eixo não ter furo.
        cur.execute(
            """WITH RECURSIVE seq(n) AS (
                   SELECT 0 UNION ALL SELECT n + 1 FROM seq WHERE n < ?
               )
               SELECT strftime('%Y-%m',
                               date('now','localtime','start of month',
                                    '-' || (? - n) || ' months')
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
