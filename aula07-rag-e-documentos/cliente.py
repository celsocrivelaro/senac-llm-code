# Aula 07 — O cliente da API.
#
# Um único cliente atende às duas modalidades usadas nesta aula. O endpoint é
# o mesmo desde a aula 01; o que difere entre as modalidades é o modelo — um
# gera texto, o outro devolve vetor.
#
# O cliente ocupa um módulo próprio porque `embedding.py` e `geracao.py`
# dependem dele e não dependem um do outro. Na aula 06 o cliente residia
# dentro de `embedding.py`, que era o único ponto de acesso à API; nesta aula
# há dois pontos de acesso, o que exige extrair a dependência comum.

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
