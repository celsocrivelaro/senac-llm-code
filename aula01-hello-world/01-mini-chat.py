from ollama import chat

conversation = [
    {"role": "user", "content": "Olá, como está?"}
]
reply = chat(model='qwen2.5:0.5b', messages=conversation)

print(reply.message.content)
