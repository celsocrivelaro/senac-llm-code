# Aula 08 — O embedding.
#
# Cópia literal de `embedding.py` da aula 06. A duplicação mantém este
# laboratório autocontido, sem depender da pasta da outra aula no `sys.path`.
#
# A função que transforma texto em vetor é a mesma; o que muda é o objeto
# indexado. Na aula 06 eram artigos de um regulamento; aqui são EPISÓDIOS —
# o que o agente fez numa execução anterior, e qual foi o resultado.

import time

import numpy as np
from openai import APIConnectionError, RateLimitError

from cliente import MODELO_EMBEDDING, client


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

    # A API devolve os vetores na ordem da entrada, mas o campo `index`
    # existe justamente para não se depender disso.
    vetores = sorted(resposta.data, key=lambda d: d.index)
    return np.array([v.embedding for v in vetores], dtype=np.float32)


def gerar_vetor_embeddings(texto: str) -> np.ndarray:
    return gerar_matrix_embbeddings([texto])[0]
