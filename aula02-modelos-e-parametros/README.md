# Aula 02 — Escolha e configuração de modelos

Laboratório da aula 02. Todos os scripts usam a **API da Mistral** pelo SDK da
OpenAI, com a mesma `OPENAI_API_KEY` do `.env` da raiz — nada novo para
instalar.

## Ordem sugerida

| Script | O que você vai ver |
|---|---|
| `00-catalogo-modelos.py` | Quais modelos a sua chave enxerga, o contexto de cada um e quem suporta *function calling*. Rode primeiro: os outros scripts citam nomes de modelo que você confirma aqui. |
| `01-temperatura.py` | A mesma pergunta em 5 temperaturas, 4 amostras cada. Mede quantas respostas distintas saem e a diversidade do vocabulário. |
| `02-top-p-e-penalidades.py` | `top_p`, `frequency_penalty` e `presence_penalty`, medindo repetição de trigramas. Inclui o experimento de penalidade **negativa**. |
| `03-limites-e-parada.py` | `max_tokens`, `stop` e o campo `finish_reason` — como detectar truncamento em vez de deixá-lo virar bug lá na frente. |
| `04-determinismo.py` | 10 chamadas idênticas com `temperature=0`. Confirma na prática que determinismo não é garantido. |
| `05-json-estruturado.py` | Três estratégias para obter JSON (só prompt · `json_object` · JSON Schema), com taxa de sucesso. É o gancho para *tool calling*. |
| `06-benchmark-modelos.py` | Vários modelos × várias tarefas: TTFT, tempo total, tokens/s, tokens e custo. Gera `benchmark.csv`. |
| `07-raciocinio.py` | Modelo de raciocínio × instruct na mesma tarefa: quanto custa "pensar" e quando isso se paga. |

## Antes de rodar

```bash
source .venv/bin/activate        # a partir da raiz do repositório
python aula02-modelos-e-parametros/00-catalogo-modelos.py
```

Dois ajustes que você provavelmente vai precisar fazer:

1. **Nomes de modelo** — dois lugares diferentes, de propósito:

   - nos scripts **`00` a `05`**, o modelo vem do `.env` (`LLM_MODELO`), junto
     com o endpoint (`LLM_BASE_URL`). Nenhum nome está escrito no código, então
     dá para apontar tudo para um Ollama local sem editar script — veja o
     README da raiz;
   - nos scripts **`06`** e **`07`**, os nomes estão **fixos no topo do
     arquivo**. Ali eles não são configuração: são o experimento. O `06`
     compara um modelo pequeno, um médio e um grande com o preço de cada um ao
     lado; o `07` compara um instruct com um de raciocínio. Trocar isso pelo
     `.env` esconderia justamente a informação que dá sentido à tabela.

   Rode o `00` primeiro e, se algum modelo não aparecer para a sua chave, edite
   o topo do `06` e do `07`.
2. **Preços** — o `06` tem um dicionário `PRECOS` logo abaixo dos modelos.
   Confira os valores em <https://mistral.ai/pricing> e anote a data da
   consulta; preço de LLM muda, e material que finge saber o preço de amanhã
   mente. Se você trocar um modelo, troque o preço na mesma linha.

## Custo e rate limit

Os scripts fazem várias chamadas em sequência. Eles já usam prompts curtos,
`max_tokens` limitado e uma pausa entre requisições, mas:

- rodar tudo de ponta a ponta custa alguns centavos de dólar — pouco, e a
  aula é justamente sobre não ignorar esse "pouco" multiplicado por volume;
- se aparecer `429`, aumente a constante `PAUSA` no topo do script e espere
  alguns segundos — a turma inteira está batendo na mesma API.

## Entregável

`aula02-respostas.md`, conforme o enunciado da aula: tabela de temperatura,
evidência de determinismo, taxa de JSON válido, tabela de benchmark com as
**suas** tarefas, decisão justificada de modelo/parâmetros e estimativa de
custo mensal.
