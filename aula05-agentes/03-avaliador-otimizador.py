# Aula 05 — Arquitetura de agentes
# 02 — AVALIADOR-OTIMIZADOR: gerar -> avaliar -> revisar.
#
# O padrão é simples. As duas armadilhas dele aparecem SEMPRE:
#
#   1. Sem critério escrito, o avaliador vira ELOGIO. Peça a um modelo que
#      "avalie se está bom" e ele dirá que está bom.
#   2. Sem teto de rodadas, o par gerador-avaliador OSCILA: o avaliador pede
#      A, o gerador entrega A e perde B, o avaliador pede B.
#
# Este script roda as duas versões — avaliador vago e avaliador com critério
# verificável — sobre exatamente o mesmo texto. Leia os dois prompts ANTES
# de olhar o resultado.
#
# Formalização do padrão: Reflexion (Shinn et al., 2023).
#
# O QUE LEVAR DAQUI, depois de rodar:
#
#   - o avaliador vago costuma aprovar na primeira rodada. Ele não está
#     errado: ninguém disse a ele o que era estar bom;
#   - a qualidade de um avaliador é a qualidade do CRITÉRIO que você
#     escreveu. O modelo só executa;
#   - `{"nota": 8}` é inútil. Item a item, com `o_que_corrigir`, é acionável;
#   - se você não consegue escrever o critério, o avaliador certo é uma pessoa.

import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from dados import PEDIDOS, HOJE

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)
MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")

PAUSA = 1.0


def estruturado(prompt: str, schema: dict, nome: str,
                system: str | None = None, temperatura: float = 0) -> dict:
    """Saída estruturada com decodificação restrita (aula 02, nota 02 §7).

    Aqui ela carrega o VEREDITO do avaliador: um booleano por item do
    critério, e não uma nota de 0 a 10 que ninguém sabe interpretar."""
    mensagens = ([{"role": "system", "content": system}] if system else [])
    mensagens.append({"role": "user", "content": prompt})
    resposta = client.chat.completions.create(
        model=MODELO, messages=mensagens, temperature=temperatura,
        response_format={"type": "json_schema",
                         "json_schema": {"name": nome, "schema": schema,
                                         "strict": True}},
    )
    uso = resposta.usage
    dados = json.loads(resposta.choices[0].message.content)
    dados["_uso"] = {"entrada": uso.prompt_tokens, "saida": uso.completion_tokens,
                     "total": uso.total_tokens}
    return dados


MAX_RODADAS = 3

PEDIDO = "48219"
DADOS = {"numero": PEDIDO, **PEDIDOS[PEDIDO]}

PROMPT_GERADOR = """Escreva a resposta ao cliente sobre o pedido abaixo.
Hoje é {hoje}.

{dados}

{critica}"""

# ------------------------------------------------------------ avaliador vago
SCHEMA_VAGO = {
    "type": "object",
    "properties": {
        "aprovado": {"type": "boolean"},
        "comentario": {"type": "string"},
    },
    "required": ["aprovado", "comentario"],
    "additionalProperties": False,
}

PROMPT_VAGO = """Avalie se a resposta ao cliente abaixo está boa.

{texto}"""

# --------------------------------------------- avaliador com critério escrito
# A diferença não é o modelo. É que aqui alguém DISSE o que é estar bom.
SCHEMA_CRITERIO = {
    "type": "object",
    "properties": {
        "cita_numero_pedido": {"type": "boolean"},
        "cita_situacao_real": {"type": "boolean"},
        "cita_dias_de_atraso": {"type": "boolean"},
        "oferece_proximo_passo": {"type": "boolean"},
        "sem_promessa_de_data": {"type": "boolean"},
        "o_que_corrigir": {"type": "string"},
    },
    "required": ["cita_numero_pedido", "cita_situacao_real",
                 "cita_dias_de_atraso", "oferece_proximo_passo",
                 "sem_promessa_de_data", "o_que_corrigir"],
    "additionalProperties": False,
}

PROMPT_CRITERIO = """Verifique a resposta ao cliente item a item, contra os
dados reais do pedido. Responda cada item com verdadeiro ou falso.

- cita_numero_pedido: a resposta cita o número do pedido?
- cita_situacao_real: cita a situação que está nos dados (e não outra)?
- cita_dias_de_atraso: diz há quantos dias a previsão foi ultrapassada?
- oferece_proximo_passo: diz o que será feito a seguir?
- sem_promessa_de_data: NÃO promete uma data nova de entrega?
  (a transportadora não pode prometer o que não controla)

Se algum item for falso, escreva em `o_que_corrigir` exatamente o que falta.
Se todos forem verdadeiros, deixe `o_que_corrigir` vazio.

Dados reais do pedido (hoje é {hoje}):
{dados}

Resposta a avaliar:
{texto}"""


def gerar(critica: str | None) -> tuple[str, float]:
    texto_critica = (f"Corrija estes pontos da versão anterior: {critica}"
                     if critica else "")
    resposta = client.chat.completions.create(
        model=MODELO, temperature=0.3, max_tokens=350,
        messages=[{"role": "user", "content": PROMPT_GERADOR.format(
            hoje=HOJE, dados=json.dumps(DADOS, ensure_ascii=False),
            critica=texto_critica)}],
    )
    uso = resposta.usage
    return (resposta.choices[0].message.content.strip(),
            uso.total_tokens)


def rodar(rotulo: str, avaliar) -> dict:
    print(f"### {rotulo}\n")
    critica, tokens, candidato = None, 0, ""
    for rodada in range(1, MAX_RODADAS + 1):
        candidato, c = gerar(critica)
        tokens += c
        print(f"  rodada {rodada} · candidato:")
        print(f"    {candidato[:180].replace(chr(10), ' ')}")

        aprovado, critica, c = avaliar(candidato)
        tokens += c
        print(f"  rodada {rodada} · avaliação: "
              f"{'APROVADO' if aprovado else 'reprovado'}")
        if critica:
            print(f"    corrigir: {critica[:150]}")
        print()
        time.sleep(PAUSA)

        if aprovado:
            # Saiu por APROVAÇÃO — e o retorno diz isso.
            return {"texto": candidato, "rodadas": rodada,
                    "saida": "aprovado", "tokens": tokens}

    # Saiu por TETO. Devolver isto como se fosse aprovação é a mentira mais
    # comum deste padrão: uma reprovação honesta vale mais que um "melhor
    # esforço" apresentado como pronto.
    return {"texto": candidato, "rodadas": MAX_RODADAS,
            "saida": "teto_de_rodadas", "tokens": tokens}


def avaliador_vago(texto: str):
    r = estruturado(PROMPT_VAGO.format(texto=texto), SCHEMA_VAGO, "aval")
    return r["aprovado"], (None if r["aprovado"] else r["comentario"]), \
        r["_uso"]["total"]


def avaliador_com_criterio(texto: str):
    r = estruturado(PROMPT_CRITERIO.format(
        hoje=HOJE, dados=json.dumps(DADOS, ensure_ascii=False), texto=texto),
        SCHEMA_CRITERIO, "aval")
    itens = {k: v for k, v in r.items()
             if isinstance(v, bool)}
    aprovado = all(itens.values())
    reprovados = [k for k, v in itens.items() if not v]
    detalhe = (f"{', '.join(reprovados)} | {r['o_que_corrigir']}"
               if reprovados else None)
    return aprovado, detalhe, r["_uso"]["total"]


print(f"Pedido {PEDIDO} · previsão {DADOS['previsao']} · hoje {HOJE}")
print(f"(a previsão venceu — a resposta PRECISA reconhecer o atraso)\n")
print("=" * 78 + "\n")

a = rodar("A) avaliador VAGO — 'avalie se está bom'", avaliador_vago)
print("=" * 78 + "\n")
b = rodar("B) avaliador COM CRITÉRIO — cinco itens verificáveis",
          avaliador_com_criterio)

print("=" * 78)
print(f"""
             rodadas  saída                tokens
vago         {a['rodadas']:>7}  {a['saida']:<18}  {a['tokens']:>6}
com critério {b['rodadas']:>7}  {b['saida']:<18}  {b['tokens']:>6}
""")
