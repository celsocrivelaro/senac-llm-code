# Aula 06 — Embeddings e busca semântica

Laboratório da aula 06. Mesma configuração das aulas anteriores — API da
Mistral pelo SDK da OpenAI, com `LLM_BASE_URL` e `OPENAI_API_KEY` vindos do
`.env` da raiz — mais **uma variável nova**:

```
LLM_MODELO_EMBEDDING=mistral-embed
```

`numpy` é a única dependência de código, e já consta do `requirements.txt`.

> **Nenhum destes scripts chama o modelo generativo.** É a primeira vez no
> curso. O objeto de estudo aqui é um modelo que transforma texto em vetor e
> não produz token nenhum — a linhagem *encoder* apresentada na aula 01
> (nota 01, §6.1) e listada na tabela de modalidades da aula 02 (nota 01, §5).

## Ordem sugerida

| Script | O que produz |
|---|---|
| `00-o-vetor.py` | Dimensão, norma e faixa de um embedding — e os dois cossenos que mostram que o sentido não está dentro do vetor, e sim entre vetores. |
| `01-similaridade.py` | Cosseno em quatro linhas de numpy e o primeiro buscador do curso. Mostra que a faixa de valores reais **não** vai de 0 a 1, e que o trecho mais parecido com a pergunta costuma não ser o que a responde. |
| `02-cegueiras.py` | **O script central.** Negação, número, entidade e tempo, cada um com previsão da turma antes de rodar. O par de CONTROLE é o que calibra a leitura. |
| `03-chunking.py` | Três estratégias de corte sobre o mesmo regulamento e as mesmas dez perguntas, com `recall@k` comparado — e as perguntas que falharam, que valem mais que a média. |
| `04-buscador.py` | O buscador completo, executável e importável, com o corte que venceu o `03`. Imprime a assimetria: construir o índice acontece uma vez, consultar acontece sempre. |

O `00`, o `01` e o `02` são **autocontidos**: cada um carrega a própria cópia
do cliente de embeddings, porque cada um demonstra um fenômeno diferente e
precisa poder ser lido inteiro. O `03` e o `04` compartilham o `busca.py` —
não são duas demonstrações, são a mesma máquina em dois momentos: um escolhe
o corte medindo `recall@k`, o outro entrega o buscador com o corte que ganhou.

O `02-cegueiras.py` pausa entre os pares para a previsão da turma. Para rodar
sem interação:

```
python 02-cegueiras.py --sem-pausa
```

O `03-chunking.py` aceita o `k` como argumento:

```
python 03-chunking.py 5
```

## Os módulos

`dados.py` — o regulamento de despesas em texto corrido, as dez perguntas com
resposta conhecida e os pares das cegueiras. As aulas 07 e 08 importam daqui.

`busca.py` — o cliente de embeddings, o cosseno, as três estratégias de
chunking, o índice em memória e o `recall@k`. **É a aula virando código.**
Leia-o antes do script `03`.

## O que fica para a aula 07

O índice deste laboratório vive em memória e morre com o processo. Com 40
chunks, busca linear em numpy é instantânea e não há motivo para mais que
isso. Chroma entra na aula 07, quando o índice precisa sobreviver — e quando
o problema deixa de ser "encontrar o trecho" e passa a ser "o que fazer com
os três trechos que voltaram".
