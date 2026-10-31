# Aula 15 — Produção: observabilidade

Laboratório da aula de observabilidade. O empacotamento em Docker está na
aula de MLOps e empacotamento (`aula13-mlops-empacotamento/`).

## O caso de uso

> Dado um agente que roda, saber o que ele fez em cada execução — quanto
> tempo levou, quanto custou, por que terminou e onde falhou — sem ler o
> código.

## Dependências novas

O SDK do OpenTelemetry e o exportador OTLP, no `requirements.txt` da raiz.

## Os módulos

| Arquivo | O que é |
|---|---|
| `01-trace-e-log.py` | **trace e log** num programa comum, sem LLM: busca um pokémon na PokeAPI. Cada busca é um *trace* (`buscar_pokemon` na raiz, com um *span* `CLIENT` para a chamada HTTP e um para a leitura da resposta); os logs, escritos com o `logging` do Python, saem presos ao *trace* e ao *span* em que aconteceram. A busca de um nome inexistente produz um 404 marcado como erro, com o aviso no log preso à chamada que falhou |
| `02-metricas.py` | **métricas** num programa comum: forma três times consultando a PokeAPI e mede o agregado — a duração das chamadas (histograma, na convenção de HTTP) e os pokémon por tipo (contador). Sem *trace* nem log, de propósito: a métrica perde o detalhe de cada consulta, e por isso é barata |
| `agente.py` | **o ponto de entrada.** O agente das aulas anteriores, **sem alteração de lógica**, instrumentado com OpenTelemetry: cada execução sai como uma árvore de *spans* nas convenções GenAI e é enviada por OTLP para o Grafana Cloud. `python agente.py` faz uma execução e imprime os *spans* que ela enviou: `invoke_agent` na raiz, um `chat` por chamada ao modelo e um `execute_tool` por ferramenta, com os atributos de cada um |
| `dominio.py` | o domínio do auditor de despesas: a política, o regulamento, as despesas, o `SYSTEM`, as três ferramentas e a extração do veredito. Nada de telemetria; fica fora do `agente.py` para que ele mostre só o grafo e os *spans* |
| `cliente.py` | o modelo, escolhido por `LLM_PROVEDOR` no `.env` entre Mistral, Ollama, Groq e OpenRouter. O mesmo das aulas de *frameworks* e de MCP |

O agente é o grafo do `04-langgraph.py` da aula de *frameworks*, escrito nó a nó, e não
o `create_agent`. A escolha tem a ver com esta aula: a telemetria precisa
medir **cada** chamada ao modelo e **cada** ferramenta, e um nó escrito à
mão é onde o *span* de cada uma se abre e se fecha.

O modelo e a telemetria são configurados no `.env` desta pasta
(`cp .env.example .env`). Sem `OTEL_EXPORTER_OTLP_ENDPOINT`, o agente roda
igual e os *spans* não saem do processo.

O `01-trace-e-log.py` e o `02-metricas.py` leem o mesmo `.env`: com o
endpoint preenchido, além de imprimir, enviam a telemetria para a mesma
plataforma, cada um com o seu nome de serviço (`buscador-de-pokemon` e
`montador-de-times`). No Grafana Cloud, os *traces* aparecem no Tempo, os
logs no Loki — cada linha com o `trace_id` da busca em que foi escrita — e
as métricas no Mimir (Prometheus), com nomes adaptados:
`http_client_request_duration_seconds` e `time_pokemon_total`.

## As duas coisas que esta pasta demonstra

**1. Convenção aberta em vez de formato próprio.** O `agente.py` emite o
*trace* que já existia nas convenções GenAI do OpenTelemetry. O dado é o
mesmo; o que muda é quem consegue lê-lo sem documentação própria, e o custo
de trocar de ferramenta depois — custo sentido duas vezes, nas aulas de *frameworks* e de MCP.

**2. `orcamento_esgotado` é degradação silenciosa.** Execuções que terminam
por orçamento devolvem uma resposta pior sem erro. A taxa de erro não se
mexe. O `agente.py` exporta o motivo de término como atributo do *span* raiz
(`agente.termino`), e no painel da plataforma ele vira um alerta. Painéis
comerciais raramente oferecem essa métrica, porque ela exige que o término
tenha sido modelado como dado.

## Custo

O `agente.py` faz uma execução por vez que é rodado.
