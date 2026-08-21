# Aula 02 — Escolha e configuração de modelos
# 05 — Saída estruturada: pedir JSON, exigir JSON e IMPOR um schema.
#
# Três estratégias para a mesma tarefa, medindo taxa de sucesso:
#   A) só prompt          — "responda em JSON" e reze;
#   B) response_format    — {"type": "json_object"}: o provedor garante que a
#                           saída é JSON válido, mas não diz QUAL formato;
#   C) json_schema        — decodificação restrita: a cada passo, só os tokens
#                           que mantêm a saída válida contra o schema podem ser
#                           amostrados. O formato deixa de ser pedido e vira
#                           garantia.
#
# Por que isso importa mais do que parece: TOOL CALLING (aula 03) é este mesmo
# mecanismo. Quando o modelo "chama uma função", ele está gerando um JSON que
# obedece ao schema dos parâmetros dela. Sem saída estruturada confiável, não
# existe agente confiável.

import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")
TENTATIVAS = 6
TEMPERATURA = 0.7      # alta de propósito: queremos ver o formato quebrar
PAUSA = 0.4

TEXTO = (
    "Oi, aqui é a Ana Souza, tenho 34 anos, moro em Campinas-SP e meu "
    "e-mail é ana.souza@exemplo.com. Queria falar sobre a fatura de julho."
)

CAMPOS = ["nome", "idade", "cidade", "email"]

SCHEMA = {
    "type": "object",
    "properties": {
        "nome":   {"type": "string"},
        "idade":  {"type": "integer"},
        "cidade": {"type": "string"},
        "email":  {"type": "string"},
    },
    "required": CAMPOS,
    "additionalProperties": False,
}


def valida(texto):
    """Retorna (ok, motivo). Só é sucesso se for JSON com TODOS os campos."""
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as erro:
        return False, f"JSON inválido ({erro.msg})"
    if not isinstance(dados, dict):
        return False, "não é objeto"
    faltando = [c for c in CAMPOS if c not in dados]
    if faltando:
        return False, f"faltam campos: {', '.join(faltando)}"
    if not isinstance(dados.get("idade"), int):
        return False, "idade não é inteiro"
    return True, "ok"


def tentar(prompt, response_format=None):
    parametros = {"response_format": response_format} if response_format else {}
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMPERATURA,
        max_tokens=200,
        **parametros,
    )
    return resposta.choices[0].message.content.strip()


ESTRATEGIAS = [
    (
        "A) só prompt",
        f"Extraia nome, idade, cidade e email do texto e responda em JSON.\n\n{TEXTO}",
        None,
    ),
    (
        "B) json_object",
        f"Extraia nome, idade, cidade e email do texto.\n\n{TEXTO}",
        {"type": "json_object"},
    ),
    (
        "C) json_schema",
        f"Extraia os dados de cadastro do texto.\n\n{TEXTO}",
        {
            "type": "json_schema",
            "json_schema": {"name": "cadastro", "schema": SCHEMA, "strict": True},
        },
    ),
]

print(f"modelo: {MODELO} | temperature: {TEMPERATURA} | {TENTATIVAS} tentativas\n")

placar = []
for rotulo, prompt, formato in ESTRATEGIAS:
    print(f"### {rotulo}")
    acertos = 0
    for i in range(TENTATIVAS):
        try:
            saida = tentar(prompt, formato)
        except Exception as erro:                  # noqa: BLE001 — didático
            print(f"  [{i + 1}] erro da API: {type(erro).__name__}: {erro}")
            time.sleep(PAUSA)
            continue
        ok, motivo = valida(saida)
        acertos += ok
        primeira_linha = saida.replace("\n", " ")[:70]
        print(f"  [{i + 1}] {'OK  ' if ok else 'FALHA'} {motivo:<28} {primeira_linha}")
        time.sleep(PAUSA)
    placar.append((rotulo, acertos))
    print(f"  -> {acertos}/{TENTATIVAS} válidos\n")

print("=" * 60)
for rotulo, acertos in placar:
    barra = "#" * acertos + "." * (TENTATIVAS - acertos)
    print(f"{rotulo:<16} {barra}  {acertos}/{TENTATIVAS}")

print(
    "\nO que observar:\n"
    "  - A estratégia A costuma falhar por um motivo bobo: o modelo embrulha\n"
    "    o JSON em ```json ... ``` ou escreve 'Claro! Aqui está:' antes.\n"
    "  - B garante JSON, mas não garante os SEUS campos — o modelo pode\n"
    "    inventar a chave 'nome_completo' e o seu código quebra.\n"
    "  - C é a única que garante as duas coisas. Custa um schema a mais.\n"
    "  - Nada disso garante que o CONTEÚDO está certo. Formato válido com\n"
    "    dado errado é o erro mais perigoso: passa por todas as validações."
)
