# Aula 06 — O cliente da API.
#
# UM CLIENTE SÓ, para as duas modalidades. O endpoint é o mesmo desde a
# aula 01; o que muda é o modelo — um devolve vetor, o outro gera texto.
#
# Até a parte 3 desta aula só o de embedding é usado: o buscador inteiro se
# constrói sem nenhuma geração. O `geracao.py` só entra na parte 4, quando
# os trechos recuperados precisam virar resposta.

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")
MODELO_EMBEDDING = os.environ.get("LLM_MODELO_EMBEDDING", "mistral-embed")
