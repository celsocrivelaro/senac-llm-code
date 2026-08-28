# Aula 03 — Prompt engineering
# 03 — Self-consistency: votar em vez de confiar.
#
# CoT com temperatura > 0 produz um raciocínio DIFERENTE a cada execução —
# e um caminho errado leva a uma resposta errada. A ideia de Wang et al.:
# gerar N raciocínios independentes e ficar com a resposta MAJORITÁRIA.
#
# Caminhos errados tendem a errar de formas diferentes; o certo tende a
# convergir. A maioria filtra o ruído.
#
# Do ponto de vista de construção de prompt, o prompt é o MESMO do script 02
# (zero-shot CoT). O que muda é o parâmetro `n` da aula 02 (nota 02, §4.5):
# uma única requisição devolve N respostas independentes.
#
# Paper: https://arxiv.org/abs/2203.11171

import os
import re
import time
from collections import Counter
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")
PAUSA = 0.6

# Temperatura > 0 é REQUISITO da técnica: sem variação entre as amostras,
# os N raciocínios seriam iguais e o voto não decidiria nada.
TEMPERATURA = 0.8

VALORES_DE_N = [1, 3, 5]

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

# O mesmo prompt do script 02, condição B.
PROMPT = ("{enunciado}\n\nVamos pensar passo a passo.\n\n"
          "Termine com uma última linha exatamente assim:\nRESPOSTA: <número>")


def extrair(texto):
    achados = re.findall(r"RESPOSTA:\s*R?\$?\s*([\d.,]+)", texto, re.IGNORECASE)
    if not achados:
        return None
    try:
        return round(float(achados[-1].replace(".", "").replace(",", ".")))
    except ValueError:
        return None


def amostrar(enunciado, n):
    """n raciocínios independentes numa única requisição."""
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": PROMPT.format(enunciado=enunciado)}],
        temperature=TEMPERATURA,
        max_tokens=800,
        n=n,
    )
    return [extrair(e.message.content or "") for e in resposta.choices]


def votar(votos):
    validos = [v for v in votos if v is not None]
    if not validos:
        return None, Counter()
    contagem = Counter(validos)
    return contagem.most_common(1)[0][0], contagem


print(f"modelo: {MODELO} | temperature={TEMPERATURA} | "
      f"{len(PROBLEMAS)} problemas\n")

resumo = []

for n in VALORES_DE_N:
    print(f"### N = {n}")
    acertos = 0

    for enunciado, esperado in PROBLEMAS:
        try:
            votos = amostrar(enunciado, n)
        except Exception as erro:              # noqa: BLE001 — didático
            print(f"  falhou (n={n} pode não ser suportado): "
                  f"{type(erro).__name__}: {str(erro)[:60]}")
            break

        vencedor, contagem = votar(votos)
        ok = vencedor == esperado
        acertos += ok

        distribuicao = " ".join(f"{v}×{c}" for v, c in contagem.most_common())
        print(f"  {'ok  ' if ok else 'ERRO'} esperado={esperado:<5} "
              f"voto={str(vencedor):<6} [{distribuicao}]")
        time.sleep(PAUSA)
    else:
        resumo.append((n, acertos))
        print(f"  -> {acertos}/{len(PROBLEMAS)} corretos\n")

if resumo:
    print("=" * 50)
    print(f"{'N':>3} {'acertos':>10}")
    for n, acertos in resumo:
        print(f"{n:>3} {acertos:>8}/{len(PROBLEMAS)}")

print(
    "\nO que observar:\n"
    "  - A coluna [distribuição] é a parte interessante: quando o modelo\n"
    "    diverge (ex.: 254×3 270×2), você está VENDO o caminho errado que o\n"
    "    N=1 poderia ter escolhido por azar.\n"
    "  - Repare que o PROMPT é o mesmo do script 02. A técnica não está no\n"
    "    texto — está em pedir várias respostas e comparar. É a primeira vez\n"
    "    no curso em que a solução não é escrever melhor, e sim MEDIR mais.\n"
    "  - Se o acerto não subiu de N=1 para N=5, a técnica não é para este\n"
    "    caso. Ela só ajuda quando o modelo ERRA POR VARIAÇÃO; se ele erra\n"
    "    sempre igual, votar não conserta nada — cinco execuções erradas\n"
    "    dão uma maioria errada.\n"
    "  - N maior não é sempre melhor. Comece em 1, e só suba se medir que\n"
    "    precisa."
)
