# Aula 13 — Os dados fixos e o RAG, no Postgres.
#
# Três consultas, todas parametrizadas: o texto que chega aqui vem do
# modelo, e o modelo não é fonte confiável. Concatenar o texto na SQL
# abriria injeção de SQL.

import os

import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://agente:agente@localhost:5432/despesas")


def despesa_do_usuario(usuario: str, despesa: str) -> dict | None:
    """A despesa, SÓ SE pertencer ao usuário. O filtro por usuário é o isolamento."""
    with psycopg.connect(DATABASE_URL) as c:
        linha = c.execute(
            "SELECT id, categoria, valor, cidade FROM despesas WHERE id = %s AND usuario_id = %s",
            (despesa, usuario),
        ).fetchone()
    if linha is None:
        return None
    return {"despesa": linha[0], "categoria": linha[1], "valor": float(linha[2]), "cidade": linha[3]}


def despesas_do_usuario(usuario: str) -> list[str]:
    with psycopg.connect(DATABASE_URL) as c:
        return [d for (d,) in c.execute("SELECT id FROM despesas WHERE usuario_id = %s ORDER BY id", (usuario,))]


def teto(categoria: str) -> float | None:
    with psycopg.connect(DATABASE_URL) as c:
        linha = c.execute("SELECT teto FROM politica WHERE categoria = %s", (categoria,)).fetchone()
    return None if linha is None else float(linha[0])


def buscar_regulamento(consulta: str, k: int = 3) -> list[dict]:
    """A RECUPERAÇÃO do RAG: os k artigos mais relevantes para a consulta.

    `websearch_to_tsquery` aceita texto livre (o que o modelo escreve) e o
    reduz aos mesmos radicais do índice; `ts_rank` ordena por relevância.
    """
    with psycopg.connect(DATABASE_URL) as c:
        linhas = c.execute(
            """
            SELECT artigo, texto, ts_rank(busca, q) AS relevancia
            FROM regulamento, websearch_to_tsquery('portuguese', %s) AS q
            WHERE busca @@ q
            ORDER BY relevancia DESC
            LIMIT %s
            """,
            (consulta, k),
        ).fetchall()
    return [{"artigo": a, "texto": t, "relevancia": round(float(r), 4)} for a, t, r in linhas]


def ok() -> bool:
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=2) as c:
            c.execute("SELECT 1")
        return True
    except psycopg.OperationalError:
        return False
