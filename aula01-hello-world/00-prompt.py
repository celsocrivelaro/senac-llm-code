# Documentação: https://docs.mistral.ai

import os
from dotenv import load_dotenv
from openai import OpenAI

# Carrega as variáveis do arquivo .env
load_dotenv()

# Initialize the client targeting Mistral's API endpoint
client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Envia um prompt único e imprime a resposta
response = client.chat.completions.create(
    model="mistral-small-latest",
    messages=[
        {"role": "user", "content": "Por que o céu é azul?"},
    ],
)
print(response.choices[0].message.content)