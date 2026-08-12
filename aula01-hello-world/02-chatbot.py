import ollama

# Choose a chat-capable model (ensured it is pulled)
model_name = 'qwen2.5:0.5b'

# Initialize conversation with a system prompt (optional) and a user message
messages = [
    {"role": "system", "content": "Você é um assistence conversacional"},
    {"role": "user", "content": "Olá!"},
]

# First response from the bot
response = ollama.chat(model=model_name, messages=messages)
print("Bot:", response.message.content)

# Continue the conversation:
while True:
    user_input = input("You: ")
    if not user_input:
        break  # exit loop on empty input
    messages.append({"role": "user", "content": user_input})
    response = ollama.chat(model=model_name, messages=messages)
    answer = response.message.content
    print("Bot:", answer)
    messages.append({"role": "assistant", "content": answer})