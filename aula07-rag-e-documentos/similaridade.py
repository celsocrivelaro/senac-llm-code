# Aula 07 — A medida de similaridade.
#
# Cópia da aula 06. Duas funções calculam a mesma grandeza — o cosseno do
# ângulo entre vetores —, e diferem apenas na forma da entrada: `cosseno`
# compara dois vetores, `cosseno_lote` compara um vetor contra uma matriz em
# uma única operação.
#
# É a única medida usada na recuperação: dados os vetores, buscar consiste em
# ordenar por este número. Nenhuma das duas funções chama a API.

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
