# Aula 03 — Prompt engineering
# 02 — Chain-of-thought: o ganho é real, o preço também.
#
# Duas condições sobre os mesmos problemas de várias etapas:
#   A) resposta direta
#   B) zero-shot CoT ("vamos pensar passo a passo")
#
# CoT gera muito mais tokens de SAÍDA — a tarifa cara (aula 02, nota 04, §1).
# Este script mede as duas coisas juntas: quanto se acerta a mais, e quanto
# se paga a mais. Uma técnica só entra em produção quando você consegue
# preencher a frase: "custa X a mais e me dá Y a mais de acerto".
#
# Papers: Wei et al. (2022)   https://arxiv.org/abs/2201.11903
#         Kojima et al. (2022) https://arxiv.org/abs/2205.11916

import os
import re
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")
PAUSA = 0.5

# Preços em US$ por 1M de tokens. CONFIRA em https://mistral.ai/pricing.
# Consultado em: ____/____/______
PRECO_ENTRADA = 0.15
PRECO_SAIDA = 0.60

# Problemas de VÁRIAS ETAPAS, com resposta numérica verificável.
# Repare que nenhum deles é difícil — são só multi-etapa, que é o critério
# que decide o uso de CoT (nota 01, §7).
PROBLEMAS = [
    ("Uma loja vende canetas em caixas de 12 por R$ 30 a caixa e avulsas por "
     "R$ 3,50. Preciso de 100 canetas gastando o mínimo possível. Qual o "
     "valor total, em reais?", 254),

    ("Três transportadoras: A cobra R$ 80 fixo mais R$ 2,00 por kg; B cobra "
     "R$ 120 fixo mais R$ 1,20 por kg; C cobra R$ 3,00 por kg sem taxa fixa. "
     "Para um envio de 60 kg, quanto custa a opção mais barata, em reais?", 180),

    ("Qual é a soma dos números ímpares deste grupo: 15, 32, 5, 13, 82, 7, 1?",
     41),

    ("Um palete comporta 48 caixas. Preciso enviar 300 caixas em paletes "
     "cheios. Quantas caixas sobram fora dos paletes cheios?", 12),
]

FORMATO = "\n\nTermine a resposta com uma última linha exatamente assim:\nRESPOSTA: <número>"

SUFIXO_COT = "\n\nVamos pensar passo a passo."


def extrair_resposta(texto):
    """Pega o número da última linha 'RESPOSTA: <n>'."""
    achados = re.findall(r"RESPOSTA:\s*R?\$?\s*([\d.,]+)", texto, re.IGNORECASE)
    if not achados:
        return None
    bruto = achados[-1].replace(".", "").replace(",", ".")
    try:
        return round(float(bruto))
    except ValueError:
        return None


def resolver(enunciado, usar_cot):
    prompt = enunciado + FORMATO + (SUFIXO_COT if usar_cot else "")
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=800,     # CoT precisa de espaço; se faltar, paga e não entrega
    )
    escolha = resposta.choices[0]
    truncou = escolha.finish_reason == "length"
    valor = None if truncou else extrair_resposta(escolha.message.content or "")
    return valor, resposta.usage, truncou


def rodar(nome, usar_cot):
    acertos = entrada = saida = 0
    print(f"### {nome}")
    for enunciado, esperado in PROBLEMAS:
        valor, uso, truncou = resolver(enunciado, usar_cot)
        entrada += uso.prompt_tokens
        saida += uso.completion_tokens
        ok = valor == esperado
        acertos += ok

        marca = "ok  " if ok else "ERRO"
        extra = "  (TRUNCOU: max_tokens insuficiente)" if truncou else ""
        print(f"  {marca} esperado={esperado:<5} obtido={str(valor):<6} "
              f"saída={uso.completion_tokens:>4} tokens{extra}")
        time.sleep(PAUSA)

    custo = (entrada * PRECO_ENTRADA + saida * PRECO_SAIDA) / 1_000_000
    print(f"  -> {acertos}/{len(PROBLEMAS)} | entrada {entrada} | "
          f"saída {saida} | US$ {custo:.6f}\n")
    return acertos, entrada, saida, custo


print(f"modelo: {MODELO} | {len(PROBLEMAS)} problemas de várias etapas\n")

direto = rodar("A) resposta direta", usar_cot=False)
cot = rodar("B) zero-shot CoT", usar_cot=True)

print("=" * 70)
print(f"{'':<18} {'acertos':>8} {'saída':>8} {'US$':>10}")
print(f"{'direto':<18} {direto[0]:>6}/{len(PROBLEMAS)} {direto[2]:>8} {direto[3]:>10.6f}")
print(f"{'CoT':<18} {cot[0]:>6}/{len(PROBLEMAS)} {cot[2]:>8} {cot[3]:>10.6f}")

if direto[2]:
    print(f"\nCoT gerou {cot[2] / direto[2]:.1f}x mais tokens de saída "
          f"e custou {cot[3] / direto[3]:.1f}x mais.")
print(f"Ganho: {cot[0] - direto[0]:+d} acerto(s).")

print(
    "\nO que observar:\n"
    "  - O ganho aparece porque estes problemas têm ETAPAS. Rode o mesmo\n"
    "    experimento com a classificação do script 00 e o CoT não ganha nada:\n"
    "    só encarece, e ainda dá espaço para o modelo se contradizer.\n"
    "  - Olhe a coluna 'saída': é o multiplicador que você vai pagar em toda\n"
    "    requisição de produção, não só neste teste.\n"
    "  - Se algum caso TRUNCOU, isso não é erro do modelo — é max_tokens mal\n"
    "    dimensionado. Com CoT você paga o raciocínio inteiro e, se o teto\n"
    "    acabar antes da conclusão, não recebe resposta nenhuma\n"
    "    (aula 02, nota 03, §2.2).\n"
    "  - E o principal: se o seu modelo for de RACIOCÍNIO, o ganho tende a\n"
    "    zero e o custo continua. Ele já faz isso internamente — pedir de\n"
    "    novo é pagar duas vezes (aula 02, nota 01, §6.3)."
)
