# Comandos — 01-agente-cli

Todos os comandos são executados **dentro desta pasta**.

## Preparar o `.env`

```bash
cp .env.example .env
# preencher LLM_PROVEDOR e a chave do provedor escolhido
```

## Rodar sem Docker

```bash
python agente.py "A despesa D-4613 está dentro da política?"
```

## Construir a imagem

```bash
docker build -t auditor-de-despesas:1.0.0 .
```

## Executar o container

```bash
# O texto depois do nome da imagem vira o objetivo do agente.
docker run --rm --env-file .env auditor-de-despesas:1.0.0 "A despesa D-4613 está dentro da política?"

# Com o Ollama rodando na máquina: dentro do container, localhost é o próprio container.
docker run --rm --env-file .env -e OLLAMA_BASE_URL=http://host.docker.internal:11434 auditor-de-despesas:1.0.0 "A despesa D-4613 está dentro da política?"
```

- `--rm` apaga o container quando o processo termina;
- `--env-file .env` entrega as chaves em tempo de execução: o `.env` não entra na imagem.

## Inspecionar a imagem

```bash
docker images auditor-de-despesas              # tamanho
docker history auditor-de-despesas:1.0.0       # camadas: nenhuma pode vir de um COPY do .env
docker run --rm --entrypoint sh auditor-de-despesas:1.0.0 -c "ls -A /app"   # o que entrou na imagem
```

## Ver o cache das camadas

```bash
# Altere uma linha do agente.py e reconstrua: a camada do pip install vem do cache.
docker build -t auditor-de-despesas:1.0.0 .
```

## Ver que o container é efêmero

```bash
docker run --rm --entrypoint sh auditor-de-despesas:1.0.0 -c "date > /app/estado.txt; cat /app/estado.txt"
docker run --rm --entrypoint sh auditor-de-despesas:1.0.0 -c "cat /app/estado.txt"   # o arquivo não existe mais

# Com um volume, o arquivo sobrevive entre execuções.
docker run --rm -v auditor-estado:/dados --entrypoint sh auditor-de-despesas:1.0.0 -c "date > /dados/estado.txt"
docker run --rm -v auditor-estado:/dados --entrypoint sh auditor-de-despesas:1.0.0 -c "cat /dados/estado.txt"
docker volume rm auditor-estado
```

## Verificar o segredo no git

```bash
git log --all -- .env                    # o .env já foi versionado alguma vez?
git log --all -S "_API_KEY=" --oneline   # alguma chave já entrou num commit?
```

## Publicar no Docker Hub

```bash
docker login
docker tag auditor-de-despesas:1.0.0 celsocrivelaro/cli-agent:1.0
docker push celsocrivelaro/cli-agent:1.0
```

## Limpar

```bash
docker rmi auditor-de-despesas:1.0.0 celsocrivelaro/cli-agent:1.0
```
