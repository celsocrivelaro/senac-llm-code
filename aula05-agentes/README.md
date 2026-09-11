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
em vez de com a solução. O **exercício 04** usa um domínio diferente —
prestação de contas — porque lá a arquitetura é escolha sua.

## Ordem sugerida

| Script | O que você vai ver |
|---|---|
| `00-roteador.py` | Triagem de 10 mensagens. Produz **um número**: quantas precisaram de LLM. A resposta é "menos do que você esperava" — e a rota mais valiosa é a que **não chama o modelo**. |
| `01-orquestrador-trabalhador.py` | O mesmo lote analisado por *sectioning* (seções no seu código) e por orquestrador (seções decididas pelo modelo). Mostra por que o segundo precisa de **teto**. |
| `02-avaliador-otimizador.py` | O mesmo texto avaliado por um avaliador vago e por um com **critério escrito**. O vago aprova na primeira rodada. |
| `03-agente-com-estado.py` | O laço da aula 03 reescrito sobre um **objeto de estado**. No fim, o objeto responde as sete perguntas que `mensagens[]` não responderia. |
| `04-orcamento-e-terminacao.py` | As **quatro formas de terminar**, disparadas de propósito, cada uma registrada no estado. |
| `05-erros-e-laco.py` | **O script central.** Erro recuperável × fatal, e o detector de laço. Compare A e C: mesma tarefa, mesmo modelo, e a única diferença é o *texto* do erro. |
| `06-compaction.py` | Uma trajetória longa com e sem *tool clearing*, com a curva de tokens por passo. |

`dados.py` guarda os pedidos, os clientes e as categorias — num lugar só,
para que todos os scripts comparem exatamente a mesma coisa. O que é usado
por um script só mora nele: o lote de mensagens da triagem, por exemplo,
está no próprio `00-roteador.py`.

`agente.py` é o módulo compartilhado: o `Estado`, o `Orcamento`, as
ferramentas e o laço. **É a nota 02 da aula virando código.** Leia-o antes
do script `03`; os scripts `03` a `06` são finos porque ele é grosso.

`checkpoints/` é criado em tempo de execução: cada execução grava o estado
completo em JSON. Não está versionado.

## Antes de rodar

```bash
source .venv/bin/activate           # a partir da raiz do repositório
python aula05-agentes/00-roteador.py
```

Todos os scripts exigem um modelo com suporte a **function calling** e a
**saída estruturada com json_schema**. Confirme com o
`00-catalogo-modelos.py` da aula 02.

## Rate limit

Estes scripts fazem **bem mais chamadas** que os das aulas anteriores — um
agente é, por definição, várias chamadas por tarefa. Todo script tem
orçamento com teto de passos, de tokens e de tempo.

O `chamar()` do `agente.py` **não repete a chamada**: se a API recusar, o
script para e diz o que aconteceu e o que fazer. É decisão de laboratório,
não descuido — três tentativas silenciosas escondem a causa, e num
laboratório a causa quase sempre é configuração.

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

**Nem todo provedor manda.** Por isso a primeira chamada de cada execução
imprime o que encontrou, ou diz que não encontrou nada: cota folgada e
provedor mudo produzem o mesmo silêncio, e você precisa saber em qual dos
dois está.

Para ver o corpo **e** os cabeçalhos, `chamar()` usa
`client.chat.completions.with_raw_response.create(...)` e depois `.parse()`.
O `create()` direto devolve só o corpo — os cabeçalhos se perdem.

Se o consumo de tokens subir mais do que você esperava, é exatamente o
ponto da aula: o `05-erros-e-laco.py` mostra de onde ele vem, e o
`06-compaction.py` mostra por que ele cresce com o quadrado do número de
passos.

## O que levar do laboratório

- **A economia não vem de um prompt melhor.** Vem de decidir o que não
  mandar para o modelo. O `00` mede isso.
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
