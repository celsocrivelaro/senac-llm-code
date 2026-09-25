# Aula 07 — 04: O PIPELINE DE RAG.
#
# RAG (retrieval-augmented generation) é a arquitetura em que a geração é
# condicionada a trechos recuperados de um índice externo, em vez de depender
# do que o modelo guardou nos parâmetros. Formulação original: LEWIS et al.
# (2020).
#
# O pipeline tem quatro passos fixos:
#
#   pergunta -> busca -> portão -> contexto + LLM -> resposta
#
# A busca vem da aula 06; a geração é a metade que esta aula acrescenta.
#
# CLASSIFICAÇÃO. Pela taxonomia da aula 05 (nota 01, §3.1), este desenho é
# PROMPT CHAINING COM PORTÃO: o caminho é fixo e o número de chamadas é
# conhecido antes da execução. Não é um agente — nenhuma decisão de fluxo
# é tomada pelo modelo.
#
# ESCOPO DESTE SCRIPT. Executa o pipeline sobre quatro perguntas cujo trecho
# de resposta existe no corpus. Todas são respondidas corretamente. Os modos
# de falha exigem perguntas construídas para provocá-los, e são assunto do
# script 05.

from dados import CORPUS_COM_RUIDO, PERGUNTAS
from indice_chroma import IndiceChroma
from pipeline import pipeline

print("=" * 74)
print("O PIPELINE")
print("=" * 74)
print("""
    pergunta --> [ busca ]  --> portão --> [ LLM ] --> resposta
                     |                        |
                 aula 06                   aula 07
""")

indice = IndiceChroma(CORPUS_COM_RUIDO)
print(f"índice: {len(indice)} chunks em Chroma (persistente em indice/)\n")

for caso in PERGUNTAS[:4]:
    r = pipeline(caso["pergunta"], indice, k=3)
    print(f"  P: {caso['pergunta']}")
    print(f"  R: {r['resposta'][:150]}")
    print(f"     fontes={r['fontes']}  esperado={caso['artigo']}  "
          f"suficiente={r['suficiente']}\n")
