# Aula 13 — O agente, com a política lida do banco.
#
# É o mesmo auditor de despesas de `02-agente-web/`, com uma diferença: a
# ferramenta `consultar_politica` não lê mais um dicionário do código, e sim
# a tabela `politica` do Postgres que o docker compose sobe ao lado (ver
# banco/01-politica.sql). As despesas continuam no código.
#
# O endereço do banco vem de DATABASE_URL, montado no docker-compose.yml.

import json
import os

import psycopg
from langchain.agents import create_agent
from langchain.tools import tool

from cliente import modelo

# Dentro do compose, o banco é alcançado pelo NOME DO SERVIÇO (`banco`), e
# não por localhost: cada container tem a própria rede, e o compose resolve o
# nome do serviço para o container certo.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://agente:agente@localhost:5432/despesas")

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
    # Consulta parametrizada: a categoria vem do modelo, e o modelo não é
    # fonte confiável. Concatenar o texto na SQL abriria injeção de SQL.
    with psycopg.connect(DATABASE_URL) as conexao:
        linha = conexao.execute("SELECT teto FROM politica WHERE categoria = %s", (categoria,)).fetchone()
        if linha is None:
            validos = [c for (c,) in conexao.execute("SELECT categoria FROM politica ORDER BY categoria")]
            return json.dumps({"erro": "categoria desconhecida", "validos": validos})
    return json.dumps({"categoria": categoria, "teto": float(linha[0])})


agente = create_agent(modelo, tools=[consultar_despesa, consultar_politica], system_prompt=SYSTEM)


def rodar(pergunta: str) -> str:
    """Uma execução do agente: devolve o texto final."""
    resultado = agente.invoke({"messages": [{"role": "user", "content": pergunta}]})
    return resultado["messages"][-1].content


def banco_ok() -> bool:
    """O banco responde? Usado pelo /saude, sem chamar o modelo."""
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=2) as conexao:
            conexao.execute("SELECT 1")
        return True
    except psycopg.OperationalError:
        return False
