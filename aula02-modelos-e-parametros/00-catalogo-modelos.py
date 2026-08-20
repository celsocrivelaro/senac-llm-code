# Aula 02 — Escolha e configuração de modelos
# 00 — Catálogo: quais modelos a API oferece e o que cada um declara.
#
# Lição: não decore nomes de modelo. Eles nascem, mudam de preço e são
# descontinuados. Pergunte ao provedor.
#
# Documentação: https://docs.mistral.ai/api/#tag/models

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("OPENAI_API_KEY"),
)

resposta = client.models.list()

print(f"{len(resposta.data)} modelos disponíveis para esta chave\n")
print(f"{'modelo':<34} {'contexto':>10}  capacidades")
print("-" * 78)

for modelo in sorted(resposta.data, key=lambda m: m.id):
    # O SDK da OpenAI guarda em `model_extra` os campos que são específicos
    # do provedor — a Mistral devolve contexto e capacidades por aqui.
    extras = modelo.model_extra or {}

    contexto = extras.get("max_context_length")
    contexto = f"{contexto:,}".replace(",", ".") if contexto else "?"

    capacidades = extras.get("capabilities") or {}
    if isinstance(capacidades, dict):
        ativas = ", ".join(nome for nome, ligada in capacidades.items() if ligada) or "-"
    else:
        ativas = str(capacidades)

    print(f"{modelo.id:<34} {contexto:>10}  {ativas}")

print(
    "\nRepare em três coisas:\n"
    "  1. Os aliases terminados em '-latest' apontam para uma versão que MUDA.\n"
    "     Em produção, fixe a versão datada; em aula, o alias é conveniente.\n"
    "  2. 'function_calling' é a capacidade que a aula 03 vai usar. Nem todo\n"
    "     modelo tem.\n"
    "  3. O tamanho do contexto é o limite de ENTRADA + SAÍDA somadas."
)
