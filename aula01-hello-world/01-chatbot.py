import ollama

# Escolhe um modelo com suporte a chat (garanta que já foi baixado)
model_name = 'qwen2.5:0.5b'

# Inicia a conversa com um prompt de sistema (opcional) e uma mensagem do usuário
# system - instruções de como o sistema deve se comportar
# user - input do usuário
# assistant - resposta do modelo
messages = [
    {"role": "system", "content": "Você é um assistence conversacional, seja engraçadinho. Faça piadas com a entrada do usuário"},
    {"role": "user", "content": "Olá!"},
]

# Primeira resposta do bot
response = ollama.chat(model=model_name, messages=messages)
print("Bot:", response.message.content)

# Continua a conversa:
while True:
    user_input = input("Usuário: ")
    if not user_input:
        break  # sai do loop quando a entrada é vazia
    # pode adicionar mais mensagens como contexto
    messages.append({"role": "user", "content": user_input})
    response = ollama.chat(model=model_name, messages=messages)
    answer = response.message.content
    print("Bot:", answer)
    messages.append({"role": "assistant", "content": answer})