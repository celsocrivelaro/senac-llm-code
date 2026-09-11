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

# Inicia a conversa com um prompt de sistema (opcional) e uma mensagem do usuário
# system - instruções de como o sistema deve se comportar
# user - input do usuário
# assistant - resposta do modelo
messages = [
    {"role": "system", "content": "Você é um assistence conversacional, seja engraçadinho. Faça piadas com a entrada do usuário"},
    {"role": "user", "content": "Olá!"},
]

# Primeira resposta do bot
response = client.chat.completions.create(model=MODELO, messages=messages)
print("Bot:", response.choices[0].message.content)

# Continua a conversa:
while True:
    user_input = input("Usuário: ")
    if not user_input:
        break  # sai do loop quando a entrada é vazia
    # pode adicionar mais mensagens como contexto
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(model=MODELO, messages=messages)
    answer = response.choices[0].message.content
    print("Bot:", answer)
    messages.append({"role": "assistant", "content": answer})
