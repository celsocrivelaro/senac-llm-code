# Documentação: https://docs.mistral.ai

import os
from dotenv import load_dotenv
from openai import OpenAI

# Carrega as variáveis do arquivo .env
load_dotenv()

# O cliente lê as três variáveis do .env, e são as mesmas em todas as
# aulas: a chave, o endereço da API e o nome do modelo. Trocar de
# provedor (Mistral, Ollama, outro) é trocar o .env — não o código.
client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)
MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")

# Envia um prompt único e imprime a resposta
response = client.chat.completions.create(
    model=MODELO,
    messages=[
        {"role": "user", "content": "Por que o céu é azul?"},
    ],
)
print(response.choices[0].message.content)
