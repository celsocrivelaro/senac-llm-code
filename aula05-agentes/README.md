# Aula 05 — Arquitetura de agentes

Laboratório da aula 05. Mesma configuração das aulas anteriores: API da
Mistral pelo SDK da OpenAI, com `LLM_BASE_URL` e `LLM_MODELO` vindos do
`.env` da raiz. Nada novo para instalar.

O assunto destes scripts **não é o modelo** — é o que existe em volta dele.
Nas aulas 01–03 o objeto de estudo era a chamada; aqui é o **sistema**. Vale
a orientação inversa da aula 03:

> **Rode primeiro, leia o código depois.** O que estes scripts mostram são
> números — passos, tokens, motivo de término — e o argumento está neles.

O domínio é o mesmo das aulas anteriores (a transportadora), de propósito:
trocar de domínio ao mesmo tempo faria você gastar atenção com o problema
em vez de com a solução.

**São dois os exercícios desta aula, e só um usa este código.** O de
projeto (`05-trabalho.md`) pede a arquitetura do **seu** case e não exige
programar. O prático (`enunciado.md`) pede o `08-analista.py`, num domínio
novo — prestação de contas. Estes scripts são o meio-termo: cada padrão
funcionando, isolado, para você ver o que ele cobra antes de escolher.

## Ordem sugerida

| Script | O que você vai ver |
|---|---|
| `00-sequencial.py` | O padrão mais simples: duas chamadas em sequência com um **portão** entre elas. Cinco mensagens — três passam, duas são barradas —, e para cada barrada o script imprime **o que a etapa 2 teria escrito sem o portão**. |
| `01-router.py` | Triagem de 10 mensagens em **cascata**: a regra tenta primeiro, o modelo pega o resto. Produz **um número** — quantas precisaram de LLM — e mostra **qual modelo atendeu cada uma**, porque o Router escolhe a rota *e* o modelo. |
| `02-orquestrador-trabalhador.py` | O mesmo lote analisado por *sectioning* (seções no seu código) e por orquestrador (seções decididas pelo modelo). Mostra por que o segundo precisa de **teto**. |
| `03-avaliador-otimizador.py` | O mesmo texto avaliado por um avaliador vago e por um com **critério escrito**. O vago aprova na primeira rodada. |
| `04-agente-com-estado.py` | O laço da aula 03 reescrito sobre um **objeto de estado**. No fim, o objeto responde as sete perguntas que `mensagens[]` não responderia. |
| `05-orcamento-e-terminacao.py` | As **quatro formas de terminar**, disparadas de propósito, cada uma registrada no estado. |
| `06-erros-e-laco.py` | **O script central.** Erro recuperável × fatal, e o detector de laço. Compare A e C: mesma tarefa, mesmo modelo, e a única diferença é o *texto* do erro. |
| `07-compaction.py` | Uma trajetória longa com e sem *tool clearing*, com a curva de tokens por passo. **A curva é assunto desta aula; a técnica que a estabiliza é da Aula 08** — o script mora aqui porque depende do laço do `agente.py`. |

`dados.py` guarda os pedidos, os clientes e as categorias — num lugar só,
para que todos os scripts comparem exatamente a mesma coisa. O que é usado
por um script só mora nele: o lote de mensagens da triagem, por exemplo,
está no próprio `01-router.py`.

`agente.py` é o agente: o `Estado`, o `Orcamento`, as ferramentas e o laço.
**É a nota 02 da aula virando código.** Leia-o antes do script `04`; os
scripts `04` a `07` são finos porque ele é grosso.

**Os scripts se dividem em dois grupos, e isso é visível no `import`:**

| | Scripts | Dependem de |
|---|---|---|
| **Workflows** | `00`, `01`, `02`, `03` | nada — cada um se explica sozinho |
| **O agente** | `04`, `05`, `06`, `07` | `agente.py` |

Os quatro primeiros demonstram padrões independentes, e carregam dentro de si
o pouco que usam: o cliente e uma função de saída estruturada. Eles fazem a
chamada **crua**, sem tratamento de erro — porque erro é assunto do `06`, e
blindar o `00` entregaria a solução antes de o problema aparecer.

Os quatro últimos não são quatro demonstrações: são **o mesmo agente visto
quatro vezes**, crescendo. A pergunta em cada um é *"o que mudou desde o
anterior?"*, e ela só tem resposta se o que não mudou estiver num lugar só.

`checkpoints/` é criado em tempo de execução: cada execução grava o estado
completo em JSON. Não está versionado.

## Antes de rodar

```bash
source .venv/bin/activate           # a partir da raiz do repositório
python aula05-agentes/00-sequencial.py
```

Todos os scripts exigem um modelo com suporte a **function calling** e a
**saída estruturada com json_schema**. Confirme com o
`00-catalogo-modelos.py` da aula 02.

## Rate limit

Estes scripts fazem **bem mais chamadas** que os das aulas anteriores — um
agente é, por definição, várias chamadas por tarefa. Os scripts `04` a `07`
têm orçamento com teto de passos, de tokens e de tempo; os quatro primeiros
não têm, e é por isso que neles existe a constante `PAUSA`.

O `chamar()` do `agente.py` — usado pelos scripts `04` a `07` — **não repete
a chamada**: se a API recusar, o script para e diz o que aconteceu e o que
fazer. É decisão de laboratório, não descuido: três tentativas silenciosas
escondem a causa, e num laboratório a causa quase sempre é configuração.

Os scripts `00` a `03` nem isso têm — fazem a chamada crua e deixam a
exceção do SDK subir. Também de propósito: tratamento de erro é o assunto
do `06`, e chegar blindado ao `00` seria entregar a solução antes do
problema.

As mensagens já trazem o encaminhamento. `429` quer dizer excesso de
requisições: aumente a constante `PAUSA` no topo do script. `401` e `404`
apontam para o `.env` — a chave e o nome do modelo.

### A cota, antes do 429

Reagir ao `429` é reagir tarde. A cota restante vem nos **cabeçalhos** de
toda resposta, e o `chamar()` os lê a cada chamada: eles ficam no dicionário
`LIMITES` do `agente.py`, e o script avisa na tela quando o menor deles cai
abaixo de `AVISAR_ABAIXO_DE` (20).

```
      [limites] {'ratelimitbysize-remaining': '3', 'retry-after': '7'}
      [limites] restam 3 — aumente a PAUSA
```

Dois detalhes que valem mais que o código:

**Os nomes desses cabeçalhos não são padronizados.** A OpenAI manda
`x-ratelimit-remaining-requests`; a Mistral, `ratelimitbysize-remaining`.
Por isso o filtro procura por *substring*, e não pela chave que você conhece
— procurar a chave exata é como concluir que o seu provedor "não tem limite".

**Nem todo provedor manda.** Se o `LIMITES` ficar vazio depois de uma
execução, a conclusão não é "sobra cota" — é que aqui só dá para reagir ao
`429`. Cota folgada e provedor mudo produzem o mesmo silêncio, e o
dicionário é o único jeito de saber em qual dos dois você está.

Para ver o corpo **e** os cabeçalhos, `chamar()` usa
`client.chat.completions.with_raw_response.create(...)` e depois `.parse()`.
O `create()` direto devolve só o corpo — os cabeçalhos se perdem.

Se o consumo de tokens subir mais do que você esperava, é exatamente o
ponto da aula: o `06-erros-e-laco.py` mostra de onde ele vem, e o
`07-compaction.py` mostra por que ele cresce com o quadrado do número de
passos.

## O que levar do laboratório

- **A economia não vem de um prompt melhor.** Vem de decidir o que não
  mandar para o modelo. O `01` mede isso.
- **Autonomia é recurso escasso.** Cada nível acima custa previsibilidade
  e — o mais caro — capacidade de depurar quando falhar.
- **`mensagens[]` é transporte, não é estado.** Sete salvaguardas dependem
  dessa separação, e nenhuma delas é implementável sem ela.
- **A mensagem de erro é prompt.** É o único texto que o modelo lê para
  decidir como se corrigir, e um erro bem escrito economiza mais tokens que
  qualquer compaction.
- **Nenhuma salvaguarda é grátis.** Orçamento apertado mata tarefa legítima,
  detector agressivo interrompe quem progredia devagar, compressão perde
  informação. Escolher a dose é o trabalho.
- O estado que estes scripts gravam em `checkpoints/` tem nome: é um
  **trace**. Ele é a matéria-prima das aulas de observabilidade e evals.
