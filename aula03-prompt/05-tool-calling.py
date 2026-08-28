# Aula 03 — Prompt engineering
# 05 — Tool calling: o laço completo, em quatro tempos.
#
#   1. VOCÊ declara as ferramentas na chamada
#   2. O MODELO decide  -> finish_reason="tool_calls" + nome e argumentos
#   3. O SEU CÓDIGO executa a função Python
#   4. VOCÊ devolve o resultado como mensagem role="tool" e chama de novo
#
# O modelo NUNCA executa nada. Ele nem sabe que as suas funções existem como
# código — só viu a descrição delas. Toda a segurança mora nessa separação.
#
# Este é o mesmo mecanismo da saída estruturada da aula 02 (nota 02, §7):
# o campo `parameters` de cada ferramenta É um JSON Schema.
#
# Documentação: https://docs.mistral.ai/capabilities/function_calling/

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
MAX_PASSOS = 6

# --------------------------------------------------------------- o "banco"
BANCO = {
    "48219": {"situacao": "em transporte", "previsao": "2026-09-02",
              "transportadora": "RápidoLog"},
    "77310": {"situacao": "entregue", "previsao": "2026-08-19",
              "transportadora": "RápidoLog"},
    "90455": {"situacao": "aguardando coleta", "previsao": "2026-09-05",
              "transportadora": "TransBrasil"},
}


# ---------------------------------------------------------- as ferramentas
def consultar_pedido(numero: str) -> dict:
    """A função Python de verdade. O modelo nunca a executa."""
    pedido = BANCO.get(numero)
    if pedido is None:
        # ERRO SE DEVOLVE, NÃO SE LEVANTA. Uma exceção mata o laço; um erro
        # no contexto o modelo LÊ e se recupera sozinho (nota 04, §7).
        # E a mensagem é escrita para ser lida — diz o que fazer a seguir.
        return {"erro": f"pedido {numero} não encontrado",
                "dica": "confirme o número com o cliente; são 5 dígitos"}
    return {"numero": numero, **pedido}


def calcular_prazo(data_prevista: str, hoje: str) -> dict:
    """Dias entre hoje e a previsão. Aritmética é trabalho de código."""
    from datetime import date
    try:
        d1 = date.fromisoformat(hoje)
        d2 = date.fromisoformat(data_prevista)
    except ValueError as erro:
        return {"erro": f"data inválida: {erro}"}
    return {"dias": (d2 - d1).days}


FERRAMENTAS = {
    "consultar_pedido": consultar_pedido,
    "calcular_prazo": calcular_prazo,
}

# A DESCRIÇÃO É PROMPT (nota 04, §4). É o único texto que o modelo lê para
# decidir se e quando chamar. Diga o que faz, QUANDO USAR e QUANDO NÃO USAR.
DECLARACOES = [
    {
        "type": "function",
        "function": {
            "name": "consultar_pedido",
            "description": (
                "Consulta a situação atual, a previsão de entrega e a "
                "transportadora de um pedido. Use quando o cliente citar um "
                "número de pedido e a resposta depender do status real. "
                "Não use para dúvidas gerais sobre prazos ou políticas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "numero": {
                        "type": "string",
                        "pattern": "^[0-9]+$",
                        "description": "Número do pedido, somente dígitos.",
                    },
                },
                "required": ["numero"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_prazo",
            "description": (
                "Calcula quantos dias faltam entre duas datas. Use para "
                "informar ao cliente quantos dias faltam para a entrega, "
                "em vez de calcular de cabeça."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "data_prevista": {"type": "string",
                                      "description": "Data no formato AAAA-MM-DD."},
                    "hoje": {"type": "string",
                             "description": "Data de hoje, AAAA-MM-DD."},
                },
                "required": ["data_prevista", "hoje"],
                "additionalProperties": False,
            },
        },
    },
]

SYSTEM = (
    "Você é o assistente de atendimento de uma transportadora.\n"
    "Use as ferramentas disponíveis sempre que precisar de dados reais — "
    "nunca invente número de pedido, situação ou data.\n"
    "Se faltar informação para usar uma ferramenta, pergunte ao cliente.\n"
    "Responda em português, de forma breve e cordial."
)


def executar(chamada):
    """Passo 3: o SEU código executa."""
    nome = chamada.function.name
    try:
        argumentos = json.loads(chamada.function.arguments)
    except json.JSONDecodeError:
        return {"erro": "argumentos não são JSON válido"}

    print(f"   [ferramenta] {nome}({argumentos})")

    funcao = FERRAMENTAS.get(nome)
    if funcao is None:                       # o modelo inventou o nome
        return {"erro": f"ferramenta desconhecida: {nome}"}
    try:
        return funcao(**argumentos)
    except TypeError as erro:                # argumentos fora do esperado
        return {"erro": f"argumentos inválidos: {erro}"}


def rodar(pergunta, max_passos=MAX_PASSOS):
    mensagens = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": pergunta},
    ]

    for passo in range(1, max_passos + 1):
        resposta = client.chat.completions.create(
            model=MODELO,
            messages=mensagens,
            tools=DECLARACOES,
            temperature=0,      # escolher ferramenta é DECISÃO: variação é defeito
        )
        escolha = resposta.choices[0]
        msg = escolha.message

        print(f"   passo {passo}: finish_reason={escolha.finish_reason} | "
              f"tokens: {resposta.usage.prompt_tokens} entrada, "
              f"{resposta.usage.completion_tokens} saída")

        if not msg.tool_calls:               # respondeu: o laço termina
            return msg.content

        mensagens.append(msg)                # 1x: a fala do assistente
        for chamada in msg.tool_calls:       # 1x por chamada de ferramenta
            resultado = executar(chamada)
            mensagens.append({
                "role": "tool",
                "tool_call_id": chamada.id,  # amarra o resultado à chamada
                "name": chamada.function.name,
                "content": json.dumps(resultado, ensure_ascii=False),
            })

    # Sem teto, um modelo em laço é uma conta aberta rodando sozinha.
    raise RuntimeError(f"não concluiu em {max_passos} passos")


PERGUNTAS = [
    "O pedido 48219 já saiu para entrega? Hoje é 2026-08-27.",
    "e o pedido 99999?",                    # não existe: o modelo se recupera
    "vocês entregam no sábado?",            # não precisa de ferramenta
]

print(f"modelo: {MODELO}\n")

for pergunta in PERGUNTAS:
    print("=" * 70)
    print(f"CLIENTE: {pergunta}\n")
    try:
        print(f"\n   ASSISTENTE: {rodar(pergunta)}\n")
    except Exception as erro:                # noqa: BLE001 — didático
        print(f"\n   FALHOU: {type(erro).__name__}: {erro}\n")
    time.sleep(0.8)

print(
    "=" * 70 + "\n"
    "O que observar:\n"
    "  1. Na primeira pergunta, o modelo chama DUAS ferramentas em sequência:\n"
    "     consulta o pedido e depois calcula o prazo com a data que recebeu.\n"
    "     A segunda decisão depende do resultado da primeira — é o laço.\n"
    "  2. No pedido inexistente, a ferramenta devolve {erro, dica} e o modelo\n"
    "     LÊ isso e pede o número de novo. Se tivesse levantado KeyError, o\n"
    "     programa teria morrido.\n"
    "  3. Na terceira, ele NÃO chama ferramenta nenhuma — porque a descrição\n"
    "     diz 'não use para dúvidas gerais'. Esse 'não use' é um exemplo\n"
    "     negativo (nota 01, §4) aplicado a ferramenta.\n"
    "  4. Olhe os tokens de ENTRADA subindo a cada passo: todo o histórico é\n"
    "     reenviado. É o custo quadrático da trajetória (aula 02, nota 04, §3),\n"
    "     e o motivo de max_passos existir.\n"
    "\n"
    "  O modelo não ficou mais inteligente — ele continua sem saber nada sobre\n"
    "  os seus pedidos. O que mudou é que agora existe um caminho para a\n"
    "  informação chegar, e ele reconheceu que devia usá-lo."
)
