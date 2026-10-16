-- Aula 13 — O esquema: dados fixos e o corpus do RAG, no mesmo Postgres.
--
-- Os scripts de /docker-entrypoint-initdb.d/ rodam em ordem alfabética, UMA
-- VEZ, com o volume vazio. `docker compose down -v` apaga o volume e faz
-- os dois rodarem de novo.

-- DADOS FIXOS: a política e as despesas. Cada despesa PERTENCE a um usuário,
-- e é essa coluna que o isolamento usa: a ferramenta só lê as despesas do
-- usuário que fez a pergunta.
CREATE TABLE politica (
    categoria TEXT PRIMARY KEY,
    teto NUMERIC(10, 2) NOT NULL CHECK (teto > 0)
);

CREATE TABLE despesas (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL,
    categoria TEXT NOT NULL REFERENCES politica (categoria),
    valor NUMERIC(10, 2) NOT NULL,
    cidade TEXT NOT NULL
);

CREATE INDEX despesas_por_usuario ON despesas (usuario_id);

-- O CORPUS DO RAG: os artigos do regulamento. A recuperação é por busca
-- textual do próprio Postgres: `busca` é um tsvector gerado a partir do
-- texto com a configuração `portuguese`, que reduz as palavras ao radical e
-- descarta as palavras vazias. O índice GIN torna a busca rápida.
--
-- É recuperação LÉXICA. A variante vetorial, com a extensão pgvector e uma
-- coluna de embeddings, troca este índice por um de similaridade — e passa
-- a exigir um modelo de embeddings para indexar e para consultar.
CREATE TABLE regulamento (
    artigo TEXT PRIMARY KEY,
    texto TEXT NOT NULL,
    busca TSVECTOR GENERATED ALWAYS AS (to_tsvector('portuguese', texto)) STORED
);

CREATE INDEX regulamento_busca ON regulamento USING GIN (busca);
