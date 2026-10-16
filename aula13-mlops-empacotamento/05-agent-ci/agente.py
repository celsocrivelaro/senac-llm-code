# Aula 13 — O agente, com o que a integração contínua precisa para testá-lo.
#
# É o auditor de despesas de `02-agente-web/`. Duas coisas foram separadas
# para serem testáveis sem chamar o modelo:
#
#   - as FERRAMENTAS, que são funções comuns sob o decorador @tool — o
#     teste unitário as chama diretamente;
#   - a extração do VEREDITO do texto final, que o eval usa para comparar a
#     resposta do agente com o gabarito.

import json
import re

from langchain.agents import create_agent
from langchain.tools import tool

from cliente import modelo

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


def rodar(pergunta: str) -> str:
    """Uma execução do agente: devolve o texto final."""
    resultado = agente.invoke({"messages": [{"role": "user", "content": pergunta}]})
    return resultado["messages"][-1].content


def veredito(texto: str) -> str:
    """O último veredito citado no texto: 'aprovado', 'reprovado' ou 'ausente'."""
    achados = re.findall(r"\b(aprovad[oa]|reprovad[oa])\b", texto.lower())
    return achados[-1][:-1] + "o" if achados else "ausente"
