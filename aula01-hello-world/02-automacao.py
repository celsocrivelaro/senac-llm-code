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

# Exemplo: resumir um parágrafo de texto
text = """
OpenAI has introduced a new tool called Ollama that lets users run large language models on local machines.
This approach emphasizes privacy and control, as data does not leave the user's environment.
Developers can leverage various open-source models through a simple interface, improving efficiency and reducing costs.
"""
prompt = f"Resuma o texto em uma sentença :\n\"\"\"\n{text}\n\"\"\""

response = client.chat.completions.create(
    model=MODELO,
    messages=[
        {"role": "user", "content": prompt},
    ],
)
print("Resumo:", response.choices[0].message.content)
