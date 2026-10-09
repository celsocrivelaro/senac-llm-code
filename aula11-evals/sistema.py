# O SISTEMA SOB TESTE — o agente de prestação de contas das aulas 05 a 10.
#
# É o `create_agent` da aula 09, com o modelo do `cliente.py`. Os casos
# desta aula não constroem agente: eles AVALIAM este, como se avalia um
# sistema que já está em produção.
#
#     rodar(entrada) -> Trace       uma execução, com o caminho percorrido
#     PARECERES                     o "mundo": o que o agente já escreveu

from __future__ import annotations

import json
from dataclasses import dataclass, field

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import convert_to_messages
from langgraph.errors import GraphRecursionError

from casos import (DESPESAS, POLITICA, REGULAMENTO, SYSTEM, VERSAO_DATASET,
                   VERSAO_RUBRICA)
from cliente import MODELO, PROVEDOR, modelo

# temperature=0 entra no próprio modelo: é o `create_agent` que faz as
# chamadas. Os três provedores do `cliente.py` têm o campo.
sistema = modelo.model_copy(update={"temperature": 0})

# O estado do mundo. A avaliação de RESULTADO (caso 04) compara este
# dicionário antes e depois da execução.
PARECERES: dict[str, dict] = {}


def limpar_pareceres() -> None:
    PARECERES.clear()


def _json(dados) -> str:
    return json.dumps(dados, ensure_ascii=False)


# ------------------------------------------------------------ ferramentas

@tool
def consultar_despesa(despesa: str) -> str:
    """Dados de uma despesa pelo identificador (D + 4 dígitos).

    Args:
        despesa: O identificador da despesa, ex: D-4612
    """
    if despesa not in DESPESAS:
        # DE PROPÓSITO mal descrito: não diz o que recebeu nem o que seria
        # válido. O caso 01 reprova esta mensagem.
        return _json({"erro": "despesa inexistente"})
    return _json({"despesa": despesa, **DESPESAS[despesa]})


@tool
def consultar_politica(categoria: str) -> str:
    """Teto de reembolso de uma categoria: refeicao, transporte, hospedagem ou outros.

    Args:
        categoria: A categoria da despesa
    """
    if categoria not in POLITICA:
        return _json({"erro": "categoria desconhecida", "recebido": categoria,
                      "validos": sorted(POLITICA),
                      "sugestao": "chame de novo com um dos valores de 'validos'"})
    return _json({"categoria": categoria, **POLITICA[categoria]})


def _busca(consulta: str, k: int = 3) -> list[dict]:
    termos = set(consulta.lower().split())
    pontuados = [{"artigo": a, "texto": t,
                  "distancia": 1 - len(termos & set(t.lower().split())) / max(len(termos), 1)}
                 for a, t in REGULAMENTO.items()]
    pontuados.sort(key=lambda d: d["distancia"])
    return pontuados[:k]


@tool
def buscar_regulamento(consulta: str) -> str:
    """Recupera artigos do regulamento. Use para exceções (capital, viagem internacional).

    Args:
        consulta: O que procurar no regulamento
    """
    resultados = _busca(consulta)
    if not resultados or resultados[0]["distancia"] > 0.6:   # portão da aula 07
        return _json({"recusa": "nada recuperado acima do limiar",
                      "sugestao": "reformule com termos do regulamento, ou recuse"})
    return _json(resultados)


VEREDITOS = ["aprovado", "reprovado", "recusa"]


@tool
def registrar_parecer(despesa: str, veredito: str, chave: str) -> str:
    """Registra o parecer de uma despesa. Idempotente pela chave.

    Args:
        despesa: O identificador da despesa
        veredito: aprovado, reprovado ou recusa
        chave: Identificador estável do parecer; repetir a chave não cria outro
    """
    if veredito not in VEREDITOS:
        return _json({"erro": "veredito inválido", "recebido": veredito,
                      "validos": VEREDITOS})
    if (existente := PARECERES.get(chave)):
        return _json({**existente, "ja_existia": True})
    parecer = {"parecer": f"P-{1000 + len(PARECERES)}", "despesa": despesa,
               "veredito": veredito}
    PARECERES[chave] = parecer
    return _json({**parecer, "ja_existia": False})


FERRAMENTAS = [consultar_despesa, consultar_politica, buscar_regulamento,
               registrar_parecer]

# As ferramentas cuja saída conta como CONTEXTO: é nele que a citação do
# artigo precisa estar para ser verificável.
FONTES = {"consultar_politica", "buscar_regulamento"}


# ------------------------------------------------------------------ trace

@dataclass
class Trace:
    """O trace da aula 05: o caminho, não só a resposta."""
    passos: list[dict] = field(default_factory=list)
    contexto: list[str] = field(default_factory=list)
    resposta: str = ""
    termino: str = ""
    tokens: int = 0
    mensagens: list = field(default_factory=list)


def trace_das_mensagens(mensagens: list) -> Trace:
    """Remonta o trace a partir da conversa que o agente devolve.

    Aceita mensagens do LangChain ou dicionários no formato da OpenAI — é
    assim que os traces GRAVADOS de `casos.py` passam pelo mesmo caminho."""
    mensagens = convert_to_messages(mensagens)
    trace = Trace(mensagens=mensagens)
    saidas = {m.tool_call_id: m.text for m in mensagens if m.type == "tool"}

    for m in mensagens:
        if m.type != "ai":
            continue
        trace.tokens += (m.usage_metadata or {}).get("total_tokens", 0)
        for chamada in m.tool_calls:
            saida = saidas.get(chamada["id"], "")
            erro = '"erro"' in saida or saida.startswith("Error")
            trace.passos.append({"ferramenta": chamada["name"],
                                 "argumentos": chamada["args"],
                                 "saida": saida, "erro": erro})
            if chamada["name"] in FONTES and not erro:
                trace.contexto.append(saida)

    ultima = mensagens[-1] if mensagens else None
    if ultima is not None and ultima.type == "ai" and not ultima.tool_calls:
        trace.termino, trace.resposta = "respondeu", ultima.text
    return trace


def rodar(entrada: str, versao_prompt: str = SYSTEM,
          max_passos: int = 6) -> Trace:
    """Uma execução do agente. Um agente por chamada, porque o prompt de
    sistema é o que o caso 08 compara entre versões."""
    agente = create_agent(model=sistema, tools=FERRAMENTAS,
                          system_prompt=versao_prompt)

    # O orçamento de passos da aula 05 vira `recursion_limit`: cada passo
    # são dois nós (modelo e ferramentas), mais a resposta final. `stream`
    # guarda o último estado — com `invoke`, o orçamento estourado levaria
    # o trace junto com a exceção.
    estado = {"messages": []}
    try:
        for estado in agente.stream(
                {"messages": [{"role": "user", "content": entrada}]},
                {"recursion_limit": 2 * max_passos + 1},
                stream_mode="values"):
            pass
    except GraphRecursionError:
        trace = trace_das_mensagens(estado["messages"])
        trace.termino = "orcamento_esgotado"
        return trace
    return trace_das_mensagens(estado["messages"])


# ---------------------------------------------------------------- carimbo

def carimbo() -> dict:
    """Treze campos. Duas execuções com qualquer um diferente não são
    comparáveis."""
    return {
        "prompt": "sistema@1.0", "modelo": f"{PROVEDOR}:{MODELO}",     # aula 03
        "temperatura": 0,                                               # aula 03
        "arquitetura": "agente-com-ferramentas",                        # aula 05
        "chunking": "por-artigo",                                       # aula 06
        "k": 3, "prompt_resposta": "resposta@1.0",                      # aula 07
        "memoria": "vazia",                                             # aula 08
        "framework": "langchain create_agent",                          # aula 09
        "protocolo": "n/a", "servidor": "n/a",                          # aula 10
        "dataset": VERSAO_DATASET, "rubrica": VERSAO_RUBRICA,           # aula 11
    }
