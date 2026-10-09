# O SISTEMA SOB TESTE — o agente de prestação de contas das aulas 05 a 10.
#
# É o `create_agent` da aula 09, com o modelo do `cliente.py`. Os casos
# desta aula não constroem agente: eles AVALIAM este, como se avalia um
# sistema que já está em produção.
#
#     rodar(entrada) -> Trace       uma execução, com o caminho percorrido
#     PARECERES                     o "mundo": o que o agente já escreveu

from dataclasses import dataclass, field

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import convert_to_messages
from langgraph.errors import GraphRecursionError

import ferramentas
from ferramentas import PARECERES, limpar_pareceres   # o "mundo", usado pelos casos 04 e 08
from casos import SYSTEM
from cliente import MODELO, PROVEDOR, modelo

# temperature=0 entra no próprio modelo: é o `create_agent` que faz as
# chamadas. Os três provedores do `cliente.py` têm o campo.
sistema = modelo.model_copy(update={"temperature": 0})


# ------------------------------------------------------------ ferramentas
# Escritas em `ferramentas.py`, como funções comuns. `tool(...)` lê a
# assinatura e a docstring de cada uma e as entrega ao agente.

consultar_despesa = tool(ferramentas.consultar_despesa)
consultar_politica = tool(ferramentas.consultar_politica)
buscar_regulamento = tool(ferramentas.buscar_regulamento)
registrar_parecer = tool(ferramentas.registrar_parecer)

FERRAMENTAS = [consultar_despesa, consultar_politica, buscar_regulamento,
               registrar_parecer]

# As ferramentas cuja saída conta como CONTEXTO: é nele que a citação do
# artigo precisa estar para ser verificável.
FONTES = {"consultar_politica", "buscar_regulamento"}


# ------------------------------------------------------------------ trace

@dataclass
class Trace:
    """O trace da aula 05: o caminho, não só a resposta."""
    passos: list[dict] = field(default_factory=list)    # cada chamada de ferramenta
    contexto: list[str] = field(default_factory=list)   # o que as FONTES devolveram
    resposta: str = ""                                  # o texto final do agente


def trace_das_mensagens(mensagens: list) -> Trace:
    """Remonta o trace a partir da conversa que o agente devolve.

    Aceita mensagens do LangChain ou dicionários — é assim que os traces
    GRAVADOS de `casos.py` passam pelo mesmo caminho."""
    mensagens = convert_to_messages(mensagens)
    saidas = {m.tool_call_id: m.text for m in mensagens if m.type == "tool"}
    trace = Trace()

    for m in mensagens:
        if m.type != "ai":
            continue
        for chamada in m.tool_calls:
            saida = saidas.get(chamada["id"], "")
            erro = '"erro"' in saida or saida.startswith("Error")
            trace.passos.append({"ferramenta": chamada["name"], "saida": saida, "erro": erro})
            if chamada["name"] in FONTES and not erro:
                trace.contexto.append(saida)

    if mensagens and mensagens[-1].type == "ai":
        trace.resposta = mensagens[-1].text
    return trace


def rodar(entrada: str, prompt: str = SYSTEM) -> Trace:
    """Uma execução do agente. O prompt é parâmetro porque o caso 08
    compara duas versões dele."""
    agente = create_agent(model=sistema, tools=FERRAMENTAS, system_prompt=prompt)
    try:
        # no máximo 6 passos: cada um são dois nós (modelo e ferramentas)
        estado = agente.invoke({"messages": [{"role": "user", "content": entrada}]},
                               {"recursion_limit": 13})
    except GraphRecursionError:
        return Trace()   # estourou os passos: sem resposta, conta como falha
    return trace_das_mensagens(estado["messages"])
