# Aula 07 — O embedding.
#
# Cópia literal de `embedding.py` da aula 06. A função que transforma texto
# em vetor não é alterada pela introdução do RAG: o Chroma armazena e
# recupera vetores, e o modelo que os produz continua sendo chamado da mesma
# forma.
#
# A duplicação, em vez de import, é deliberada. Na aula 06 este módulo era o
# objeto de estudo; nesta aula ele é premissa. Manter cópias independentes
# permite que uma aula modifique seu próprio laboratório sem invalidar as
# medições da outra.

import time

import numpy as np
from openai import APIConnectionError, RateLimitError

from cliente import MODELO_EMBEDDING, client
from consumo import registrar_embedding


def gerar_matrix_embbeddings(textos: list[str],
                             tentativas: int = 5) -> np.ndarray:
    """Transforma uma lista de textos numa matriz (n_textos, n_dimensoes).

    O retry é o mesmo da aula 02 (nota 01 §8.2): backoff exponencial para
    falha de TRANSPORTE. Erro de conteúdo não tem retry.
    """
    for tentativa in range(tentativas):
        try:
            resposta = client.embeddings.create(
                model=MODELO_EMBEDDING, input=textos)
            break
        except (RateLimitError, APIConnectionError):
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)

    registrar_embedding(resposta.usage.total_tokens)

    # A API devolve os vetores na ordem da entrada, mas o campo `index`
    # existe justamente para não se depender disso.
    vetores = sorted(resposta.data, key=lambda d: d.index)
    return np.array([v.embedding for v in vetores], dtype=np.float32)


def gerar_vetor_embeddings(texto: str) -> np.ndarray:
    return gerar_matrix_embbeddings([texto])[0]
