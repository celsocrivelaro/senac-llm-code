# https://cohorte.co/blog/using-ollama-with-python-step-by-step-guide

import ollama

# Usa a função generate para um prompt único
result = ollama.generate(model='qwen2.5:0.5b', prompt='Por que o céu é azul?')
print(result['response'])