import ollama

# Choose a chat-capable model (ensured it is pulled)
model_name = 'qwen2.5:0.5b'

# Initialize conversation with a system prompt (optional) and a user message
messages = [
    {"role": "system", "content": "Você é um assistente de cadastro de pessoas em um sistema. Seja amigável nos seus pedidos"},
    {"role": "system", "content": "Peça os dados de cadastro: Nome completo, CPF e data de nascimento." },
]

# First response from the bot
response = ollama.chat(model=model_name, messages=messages)
print("Bot:", response.message.content)

# Continue the conversation:
user_input = input("Usuário: ")
if user_input:
  messages.append({"role": "user", "content": user_input})
  instrucoes = """Com o input do usuário, retorne os dados no formato json:
{
  "nome": "<Nome da pessoa>"
  "cpf": "<cpf no formato 000.000.000-00>"
  "nascimento": "<nascimento no formato iso8601 yyyy-mm-dd>"
}
  """
  messages.append({"role": "system", "content": instrucoes})

  response = ollama.chat(model=model_name, messages=messages)
  answer = response.message.content
  print("Json de saída:")
  print(answer)