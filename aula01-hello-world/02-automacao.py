import os
from dotenv import load_dotenv
from openai import OpenAI

# Carrega as variáveis do arquivo .env
load_dotenv()

# Initialize the client targeting Mistral's API endpoint
client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("MISTRAL_API_KEY")
)

# Exemplo: resumir um parágrafo de texto
text = """
OpenAI has introduced a new tool called Ollama that lets users run large language models on local machines.
This approach emphasizes privacy and control, as data does not leave the user's environment.
Developers can leverage various open-source models through a simple interface, improving efficiency and reducing costs.
"""
prompt = f"Resuma o texto em uma sentença :\n\"\"\"\n{text}\n\"\"\""

response = client.chat.completions.create(
    model="mistral-small-latest",
    messages=[
        {"role": "user", "content": prompt},
    ],
)
print("Resumo:", response.choices[0].message.content)
