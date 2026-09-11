# Aula 05 — Arquitetura de agentes
# 00 — SEQUENCIAL (prompt chaining) COM PORTÃO: o padrão mais simples dos cinco.
#
# Duas chamadas em sequência, e entre elas uma VALIDAÇÃO EM CÓDIGO:
#
#     entrada ──> [ LLM 1: extrai ] ──> PORTÃO ──> [ LLM 2: redige ] ──> saída
#                                          │
#                                          └── falhou ──> para aqui
#
# O padrão em si é trivial. O assunto do script é o PORTÃO, e a tese é uma:
#
#     REGRA EXPRESSÁVEL EM PYTHON SE IMPLEMENTA EM PYTHON.
#
# Sai mais barata, é determinística e não alucina. A etapa 1 extrai o que o
# cliente disse; o portão confere contra os dados REAIS; só então a etapa 2
# escreve. Sem o portão, a etapa 2 recebe lixo e produz uma resposta
# impecavelmente redigida sobre um pedido que não existe.
#
# SUGESTÃO DE USO EM SALA: rode e compare as duas colunas do relatório final.
# Peça à turma que leia a resposta gerada SEM portão para a mensagem 3 antes
# de dizer qual é o problema dela.
#
# O QUE LEVAR DAQUI, depois de rodar:
#
#   - o portão não melhora a resposta: ele IMPEDE que uma resposta errada
#     seja produzida. São coisas diferentes, e a segunda é mais valiosa;
#   - cada validação do portão é um `if`. Nenhuma delas precisaria de um
#     modelo, e nenhuma delas erra;
#   - o custo de parar no portão é UMA chamada. O custo de não parar é duas
#     chamadas e uma resposta errada entregue ao cliente;
#   - repare no que a etapa 2 recebe: os dados do SISTEMA, não os do cliente.
#     O que o cliente disse serviu para localizar o pedido, e só.

import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from dados import PEDIDOS, HOJE

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)
MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")


def estruturado(prompt: str, schema: dict, nome: str,
                temperatura: float = 0) -> dict:
    """Saída estruturada com decodificação restrita (aula 02, nota 02 §7).

    Aqui ela carrega a EXTRAÇÃO: o schema garante que a etapa 1 devolva
    campos, e não prosa descrevendo campos."""
    resposta = client.chat.completions.create(
        model=MODELO, temperature=temperatura,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": nome, "schema": schema,
                                         "strict": True}},
    )
    dados = json.loads(resposta.choices[0].message.content)
    dados["_tokens"] = resposta.usage.total_tokens
    return dados


# ------------------------------------------------------- as mensagens de teste
# Três delas passam no portão e duas são barradas — por motivos diferentes,
# e é a diferença entre os dois motivos que interessa.
MENSAGENS = [
    # 1. caminho feliz: pedido existe, e está mesmo atrasado
    "Bom dia, o pedido 48219 era pra ter chegado semana passada e nada. "
    "Podem verificar?",

    # 2. caminho feliz: pedido existe, entrega concluída
    "gostaria de confirmar se o 77310 foi entregue mesmo",

    # 3. (*) O CASO DO SCRIPT: o número não existe na base.
    #    Sem portão, a etapa 2 escreve uma resposta perfeita sobre ele.
    "Meu pedido 99999 está parado há dias, isso é inaceitável!",

    # 4. (*) o cliente cita uma data que ainda não aconteceu — erro de
    #    digitação comum (2026-09-30 no lugar de 2026-08-30). O portão pega;
    #    um modelo tende a aceitar e raciocinar em cima.
    "O pedido 55870 deveria ter chegado em 2026-12-30 e não chegou",

    # 5. sem número de pedido: a extração devolve vazio, e o portão para
    "vocês entregam em Portugal? nunca pedi nada mas queria saber",
]

# ============================================================ ETAPA 1 — EXTRAIR
SCHEMA_EXTRACAO = {
    "type": "object",
    "properties": {
        "numero_pedido": {
            "type": "string",
            "description": "o número citado, ou string vazia se não houver"},
        "tipo": {
            "type": "string",
            "enum": ["atraso", "confirmacao_entrega", "avaria", "outro"]},
        "data_citada": {
            "type": "string",
            "description": "data no formato AAAA-MM-DD citada pelo cliente, "
                           "ou string vazia"},
    },
    "required": ["numero_pedido", "tipo", "data_citada"],
    "additionalProperties": False,
}

PROMPT_EXTRACAO = """Extraia os campos da mensagem de um cliente de
transportadora. NÃO invente: se um campo não estiver na mensagem, devolva
string vazia.

Mensagem: {mensagem}"""


def extrair(mensagem: str) -> dict:
    return estruturado(PROMPT_EXTRACAO.format(mensagem=mensagem),
                       SCHEMA_EXTRACAO, "extracao")


# ================================================================ O PORTÃO
# Quatro validações, quatro `if`. Nenhuma precisa de modelo, e nenhuma erra.
#
# Repare que elas são de DUAS naturezas:
#   - forma   (o campo tem o formato certo?)     -> 1 e 3
#   - fato    (o que o cliente disse é verdade?) -> 2 e 4
# A segunda natureza é a que o modelo não tem como verificar sozinho: ele não
# conhece a base de pedidos.

class PortaoFechou(Exception):
    """Levanta com o motivo. O motivo é o que o usuário vai ler."""


def portao(extraido: dict) -> dict:
    numero = extraido["numero_pedido"]

    if not numero:                                              # 1. forma
        raise PortaoFechou("a mensagem não cita número de pedido")

    if not re.fullmatch(r"\d{5}", numero):                      # 2. forma
        raise PortaoFechou(
            f"'{numero}' não tem formato de pedido (5 dígitos)")

    pedido = PEDIDOS.get(numero)
    if pedido is None:                                          # 3. fato
        raise PortaoFechou(f"o pedido {numero} não existe na base")

    data = extraido["data_citada"]
    if data and data > str(HOJE):                               # 4. fato
        raise PortaoFechou(
            f"a data citada ({data}) é futura — hoje é {HOJE}")

    # O portão não devolve o que o cliente disse: devolve o que o SISTEMA sabe.
    return {"numero": numero, **pedido}


# ============================================================ ETAPA 2 — REDIGIR
PROMPT_RESPOSTA = """Escreva a resposta ao cliente, em no máximo 3 linhas.
Hoje é {hoje}.

Dados REAIS do pedido, vindos do sistema:
{dados}

O cliente escreveu: {mensagem}

Não prometa data nova de entrega. Não invente informação que não esteja nos
dados acima."""


def redigir(mensagem: str, dados: dict) -> tuple[str, int]:
    resposta = client.chat.completions.create(
        model=MODELO, temperature=0.3, max_tokens=200,
        messages=[{"role": "user", "content": PROMPT_RESPOSTA.format(
            hoje=HOJE, dados=json.dumps(dados, ensure_ascii=False),
            mensagem=mensagem)}],
    )
    return (resposta.choices[0].message.content.strip(),
            resposta.usage.total_tokens)


# ------------------------------------------------------------------ o laço
LINHA = "=" * 78
print(f"Sequencial com portão · {len(MENSAGENS)} mensagens · hoje é {HOJE}\n")

barradas = 0
tokens_com = 0
tokens_sem = 0

for i, mensagem in enumerate(MENSAGENS, 1):
    print(f"{LINHA}\n{i}. {mensagem[:70]}\n")

    extraido = extrair(mensagem)
    tokens_com += extraido["_tokens"]
    tokens_sem += extraido["_tokens"]
    print(f"   [etapa 1] pedido={extraido['numero_pedido'] or '—'}  "
          f"tipo={extraido['tipo']}  data={extraido['data_citada'] or '—'}")

    # ---------------------------------------------------------- COM portão
    try:
        dados = portao(extraido)
        print("   [portão ] passou")
        texto, t = redigir(mensagem, dados)
        tokens_com += t
        print(f"   [etapa 2] {texto[:66]}")
    except PortaoFechou as motivo:
        barradas += 1
        print(f"   [portão ] BARRADA — {motivo}")
        print("   [etapa 2] não executada")

        # ------------------------------------------------------ SEM portão
        # O que teria acontecido: a etapa 2 roda com o que o cliente disse,
        # sem nada que o confirme.
        inventado = {"numero": extraido["numero_pedido"] or "?",
                     "situacao": "desconhecida",
                     "previsao": extraido["data_citada"] or "desconhecida"}
        texto, t = redigir(mensagem, inventado)
        tokens_sem += t
        print(f"   [SEM portão, o que sairia] {texto[:60]}")
    print()

print(LINHA)
print(f"mensagens .......... {len(MENSAGENS)}")
print(f"barradas no portão . {barradas}   (zero chamadas de redação gastas)")
print(f"tokens com portão .. {tokens_com}")
print(f"tokens sem portão .. {tokens_com + tokens_sem}   "
      f"(+{tokens_sem} para produzir respostas que não deveriam existir)")
