# COM BIBLIOTECA — dá para não manter as métricas à mão?
#
# A TÉCNICA: trocar as métricas escritas à mão por bibliotecas prontas.
#
# https://github.com/langchain-ai/agentevals
# https://github.com/langchain-ai/openevals
#
# As técnicas dos casos 04 e 06, refeitas com as bibliotecas do
# ecossistema LangChain. É o último degrau da escada da aula 10: à mão,
# depois a dependência — e o aluno consegue dizer o que sumiu.
#
# O CASO: a equipe quer parar de manter `metricas.py`. Antes de trocar,
# roda as bibliotecas sobre os MESMOS traces gravados (caso 04) e os MESMOS
# rótulos humanos (casos 05 e 06), e compara.
#
#     python 09-agentevals-openevals.py      # parte 1 sem modelo; parte 2 ~10 chamadas

from agentevals.trajectory.match import create_trajectory_match_evaluator
from openevals.llm import create_llm_as_judge
from openevals.prompts import RAG_GROUNDEDNESS_PROMPT

from casos import CASOS, ROTULOS_FIDELIDADE, TRACES_GRAVADOS, chamada
from cliente import MODELO, PROVEDOR, juiz
from metricas import concordancia, imprimir_matriz

CASOS_POR_ID = {c["id"]: c for c in CASOS}


def referencia(ferramentas: list[str]) -> list[dict]:
    """A trajetória esperada de um caso, no formato de mensagens."""
    return [{"role": "assistant", "content": "",
             "tool_calls": [chamada(f"r{i}", nome) for i, nome in enumerate(ferramentas)]}]


# ============================================ 1. trajetória (agentevals)
# Três trajetórias para o C-005 (Lisboa). Uma delas é uma solução VÁLIDA
# por outro caminho: leu o regulamento primeiro e consultou a despesa duas
# vezes.
OUTRO_CAMINHO = [
    {"role": "user", "content": CASOS_POR_ID["C-005"]["entrada"]},
    {"role": "assistant", "content": "", "tool_calls": [chamada("o1", "buscar_regulamento", consulta="viagem internacional hospedagem")]},
    {"role": "tool", "tool_call_id": "o1", "content": "[art-19 ...]"},
    {"role": "assistant", "content": "", "tool_calls": [chamada("o2", "consultar_despesa", despesa="D-4613"),
                                                       chamada("o3", "consultar_politica", categoria="hospedagem")]},
    {"role": "tool", "tool_call_id": "o2", "content": "{...}"},
    {"role": "tool", "tool_call_id": "o3", "content": "{...}"},
    {"role": "assistant", "content": "", "tool_calls": [chamada("o4", "consultar_despesa", despesa="D-4613")]},
    {"role": "tool", "tool_call_id": "o4", "content": "{...}"},
    {"role": "assistant", "content": "Com o acréscimo de 60% do art. 19, o teto é R$ 768. Veredito: aprovado."},
]

TRAJETORIAS = [("outro caminho (válido)", "C-005", OUTRO_CAMINHO)] + [
    (g["id"], g["caso"], g["mensagens"]) for g in TRACES_GRAVADOS]

modos = {m: create_trajectory_match_evaluator(trajectory_match_mode=m, tool_args_match_mode="ignore")
         for m in ("strict", "superset")}

print("1 — TRAJETÓRIA COM agentevals (argumentos ignorados)\n")
print(f"  {'trajetória':<24} {'caso':<6} {'strict':>8} {'superset':>9}")
for nome, caso_id, mensagens in TRAJETORIAS:
    ref = referencia(CASOS_POR_ID[caso_id]["esperado"]["ferramentas"])
    notas = {m: avaliador(outputs=mensagens, reference_outputs=ref)["score"] for m, avaliador in modos.items()}
    print(f"  {nome:<24} {caso_id:<6} {'ok' if notas['strict'] else 'FALHA':>8} {'ok' if notas['superset'] else 'FALHA':>9}")

# `strict` reprova a solução válida: exigir o caminho exato pune quem chega
# por outra ordem. `superset` — "fez ao menos isto" — é o que `metricas.py`
# chama de cobertura. E nenhum dos dois reprova o ticket #318: as chamadas
# estão todas lá. O parecer duplicado é estado do MUNDO, e biblioteca de
# trajetória não olha o mundo (caso 04, nível de resultado).


# ======================================= 2. juiz de fidelidade (openevals)
# A rubrica pronta de "groundedness" da biblioteca, com o modelo do
# `cliente.py` como juiz. A pergunta é a do caso 06: ela concorda com os
# humanos?
avaliador = create_llm_as_judge(prompt=RAG_GROUNDEDNESS_PROMPT, judge=juiz,
                                feedback_key="fiel")


def julgar(resposta: str, contexto: str) -> bool | None:
    try:
        return bool(avaliador(outputs=resposta, context=contexto)["score"])
    except Exception:
        return None


print(f"\n2 — JUIZ COM openevals (RAG_GROUNDEDNESS_PROMPT)  [{PROVEDOR}:{MODELO}]\n")
consenso = [r for r in ROTULOS_FIDELIDADE if r["humano_a"] == r["humano_b"]]
resultado = concordancia([(r["id"], r["humano_a"], julgar(r["resposta"], r["contexto"]))
                          for r in consenso])
imprimir_matriz(resultado, ref="humano", aval="juiz")
for r in consenso:
    if r["id"] in resultado["desacordos"]:
        print(f"  desacordo {r['id']}: {r['nota']}")

# Some o código da métrica. NÃO some a calibração: a rubrica pronta foi
# escrita para outro critério de "groundedness", e só a matriz contra os
# SEUS rótulos diz se ela mede o que você precisa. Compare com o caso 06.
