# Aula 02 — Escolha e configuração de modelos
# 03 — max_tokens, stop e finish_reason: onde a geração termina.
#
# Truncamento silencioso é um dos bugs mais comuns de aplicação com LLM:
# o JSON vem pela metade, o código vem sem o fechamento, e o programa quebra
# lá na frente — longe da causa. A informação para detectar isso SEMPRE veio
# na resposta: o campo finish_reason.
#
#   finish_reason = "stop"           -> o modelo terminou por conta própria
#   finish_reason = "length"         -> bateu no max_tokens (truncou!)
#   finish_reason = "tool_calls"     -> pediu uma ferramenta (aula 03)
#   finish_reason = "content_filter" -> bloqueado por política

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")
PROMPT = "Explique o que é uma janela de contexto em LLMs."


def chamar(**parametros):
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0,
        **parametros,
    )
    escolha = resposta.choices[0]
    return escolha.message.content, escolha.finish_reason, resposta.usage


print("### Parte 1 — provocando o truncamento de propósito\n")
for limite in [20, 80, 400]:
    texto, motivo, uso = chamar(max_tokens=limite)
    marca = "  <-- TRUNCOU" if motivo == "length" else ""
    print(f"--- max_tokens={limite:>3} | finish_reason={motivo!r}"
          f" | tokens de saída={uso.completion_tokens}{marca}")
    print(f"    ...{texto[-90:]!r}\n")

print("### Parte 2 — o jeito certo de tratar isso no código\n")
texto, motivo, uso = chamar(max_tokens=25)
if motivo == "length":
    print("A resposta veio incompleta. Opções, em ordem de preferência:")
    print("  1. aumentar max_tokens e refazer (mais simples, custa mais);")
    print("  2. pedir uma resposta mais curta no prompt;")
    print("  3. continuar a geração a partir do que veio (streaming/continuação).")
    print("\nO que NUNCA fazer: seguir em frente fingindo que a resposta")
    print("está completa. É assim que um JSON pela metade chega no banco.\n")

print("### Parte 3 — stop: cortar a geração numa marca sua\n")
# A sequência de parada NÃO aparece na saída — o modelo para antes dela.
# Serve para delimitar formatos e para economizar tokens de saída (você paga
# por token gerado, então parar cedo é dinheiro).
resposta = client.chat.completions.create(
    model=MODELO,
    messages=[{
        "role": "user",
        "content": "Liste 5 modelos de LLM, um por linha, numerados de 1 a 5.",
    }],
    temperature=0,
    max_tokens=200,
    stop=["3."],          # queremos só os dois primeiros
)
escolha = resposta.choices[0]
print(f"finish_reason={escolha.finish_reason!r} "
      f"| tokens de saída={resposta.usage.completion_tokens}")
print(escolha.message.content)
print(
    "\nRepare: paramos no '3.' e pagamos só pelos tokens até ali.\n"
    "Em um provedor que devolve finish_reason='stop' para sequência de\n"
    "parada, você não consegue distinguir 'terminou' de 'bati no stop' —\n"
    "outro detalhe que varia por provedor e precisa ser conferido."
)
