# O cliente do modelo — e o único arquivo do laboratório que sabe qual
# provedor está em uso.
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

import os

from dotenv import load_dotenv

load_dotenv()

PROVEDOR = os.environ.get("LLM_PROVEDOR", "mistral").strip().lower()

if PROVEDOR == "mistral":
    from langchain_mistralai.chat_models import ChatMistralAI

    MODELO = os.environ.get("MISTRAL_MODELO", "mistral-small-latest")
    modelo = ChatMistralAI(
        model=MODELO,
        api_key=os.environ.get("MISTRAL_API_KEY"),
    )

elif PROVEDOR == "ollama":
    from langchain_ollama import ChatOllama

    MODELO = os.environ.get("OLLAMA_MODELO", "qwen3.6:35b")
    # `validate_model_on_init` falha aqui, com mensagem clara, se a tag não
    # estiver baixada — em vez de dar erro no meio da conversa.
    modelo = ChatOllama(
        model=MODELO,
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        validate_model_on_init=True,
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
    )

else:
    raise ValueError(f"LLM_PROVEDOR inválido no .env: {PROVEDOR!r}. Use 'mistral', 'ollama' ou 'groq'.")
