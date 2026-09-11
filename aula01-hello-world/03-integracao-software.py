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
messages = [
    {"role": "system", "content": "Você é um assistente de cadastro de pessoas em um sistema. Seja amigável nos seus pedidos"},
    {"role": "system", "content": "Peça os dados de cadastro: Nome completo, CPF e data de nascimento." },
]

# Primeira resposta do bot
response = client.chat.completions.create(model=MODELO, messages=messages)
print("Bot:", response.choices[0].message.content)

# Continua a conversa:
user_input = input("Usuário: ")
if user_input:
  messages.append({"role": "user", "content": user_input})
  instrucoes = """Com o input do usuário, retorne os dados no formato json:
{
  "nome": "<Nome da pessoa>",
  "cpf": "<cpf no formato 000.000.000-00>",
  "nascimento": "<nascimento no formato iso8601 yyyy-mm-dd>"
}
  """
  messages.append({"role": "system", "content": instrucoes})

  response = client.chat.completions.create(model=MODELO, messages=messages)
  answer = response.choices[0].message.content
  print("Json de saída:")
  print(answer)
