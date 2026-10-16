# Testes unitários: as ferramentas e a extração do veredito.
#
# Nenhum chama o modelo. São rápidos, determinísticos e gratuitos — por isso
# rodam em todo push.

import json

import pytest

from agente import consultar_despesa, consultar_politica, veredito


def test_despesa_existente():
    dados = json.loads(consultar_despesa.invoke({"despesa": "D-4612"}))
    assert dados == {"despesa": "D-4612", "categoria": "refeicao", "valor": 138.0, "cidade": "Sao Paulo"}


def test_despesa_inexistente_devolve_erro_e_nao_excecao():
    # A ferramenta devolve o erro ao modelo, que pode se corrigir; uma exceção
    # derrubaria a execução inteira.
    dados = json.loads(consultar_despesa.invoke({"despesa": "D-9999"}))
    assert dados["erro"] == "despesa inexistente"


@pytest.mark.parametrize("categoria, teto", [("refeicao", 120.0), ("transporte", 250.0), ("hospedagem", 480.0), ("outros", 90.0)])
def test_teto_por_categoria(categoria, teto):
    assert json.loads(consultar_politica.invoke({"categoria": categoria}))["teto"] == teto


def test_categoria_desconhecida_lista_as_validas():
    dados = json.loads(consultar_politica.invoke({"categoria": "lazer"}))
    assert dados["erro"] == "categoria desconhecida"
    assert dados["validos"] == ["hospedagem", "outros", "refeicao", "transporte"]


@pytest.mark.parametrize("texto, esperado", [
    ("O valor excede o teto. **Veredito:** reprovado", "reprovado"),
    ("Dentro do teto. Veredito: Aprovado.", "aprovado"),
    ("Não seria aprovado sem nota; com a nota, fica aprovada.", "aprovado"),
    ("Faltam dados para concluir.", "ausente"),
])
def test_veredito(texto, esperado):
    assert veredito(texto) == esperado
