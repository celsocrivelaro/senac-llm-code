# Aula 06 — Embeddings e RAG

Laboratório da aula 06. Mesma configuração das aulas anteriores — API da
Mistral pelo SDK da OpenAI, com `LLM_BASE_URL` e `OPENAI_API_KEY` vindos do
`.env` da raiz — mais **uma variável nova**:

```
LLM_MODELO_EMBEDDING=mistral-embed
```

`numpy` e `chromadb` são as dependências de código, e as duas já constam do
`requirements.txt`. Nenhum serviço sobe: o Chroma escreve num diretório
local, `indice/`, criado em tempo de execução e não versionado.

> **Os cinco primeiros scripts não chamam o modelo generativo.** O buscador
> inteiro — vetor, cosseno, chunking, índice, medida, router e banco de
> vetores — se constrói sem que nada escreva uma palavra. O objeto de estudo dessa metade é a
> linhagem *encoder* da aula 01 (nota 01, §6.1), listada na tabela de
> modalidades da aula 02 (nota 01, §5).
>
> A geração entra no `06`, e é ela que fecha o RAG.

## Ordem sugerida

| Script | O que produz |
|---|---|
| `00-o-vetor.py` | Dimensão, norma e faixa de um embedding — e os dois cossenos que mostram que o sentido não está dentro do vetor, e sim entre vetores. |
| `01-similaridade.py` | Cosseno em quatro linhas de numpy e o primeiro buscador do curso. Mostra que a faixa de valores reais **não** vai de 0 a 1, e que o trecho mais parecido com a pergunta costuma não ser o que a responde. |
| `02-chunking.py` | Três estratégias de corte sobre o mesmo regulamento e as mesmas dez perguntas, com `recall@k` comparado — e as perguntas que falharam, que valem mais que a média. |
| `03-buscador.py` | O buscador completo, executável e importável, com o corte que venceu o `02`. Imprime a assimetria: construir o índice acontece uma vez, consultar acontece sempre. |
| `04-router.py` | O router por embedding que a Aula 05 nomeou e não implementou. Classificar é buscar com outro índice — e duas mensagens que diferem em uma palavra caem na mesma rota, sem nenhum modelo gerar texto. |
| `05-banco-vetorial.py` | O banco de vetores por dentro: inserção, quatro situações de busca e a leitura do retorno — inclusive a pergunta fora do domínio, que volta com distância quase igual à da pertinente. |
| `06-rag-simples.py` | O RAG mínimo: o índice sai da memória e vai para um banco de vetores, e os trechos viram resposta. A primeira chamada de geração da aula — e o portão que deveria barrar a pergunta fora de domínio, mas não barra, porque o limiar foi chutado. |

Cada script importa o que precisa dos módulos, e nada além disso. O `00`, o
`01` e o `04` não constroem índice nenhum: são demonstrações conceituais. O
`02` e o `03` são a mesma máquina em dois momentos — um escolhe o corte
medindo `recall@k`, o outro entrega o buscador com o corte que ganhou. O `05`
usa o Chroma direto, sem passar pelo `indice_chroma.py`, porque o assunto
dele é justamente a API do banco. E o `06` é o único que chama o modelo
generativo.

O `02-chunking.py` aceita o `k` como argumento:

```
python 02-chunking.py 5
```

## Os módulos

Um arquivo, uma responsabilidade, e é a ordem em que a aula os apresenta:

`cliente.py` — **um cliente só, para as duas modalidades.** O endpoint é o
mesmo desde a aula 01; o que muda é o modelo. Trocar de modelo de embedding
é editar uma linha aqui.

`embedding.py` — **a porta para a modalidade que não gera texto.**
`gerar_matrix_embbeddings` (uma lista, uma chamada) e
`gerar_vetor_embeddings`. É o único arquivo que pede vetor à API.

`similaridade.py` — **a medida**: `cosseno` entre dois vetores e
`cosseno_lote` de um contra muitos. É a mesma conta em dois formatos, e é o
único número que a aula usa. Não chama a API.

`estrategias_chunking.py` — **os três cortes**, lado a lado: por contagem de
caracteres, por contagem com sobreposição e por estrutura. Nenhum chama a
API; chunking é manipulação de texto. Estão juntos porque a aula não ensina
nenhum isoladamente — ensina a comparação entre eles, que o `02` mede.

`indice_memoria.py` — **o índice**: os chunks, seus vetores, e a busca de um
vetor contra todos. Recebe vetores prontos e devolve trechos ordenados. O
nome diz onde ele vive, e atravessa os scripts `02` e `03` — com 40 chunks,
busca linear em numpy é instantânea e não há motivo para mais que isso.

`indice_chroma.py` — **o mesmo índice, num banco de vetores.** Mesma
interface do `IndiceMemoria`; o que muda é que os vetores sobrevivem ao
processo. Devolve **distância**, não score: no Chroma com métrica de cosseno,
baixo é bom.

`geracao.py` — **a metade que faltava.** Uma chamada, um prompt, texto de
volta. O contrato de saída e a citação conferível são da aula 07.

`dados.py` — **o corpus**: o regulamento de despesas em texto corrido. Só o
`02`, o `03` e o `05` o usam. Todo o resto mora no script que o consome — o
trio de relevância e as dez frases no `01`, as dez perguntas com resposta
conhecida no `02`, os exemplares de rota no `04` e as três do RAG no `06`.

## O que fica para a aula 07

O `05` monta um RAG que funciona, e **não confere nada do que ele produz**.
Não pergunta se a resposta usou os trechos que voltaram, não confere se a
fonte citada existe, não recusa com contrato, e o portão dele tem um limiar
chutado.

Cada uma dessas quatro lacunas é um bloco da aula 07 — e as quatro juntas
são o que separa "o pipeline roda" de "dá para confiar no que ele devolve".
