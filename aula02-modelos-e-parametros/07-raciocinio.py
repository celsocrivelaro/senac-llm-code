# Aula 02 — Escolha e configuração de modelos
# 07 — Modelos de raciocínio: o preço de "pensar antes de responder".
#
# Um modelo de raciocínio (reasoning) gera, antes da resposta, uma cadeia de
# pensamento. Esses tokens de raciocínio:
#   - são COBRADOS como tokens de saída;
#   - aumentam a latência (e o TTFT útil, porque o usuário espera o pensamento
#     terminar antes de ver a resposta);
#   - melhoram tarefas de várias etapas — e não melhoram quase nada em tarefas
#     simples, onde só encarecem.
#
# É a mesma ideia de "test-time compute": em vez de um modelo maior, gastar
# mais computação NA HORA da inferência. Volta na aula de agentes, quando o
# planejamento do agente passa a ser a parte cara.

import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Confirme os nomes com 00-catalogo-modelos.py e ajuste se necessário.
MODELO_INSTRUCT = "mistral-small-latest"
MODELO_RACIOCINIO = "magistral-small-latest"

TAREFAS = [
    ("simples", "Qual é a capital da França? Responda apenas o nome."),
    ("multi-etapa",
     "Uma loja vende canetas em caixas de 12 por R$ 30 a caixa e avulsas por "
     "R$ 3,50. Preciso de 100 canetas gastando o mínimo possível. Quantas "
     "caixas e quantas avulsas devo comprar, e qual o total?"),
]

MAX_TOKENS = 1500


def medir(modelo, prompt):
    inicio = time.perf_counter()
    resposta = client.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=MAX_TOKENS,
    )
    duracao = time.perf_counter() - inicio
    mensagem = resposta.choices[0].message

    # Alguns provedores separam o raciocínio num campo próprio; outros o
    # devolvem embutido no conteúdo, entre marcadores. Tratamos os dois casos.
    extras = mensagem.model_extra or {}
    raciocinio = extras.get("reasoning_content") or extras.get("thinking") or ""

    return {
        "conteudo": (mensagem.content or "").strip(),
        "raciocinio": raciocinio if isinstance(raciocinio, str) else str(raciocinio),
        "duracao": duracao,
        "entrada": resposta.usage.prompt_tokens,
        "saida": resposta.usage.completion_tokens,
        "motivo": resposta.choices[0].finish_reason,
    }


for nome_tarefa, prompt in TAREFAS:
    print("=" * 78)
    print(f"TAREFA: {nome_tarefa} — {prompt}")
    print("=" * 78)

    for modelo in [MODELO_INSTRUCT, MODELO_RACIOCINIO]:
        try:
            m = medir(modelo, prompt)
        except Exception as erro:                  # noqa: BLE001 — didático
            print(f"\n--- {modelo}: falhou ({type(erro).__name__}: {erro})")
            continue

        print(f"\n--- {modelo}")
        print(f"    tempo: {m['duracao']:.2f}s | tokens de saída: {m['saida']} "
              f"| finish_reason: {m['motivo']}")
        if m["raciocinio"]:
            print(f"    raciocínio ({len(m['raciocinio'])} caracteres), início:")
            print(f"      {m['raciocinio'][:300]}...")
        print(f"    resposta: {m['conteudo'][:400]}")
    print()

print(
    "O que observar:\n"
    "  - Na tarefa SIMPLES o modelo de raciocínio gasta mais tokens e mais\n"
    "    tempo para chegar na mesma resposta de uma palavra. É desperdício.\n"
    "  - Na tarefa MULTI-ETAPA compare a CORREÇÃO, não a velocidade — é aqui\n"
    "    que o custo extra se paga (ou não).\n"
    "  - Cuidado com max_tokens: se o orçamento acabar no meio do raciocínio,\n"
    "    você paga tudo e não recebe resposta nenhuma. Veja o finish_reason.\n"
    "  - Regra prática: raciocínio para decidir, instruct para redigir."
)
