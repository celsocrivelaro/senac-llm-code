# Aula 05 — Arquitetura de agentes
# 01 — SECTIONING × ORQUESTRADOR-TRABALHADOR: a diferença é uma só.
#
#     No sectioning, as subtarefas estão no SEU código.
#     No orquestrador, quem as define é o MODELO, em tempo de execução.
#
# Os dois parecem iguais no diagrama e são profundamente diferentes na
# operação: você consegue testar o primeiro; o segundo você precisa LIMITAR.
#
# A pergunta prática que resolve os dois casos:
#
#     você consegue escrever `for parte in partes` sem chamar o modelo antes?
#
# Se consegue, é sectioning. Use sectioning: é mais barato e não surpreende.

import json
import time

from agente import estruturado, chamar_com_retry, MODELO
from dados import PEDIDOS, CLIENTES, HOJE, custo

PAUSA = 1.0
MAX_SUBTAREFAS = 5          # o teto. Um orquestrador sem teto é uma conta
                            # aberta assinada por um modelo.

# O material a analisar: os pedidos em aberto da transportadora.
LOTE = [{"numero": n, **p} for n, p in PEDIDOS.items()]


# ============================================================ SECTIONING
# As seções estão AQUI, no código. Nenhuma decisão do modelo as define.
SECOES = [
    ("atrasos", "Liste os pedidos cuja previsão já passou e diga há quantos dias."),
    ("carteira", "Agrupe os pedidos por transportadora e conte quantos há em cada."),
    ("risco", "Aponte os pedidos que vencem nos próximos 5 dias."),
]


def rodar_sectioning() -> dict:
    print("A) SECTIONING — as seções estão no código\n")
    resultados, gasto = {}, 0.0
    for nome, instrucao in SECOES:
        resposta = chamar_com_retry(
            model=MODELO, temperature=0, max_tokens=300,
            messages=[{"role": "user", "content":
                       f"Hoje é {HOJE}.\n{instrucao}\n\n"
                       f"Pedidos:\n{json.dumps(LOTE, ensure_ascii=False)}"}],
        )
        uso = resposta.usage
        gasto += custo(uso.prompt_tokens, uso.completion_tokens)
        resultados[nome] = resposta.choices[0].message.content.strip()
        print(f"   seção `{nome}` ({uso.total_tokens} tokens)")
        print(f"      {resultados[nome][:100]}...")
        time.sleep(PAUSA)
    print(f"\n   {len(SECOES)} chamadas — sempre {len(SECOES)}. "
          f"Custo R$ {gasto:.4f}\n")
    return {"resultados": resultados, "custo": gasto}


# =================================================== ORQUESTRADOR-TRABALHADOR
SCHEMA_PLANO = {
    "type": "object",
    "properties": {
        "subtarefas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string"},
                    "instrucao": {"type": "string"},
                    "por_que": {"type": "string"},
                },
                "required": ["nome", "instrucao", "por_que"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["subtarefas"],
    "additionalProperties": False,
}

PROMPT_ORQUESTRADOR = f"""Você vai analisar a carteira de pedidos de uma
transportadora e precisa decidir QUAIS análises fazem sentido para ESTE lote
específico — não uma lista genérica.

Hoje é {{hoje}}. Os pedidos:
{{lote}}

Devolva no máximo {MAX_SUBTAREFAS} subtarefas. Para cada uma, diga o que
analisar e POR QUE ela faz sentido para este lote em particular.
Não proponha análises que os dados não permitem responder."""


class PlanoGrandeDemais(Exception):
    pass


def rodar_orquestrador() -> dict:
    print("B) ORQUESTRADOR-TRABALHADOR — o modelo define as subtarefas\n")
    plano = estruturado(
        PROMPT_ORQUESTRADOR.format(hoje=HOJE,
                                   lote=json.dumps(LOTE, ensure_ascii=False)),
        SCHEMA_PLANO, "plano")
    gasto = plano["_uso"]["custo"]
    subtarefas = plano["subtarefas"]

    # O TETO. Sem isto, um plano com 400 subtarefas roda até o dinheiro acabar.
    if len(subtarefas) > MAX_SUBTAREFAS:
        raise PlanoGrandeDemais(
            f"o orquestrador pediu {len(subtarefas)} subtarefas, "
            f"o teto é {MAX_SUBTAREFAS}")

    print(f"   o modelo decidiu por {len(subtarefas)} subtarefas "
          f"(você não sabia quantas seriam):")
    for s in subtarefas:
        print(f"      - {s['nome']}: {s['por_que'][:70]}")
    print()

    resultados = {}
    for s in subtarefas:                       # os TRABALHADORES
        resposta = chamar_com_retry(
            model=MODELO, temperature=0, max_tokens=300,
            messages=[{"role": "user", "content":
                       f"Hoje é {HOJE}.\n{s['instrucao']}\n\n"
                       f"Pedidos:\n{json.dumps(LOTE, ensure_ascii=False)}"}],
        )
        uso = resposta.usage
        gasto += custo(uso.prompt_tokens, uso.completion_tokens)
        resultados[s["nome"]] = resposta.choices[0].message.content.strip()
        time.sleep(PAUSA)

    sintese = chamar_com_retry(                # o SINTETIZADOR
        model=MODELO, temperature=0, max_tokens=400,
        messages=[{"role": "user", "content":
                   "Escreva um parecer curto da carteira a partir destas "
                   "análises:\n" + json.dumps(resultados, ensure_ascii=False)}],
    )
    uso = sintese.usage
    gasto += custo(uso.prompt_tokens, uso.completion_tokens)

    print(f"   PARECER:\n      {sintese.choices[0].message.content.strip()[:300]}")
    print(f"\n   {1 + len(subtarefas) + 1} chamadas — mas você só soube "
          f"quantas DEPOIS de rodar. Custo R$ {gasto:.4f}\n")
    return {"resultados": resultados, "custo": gasto}


print(f"Carteira: {len(LOTE)} pedidos · hoje é {HOJE}\n" + "=" * 78 + "\n")
a = rodar_sectioning()
print("=" * 78 + "\n")
try:
    b = rodar_orquestrador()
except PlanoGrandeDemais as erro:
    print(f"   ABORTADO: {erro}")
    print("   (é isto que o teto faz. Melhor abortar do que descobrir na fatura.)")
    b = {"custo": 0.0}

print("=" * 78)
print(f"""
sectioning:    R$ {a['custo']:.4f}  ·  {len(SECOES)} chamadas, SEMPRE
orquestrador:  R$ {b['custo']:.4f}  ·  número de chamadas desconhecido a priori

O que levar daqui:
  - o orquestrador não é "melhor". Ele é NECESSÁRIO quando a decomposição
    depende do conteúdo — e desnecessário, caro e imprevisível quando não;
  - na dúvida entre os dois, escolha sectioning;
  - o `MAX_SUBTAREFAS` é o primeiro orçamento desta aula. Ele aparece aqui,
    e não no agente, porque este é o primeiro padrão com autonomia real.
""")
