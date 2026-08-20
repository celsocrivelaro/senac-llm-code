# Aula 02 — Escolha e configuração de modelos
# 06 — Benchmark próprio: a mesma bateria de tarefas em vários modelos,
#      medindo latência, TTFT, tokens e custo.
#
# Esta é a peça central da aula. Leaderboard público não decide nada por você:
# ele mede tarefas que não são a sua, com prompts que não são os seus, e a
# média esconde a variância. O que decide é ESTA tabela, com as SUAS tarefas.
#
# Três coisas são medidas:
#   TTFT (time to first token) — quanto o usuário espera para ver algo;
#   tokens/s                   — quão rápido o texto sai depois disso;
#   custo                      — tokens de entrada e saída × preço.
#
# Saída: tabela no terminal + arquivo benchmark.csv para você analisar.

import os
import csv
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# --------------------------------------------------------------------------
# PREENCHA os preços consultando https://mistral.ai/pricing (US$ por 1M tokens)
# e anote a data da consulta. Preço de LLM muda; material impresso mente.
# Deixe None no que você não preencher — o script mostra "-" no custo.
# Consultado em: ____/____/______
# --------------------------------------------------------------------------
PRECOS = {
    # "modelo":                  {"entrada": 0.00, "saida": 0.00},
    "ministral-3b-latest":       {"entrada": 0.10, "saida": 0.10},
    "mistral-small-latest":      {"entrada": 0.15, "saida": 0.60},
    "mistral-large-latest":      {"entrada": 0.50, "saida": 1.50},
}

# Confirme com 00-catalogo-modelos.py quais destes a sua chave enxerga.
MODELOS = list(PRECOS.keys())

# Troque por tarefas do SEU domínio — é esse o ponto do benchmark próprio.
TAREFAS = [
    ("resumo", "Resuma em duas frases: a Revolução Industrial foi um período de "
               "transição para novos processos de manufatura entre 1760 e 1840."),
    ("codigo", "Escreva uma função Python que retorna o n-ésimo número de Fibonacci."),
    ("raciocinio", "Três caixas com 4 bolas cada. Transfiro 2 da primeira para a "
                   "terceira. Quantas bolas tem cada caixa? Pense passo a passo."),
]

MAX_TOKENS = 200
PAUSA = 0.6


def medir(modelo, prompt):
    """Uma chamada em streaming, cronometrando o primeiro token."""
    inicio = time.perf_counter()
    ttft = None
    pedacos = []
    uso = None

    fluxo = client.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=MAX_TOKENS,
        stream=True,
        stream_options={"include_usage": True},
    )
    for evento in fluxo:
        if getattr(evento, "usage", None):
            uso = evento.usage           # o provedor manda no último evento
        if evento.choices and evento.choices[0].delta.content:
            if ttft is None:
                ttft = time.perf_counter() - inicio
            pedacos.append(evento.choices[0].delta.content)

    total = time.perf_counter() - inicio
    texto = "".join(pedacos)

    if uso is None:
        # Alguns provedores não devolvem uso no streaming. Aviso em vez de chutar.
        entrada, saida = None, None
    else:
        entrada, saida = uso.prompt_tokens, uso.completion_tokens

    return {
        "texto": texto,
        "ttft": ttft or total,
        "total": total,
        "entrada": entrada,
        "saida": saida,
    }


def custo(modelo, entrada, saida):
    preco = PRECOS.get(modelo) or {}
    if not preco.get("entrada") or not preco.get("saida") or entrada is None:
        return None
    return (entrada * preco["entrada"] + saida * preco["saida"]) / 1_000_000


linhas = []
print(f"{'modelo':<24} {'tarefa':<11} {'TTFT':>7} {'total':>7} "
      f"{'tok/s':>7} {'in':>5} {'out':>5} {'US$':>10}")
print("-" * 84)

for modelo in MODELOS:
    for nome_tarefa, prompt in TAREFAS:
        try:
            m = medir(modelo, prompt)
        except Exception as erro:                  # noqa: BLE001 — didático
            print(f"{modelo:<24} {nome_tarefa:<11} falhou: "
                  f"{type(erro).__name__}: {str(erro)[:40]}")
            time.sleep(PAUSA)
            continue

        tps = (m["saida"] / m["total"]) if m["saida"] else 0
        preco = custo(modelo, m["entrada"], m["saida"])

        print(f"{modelo:<24} {nome_tarefa:<11} {m['ttft']:>6.2f}s {m['total']:>6.2f}s "
              f"{tps:>7.1f} {str(m['entrada'] or '-'):>5} {str(m['saida'] or '-'):>5} "
              f"{(f'{preco:.6f}' if preco else '-'):>10}")

        linhas.append({
            "modelo": modelo,
            "tarefa": nome_tarefa,
            "ttft_s": round(m["ttft"], 3),
            "total_s": round(m["total"], 3),
            "tokens_s": round(tps, 1),
            "tokens_entrada": m["entrada"],
            "tokens_saida": m["saida"],
            "custo_usd": f"{preco:.8f}" if preco else "",
            "resposta": m["texto"].replace("\n", " "),
        })
        time.sleep(PAUSA)

if linhas:
    caminho = os.path.join(os.path.dirname(__file__), "benchmark.csv")
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"\nCSV salvo em {caminho}")

print(
    "\nComo LER esta tabela (esta é a parte que vale a nota):\n"
    "  1. Velocidade e custo estão medidos. QUALIDADE não — leia as respostas\n"
    "     do CSV e julgue. Uma medição sem julgamento não decide nada.\n"
    "  2. Pergunte por tarefa, não em geral: o modelo pequeno pode empatar no\n"
    "     resumo e perder feio no raciocínio. É aí que nasce o roteamento.\n"
    "  3. Uma medição por tarefa tem ruído (fila do provedor, rede). Para\n"
    "     decidir de verdade, repita N vezes e olhe a mediana.\n"
    "  4. Multiplique o custo pelo volume real (10 mil chamadas/dia?) antes\n"
    "     de dizer que 'a diferença é pequena'."
)
