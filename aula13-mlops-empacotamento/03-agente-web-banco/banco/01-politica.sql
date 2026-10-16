-- Aula 13 — A política de reembolso, no banco.
--
-- SCRIPT DE INICIALIZAÇÃO: a imagem oficial do Postgres executa os arquivos
-- de /docker-entrypoint-initdb.d/ em ordem alfabética, UMA VEZ, quando o
-- diretório de dados está vazio — isto é, na primeira subida do volume.
-- Mudar este arquivo depois disso não altera um banco que já existe: é
-- preciso apagar o volume (`docker compose down -v`) para que ele rode de novo.

CREATE TABLE politica (
    categoria TEXT PRIMARY KEY,
    teto NUMERIC(10, 2) NOT NULL CHECK (teto > 0)
);

INSERT INTO politica (categoria, teto) VALUES
    ('refeicao', 120.00),
    ('transporte', 250.00),
    ('hospedagem', 480.00),
    ('outros', 90.00);
