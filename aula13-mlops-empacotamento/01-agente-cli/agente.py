# Aula 13 — Um agente simples, empacotado em imagem Docker.
#
# CASO DE USO: dado um agente que roda na máquina de quem o escreveu,
# empacotá-lo de modo que qualquer máquina com Docker o execute igual.
#
# O agente é deliberadamente pequeno — um auditor de despesas com duas
# ferramentas, montado com `create_agent` —, porque o assunto não é ele: é a
# imagem que o carrega (ver o Dockerfile ao lado).
#
#     python agente.py                                   # objetivo padrão
#     python agente.py "A despesa D-4613 está dentro da política?"
#
#     docker build -t auditor-de-despesas:1.0.0 .
#     docker run --rm --env-file .env auditor-de-despesas:1.0.0 "A despesa D-4613 está dentro da política?"

import json
import os
import sys

from langchain.agents import create_agent
from langchain.tools import tool

from cliente import MODELO, PROVEDOR, modelo

POLITICA = {"refeicao": 120.00, "transporte": 250.00, "hospedagem": 480.00, "outros": 90.00}

DESPESAS = {
    "D-4612": {"categoria": "refeicao", "valor": 138.00, "cidade": "Sao Paulo"},
    "D-4613": {"categoria": "hospedagem", "valor": 590.00, "cidade": "Lisboa"},
    "D-4614": {"categoria": "transporte", "valor": 96.00, "cidade": "Recife"},
    "D-4615": {"categoria": "refeicao", "valor": 84.00, "cidade": "Sorocaba"},
}

SYSTEM = "Você analisa despesas segundo a política vigente. Use as ferramentas antes de concluir. Termine com o veredito: aprovado ou reprovado."


@tool
def consultar_despesa(despesa: str) -> str:
    """Dados de uma despesa pelo identificador (D + 4 dígitos).

    Args:
        despesa: O identificador da despesa, ex: D-4612
    """
    if despesa not in DESPESAS:
        return json.dumps({"erro": "despesa inexistente", "recebido": despesa})
    return json.dumps({"despesa": despesa, **DESPESAS[despesa]}, ensure_ascii=False)


@tool
def consultar_politica(categoria: str) -> str:
    """Teto de reembolso por categoria: refeicao, transporte, hospedagem, outros.

    Args:
        categoria: A categoria da despesa
    """
    if categoria not in POLITICA:
        return json.dumps({"erro": "categoria desconhecida", "validos": sorted(POLITICA)})
    return json.dumps({"categoria": categoria, "teto": POLITICA[categoria]})


agente = create_agent(modelo, tools=[consultar_despesa, consultar_politica], system_prompt=SYSTEM)


def rodar(objetivo: str) -> str:
    """Uma execução do agente: devolve o texto final."""
    resultado = agente.invoke({"messages": [{"role": "user", "content": objetivo}]})
    return resultado["messages"][-1].content


if __name__ == "__main__":
    objetivo = " ".join(sys.argv[1:]) or "A despesa D-4612 está dentro da política?"
    print(f"auditor-de-despesas · {PROVEDOR}/{MODELO}")
    print(f"objetivo: {objetivo}\n")
    print(rodar(objetivo))
