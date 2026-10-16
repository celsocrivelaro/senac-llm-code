# Comandos — 03-agente-web-banco

Todos os comandos são executados **dentro desta pasta**. Aqui não se usa
`docker run`: o `docker compose` sobe os dois containers — o banco e a API —
e os liga numa rede própria.

## Preparar o `.env`

```bash
cp .env.example .env
# preencher LLM_PROVEDOR, a chave do provedor e as credenciais do banco
```

## Subir e derrubar

```bash
docker compose up --build        # em primeiro plano, com os logs dos dois (Ctrl+C para)
docker compose up -d --build     # em segundo plano

docker compose down              # derruba os containers; o volume do banco fica
docker compose down -v           # derruba e APAGA o volume: o script de inicialização roda de novo na próxima subida
```

## Testar a API

```bash
curl localhost:8000/saude        # "banco": true quando o Postgres responde

curl -X POST localhost:8000/perguntas \
     -H 'content-type: application/json' \
     -d '{"pergunta": "A despesa D-4613 está dentro da política?"}'
```

## Acompanhar

```bash
docker compose ps                # os dois serviços e o estado do healthcheck
docker compose logs -f agente    # log da API
docker compose logs banco        # log do Postgres: na primeira subida, mostra o 01-politica.sql rodando
```

## Olhar dentro do banco

```bash
docker compose exec banco sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT * FROM politica;"'

# Mudar a política sem tocar no código, e perguntar de novo:
docker compose exec banco sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "UPDATE politica SET teto = 700 WHERE categoria = '\''hospedagem'\'';"'
```

## Ver o estado sobreviver (e não sobreviver)

```bash
docker compose down && docker compose up -d     # o UPDATE acima continua lá: o dado mora no volume
docker compose down -v && docker compose up -d  # o volume foi apagado: o script recria a política original
```

## Publicar a imagem da API no Docker Hub

```bash
docker login
docker tag auditor-de-despesas-banco:1.0.0 celsocrivelaro/web-agent-banco:1.0
docker push celsocrivelaro/web-agent-banco:1.0
```

A imagem do banco é a oficial (`postgres:16.10`) e não precisa ser publicada.

## Limpar

```bash
docker compose down -v --rmi local    # containers, volume e a imagem da API
```
