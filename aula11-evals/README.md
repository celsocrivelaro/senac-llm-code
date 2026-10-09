# Aula 11 — Evals: avaliar sistemas não determinísticos

Laboratório da aula 11. Onze encontros construíram um sistema e nenhum
instrumento para dizer se ele piorou. Esta pasta é o instrumento.

## O caso de uso

> Dado um sistema que mudou, decidir se a mudança pode subir.

## Os estudos de caso

Cada script parte de uma situação concreta — um ticket, um incidente, uma
decisão — e leva no nome a técnica que aplica.

| Script | Técnica | A situação | Modelo |
|---|---|---|---|
| `01-tool-unit-tests.py` | 05 Tool unit tests | O agente repetiu `D4612` seis vezes: o erro não dizia o que estava errado. | não |
| `02-golden-set.py` | 01 Golden set | O ticket #412 vira caso, e o dataset é validado. | não |
| `03-pass-k.py` | (fundamento de 04 e 06) | "Testei e funcionou": a mesma entrada 20 vezes. | 20× |
| `04-trajectory-eval.py` | 04 Trajectory eval | O parecer duplicado e o acerto por palpite: a resposta estava certa. | 2× |
| `05-human-review.py` | 08 Human review | Antes de automatizar, os humanos concordam entre si? | não |
| `06-llm-as-judge.py` | 02 LLM as judge | O juiz de fidelidade, calibrado contra o consenso humano. | ~10× |
| `07-rubric-scoring.py` | 03 Rubric scoring | Atendimento ao cliente: dimensões sim/não, viés de posição e de comprimento. | ~36× |
| `08-regression-suite.py` | 06 Regression suite | O prompt B "corrige" a exceção internacional. Sobe? **A entrega.** | ~64× |
| `09-agentevals-openevals.py` | 04 e 02, com biblioteca | As mesmas medidas com `agentevals` e `openevals`. | ~8× |

A coluna "Modelo" é o número de chamadas ao agente ou ao juiz. Os scripts
mais caros têm a constante de custo no topo (`N`, `REPETICOES`).

As práticas 07 e 09 da lista (A/B em produção e *shadow run*) exigem sistema
no ar e ficam para a aula 12; a 10 (*red team*) é a aula 13.

## Os módulos

| Arquivo | O que é |
|---|---|
| `ferramentas.py` | as quatro ferramentas de despesas, como funções Python comuns — testáveis sem LangChain e sem modelo (`01`) |
| `sistema.py` | o agente sob teste — o `create_agent` da aula 09 com as ferramentas do `ferramentas.py` — e o `Trace` remontado das mensagens |
| `casos.py` | o *golden dataset*: casos com origem declarada, os traces gravados dos incidentes e os rótulos humanos de fidelidade (dois rotuladores) |
| `atendimento.py` | o outro domínio: respostas de atendimento ao cliente, em pares, com versões infladas |
| `metricas.py` | as métricas usadas por mais de um caso, escritas à mão — os três níveis (veredito, trajetória, resultado) e a concordância. Nenhuma chama modelo. As que um caso só usa (`pass^k` no `03`, o holdout no `08`) estão no próprio caso |
| `cliente.py` | o modelo, escolhido por `LLM_PROVEDOR` no `.env` entre Mistral, Ollama e Groq, e o juiz dos casos `06` e `09` (`LLM_MODELO_JUIZ`). O mesmo das aulas 09 e 10 |

## À mão, depois a biblioteca

As métricas são escritas à mão primeiro, pela mesma razão que o protocolo
MCP apareceu à mão na aula 10: uma abstração que nunca foi aberta não pode
ser diagnosticada quando falha. O `09` refaz trajetória e juiz com
`agentevals` e `openevals` — e mostra o que a biblioteca não faz: olhar o
estado do mundo, e calibrar o juiz contra os rótulos humanos do projeto.

## Uma limitação declarada

O juiz é do mesmo modelo que o sistema, o que expõe o viés de
auto-preferência. `LLM_MODELO_JUIZ` no `.env` troca o modelo do juiz, mas
dentro do mesmo provedor.

## Dependências novas

`agentevals` e `openevals`, só para o `09`.
