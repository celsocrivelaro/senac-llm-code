# Comandos — 05-agent-ci

Todos os comandos são executados **dentro desta pasta**. Eles reproduzem,
na máquina, os três jobs do `.github/workflows/ci.yml`.

## Preparar

```bash
cp .env.example .env                 # chave do modelo, para o eval
pip install -r requirements-dev.txt  # dependências do agente + pytest
```

## Job 1 — segurança do Dockerfile

```bash
# hadolint: boas práticas do Dockerfile (falha só em "error")
docker run --rm -i hadolint/hadolint:v2.12.0 hadolint --failure-threshold error - < Dockerfile

# Trivy: má configuração de segurança (aponta o processo rodando como root)
docker run --rm -v "$PWD":/src aquasec/trivy:0.57.1 config --severity HIGH,CRITICAL /src
```

## Job 2 — testes e eval

```bash
pytest -v              # unitários: ferramentas, veredito e API, sem chamar o modelo
pytest -v -s -m eval   # eval: o agente contra o gabarito, chamando o modelo (custa tokens)
```

## Job 3 — construir e publicar

```bash
docker build -t agent-ci:dev .
docker run --rm -p 8000:8000 --env-file .env agent-ci:dev

docker login
docker tag agent-ci:dev celsocrivelaro/agent-ci:latest
docker push celsocrivelaro/agent-ci:latest
```

## Colocar o pipeline para rodar no GitHub

O GitHub só executa workflows em `.github/workflows/` na **raiz** do
repositório. Com esta pasta como raiz de um repositório próprio:

```bash
git init && git add . && git commit -m "agente com CI"
git remote add origin git@github.com:<usuario>/<repositorio>.git
git push -u origin main
```

Depois, em **Settings > Secrets and variables > Actions**, crie os secrets:

| Secret | Para quê |
|---|---|
| `DOCKERHUB_USERNAME` | o usuário do Docker Hub |
| `DOCKERHUB_TOKEN` | um token de acesso do Docker Hub (*Account settings > Personal access tokens*), não a senha |
| `GROQ_API_KEY` | a chave do modelo, para o eval; sem ela, o passo do eval é pulado |

E, na aba **Variables** da mesma tela, a variável:

| Variável | Para quê |
|---|---|
| `GROQ_MODELO` | o modelo da Groq usado no eval (ex.: `openai/gpt-oss-20b`). Sem ela, vale o padrão do `cliente.py` |

Cada push para a `main` roda os três jobs; um *pull request* roda só os dois
primeiros. O andamento fica na aba **Actions** do repositório.
