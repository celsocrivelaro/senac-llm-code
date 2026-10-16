-- Aula 13 — Os dados: política, despesas de dois usuários, e o regulamento.

INSERT INTO politica (categoria, teto) VALUES
    ('refeicao', 120.00),
    ('transporte', 250.00),
    ('hospedagem', 480.00),
    ('outros', 90.00);

-- Dois usuários, cada um com as suas despesas. `ana` não vê as de `bruno`,
-- e vice-versa — nem perguntando pelo identificador exato.
INSERT INTO despesas (id, usuario_id, categoria, valor, cidade) VALUES
    ('D-4612', 'ana', 'refeicao', 138.00, 'Sao Paulo'),
    ('D-4613', 'ana', 'hospedagem', 590.00, 'Lisboa'),
    ('D-4614', 'bruno', 'transporte', 96.00, 'Recife'),
    ('D-4615', 'bruno', 'refeicao', 84.00, 'Sorocaba'),
    ('D-4616', 'bruno', 'hospedagem', 610.00, 'Rio de Janeiro');

INSERT INTO regulamento (artigo, texto) VALUES
    ('art-7', 'Art. 7º Refeição: teto de R$ 120,00 por refeição, mediante nota fiscal. Bebida alcoólica não é reembolsável.'),
    ('art-12', 'Art. 12. Hospedagem: teto de R$ 480,00 por diária. §1º Nas capitais, o teto da hospedagem é de R$ 620,00 por diária.'),
    ('art-19', 'Art. 19. Viagem internacional: os tetos de refeição, transporte e hospedagem são acrescidos de 60%, vedada a cumulação com o acréscimo das capitais.'),
    ('art-23', 'Art. 23. Transporte por aplicativo ou táxi: teto de R$ 250,00 por trecho, com o recibo do aplicativo.'),
    ('art-31', 'Art. 31. Prazo: a despesa deve ser apresentada em até 30 dias da data da nota fiscal; fora do prazo, não é reembolsada.');
