# Aula 05 — Arquitetura de agentes
# 00 — O ROTEADOR: o modelo classifica, o SEU código despacha.
#
# Este script existe para produzir UM número, e é o número que organiza a
# aula inteira:
#
#     quantas das 10 mensagens precisaram de LLM?
#
# A resposta é "menos do que você esperava". A rota mais valiosa de um
# roteador costuma ser a que NÃO CHAMA O MODELO — e é a que quase todo mundo
# esquece de escrever, porque não parece IA.
#
# Dois pontos de engenharia, e os dois estão no código abaixo:
#
#   1. A rota `nenhuma` é OBRIGATÓRIA. Sem escape, o modelo é forçado a
#      escolher entre opções que não servem — e escolhe, com confiança.
#   2. O roteador é SAÍDA ESTRUTURADA com enum (aula 02, nota 02 §7).
#      Não é uma técnica nova; é a mesma, decidindo o fluxo do programa.

import re
import time

from agente import estruturado
from dados import MENSAGENS, PEDIDOS, HOJE

PAUSA = 1.0

ROTAS = ["consulta_status", "reclamacao", "fora_de_escopo", "nenhuma"]

# --------------------------------------------------------- a rota sem LLM
# Uma consulta de status é: um número de pedido + uma intenção de consulta,
# e NADA MAIS. Se a mensagem também traz reclamação, a regra não se aplica.
RE_PEDIDO = re.compile(r"\b(\d{5})\b")
RE_CONSULTA = re.compile(r"\b(status|onde|situa|saber|qual|cad[êe])\b", re.I)
RE_PROBLEMA = re.compile(
    r"\b(atras|absurd|n[ãa]o recebi|n[ãa]o cheg|rasgad|trincad|quebrad|"
    r"avariad|reclama|inaceit)\w*", re.I)


def regra_status(mensagem: str) -> dict | None:
    """Resolve por REGRA, sem nenhuma chamada de LLM. Devolve None quando
    não tem certeza — na dúvida, deixa para o classificador."""
    numeros = RE_PEDIDO.findall(mensagem)
    if len(numeros) != 1:
        return None
    if not RE_CONSULTA.search(mensagem) or RE_PROBLEMA.search(mensagem):
        return None
    pedido = PEDIDOS.get(numeros[0])
    if pedido is None:
        return None
    return {"rota": "consulta_status", "pedido": numeros[0],
            "resposta": (f"Pedido {numeros[0]}: {pedido['situacao']}, "
                         f"previsão {pedido['previsao']} "
                         f"({pedido['transportadora']}).")}


# ------------------------------------------------- a rota que usa o modelo
SCHEMA_ROTA = {
    "type": "object",
    "properties": {
        "rota": {"type": "string", "enum": ROTAS},
        "justificativa": {"type": "string"},
    },
    "required": ["rota", "justificativa"],
    "additionalProperties": False,
}

PROMPT_ROTEADOR = """Classifique a mensagem de um cliente de transportadora
em UMA das rotas:

- consulta_status: só quer saber onde está o pedido, sem reclamação
- reclamacao: relata um problema (atraso, avaria, entrega não recebida)
- fora_de_escopo: assunto que a transportadora não trata
- nenhuma: falta informação para classificar, ou não se encaixa em nenhuma

Se a mensagem não permitir classificar com segurança, use `nenhuma`.
Não invente uma rota para forçar um encaixe.

Mensagem: {mensagem}"""


def classificar(mensagem: str) -> dict:
    return estruturado(PROMPT_ROTEADOR.format(mensagem=mensagem),
                       SCHEMA_ROTA, "rota")


# ------------------------------------------------------------------ o laço
print(f"Triagem de {len(MENSAGENS)} mensagens · hoje é {HOJE}\n")

contagem = {"regra": 0, "llm": 0}
por_rota = {rota: 0 for rota in ROTAS}
custo_total = 0.0

for i, mensagem in enumerate(MENSAGENS, 1):
    curta = mensagem.replace("\n", " ")[:58]

    if (decidido := regra_status(mensagem)):
        contagem["regra"] += 1
        por_rota["consulta_status"] += 1
        print(f"{i:2}. [regra ] {curta:<60} -> consulta_status  (0 chamadas)")
        print(f"              {decidido['resposta']}")
        continue

    resultado = classificar(mensagem)
    contagem["llm"] += 1
    por_rota[resultado["rota"]] += 1
    custo_total += resultado["_uso"]["custo"]
    print(f"{i:2}. [ LLM  ] {curta:<60} -> {resultado['rota']}")
    print(f"              {resultado['justificativa'][:70]}")
    time.sleep(PAUSA)

# ------------------------------------------------------------------ a conta
print("\n" + "=" * 78)
print(f"resolvidas por REGRA: {contagem['regra']:>2}  "
      f"(zero chamadas de LLM, zero risco de alucinação)")
print(f"enviadas ao MODELO:   {contagem['llm']:>2}  "
      f"custo R$ {custo_total:.4f}")
print()
for rota, n in por_rota.items():
    print(f"  {rota:<18} {'#' * n}{'.' * (len(MENSAGENS) - n)}  {n}")

if contagem["regra"]:
    projecao = custo_total / contagem["llm"] * len(MENSAGENS)
    print(f"\nSe TUDO tivesse ido para o modelo: ~R$ {projecao:.4f} "
          f"({projecao / custo_total:.1f}x o que você pagou)")

print("""
O que levar daqui:
  - a economia não veio de um prompt melhor nem de um modelo melhor.
    Veio de decidir o que NÃO mandar para o modelo;
  - os itens resolvidos por regra são MAIS confiáveis, não menos:
    regra não alucina;
  - a rota `nenhuma` pegou a mensagem sem número de pedido. Sem ela, o
    modelo teria escolhido alguma coisa — e você não saberia que ele chutou.
""")
