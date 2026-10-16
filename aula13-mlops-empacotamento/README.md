# Aula 13 — MLOps e empacotamento

Laboratório da parte de empacotamento: o mesmo agente simples, empacotado
em imagem Docker de quatro formas, da mais simples à mais completa, e um pipeline de CI/CD que o verifica, testa e publica (05).

## O caso de uso

> Dado um agente que roda na máquina de quem o escreveu, empacotá-lo de modo
> que qualquer máquina com Docker o execute igual — como programa de linha de
> comando e como API.

O agente é um auditor de despesas com duas ferramentas
(`consultar_despesa`, `consultar_politica`), montado com `create_agent`. O
modelo é escolhido por `LLM_PROVEDOR` no `.env` entre Mistral, Ollama e Groq.

## As pastas

Cada pasta é autossuficiente e é também o **contexto de build** da sua
imagem: tem o próprio `agente.py`, `cliente.py`, `requirements.txt`,
`Dockerfile`, `.dockerignore` e `.env.example`.

| Pasta | O que é | A imagem |
|---|---|---|
| `01-agente-cli/` | o agente como programa: o objetivo vem da linha de comando, a resposta sai na tela, e o processo termina | `ENTRYPOINT ["python", "agente.py"]` |
| `02-agente-web/` | o agente como API: `POST /perguntas` recebe a pergunta e devolve a resposta; `GET /saude` diz se o processo está de pé | `CMD ["uvicorn", "api:app", ...]`, porta 8000 |
| `03-agente-web-banco/` | o mesmo agente como API, com a política de reembolso numa tabela do Postgres; o `docker-compose.yml` sobe o banco e a API juntos, e o banco nasce de um script de inicialização | a imagem da 02, sem mudança; o banco é a imagem oficial `postgres:16.10` |
| `04-agente-complexo/` | o agente completo como API: despesas por usuário e política no Postgres (dados fixos), regulamento recuperado por busca textual no Postgres (RAG), histórico da sessão e fatos do usuário no Redis (memória), tudo isolado por `X-Usuario-Id` e `X-Sessao-Id` | três serviços no compose: `postgres:16.10`, `redis:7.4.2` e a API |
| `05-agent-ci/` | a API da 02 com um pipeline de GitHub Actions (`.github/workflows/ci.yml`): verificação de segurança do `Dockerfile` (hadolint e Trivy), testes unitários e eval do agente contra um gabarito, e publicação da imagem no Docker Hub | a imagem da 02, construída e publicada pelo pipeline |

O `.gitignore` desta pasta vale para as duas.

## 01 — o agente na linha de comando

```bash
cd 01-agente-cli
cp .env.example .env    # e preencher a chave
python agente.py "A despesa D-4613 está dentro da política?"

docker build -t auditor-de-despesas:1.0.0 .
docker run --rm --env-file .env auditor-de-despesas:1.0.0 "A despesa D-4613 está dentro da política?"
```

## 02 — o agente como API

```bash
cd 02-agente-web
cp .env.example .env
uvicorn api:app --port 8000

docker build -t auditor-de-despesas-web:1.0.0 .
docker run --rm -p 8000:8000 --env-file .env auditor-de-despesas-web:1.0.0
```

Em outro terminal:

```bash
curl localhost:8000/saude
curl -X POST localhost:8000/perguntas \
     -H 'content-type: application/json' \
     -d '{"pergunta": "A despesa D-4613 está dentro da política?"}'
```

A documentação interativa da API fica em `http://localhost:8000/docs`.

O que muda em relação à 01 está no bloco 4 do `Dockerfile`: em vez de um
programa que roda e termina, um servidor que fica de pé. Daí o
`--host 0.0.0.0` — com o padrão `127.0.0.1`, o uvicorn escuta só dentro do
container e o `-p 8000:8000` não alcança nada — e o `-p` no `docker run`,
que publica a porta do container na máquina.

A API é **síncrona**: a conexão fica aberta enquanto o agente trabalha. Serve
a um agente de poucos passos, como este; para execuções que levam minutos,
a entrega passa a ser por fila, *webhook* ou SSE.

## 03 — o agente como API, com a política no banco

```bash
cd 03-agente-web-banco
cp .env.example .env    # chave do modelo e credenciais do banco
docker compose up --build
```

Em outro terminal, os mesmos `curl` da 02; o `/saude` passa a dizer também
se o banco responde.

O que muda em relação à 02 não está na imagem da API, e sim no ambiente em
volta dela:

- **a política é um dado no banco**, e não um dicionário no código: a
  ferramenta `consultar_politica` faz uma consulta parametrizada à tabela
  `politica`;
- **o banco nasce de um script de inicialização** (`banco/01-politica.sql`),
  montado em `/docker-entrypoint-initdb.d/`. A imagem do Postgres o executa
  **uma vez**, com o volume vazio. Mudar o script depois não altera o banco
  existente: `docker compose down -v` apaga o volume e faz o script rodar de
  novo;
- **o estado tem endereço declarado**: os dados vivem no volume `dados`,
  fora do container — derrubar e subir de novo não perde a política;
- **a API alcança o banco pelo nome do serviço** (`banco:5432`), e não por
  `localhost`; o banco não publica porta na máquina hospedeira;
- **o `depends_on` com `service_healthy`** faz a API esperar o banco aceitar
  conexões, e não apenas iniciar.

## 04 — o agente completo: dados fixos, RAG, memória e isolamento

```bash
cd 04-agente-complexo
cp .env.example .env
docker compose up --build
```

Toda requisição diz **quem** pergunta e **em qual conversa**, nos cabeçalhos:

```bash
curl -X POST localhost:8000/perguntas -H 'content-type: application/json' \
     -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s1' \
     -d '{"pergunta": "Quais são as minhas despesas? A D-4613 é reembolsável?"}'

curl localhost:8000/memoria -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s1'
curl -X DELETE localhost:8000/memoria/sessao -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s1'
curl -X DELETE localhost:8000/memoria -H 'X-Usuario-Id: ana'
```

| Peça | Onde | O que mostra |
|---|---|---|
| **dados fixos** | Postgres, `despesas` e `politica` (`banco/*.sql`) | cada despesa pertence a um usuário; a ferramenta filtra pelo usuário da requisição |
| **RAG** | Postgres, `regulamento`, com `tsvector` em português e índice GIN | o modelo pede artigos por texto livre, e os mais relevantes voltam como contexto; a variante vetorial seria pgvector com embeddings |
| **memória de curto prazo** | Redis, `sessao:{usuario}:{sessao}` | o histórico da conversa, com janela (`JANELA_MENSAGENS`) e prazo (`SESSAO_TTL_S`) |
| **memória de longo prazo** | Redis, `fatos:{usuario}` | o que o usuário declarou sobre si, gravado pela ferramenta `anotar_fato`, válido entre sessões |
| **isolamento** | `agente.py` e `memoria.py` | as ferramentas são construídas por requisição, presas ao usuário do cabeçalho; o modelo escolhe **qual** despesa, nunca **de quem** |

Para ver o isolamento: pergunte como `bruno` pela `D-4613`, que é da `ana` —
a resposta é "despesa inexistente para este usuário". E abra outra sessão da
`ana` (`X-Sessao-Id: s2`): o histórico começa vazio, mas os fatos dela vêm
junto.

`DELETE /memoria` apaga tudo o que o agente guarda do usuário — fatos e todas
as sessões: é a operação que um pedido de esquecimento exige.

## Ollama dentro do container

Dentro do container, `localhost` é o próprio container, e não a máquina onde
o Ollama roda. Sobrescreva o endereço no `docker run`:

```bash
-e OLLAMA_BASE_URL=http://host.docker.internal:11434
```

## A imagem

Os três `Dockerfile` têm quatro blocos, comentados no próprio arquivo: base com
versão fixada até o *patch*, dependências **antes** do código, `COPY` com
lista explícita, e o comando — que é o que distingue a 01 das outras duas.

A ordem das camadas aparece no build seguinte: altere uma linha do
`agente.py` e reconstrua — a camada do `pip install` vem do cache.

## O segredo, e o que o histórico guarda — duas vezes

**No git.** Apagar o arquivo **não apaga o segredo**: ele fica no histórico,
em todos os clones.

```bash
git log --all -- .env
git log --all -S "_API_KEY=" --oneline
```

**Na imagem.** Um `COPY .env .` seguido de `RUN rm .env` deixa a chave na
camada do `COPY`: o `rm` só acrescenta uma camada que a esconde. O
`docker history` lista as camadas, e o `docker save` as extrai.

```bash
docker history auditor-de-despesas:1.0.0
```

Os `Dockerfile` da aula se protegem duas vezes: o `.env` está no
`.dockerignore`, e o `COPY` lista os arquivos por nome. A chave chega em
tempo de execução, pelo `--env-file`.

Nas duas formas, a correção é **revogar a chave** no provedor — e não
reescrever o histórico nem reconstruir a imagem, que não alcançam os clones
e as cópias que já existem.

## Custo

O build não chama o modelo. Cada `docker run` da 01, e cada `POST /perguntas`
da 02, faz uma execução do agente.
