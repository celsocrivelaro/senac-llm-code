# Aula 06 — O índice em memória.
#
# Os chunks, seus vetores, e a comparação de um vetor contra todos. É o que
# transforma "tenho vetores" em "sei qual trecho responde".
#
# Repare no que NÃO está aqui, e onde cada coisa mora:
#
#   embedding.py              texto -> vetor (a única porta para a API)
#   estrategias_chunking.py   documento -> chunks (manipulação de texto)
#   indice_memoria.py         vetor -> trechos (este arquivo)
#
# Os três se encaixam nesta ordem, e é a ordem da aula. O 02-chunking.py e o
# 03-buscador.py importam daqui; os demais scripts não precisam de índice.

import numpy as np

from embedding import gerar_matrix_embbeddings, gerar_vetor_embeddings
from similaridade import cosseno_lote

# ============================================================ O ÍNDICE

class IndiceMemoria:
    """Um índice em memória: os chunks, seus vetores e nada mais.

    Com 40 chunks, busca linear em numpy é instantânea — não há motivo para
    um banco vetorial ainda. Ele entra na aula 07, quando o índice precisa
    SOBREVIVER ao processo.
    """

    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.matriz = gerar_matrix_embbeddings([c["texto"] for c in chunks])

    def buscar_vetor(self, vetor: np.ndarray, k: int = 3) -> list[dict]:
        """A busca propriamente dita: comparar um vetor com a matriz.

        NÃO chama a API. Quem já tem o vetor da pergunta não precisa embuti-la
        de novo — e o 02-chunking.py depende disso: ele mede as mesmas dez
        perguntas sete vezes, e embuti-las de novo a cada medição seria pagar
        setenta chamadas idênticas.
        """
        scores = cosseno_lote(vetor, self.matriz)
        ordem = np.argsort(-scores)[:k]
        return [{**self.chunks[i], "score": float(scores[i])} for i in ordem]

    def buscar(self, pergunta: str, k: int = 3) -> list[dict]:
        """Texto -> vetor -> busca. Uma chamada de embedding, a da pergunta."""
        return self.buscar_vetor(gerar_vetor_embeddings(pergunta), k=k)

    def __len__(self) -> int:
        return len(self.chunks)


