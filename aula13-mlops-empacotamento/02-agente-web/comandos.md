# Comandos — 02-agente-web

Todos os comandos são executados **dentro desta pasta**.

## Preparar o `.env`

```bash
cp .env.example .env
# preencher LLM_PROVEDOR e a chave do provedor escolhido
```

## Rodar sem Docker

```bash
uvicorn api:app --port 8000
```

## Construir a imagem

```bash
docker build -t auditor-de-despesas-web:1.0.0 .
```

## Executar o container

```bash
# Em primeiro plano (Ctrl+C para parar):
docker run --rm -p 8000:8000 --env-file .env auditor-de-despesas-web:1.0.0

# Em segundo plano, com nome:
docker run -d --rm -p 8000:8000 --env-file .env --name web-agent auditor-de-despesas-web:1.0.0
```

- `-p <porta-no-seu-pc>:<porta-do-container>` publica a porta. Ex.: `-p 8088:8000` atende em `localhost:8088`;
- `-d` roda **em segundo plano** (*detached*) e devolve o terminal;
- `--rm` **apaga o container** quando ele para;
- `--name` dá um nome ao container: só letras, dígitos, `_`, `.` e `-` — sem `/`;
- o nome da imagem vem **por último**.

Com o Ollama rodando na máquina, acrescente
`-e OLLAMA_BASE_URL=http://host.docker.internal:11434`.

## Testar a API

```bash
curl localhost:8000/saude

curl -X POST localhost:8000/perguntas \
     -H 'content-type: application/json' \
     -d '{"pergunta": "A despesa D-4613 está dentro da política?"}'
```

A documentação interativa fica em `http://localhost:8000/docs`.

## Acompanhar o container

```bash
docker ps                      # containers rodando
docker logs -f web-agent       # log do uvicorn (Ctrl+C sai do log, não para o container)
docker exec -it web-agent sh   # um shell dentro do container
docker stop web-agent          # para (e, com --rm, apaga)
```

## Inspecionar a imagem

```bash
docker images auditor-de-despesas-web
docker history auditor-de-despesas-web:1.0.0
```

## Publicar no Docker Hub

```bash
docker login
docker tag auditor-de-despesas-web:1.0.0 celsocrivelaro/web-agent:1.0
docker push celsocrivelaro/web-agent:1.0

# Ou construir já com o nome do Docker Hub:
docker build -t celsocrivelaro/web-agent:1.0 .
docker push celsocrivelaro/web-agent:1.0

# Em qualquer máquina com Docker:
docker run -d --rm -p 8088:8000 --env-file .env --name web-agent celsocrivelaro/web-agent:1.0
```

## Limpar

```bash
docker rmi auditor-de-despesas-web:1.0.0 celsocrivelaro/web-agent:1.0
```
