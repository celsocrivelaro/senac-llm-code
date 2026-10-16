from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool

from cliente import MODELO, PROVEDOR, modelo

print(f"[{PROVEDOR}:{MODELO}]")


@tool
def get_weather(cidade: str) -> str:
    """Pegue a temperatura em uma cidade.

    Args:
        cidade: O nome da cidade
    """
    return f"Está ensolarado em {cidade}!"


agent = create_agent(
    model=modelo,
    tools=[get_weather],
    system_prompt="Aja como um assistente",
)

# result = agent.invoke(
#     {"messages": [HumanMessage(content="Como está o tempo na cidade de São Paulo?")]}
# )

result = agent.invoke(
    {"messages": [HumanMessage(content="O gato caiu do telhado")]}
)

for mensagem in result["messages"]:
    mensagem.pretty_print()
