# Aula 07 — RAG e Documentos

Laboratório da aula 07. O ponto de partida é o estado em que a aula 06
terminou: trechos recuperados de um índice vetorial, sem etapa de geração.

**Dependência nova: Chroma** (`chromadb`, já no `requirements.txt`). Nenhum
serviço sobe — o índice é um diretório local em `indice/`, criado em tempo
de execução e não versionado.

**Dependência nova para a extração: `pdfplumber` (MIT)**, no
`requirements.txt`. É a mais completa das permissivas — o mesmo objeto
devolve texto corrido e tabela. A alternativa mais rápida, a PyMuPDF, é
**AGPL-3** — e licença é critério de escolha de dependência.

**Este laboratório é autocontido.** Nenhum script importa da aula 06 — não há
`sys.path` apontando para fora desta pasta. O `gerar_matrix_embbeddings`, o
corte `por_estrutura` e o regulamento são **cópias** do material de lá.

A duplicação é exigida pelo `CORPUS_COM_RUIDO`: esta aula acrescenta ao
regulamento um parágrafo **revogado** que não existe na aula 06, necessário
para provocar o quarto modo de falha. Como a aula 06 mede `recall@k` sobre o
regulamento original, alterar o dado compartilhado invalidaria aquela
medição.

O `gerar_matrix_embbeddings` é idêntico linha por linha ao da aula 06: o
Chroma armazena e recupera vetores, e não os calcula.

## Ordem sugerida

| Script | O que produz |
|---|---|
| `00-extrair-pdf.py` | **De onde vem o texto.** O mesmo regulamento lido a partir de um PDF de quatro páginas: o conteúdo extraído impresso na íntegra, página a página (a quarta é digitalizada, e volta vazia), a tabela do anexo como texto e como estrutura, e a conferência de que os marcadores de artigo sobreviveram à extração. |
| `01-cegueiras.py` | As quatro propriedades que o embedding não representa — negação, número, entidade e tempo —, medidas contra um par de controle. O material vem da aula 06; está aqui porque é num pipeline de RAG que o defeito ganha consequência: os modos de falha 1 e 4 do `05` são estas cegueiras na forma de resposta gerada. |
| `02-avaliar.py` | `recall@k` e fidelidade calculados **separados**, com a tabela de diagnóstico: baixo recall = índice; alta recall e baixa fidelidade = prompt; ambas altas e a resposta errada = corpus. |
| `03-recuperacao-como-ferramenta.py` | A pergunta de Lisboa: o pipeline erra com fonte citada, o agente com `buscar_politica` acerta. É o orquestrador-trabalhador da aula 05, com teto de buscas. |
| `04-pipeline-demo.py` | O RAG mínimo funcionando, e a classificação dele na taxonomia da aula 05: `pergunta → busca → portão → resposta` é **prompt chaining com portão**, não é um agente. |
| `05-modos-de-falha.py` | As quatro falhas, cada uma provocada por construção: recuperou errado · recuperou certo e ignorou (a mesma pergunta em duas ordens) · não havia resposta e respondeu · trechos contraditórios. |
| `06-citacao-e-recusa.py` | O contrato de saída com `fontes` e `suficiente`, e a mesma pergunta antes e depois. `suficiente: false` **é a rota `nenhuma`** do roteador da aula 05. A citação é verificada em código, sem chamada. |

## Os dados em disco

`regulamento.pdf` — o mesmo `REGULAMENTO` do `dados.py`, em PDF de quatro
páginas: duas de texto corrido, uma com o **anexo em tabela** (com réguas
desenhadas, que é o que a detecção de tabela utiliza) e uma **sem camada de
texto**, equivalente a uma página digitalizada. É um PDF híbrido construído
para o exercício: a classe que falha sem emitir erro.

## Os módulos

`dados.py` — importa o regulamento e as dez perguntas da aula 06 e acrescenta
o que provoca as falhas: a versão **revogada** do Art. 4º §1º (contradição),
três perguntas **sem resposta no corpus**, e o caso de Lisboa.

`cliente.py` — **um cliente para as duas modalidades.** O endpoint é o mesmo
desde a aula 01; o que difere é o modelo. Na aula 06 o cliente residia dentro
do `embedding.py`, único ponto de acesso à API; aqui há dois pontos de
acesso, o que exige extrair a dependência comum.

`consumo.py` — **dois contadores independentes.** Embedding e geração têm
preços distintos por token, e um total único não indica qual das duas
modalidades responde pelo consumo. O `03` os usa para comparar as chamadas do
pipeline com as do laço de ferramentas.

`embedding.py` — **cópia da aula 06**, linha por linha. A função que
transforma texto em vetor não é alterada pela introdução do RAG.

`estrategias_chunking.py` — **o corte por estrutura**, também cópia. Na aula
06 era a conclusão de uma medição; aqui entra como premissa.

`indice_chroma.py` — **a diferença em relação à aula 06.** A interface é a
mesma nas duas — recebe corpus, devolve trechos ordenados —, e o que muda é
onde os vetores residem entre execuções: memória lá (`IndiceMemoria`),
arquivo aqui (`IndiceChroma`).

`geracao.py` — **a metade que a aula 06 não implementava.** A chamada de
geração, o contexto rotulado e os dois prompts: o de texto livre e o com
contrato de saída.

`pipeline.py` — as duas metades encadeadas, em vinte linhas, metade delas o
portão de distância.

`similaridade.py` — **o cosseno implementado diretamente**, cópia da aula 06.
O `01` depende dele: as cegueiras são medidas par a par, fora do índice.

`metricas.py` — `recall@k`, fidelidade e a verificação de citação. Ficam no
mesmo módulo, e são calculadas **separadamente**: um índice único de
qualidade não distingue defeito de índice de defeito de prompt, e portanto
não indica onde intervir.

## O caso de Lisboa

O script `03` usa a mesma despesa do **exemplo 4 da nota 03 da aula 05** — a
refeição em Lisboa, que lá falhou porque o sub-agente não relatou a exceção
de viagem internacional. Aqui ela falha por recuperação insuficiente. São
causas distintas com o mesmo sintoma: uma despesa legítima reprovada, sem
indício de informação faltante.

## Cuidado com o custo

O `05` e o `02` fazem várias chamadas de geração por execução — o `02` faz
uma chamada de fidelidade por pergunta, sobre dez perguntas. Todos os
scripts imprimem o consumo no fim, separando embeddings de geração. Confira
o *rate limit* antes de execuções simultâneas: o limite é por chave.
