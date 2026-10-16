# Comandos — 04-agente-complexo

Todos os comandos são executados **dentro desta pasta**. O `docker compose`
sobe três containers: o banco (Postgres), a memória (Redis) e a API.

## Preparar o `.env`

```bash
cp .env.example .env
# preencher LLM_PROVEDOR, a chave do provedor e as credenciais do banco
```

## Subir e derrubar

```bash
docker compose up --build        # em primeiro plano (Ctrl+C para)
docker compose up -d --build     # em segundo plano

docker compose down              # derruba; os volumes do banco e da memória ficam
docker compose down -v           # derruba e APAGA os volumes: banco volta aos scripts, memória volta vazia
```

## Testar a API

Toda requisição diz quem pergunta (`X-Usuario-Id`) e em qual conversa
(`X-Sessao-Id`).

```bash
curl localhost:8000/saude        # "banco" e "memoria" devem vir true

curl -X POST localhost:8000/perguntas -H 'content-type: application/json' \
     -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s1' \
     -d '{"pergunta": "Quais são as minhas despesas?"}'
```

## Ver a memória de curto prazo (a sessão)

```bash
# Segunda pergunta na mesma sessão: "a segunda" só faz sentido com o histórico.
curl -X POST localhost:8000/perguntas -H 'content-type: application/json' \
     -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s1' \
     -d '{"pergunta": "A segunda delas é reembolsável? Lisboa é viagem internacional."}'

curl localhost:8000/memoria -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s1'
```

## Ver a memória de longo prazo (os fatos do usuário)

```bash
curl -X POST localhost:8000/perguntas -H 'content-type: application/json' \
     -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s1' \
     -d '{"pergunta": "Para registro: trabalho baseada em São Paulo e viajo sempre a serviço."}'

# Outra sessão da mesma usuária: o histórico começa vazio, os fatos vêm junto.
curl localhost:8000/memoria -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s2'
```

## Ver o isolamento

```bash
# A D-4613 é da ana. Para o bruno, ela não existe.
curl -X POST localhost:8000/perguntas -H 'content-type: application/json' \
     -H 'X-Usuario-Id: bruno' -H 'X-Sessao-Id: s1' \
     -d '{"pergunta": "A despesa D-4613 está dentro da política?"}'

# A sessão s1 do bruno não é a sessão s1 da ana.
curl localhost:8000/memoria -H 'X-Usuario-Id: bruno' -H 'X-Sessao-Id: s1'

# Identificador com ":" é recusado (400): ele escreveria na chave de outro usuário.
curl localhost:8000/memoria -H 'X-Usuario-Id: ana:s1' -H 'X-Sessao-Id: x'
```

## Ver o RAG

```bash
# A hospedagem de Lisboa (D-4613) depende de exceções do regulamento: capital e viagem internacional.
curl -X POST localhost:8000/perguntas -H 'content-type: application/json' \
     -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s3' \
     -d '{"pergunta": "A D-4613 é reembolsável? Considere as regras do regulamento."}'

# A busca que a ferramenta faz, direto no banco:
docker compose exec banco sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT artigo, ts_rank(busca, q) FROM regulamento, websearch_to_tsquery('\''portuguese'\'', '\''hospedagem em capital'\'') q WHERE busca @@ q ORDER BY 2 DESC;"'
```

## Esquecer

```bash
curl -X DELETE localhost:8000/memoria/sessao -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s1'   # só esta sessão
curl -X DELETE localhost:8000/memoria -H 'X-Usuario-Id: ana'                                # tudo da ana
```

## Olhar dentro do Redis e do banco

```bash
docker compose exec memoria redis-cli KEYS '*'                    # as chaves: sessao:<usuario>:<sessao> e fatos:<usuario>
docker compose exec memoria redis-cli LRANGE sessao:ana:s1 0 -1   # o histórico guardado
docker compose exec memoria redis-cli TTL sessao:ana:s1           # segundos até a sessão expirar
docker compose exec memoria redis-cli LRANGE fatos:ana 0 -1       # os fatos da ana

docker compose exec banco sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT * FROM despesas ORDER BY usuario_id, id;"'
```

## Acompanhar

```bash
docker compose ps
docker compose logs -f agente
```

## Publicar a imagem da API no Docker Hub

```bash
docker login
docker tag auditor-de-despesas-complexo:1.0.0 celsocrivelaro/agente-complexo:1.0
docker push celsocrivelaro/agente-complexo:1.0
```

As imagens do banco (`postgres:16.10`) e da memória (`redis:7.4.2`) são
oficiais e não precisam ser publicadas.

## Limpar

```bash
docker compose down -v --rmi local    # containers, volumes e a imagem da API
```
