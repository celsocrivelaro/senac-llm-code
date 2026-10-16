# O eval: o agente de verdade, com o modelo de verdade, contra um gabarito.
#
# Cada caso tem a resposta certa conhecida pela política. O agente não é
# determinístico, então o critério não é "acertar todos", e sim uma TAXA
# mínima de acerto sobre o conjunto — a suíte de regressão da aula de evals,
# em miniatura, como portão do pipeline.
#
#     pytest -m eval

import pytest

from agente import rodar, veredito
from cliente import MODELO, PROVEDOR

GABARITO = [
    ("A despesa D-4612 está dentro da política?", "reprovado"),   # refeição 138 > 120
    ("A despesa D-4613 está dentro da política?", "reprovado"),   # hospedagem 590 > 480
    ("A despesa D-4614 está dentro da política?", "aprovado"),    # transporte 96 <= 250
    ("A despesa D-4615 está dentro da política?", "aprovado"),    # refeição 84 <= 120
]

TAXA_MINIMA = 0.75


@pytest.mark.eval
def test_taxa_de_acerto_contra_o_gabarito():
    print(f"modelo avaliado: {PROVEDOR}/{MODELO}")
    resultados = []
    for pergunta, esperado in GABARITO:
        obtido = veredito(rodar(pergunta))
        resultados.append((pergunta, esperado, obtido))
        print(f"{'OK ' if obtido == esperado else 'ERR'} {pergunta} esperado={esperado} obtido={obtido}")

    taxa = sum(e == o for _, e, o in resultados) / len(resultados)
    print(f"taxa de acerto: {taxa:.0%} (mínimo {TAXA_MINIMA:.0%})")
    assert taxa >= TAXA_MINIMA, resultados
