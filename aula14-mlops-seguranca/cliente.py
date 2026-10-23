# Aula 14 — O cliente do modelo — e o único arquivo do laboratório que
# sabe qual provedor está em uso.
#
# `LLM_PROVEDOR`, no .env, decide qual integração nativa do LangChain é
# construída. As três devolvem a mesma interface de chat model, então tudo o
# que vem depois — `create_agent`, as ferramentas, o grafo — é idêntico nos
# três caminhos.
#
#   mistral — API, paga por token, o padrão da disciplina
#   ollama  — modelo local, de graça e lento
#   groq    — API, muito rápida, com cota gratuita generosa
#
# É o mesmo arranjo de `cliente.py` nas Aulas 06, 07 e 08: um módulo só para
# resolver a configuração, para que nenhum script precise repetir isso.
#
# A temperatura é zero nos três: o laboratório compara a mesma pergunta sem e
# com o ataque, e a diferença precisa vir do ataque, não da amostragem.
#
# Depois do modelo vêm os dados fictícios do laboratório e as três ferramentas
# de consulta que os leem. Os scripts importam daqui; o que é assunto da aula
# (o ataque, a ferramenta de envio, as defesas) fica no próprio script.

import json
import os

from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

PROVEDOR = os.environ.get("LLM_PROVEDOR", "mistral").strip().lower()

if PROVEDOR == "mistral":
    from langchain_mistralai.chat_models import ChatMistralAI

    MODELO = os.environ.get("MISTRAL_MODELO", "mistral-small-latest")
    modelo = ChatMistralAI(
        model=MODELO,
        api_key=os.environ.get("MISTRAL_API_KEY"),
        temperature=0,
    )

elif PROVEDOR == "ollama":
    from langchain_ollama import ChatOllama

    MODELO = os.environ.get("OLLAMA_MODELO", "gpt-oss:20b")
    # `validate_model_on_init` falha aqui, com mensagem clara, se a tag não
    # estiver baixada — em vez de dar erro no meio da conversa.
    modelo = ChatOllama(
        model=MODELO,
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        validate_model_on_init=True,
        temperature=0,
    )

elif PROVEDOR == "groq":
    from langchain_groq import ChatGroq

    MODELO = os.environ.get("GROQ_MODELO", "llama-3.3-70b-versatile")
    # ARMADILHA, espelhada à do Ollama: o `ChatGroq` fala a API nativa e
    # acrescenta `/openai/v1` sozinho. Se o .env trouxer a URL do endpoint
    # compatível com a OpenAI — que é a que a Groq documenta —, o sufixo
    # dobra e vira 404. Por isso tiramos.
    endereco = (os.environ.get("GROQ_BASE_URL") or "").removesuffix("/openai/v1")
    modelo = ChatGroq(
        model=MODELO,
        api_key=os.environ.get("GROQ_API_KEY"),
        base_url=endereco or None,
        temperature=0,
    )

else:
    raise ValueError(f"LLM_PROVEDOR inválido no .env: {PROVEDOR!r}. Use 'mistral', 'ollama' ou 'groq'.")


# ============================================================================
# DADOS DO LABORATÓRIO
# ============================================================================
# --------------------------------------------------- dados "privados"
# A primeira perna da trifecta. Nada aqui é real.
DADOS_PRIVADOS = {
    "F-088": {"nome": "[funcionário 088]", "cpf": "000.000.000-00",
              "salario": 9800.00, "conta": "00000-0"},
    "orcamento_2026": {"total": 1_450_000.00, "comprometido": 903_400.00},
}

DESPESAS = {
    "D-4612": {"categoria": "refeicao", "valor": 138.00,
               "funcionario": "F-088", "cidade": "Sao Paulo"},
    "D-4613": {"categoria": "hospedagem", "valor": 590.00,
               "funcionario": "F-102", "cidade": "Lisboa"},
}

POLITICA = {"refeicao": 120.00, "transporte": 250.00,
            "hospedagem": 480.00, "outros": 90.00}


# ============================================================================
# FERRAMENTAS DE CONSULTA DO AGENTE
# ============================================================================
@tool
def consultar_politica(categoria: str) -> str:
    """Teto de reembolso de uma categoria.

    Args:
        categoria: A categoria da despesa
    """
    if categoria not in POLITICA:
        return json.dumps({"erro": "categoria desconhecida"})
    return json.dumps({"categoria": categoria, "teto": POLITICA[categoria]})


@tool
def consultar_despesa(despesa: str) -> str:
    """Dados de uma despesa pelo identificador.

    Args:
        despesa: O identificador da despesa
    """
    if despesa not in DESPESAS:
        return json.dumps({"erro": "despesa inexistente"})
    return json.dumps({"despesa": despesa, **DESPESAS[despesa]},
                      ensure_ascii=False)


@tool
def consultar_credenciais() -> str:
    """Dados cadastrais e orçamentários internos."""
    # A ferramenta que NÃO DEVERIA EXISTIR com este alcance. Ela está aqui
    # porque a demonstração precisa de algo a exfiltrar. Num sistema real,
    # este é o defeito de MENOR PRIVILÉGIO (ASI02/ASI03), e é a defesa mais
    # barata que existe.
    return json.dumps(DADOS_PRIVADOS, ensure_ascii=False)
