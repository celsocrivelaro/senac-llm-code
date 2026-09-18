# Aula 06 — 03: O BUSCADOR.
#
# O artefato que a aula entrega: o buscador executável, com o corte que
# venceu a medição do script 02.
#
#     python 03-buscador.py "qual o teto de refeição em viagem?"
#
# Repare no que este script NÃO faz: não responde nada. Devolve trechos. A
# geração sobre os trechos recuperados é o assunto da aula 07, e a fronteira
# entre as duas aulas é exatamente essa.

import sys

from indice_memoria import IndiceMemoria
from dados import REGULAMENTO
from estrategias_chunking import por_estrutura

# A estratégia vencedora do script 02. O nome é CONSTANTE, e não um detalhe
# escondido na chamada: trocar o corte muda o recall, e por isso ele entra no
# carimbo da versão junto com o prompt e o modelo (aula 03, nota 03).
#
# Das três do `estrategias_chunking.py`, só esta chega aqui. As outras duas
# existem para perder a medição do 02, e é lá que elas são executadas.
ESTRATEGIA = "estrutura"
K_PADRAO = 3


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or "qual o teto de refeição em viagem?"

    # O índice é construído UMA VEZ, aqui, e a busca logo abaixo o RECEBE
    # pronto. Não há atalho que o reconstrua sob demanda: seria a assimetria
    # do fim deste script ao contrário, e o aluno copiaria o atalho.
    indice = IndiceMemoria(por_estrutura(REGULAMENTO))

    print("=" * 74)
    print(f"BUSCADOR — estratégia={ESTRATEGIA} · {len(indice)} chunks · k={K_PADRAO}")
    print("=" * 74)
    print(f"\npergunta: {pergunta!r}\n")

    for posicao, chunk in enumerate(indice.buscar(pergunta, k=K_PADRAO), start=1):
        print(f"  {posicao}. [{chunk['id']}] score {chunk['score']:.4f}")
        for linha in chunk["texto"].strip().split("\n"):
            print(f"       {linha}")
        print()

    # ------------------------------------------------------------ a assimetria
    #
    # Os números abaixo não são medidos: são lidos do próprio desenho do
    # código. `construir_indice()` embute os chunks em UMA chamada, e roda uma
    # vez; `buscar()` embute a pergunta em UMA chamada, e roda a cada pergunta.
    print("=" * 74)
    print("A ASSIMETRIA: O ÍNDICE UMA VEZ, A PERGUNTA SEMPRE")
    print("=" * 74)
    print(f"""
  construir o índice ... 1 chamada, com os {len(indice)} chunks juntos   UMA VEZ
  esta consulta ........ 1 chamada, só com a pergunta        A CADA PERGUNTA

A segunda linha é o que se paga em TODA pergunta. A primeira acontece uma
vez, e a próxima consulta não vai tocar no índice de novo — ele está pronto.

É essa assimetria, e não o tamanho de nenhum dos dois, que torna a busca
vetorial viável: indexar é trabalho de construção, consultar é trabalho de
operação. Um sistema que reconstruísse o índice a cada pergunta pagaria a
primeira linha toda vez, e não haveria vantagem nenhuma sobre ler o
documento inteiro.

Na aula 07 o índice sai da memória e vai para disco, e é aí que o "uma vez"
passa a valer entre execuções, e não só dentro de uma.""")

    print("=" * 74)
    print("ONDE ESTE SCRIPT PARA")
    print("=" * 74)
    print("""
O buscador não sabe qual dos três trechos responde a pergunta, nem se algum
responde — sabe apenas quais são os mais parecidos.

Transformar isso em resposta é a aula 07, e o primeiro problema de lá já
está visível acima: se três trechos voltam e dois são irrelevantes, o
modelo vai citar algum deles.""")
