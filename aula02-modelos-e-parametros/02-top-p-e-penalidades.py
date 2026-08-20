# Aula 02 — Escolha e configuração de modelos
# 02 — top_p e as penalidades: os outros botões da amostragem.
#
# top_p (nucleus sampling): mantém os tokens mais prováveis até somarem p da
#   massa e descarta a cauda. O corte se ADAPTA à confiança do modelo.
# frequency_penalty: desconta o logit de um token proporcionalmente a quantas
#   vezes ele já apareceu  -> combate repetição literal.
# presence_penalty: desconta uma vez, se o token já apareceu
#   -> empurra para assuntos novos.
#
# Nota sobre top_k: ele existe nos runtimes locais (Ollama, vLLM), mas a API
# no formato chat/completions da Mistral não o expõe. Isso é a lição do dia:
# PARÂMETRO É CONTRATO DE API. O que o provedor não aceita, ele ignora — às
# vezes em silêncio. Sempre confira na documentação do provedor.

import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MODELO = "mistral-small-latest"
PROMPT = "Liste ideias de nomes para uma cafeteria. Escreva um parágrafo corrido."
PAUSA = 0.5


def gerar(**parametros):
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=120,
        **parametros,
    )
    return resposta.choices[0].message.content.strip()


def repeticao_trigramas(texto):
    """Fração de trigramas de palavras que já tinham aparecido antes."""
    palavras = texto.lower().split()
    trigramas = [tuple(palavras[i:i + 3]) for i in range(len(palavras) - 2)]
    if not trigramas:
        return 0.0
    return 1 - len(set(trigramas)) / len(trigramas)


print(f"modelo: {MODELO}\nprompt: {PROMPT!r}\n")

print("### Parte 1 — varrendo top_p (temperature fixa em 1.0)")
print("A recomendação é ajustar UM dos dois. Aqui mexemos só no top_p.\n")
for top_p in [0.1, 0.5, 0.9, 1.0]:
    texto = gerar(temperature=1.0, top_p=top_p)
    print(f"--- top_p={top_p} | repetição de trigramas: {repeticao_trigramas(texto):.2f}")
    print(f"    {texto}\n")
    time.sleep(PAUSA)

print("### Parte 2 — penalidades (temperature 0.7, top_p padrão)")
print("Valores aceitos: -2.0 a 2.0. Positivo desencoraja; negativo encoraja.\n")
for rotulo, parametros in [
    ("sem penalidade    ", {}),
    ("frequency = 1.5   ", {"frequency_penalty": 1.5}),
    ("presence  = 1.5   ", {"presence_penalty": 1.5}),
    ("frequency = -1.5  ", {"frequency_penalty": -1.5}),
]:
    texto = gerar(temperature=0.7, **parametros)
    print(f"--- {rotulo} | repetição de trigramas: {repeticao_trigramas(texto):.2f}")
    print(f"    {texto}\n")
    time.sleep(PAUSA)

print(
    "O que observar:\n"
    "  - top_p=0.1 corta quase tudo: o texto fica seguro e sem graça.\n"
    "  - A penalidade negativa é o experimento mais revelador: force o\n"
    "    modelo a repetir e veja o texto degringolar.\n"
    "  - Na prática, penalidade raramente é a resposta certa. Se o texto\n"
    "    repete, quase sempre o problema está no PROMPT, não no botão."
)
