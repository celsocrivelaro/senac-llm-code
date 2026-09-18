# Aula 06 — O RAG mínimo.
#
# As quatro etapas, encaixadas:
#
#   pergunta ──> [ busca ] ──> portão ──> [ contexto + LLM ] ──> resposta
#                    │                            │
#              partes 1 a 3                   parte 4
#
# O nome consagrado é RAG — retrieval-augmented generation —, de LEWIS et
# al. (2020). E o nome da ARQUITETURA importa tanto quanto: pela taxonomia
# da aula 05, isto é PROMPT CHAINING COM PORTÃO. O caminho está no código,
# o número de chamadas é conhecido antes de executar, e nenhuma etapa
# depende de descoberta feita durante a execução.
#
# Um pipeline RAG NÃO É UM AGENTE. Chamá-lo de agente é o agent washing da
# aula 04 — e a distinção não é de vocabulário: um workflow é testável
# etapa por etapa e tem custo previsível.

from geracao import responder
from indice_chroma import IndiceChroma


def rag_simples(pergunta: str, indice: IndiceChroma, k: int = 3,
                piso_distancia: float = 0.6) -> dict:
    """pergunta -> busca -> portão -> contexto -> resposta."""
    trechos = indice.buscar(pergunta, k=k)

    # O PORTÃO, a etapa que quase ninguém escreve: se a busca não trouxe
    # nada próximo, a geração NÃO RODA. É o mesmo portão do prompt chaining
    # da aula 05 — código determinístico entre duas chamadas, interrompendo
    # a cadeia antes que uma etapa opere sobre entrada inválida.
    if not trechos or trechos[0]["distancia"] > piso_distancia:
        return {"resposta": "A busca não recuperou trecho suficientemente "
                            "próximo. Encaminhado para revisão.",
                "trechos": trechos, "barrado_no_portao": True}

    return {"resposta": responder(pergunta, trechos),
            "trechos": trechos, "barrado_no_portao": False}
