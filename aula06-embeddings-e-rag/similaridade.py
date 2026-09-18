# Aula 06 — A medida de similaridade.
#
# Duas funções, e as duas fazem a mesma conta: o cosseno do ângulo entre
# vetores. A diferença é o formato — uma compara dois, a outra compara um
# contra muitos numa operação só.
#
# É o único número que a aula inteira usa. Depois que os vetores existem,
# BUSCAR É ORDENAR POR ESTE NÚMERO — e nada aqui chama a API.

import numpy as np


def cosseno(a: np.ndarray, b: np.ndarray) -> float:
    """Similaridade de cosseno entre dois vetores.

    Por que cosseno e não distância euclidiana: o comprimento do texto vira
    NORMA do vetor, e comprimento não deveria pesar na comparação de
    significado. O cosseno olha só o ângulo — divide a norma fora.

    (Com `mistral-embed` a norma já vem 1, e a divisão é por 1. A conta fica
    porque nem todo modelo normaliza, e um código que assume isso quebra em
    silêncio ao trocar de modelo.)
    """
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def cosseno_lote(consulta: np.ndarray, matriz: np.ndarray) -> np.ndarray:
    """O mesmo cálculo, de um vetor contra N — em uma operação só.

    Uma multiplicação de matriz por vetor compara a pergunta com o corpus
    inteiro. Com quarenta chunks é imperceptível; a complexidade é O(n·d),
    linear no número de documentos e na dimensão.
    """
    normas = np.linalg.norm(matriz, axis=1) * np.linalg.norm(consulta)
    return (matriz @ consulta) / normas
