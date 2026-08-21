# Aula 02 — Escolha e configuração de modelos
# 04 — temperature=0 não é garantia de determinismo.
#
# A aula 01 (nota 02, §3.4) afirmou isso. Aqui a gente MEDE.
#
# Por que varia mesmo com T=0:
#   - o provedor agrupa requisições em lotes de tamanho variável, e soma de
#     ponto flutuante não é associativa: a ordem das operações muda o último
#     dígito, que às vezes muda o argmax;
#   - modelos mixture-of-experts roteiam tokens de forma sensível ao lote;
#   - o alias '-latest' pode apontar para outro modelo de um dia para o outro.
#
# Consequência de engenharia: NÃO escreva teste que exija string idêntica da
# saída de um LLM. Teste propriedades. Isso volta na aula de evals.

import os
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
PROMPT = "Cite três causas da Revolução Industrial. Seja breve."
REPETICOES = 5
PAUSA = 0.4


def rodar(usar_semente):
    saidas = []
    for _ in range(REPETICOES):
        extras = {}
        if usar_semente:
            # ATENÇÃO: o nome do parâmetro muda por provedor.
            # OpenAI usa "seed"; a Mistral usa "random_seed". O SDK da OpenAI
            # não conhece "random_seed", então mandamos pelo extra_body —
            # que é o escape hatch para campos específicos do provedor.
            extras["extra_body"] = {"random_seed": 42}
        resposta = client.chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": PROMPT}],
            temperature=0,
            max_tokens=150,
            **extras,
        )
        saidas.append(resposta.choices[0].message.content.strip())
        time.sleep(PAUSA)
    return saidas


for rotulo, usar_semente in [("temperature=0", False),
                             ("temperature=0 + random_seed=42", True)]:
    print(f"### {rotulo} — {REPETICOES} chamadas idênticas")
    try:
        saidas = rodar(usar_semente)
        print("-------- Saídas --------")
        for saida in saidas:
            print(saida)
            print("-------------------------")
        print("-------------------------")
    except Exception as erro:                      # noqa: BLE001 — didático
        print(f"  falhou: {type(erro).__name__}: {erro}\n")
        continue

    contagem = Counter(saidas)
    mais_comum, frequencia = contagem.most_common(1)[0]
    print(f"  saídas distintas: {len(contagem)}/{REPETICOES}")
    print(f"  a mais frequente apareceu {frequencia}x")
    if len(contagem) > 1:
        print("  -> confirmado: MESMA entrada, saídas diferentes.")
    else:
        print("  -> todas iguais NESTA execução. Rode de novo mais tarde:")
        print("     estabilidade num momento não é garantia contratual.")
    print()

print(
    "Como testar um LLM, então? Por propriedade, não por igualdade:\n"
    "  ruim : assert resposta == 'texto exato esperado'\n"
    "  bom  : assert json.loads(resposta)['cpf'] casa com a regex\n"
    "  bom  : assert todas as 3 causas citadas estão na lista de aceitas\n"
    "  bom  : assert len(resposta) < 500 and 'desculpe' not in resposta.lower()"
)
