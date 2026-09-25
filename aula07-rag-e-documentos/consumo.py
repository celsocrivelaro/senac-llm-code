# Aula 07 — A contabilidade das chamadas.
#
# Dois contadores independentes, um por modalidade. A separação é necessária
# porque embedding e geração têm preços distintos por token: um total único
# não indica qual das duas modalidades responde pelo consumo.
#
# Escrevem aqui `embedding.py` e `geracao.py`, cada um em seu dicionário. Lê
# daqui qualquer script que precise comparar dois caminhos de execução — o
# script 03 usa os contadores para comparar as chamadas do pipeline com as do
# laço de ferramentas. O cálculo de custo em moeda é assunto da aula 13.

from dados import custo, custo_embedding

CONSUMO = {"chamadas": 0, "tokens": 0, "custo": 0.0}
GERACAO = {"chamadas": 0, "entrada": 0, "saida": 0, "custo": 0.0}


def registrar_embedding(tokens: int) -> None:
    CONSUMO["chamadas"] += 1
    CONSUMO["tokens"] += tokens
    CONSUMO["custo"] += custo_embedding(tokens)


def registrar_geracao(entrada: int, saida: int) -> None:
    GERACAO["chamadas"] += 1
    GERACAO["entrada"] += entrada
    GERACAO["saida"] += saida
    GERACAO["custo"] += custo(entrada, saida)
