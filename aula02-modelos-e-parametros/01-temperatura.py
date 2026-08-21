# Aula 02 — Escolha e configuração de modelos
# 01 — Temperatura: a mesma pergunta, várias temperaturas, várias amostras.
#
# Na aula 01 vimos a fórmula:  P(token_i) = e^(z_i/T) / Σ e^(z_j/T)
# T < 1 deixa a distribuição pontuda (previsível); T > 1 achata (variado).
# Aqui medimos o efeito no texto de verdade, não na tabela de logits.
#
# Documentação: https://docs.mistral.ai/api/

import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")
PROMPT = "Em uma única frase, descreva um café da manhã."

TEMPERATURAS = [0.0, 0.3, 0.7, 1.0, 1.5]
AMOSTRAS = 4          # quantas vezes repetimos a MESMA pergunta em cada T
PAUSA = 0.5           # segundos entre chamadas, para não tomar 429


def gerar(temperatura):
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": PROMPT}],
        temperature=temperatura,
        max_tokens=60,
    )
    return resposta.choices[0].message.content.strip()


def diversidade_lexical(textos):
    """Razão tipo/token: palavras distintas ÷ palavras totais no conjunto."""
    palavras = [p.lower() for t in textos for p in t.split()]
    return len(set(palavras)) / len(palavras) if palavras else 0.0


print(f"modelo: {MODELO}")
print(f"prompt: {PROMPT!r}")
print(f"{AMOSTRAS} amostras por temperatura\n")

resumo = []

for temperatura in TEMPERATURAS:
    print(f"=== temperature = {temperatura} " + "=" * 40)
    textos = []
    for i in range(AMOSTRAS):
        texto = gerar(temperatura)
        textos.append(texto)
        print(f"  [{i + 1}] {texto}")
        time.sleep(PAUSA)

    distintas = len(set(textos))
    ttr = diversidade_lexical(textos)
    resumo.append((temperatura, distintas, ttr))
    print(f"  -> respostas distintas: {distintas}/{AMOSTRAS} | "
          f"diversidade lexical: {ttr:.2f}\n")

print("=" * 60)
print(f"{'T':>5}  {'distintas':>10}  {'divers.lexical':>15}")
for temperatura, distintas, ttr in resumo:
    print(f"{temperatura:5.1f}  {distintas:>7}/{AMOSTRAS}  {ttr:>15.2f}")

print(
    "\nO que observar:\n"
    "  - Em T=0 as respostas tendem a ser iguais entre si — mas 'tendem'\n"
    "    não é 'garantido' (veja 04-determinismo.py).\n"
    "  - A diversidade sobe com T. A UTILIDADE não: em algum ponto entre\n"
    "    1.0 e 1.5 a frase começa a ficar estranha. Ache esse ponto.\n"
    "  - Variação é qualidade em texto criativo e é DEFEITO em extração\n"
    "    de dados. O parâmetro não é bom nem ruim: depende da tarefa."
)
