# Aula 06 — 06: O RAG MÍNIMO.
#
# O buscador dos scripts 02 e 03 devolve trechos. Este script fecha a volta:
# os trechos viram RESPOSTA, e a arquitetura ganha nome.
#
# Duas coisas mudam em relação ao 03, e as duas são deliberadas:
#
#   1. o índice sai da memória e vai para um BANCO DE VETORES. Não é por
#      desempenho — com 40 chunks numpy é instantâneo. É por persistência:
#      reconstruir o índice a cada execução custa uma chamada de embedding
#      sobre o corpus inteiro, toda vez;
#   2. entra a primeira chamada de GERAÇÃO da aula. Até aqui nenhum script
#      tinha escrito uma palavra.
#
# O que este script NÃO faz: conferir a citação, recusar com contrato,
# medir fidelidade. É a aula 07.

from dados import REGULAMENTO
from geracao import responder
from indice_chroma import IndiceChroma


# ============================================================ O PIPELINE
#
# As quatro etapas, encaixadas:
#
#   pergunta ──> [ busca ] ──> portão ──> [ contexto + LLM ] ──> resposta
#                    │                            │
#              notas 01 a 04                   esta nota
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
#
# A função inteira ocupa quinze linhas, e metade delas é o portão.

def rag_simples(pergunta: str, indice: IndiceChroma, k: int = 3,
                piso_distancia: float = 0.6) -> dict:
    """pergunta -> busca -> portão -> contexto -> resposta."""
    trechos = indice.buscar(pergunta, k=k)

    # O PORTÃO, etapa frequentemente omitida: se a busca não trouxe nada
    # próximo, a geração NÃO RODA. É o mesmo portão do prompt chaining
    # da aula 05 — código determinístico entre duas chamadas, interrompendo
    # a cadeia antes que uma etapa opere sobre entrada inválida.
    if not trechos or trechos[0]["distancia"] > piso_distancia:
        return {"resposta": "A busca não recuperou trecho suficientemente "
                            "próximo. Encaminhado para revisão.",
                "trechos": trechos, "barrado_no_portao": True}

    return {"resposta": responder(pergunta, trechos),
            "trechos": trechos, "barrado_no_portao": False}


# ============================================================ O LABORATÓRIO

PERGUNTAS = [
    "qual o teto de refeição em viagem?",
    "e em viagem internacional?",
    # Esta o regulamento NÃO responde. É o caso que o portão deveria barrar.
    "qual o índice de reajuste da tabela de fretes marítimos?",
]

indice = IndiceChroma(REGULAMENTO)

print("=" * 74)
print(f"RAG MÍNIMO — {len(indice)} chunks no banco de vetores")
print("=" * 74)
print("""
A construção do índice acima custou UMA chamada de embedding, com os chunks
todos juntos. As consultas abaixo custam uma de embedding e uma de geração
cada — e, no banco, o índice sobrevive a esta execução.

A busca devolve DISTÂNCIA, e não score: o Chroma com métrica de cosseno
entrega d = 1 - cosseno. Aqui, valores baixos indicam proximidade — o
inverso da escala que o script 01 imprimia.
""")

resultados = {}
for pergunta in PERGUNTAS:
    r = rag_simples(pergunta, indice)
    resultados[pergunta] = r
    print("-" * 74)
    print(f"pergunta: {pergunta!r}\n")
    for t in r["trechos"]:
        print(f"  [{t['artigo']}] distância {t['distancia']:.4f}")
    if r["barrado_no_portao"]:
        print("\n  >>> BARRADO NO PORTÃO — a geração não rodou.")
    print(f"\n  {r['resposta']}\n")

# A última das três é a pergunta que o regulamento não responde.
distancia_fora = resultados[PERGUNTAS[-1]]["trechos"][0]["distancia"]

print("=" * 74)
print("ONDE ESTE SCRIPT PARA")
print("=" * 74)
print(f"""
A terceira pergunta NÃO TEM RESPOSTA no regulamento — fretes marítimos não
são assunto de política de reembolso —, e mesmo assim o portão a deixou
passar. O trecho mais próximo veio a {distancia_fora:.4f} de distância, o
equivalente a {1 - distancia_fora:.4f} de cosseno.

E esse número já era conhecido: é o PISO que o script 01 mediu entre textos
sem relação nenhuma. Um limiar de 0,6 de distância corresponde a 0,4 de
cosseno, muito abaixo do piso — então ele não barra nada que não seja índice
vazio.

    O PORTÃO EXISTE E ESTÁ NO LUGAR CERTO. O LIMIAR É QUE FOI CHUTADO.

É a mesma conclusão do script 01, agora com consequência: limiar absoluto
escolhido no chute não funciona, e calibrá-lo exige o conjunto de perguntas
com resposta conhecida do script 02.

E repare no que ainda falta: nada aqui confere se a resposta usou os trechos
que voltaram, nem se a fonte citada existe. Os quatro modos de falha deste
pipeline são a aula 07 — e o próximo script desta aula mostra que o defeito
que derruba a busca já estava no vetor desde o começo.""")
