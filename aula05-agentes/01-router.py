# Aula 05 — Arquitetura de agentes
# 00 — O ROUTER: analisa a entrada e decide QUEM a processa.
#
# Um ponto de triagem. Em vez de mandar toda pergunta para um modelo grande,
# o Router direciona cada entrada para o recurso adequado a ela — que às
# vezes é código, sem modelo nenhum.
#
# Este script produz UM número, e é o número que organiza a aula inteira:
#
#     quantas das 10 mensagens precisaram de LLM?
#
# A resposta é "menos do que você esperava". A rota mais valiosa de um Router
# costuma ser a que NÃO CHAMA O MODELO — e é a que quase todo mundo esquece
# de escrever, porque não parece IA.
#
# AS TRÊS FORMAS DE ROTEAR, em ordem crescente de custo:
#
#   1. REGRA        palavra-chave, regex, metadado.  Zero chamadas.
#                   Não alucina, e não generaliza.
#   2. EMBEDDING    vetor da entrada × exemplos de cada rota. Uma chamada
#                   barata, sem gerar texto.  -> é a AULA 06.
#   3. SEMÂNTICA    um modelo devolve {"rota": "..."}.  Uma chamada de
#                   geração. Lida com o que as duas anteriores não previram.
#
# Elas se COMBINAM, e este script usa a 1 e a 3 em cascata: tenta a barata,
# cai para a cara. A do meio aparece aqui nomeada e desligada — ela depende
# de embeddings, que é a aula seguinte.
#
# E o Router decide mais que a rota: decide O MODELO. Consulta simples e
# recusa vão para o modelo pequeno; reclamação, que exige ponderar e cuja
# resposta vai para um cliente irritado, vai para o grande.
#
# Dois pontos de engenharia, e os dois estão no código abaixo:
#
#   1. A rota `nenhuma` é OBRIGATÓRIA. Sem escape, o modelo é forçado a
#      escolher entre opções que não servem — e escolhe, com confiança.
#   2. A classificação é SAÍDA ESTRUTURADA com enum (aula 02, nota 02 §7).
#      Não é uma técnica nova; é a mesma, decidindo o fluxo do programa.
#
# O QUE LEVAR DAQUI, depois de rodar:
#
#   - a economia não veio de um prompt melhor nem de um modelo melhor.
#     Veio de decidir o que NÃO mandar para o modelo;
#   - os itens resolvidos por regra são MAIS confiáveis, não menos:
#     regra não alucina;
#   - a rota `nenhuma` pegou a mensagem sem número de pedido. Sem ela, o
#     modelo teria escolhido alguma coisa — e você não saberia que ele chutou;
#   - repare em quantas mensagens chegaram ao modelo GRANDE. Um Router que
#     manda tudo para ele não é Router — é um `if` que sempre dá verdadeiro.

import json
import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI

from dados import PEDIDOS, HOJE

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)
# Os dois modelos entre os quais o Router escolhe. Se você não definir o
# grande, ele vira o mesmo do pequeno e o experimento fica degenerado — o
# script avisa na tela quando isso acontece.
MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")
MODELO_GRANDE = os.environ.get("LLM_MODELO_GRANDE", MODELO)

PAUSA = 1.0


def estruturado(prompt: str, schema: dict, nome: str, modelo: str = MODELO,
                temperatura: float = 0) -> dict:
    """Saída estruturada com decodificação restrita (aula 02, nota 02 §7).

    É o mecanismo por trás do Router: `enum` no schema significa que o modelo
    não tem como devolver uma rota que não existe."""
    mensagens = [{"role": "user", "content": prompt}]
    resposta = client.chat.completions.create(
        model=modelo, messages=mensagens, temperature=temperatura,
        response_format={"type": "json_schema",
                         "json_schema": {"name": nome, "schema": schema,
                                         "strict": True}},
    )
    uso = resposta.usage
    dados = json.loads(resposta.choices[0].message.content)
    dados["_uso"] = {"entrada": uso.prompt_tokens, "saida": uso.completion_tokens,
                     "total": uso.total_tokens}
    return dados

ROTAS = ["consulta_status", "reclamacao", "fora_de_escopo", "nenhuma"]

# ------------------------------------------------------- o lote de mensagens
# Fica aqui, e não em `dados.py`, porque só este script o usa — ao contrário
# de PEDIDOS e HOJE, que os outros scripts compartilham.
#
# A mistura é deliberada: a MAIORIA é consulta de status pura, que uma regra
# resolve sem chamar o modelo. Se você mandar tudo para o LLM, funciona — e
# chama o modelo dez vezes onde a regra bastaria.
# Quatro delas são as instrutivas, marcadas abaixo com (*).
MENSAGENS = [
    # (*) a maioria do lote: número + intenção de consulta, e NADA MAIS.
    #     Não deveria consumir modelo nenhum.
    "Qual o status do pedido 48219?",
    "onde está meu pedido 31002",
    "Status 90455 por favor",
    "quero saber do 55870",

    # (*) tem número E intenção de consulta — mas também tem reclamação.
    #     A REGRA DECLINA de propósito: na dúvida, deixa para o modelo.
    "O pedido 48219 está atrasado há duas semanas e ninguém me responde. "
    "Isso é um absurdo, quero uma solução hoje.",

    # (*) divergência entre o que o cliente diz e o que o sistema registra.
    #     É o caso que a nota 02 usa para justificar um AGENTE.
    "Consta que o 77310 foi entregue mas eu não recebi nada. "
    "Falei com o porteiro e ele também não viu.",

    "A caixa do 55870 chegou rasgada e o produto está trincado",
    "vocês entregam em Portugal?",
    "Só queria dizer que a entrega do 31002 foi rapidíssima, parabéns!",

    # (*) sem número: não há rota aplicável. Revela se existe escape.
    "meu pedido não chegou",
]

# --------------------------------------------------------- a rota sem LLM
# Uma consulta de status é: um número de pedido + uma intenção de consulta,
# e NADA MAIS. Se a mensagem também traz reclamação, a regra não se aplica.
RE_PEDIDO = re.compile(r"\b(\d{5})\b")
RE_CONSULTA = re.compile(r"\b(status|onde|situa|saber|qual|cad[êe])\b", re.I)
RE_PROBLEMA = re.compile(
    r"\b(atras|absurd|n[ãa]o recebi|n[ãa]o cheg|rasgad|trincad|quebrad|"
    r"avariad|reclama|inaceit)\w*", re.I)


def router_regra(mensagem: str) -> dict | None:
    """FORMA 1 — resolve por REGRA, sem nenhuma chamada de LLM.

    Devolve None quando não tem certeza. Esse `None` é o desenho todo: a
    regra não tenta adivinhar, ela DECLINA — e a cascata leva o caso para a
    forma seguinte."""
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


def router_modelo(mensagem: str) -> dict:
    """FORMA 3 — classifica com o modelo PEQUENO.

    Classificar é tarefa fácil: quatro opções e um enum que impede inventar
    uma quinta. Gastar o modelo grande aqui seria pagar caro pela parte
    barata do problema."""
    return estruturado(PROMPT_ROTEADOR.format(mensagem=mensagem),
                       SCHEMA_ROTA, "rota", modelo=MODELO)


# FORMA 2 — por EMBEDDING. Não está implementada, e a ausência é o ponto:
# ela converteria a mensagem em vetor e a compararia com exemplos de cada
# rota, decidindo sem gerar texto. Isso depende de embeddings, que é a
# AULA 06 — e é lá que esta linha vira código.
router_embedding = None

FORMAS = {
    "regra": router_regra,          # zero chamadas
    "embedding": router_embedding,  # Aula 06
    "modelo": router_modelo,        # uma chamada de geração, modelo pequeno
}


def router(mensagem: str) -> tuple[str, dict]:
    """A CASCATA: tenta a forma barata, cai para a cara.

    Devolve qual forma decidiu, e é esse dado que o relatório do fim conta.
    Um Router em que a forma cara resolve tudo não está economizando nada."""
    if (decidido := router_regra(mensagem)):
        return "regra", decidido
    return "modelo", router_modelo(mensagem)


# --------------------------------- a segunda decisão: QUAL modelo atende
# O Router não escolhe só a rota — escolhe o modelo que vai processá-la.
# A rota `nenhuma` não chega a modelo nenhum: vai para uma fila humana.
MODELO_POR_ROTA = {
    "consulta_status": MODELO,          # dado estruturado, resposta curta
    "fora_de_escopo": MODELO,           # recusar é fácil
    "reclamacao": MODELO_GRANDE,        # exige ponderar, e o cliente está irritado
    "nenhuma": None,                    # ninguém: fila de revisão
}

PROMPT_ATENDIMENTO = """Você atende clientes de uma transportadora.
Responda à mensagem abaixo em no máximo 3 linhas, sem prometer data nova
de entrega.

Mensagem: {mensagem}"""


def atender(mensagem: str, rota: str) -> tuple[str | None, str, int]:
    """Processa a mensagem no modelo que a rota determina."""
    modelo = MODELO_POR_ROTA[rota]
    if modelo is None:
        return None, "—", 0
    resposta = client.chat.completions.create(
        model=modelo, temperature=0.3, max_tokens=200,
        messages=[{"role": "user",
                   "content": PROMPT_ATENDIMENTO.format(mensagem=mensagem)}],
    )
    return (resposta.choices[0].message.content.strip(),
            modelo, resposta.usage.total_tokens)


# ------------------------------------------------------------------ o laço
# A decisão inteira está em `router()` e em `atender()`. Daqui para baixo é
# relatório.
print(f"Triagem de {len(MENSAGENS)} mensagens · hoje é {HOJE}")
print(f"pequeno: {MODELO}   grande: {MODELO_GRANDE}")
if MODELO_GRANDE == MODELO:
    print("AVISO: os dois são o mesmo modelo. Defina LLM_MODELO_GRANDE no "
          ".env\n       para ver o Router escolhendo de verdade.")
print()

por_forma = {forma: 0 for forma in FORMAS}      # o catálogo das três, vivo
por_modelo: dict[str, list[int]] = {}
por_rota = {rota: [] for rota in ROTAS}
tokens_total = 0

for i, mensagem in enumerate(MENSAGENS, 1):
    curta = mensagem.replace("\n", " ")[:56]
    forma, decidido = router(mensagem)
    por_forma[forma] += 1

    if forma == "regra":
        rota = decidido["rota"]
        print(f"{i:2}. [regra ] {curta:<58} -> {rota}")
        print(f"              {decidido['resposta']}")
    else:
        rota = decidido["rota"]
        tokens_total += decidido["_uso"]["total"]
        print(f"{i:2}. [modelo] {curta:<58} -> {rota}")
        print(f"              {decidido['justificativa'][:66]}")
        time.sleep(PAUSA)

    por_rota[rota].append(i)

    # A segunda decisão: quem processa esta rota.
    texto, modelo_usado, tokens = atender(mensagem, rota)
    tokens_total += tokens
    por_modelo.setdefault(modelo_usado, []).append(i)
    if texto:
        print(f"              [{modelo_usado}] {texto[:64]}")
        time.sleep(PAUSA)
    else:
        print("              [fila humana] rota `nenhuma`: ninguém foi chamado")

# ------------------------------------------------------------------ a conta
print("\n" + "=" * 78)
print("POR FORMA DE ROTEAR")
for forma, n in por_forma.items():
    nota = "  (Aula 06)" if forma == "embedding" else ""
    print(f"  {forma:<12} {n:>2} mensagens{nota}")

print("\nPOR MODELO QUE ATENDEU")
for modelo_usado, quais in por_modelo.items():
    rotulo = "fila humana" if modelo_usado == "—" else modelo_usado
    numeros = " ".join(f"#{n}" for n in quais)
    print(f"  {rotulo:<24} {len(quais):>2}   {numeros}")

print("\nPOR ROTA")
for rota, quais in por_rota.items():
    numeros = " ".join(f"#{n}" for n in quais)
    print(f"  {rota:<18} {len(quais):>2}   {numeros}")

print(f"\ntokens da execução: {tokens_total}")
if por_forma["regra"] and por_forma["modelo"]:
    media = tokens_total / (len(MENSAGENS) - por_forma["regra"])
    projecao = media * len(MENSAGENS)
    print(f"Se TUDO tivesse ido para o modelo: ~{projecao:.0f} tokens "
          f"({projecao / tokens_total:.1f}x esta execução)")
