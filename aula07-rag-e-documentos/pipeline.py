# Aula 07 — O pipeline de RAG.
#
# Encadeia as duas metades: a recuperação, da aula 06, e a geração, desta
# aula.
#
# CLASSIFICAÇÃO. Pela taxonomia da aula 05 (nota 01, §3.1), este desenho é
# PROMPT CHAINING COM PORTÃO: o caminho é fixo e o número de chamadas é
# conhecido antes da execução. Nenhuma decisão de fluxo é tomada pelo modelo,
# e portanto não se trata de um agente — designá-lo assim é o caso de `agent
# washing` descrito na aula 04.
#
# A função ocupa vinte linhas, das quais metade implementa o portão.

from geracao import responder
from indice_chroma import IndiceChroma


def pipeline(pergunta: str, indice: IndiceChroma, k: int = 3,
             com_contrato: bool = True, com_portao: bool = True) -> dict:
    """pergunta -> busca -> [portão] -> contexto -> resposta."""
    trechos = indice.buscar(pergunta, k=k)

    # O PORTÃO. Se o trecho mais próximo estiver acima do limiar de
    # distância, a etapa de geração não é executada. Em distância de cosseno,
    # valores menores indicam maior proximidade. O limiar de 0,6 é
    # deliberadamente frouxo: o script 05 depende dele para demonstrar que
    # perguntas fora de domínio o atravessam.
    if com_portao and (not trechos or trechos[0]["distancia"] > 0.6):
        return {"resposta": "A busca não recuperou trecho suficientemente "
                            "próximo. Encaminhado para revisão.",
                "fontes": [], "suficiente": False, "trechos": trechos,
                "barrado_no_portao": True}

    resultado = responder(pergunta, trechos, com_contrato=com_contrato)
    return {**resultado, "trechos": trechos, "barrado_no_portao": False}
