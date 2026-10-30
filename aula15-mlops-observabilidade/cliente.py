# O cliente do modelo — e o único arquivo do laboratório que sabe qual
# provedor está em uso.
#
# `LLM_PROVEDOR`, no .env, decide qual integração nativa do LangChain é
# construída. As quatro devolvem a mesma interface de chat model, então tudo o
# que vem depois — `create_agent`, as ferramentas, o grafo — é idêntico nos
# quatro caminhos.
#
#   mistral — API, paga por token, o padrão da disciplina
#   ollama  — modelo local, de graça e lento
#   groq    — API, muito rápida, com cota gratuita generosa
#   openrouter — gateway: uma chave para modelos de vários provedores
#
# É o mesmo arranjo de `cliente.py` nas aulas de embeddings e RAG, de RAG e
# documentos e de memória: um módulo só para resolver a configuração, para
# que nenhum script precise repetir isso.

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

elif PROVEDOR == "openrouter":
    from langchain_openai import ChatOpenAI

    # O OpenRouter é um gateway: uma chave só, e o modelo de qualquer
    # provedor escolhido pelo nome (`provedor/modelo`). Ele fala o protocolo
    # da OpenAI, então a integração é o `ChatOpenAI` — o SDK da OpenAI por
    # baixo — com o endereço trocado.
    MODELO = os.environ.get("OPENROUTER_MODELO", "openai/gpt-oss-20b")
    modelo = ChatOpenAI(
        model=MODELO,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )

else:
    raise ValueError(f"LLM_PROVEDOR inválido no .env: {PROVEDOR!r}. Use 'mistral', 'ollama', 'groq' ou 'openrouter'.")
