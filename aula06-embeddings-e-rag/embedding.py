# Aula 06 — O embedding.
#
# A porta da aula para a modalidade que NÃO gera texto, e o único arquivo
# que a chama. Importam daqui os scripts, o `indice_memoria.py`, o
# `indice_chroma.py` e, por tabela, os dois índices.
#
# Concentrar isso num arquivo tem uma consequência que vale dizer em voz
# alta: trocar de modelo de embedding é editar UMA linha no `cliente.py`, e
# a aula inteira passa a rodar com o modelo novo. É o mesmo argumento da
# aula 02 sobre escolha de modelo, aplicado a uma modalidade nova.

import numpy as np

from cliente import MODELO_EMBEDDING, client


def gerar_matrix_embbeddings(textos: list[str]) -> np.ndarray:
    """Transforma uma lista de textos numa matriz (n_textos, n_dimensoes).

    Recebe uma LISTA porque a API recebe uma lista: embutir quarenta chunks
    numa chamada é o modo normal de usá-la, e quarenta chamadas de um texto
    seria o erro que o 02 e o 04 já cometeram uma vez.

    Uma chamada, e só. Se a API recusar, o script para e mostra o erro dela
    — que diz o que aconteceu muito melhor que qualquer mensagem nossa.
    """
    resposta = client.embeddings.create(model=MODELO_EMBEDDING, input=textos)

    # A API devolve os vetores na ordem da entrada, mas o campo `index`
    # existe justamente para não se depender disso.
    vetores = sorted(resposta.data, key=lambda d: d.index)
    return np.array([v.embedding for v in vetores], dtype=np.float32)


def gerar_vetor_embeddings(texto: str) -> np.ndarray:
    """A conveniência para quem tem um texto só — uma consulta, um par."""
    return gerar_matrix_embbeddings([texto])[0]
