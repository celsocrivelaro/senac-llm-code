# Aula 08 — O cliente da API.
#
# Um único cliente atende às duas modalidades. O endpoint é o mesmo desde a
# aula 01; o que difere é o modelo — um gera texto, o outro devolve vetor.
#
# O cliente ocupa um módulo próprio porque `embedding.py` e `escrita.py`
# dependem dele e não dependem um do outro. É o mesmo arranjo da aula 07.

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
