# Agente que pesquisa pokemons na PokeAPI
# Documentação: https://pokeapi.co/docs/v2#pokemon

import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import requests

# Carrega as variáveis do arquivo .env
load_dotenv()

# Initialize the client targeting Mistral's API endpoint
client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("OPENAI_API_KEY")
)

POKEAPI = "https://pokeapi.co/api/v2/pokemon/"


# --- Ferramentas: funções Python que o modelo pode chamar ---

def listar_pokemons(offset=0, limit=20):
    """Lista uma página de nomes de pokemons, para o agente navegar até achar."""
    r = requests.get(POKEAPI, params={"offset": offset, "limit": limit}, timeout=10)
    r.raise_for_status()
    dados = r.json()
    return {
        "total": dados["count"],
        "offset": offset,
        "nomes": [p["name"] for p in dados["results"]],
    }


def detalhar_pokemon(nome):
    """Busca os dados de um pokemon pelo nome ou pelo id."""
    r = requests.get(f"{POKEAPI}{str(nome).strip().lower()}", timeout=10)
    if r.status_code == 404:
        return {"erro": f"Pokemon '{nome}' não encontrado. Use listar_pokemons para descobrir o nome correto."}
    r.raise_for_status()
    dados = r.json()
    return {
        "id": dados["id"],
        "nome": dados["name"],
        "peso_kg": dados["weight"] / 10,  # a API devolve o peso em hectogramas
        "habilidades": [h["ability"]["name"] for h in dados["abilities"]],
    }


# Mapeia o nome que o modelo usa para a função Python de verdade
FERRAMENTAS = {
    "listar_pokemons": listar_pokemons,
    "detalhar_pokemon": detalhar_pokemon,
}

# Descrição das ferramentas enviada ao modelo (é assim que ele sabe o que pode chamar)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "listar_pokemons",
            "description": "Lista os nomes dos pokemons em páginas. Use para procurar quando não souber o nome exato.",
            "parameters": {
                "type": "object",
                "properties": {
                    "offset": {"type": "integer", "description": "A partir de qual posição começar (0 é o início)"},
                    "limit": {"type": "integer", "description": "Quantos nomes trazer por página (máximo 100)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detalhar_pokemon",
            "description": "Retorna id, nome, peso em kg e habilidades de um pokemon.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome em inglês e minúsculas, ou o id numérico"},
                },
                "required": ["nome"],
            },
        },
    },
]

messages = [
    {
        "role": "system",
        "content": (
            "Você é um assistente de pesquisas sobre pokemons. "
            "Use as ferramentas disponíveis para buscar os dados na PokeAPI — nunca invente informação. "
            "Os nomes na API são em inglês e minúsculas: se a busca falhar, tente traduzir o nome "
            "ou navegue pela listagem com listar_pokemons até encontrar. "
            "No final, responda em português com: id, nome, peso e a lista de habilidades."
        ),
    },
]

# Pergunta ao usuário qual pokemon pesquisar
pergunta = input("Qual pokemon você quer pesquisar? ")
messages.append({"role": "user", "content": pergunta})

# Loop do agente: o modelo pede ferramentas, executamos e devolvemos o resultado,
# até ele ter dados suficientes para responder. O limite de passos evita loop infinito.
for passo in range(8):
    response = client.chat.completions.create(
        model="mistral-small-latest",
        messages=messages,
        tools=TOOLS,
    )
    resposta = response.choices[0].message
    messages.append(resposta)

    # Sem pedido de ferramenta = é a resposta final
    if not resposta.tool_calls:
        print()
        print(resposta.content)
        break

    for chamada in resposta.tool_calls:
        argumentos = json.loads(chamada.function.arguments or "{}")
        print(f"[ferramenta] {chamada.function.name}({argumentos})")

        resultado = FERRAMENTAS[chamada.function.name](**argumentos)

        # Devolve o resultado para o modelo, amarrado ao id da chamada
        messages.append({
            "role": "tool",
            "tool_call_id": chamada.id,
            "content": json.dumps(resultado, ensure_ascii=False),
        })
else:
    print("Não consegui concluir a pesquisa em 8 passos.")
