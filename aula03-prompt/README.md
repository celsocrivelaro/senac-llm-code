# Aula 03 — Prompt engineering

Laboratório da aula 03. Mesma configuração das aulas anteriores: API da
Mistral pelo SDK da OpenAI, com `LLM_BASE_URL` e `LLM_MODELO` vindos do
`.env` da raiz. Nada novo para instalar.

O assunto destes scripts é **como se monta um prompt**. Em todos eles, a
tarefa e o modelo ficam fixos — o que muda de uma condição para outra é
**o texto do pedido**. Por isso vale a mesma orientação em todos:

> **Abra o código e leia os prompts antes de olhar o resultado.**

## Ordem sugerida

| Script | O que você vai ver |
|---|---|
| `00-zero-vs-few-shot.py` | A mesma classificação com e sem exemplos. O ganho do few-shot costuma ser de **formato**, antes de ser de acerto. |
| `01-rotulos-errados.py` | O experimento do **Min et al. (2022)**: exemplos com rótulos corretos × embaralhados × sem exemplos. Rode este **antes** de ler a explicação e tente prever o resultado. |
| `02-chain-of-thought.py` | Três formas de montar o mesmo pedido: direto, com "vamos pensar passo a passo", e com um exemplo resolvido. Mostra o que muda **no texto da resposta**. |
| `03-self-consistency.py` | O mesmo prompt do `02`, pedindo N respostas e ficando com a majoritária. Mostra a distribuição dos votos. |
| `04-tool-calling.py` | O laço completo em quatro tempos, com duas ferramentas e log de cada chamada. |

`dados.py` guarda o conjunto de teste e os exemplos usados pelos scripts
`00` e `01` — num lugar só, de propósito: é o mesmo conjunto nos dois,
senão os experimentos não seriam comparáveis entre si.

## Antes de rodar

```bash
source .venv/bin/activate           # a partir da raiz do repositório
python aula03-prompt/00-zero-vs-few-shot.py
```

O `04-tool-calling.py` exige um modelo com suporte a **function calling**.
Confirme com o script `00-catalogo-modelos.py` da aula 02: o modelo precisa
declarar `function_calling` nas capacidades.

## Rate limit

Os scripts fazem várias chamadas em sequência e já trazem uma pausa entre
elas. Se aparecer `429`, aumente a constante `PAUSA` no topo do script e
espere alguns segundos — a turma inteira está batendo na mesma API.

## O que levar do laboratório

- **Comece pelo prompt mais simples que pode funcionar.** Em quase todos os
  scripts, a condição mais barata de escrever (zero-shot, ou uma frase a
  mais) já resolve. Escalar a técnica sem medir é adivinhação.
- **Cada frase do prompt deve eliminar uma possibilidade.** Se você apagar
  uma frase e não souber dizer o que ela impedia, ela não estava fazendo
  nada.
- **Uma medição não é uma medição.** Com 10 mensagens de teste, diferenças
  de 1 ou 2 acertos podem ser ruído. Antes de concluir, aumente o conjunto.
- O conjunto de teste do `dados.py` é o mesmo do exercício: ele é o **ativo**
  que permite comparar qualquer mudança futura de prompt ou de modelo.
