"""O que o app mostra ao aluno sobre ele mesmo."""
from __future__ import annotations

from ..database import db_cursor


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
