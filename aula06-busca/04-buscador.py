# Aula 06 — 04: O BUSCADOR.
#
# O artefato que a aula entrega: o buscador executável, com o corte que
# venceu a medição do script 03.
#
#     python 04-buscador.py "qual o teto de refeição em viagem?"
#
# Repare no que este script NÃO faz: não responde nada. Devolve trechos. A
# geração sobre os trechos recuperados é o assunto da aula 07, e a fronteira
# entre as duas aulas é exatamente essa.

import sys

from busca import CONSUMO, Indice, por_estrutura, resumo_consumo
from dados import REGULAMENTO

# A estratégia vencedora do script 03. O nome é CONSTANTE, e não um detalhe
# escondido na chamada: trocar o corte muda o recall, e por isso ele entra no
# carimbo da versão junto com o prompt e o modelo (aula 03, nota 03).
#
# É também o motivo de só `por_estrutura` viver em `busca.py`: as outras duas
# estratégias ficaram no 03, onde servem de comparação e nada mais.
ESTRATEGIA = "estrutura"
K_PADRAO = 3


def construir_indice() -> Indice:
    """Constrói o índice do regulamento, cortado por artigo e parágrafo."""
    return Indice(por_estrutura(REGULAMENTO))


def buscar(pergunta: str, k: int = K_PADRAO, indice: Indice | None = None):
    return (indice or construir_indice()).buscar(pergunta, k=k)


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or "qual o teto de refeição em viagem?"

    # O índice é construído UMA VEZ. Guardamos o consumo antes e depois para
    # medir a assimetria no fim — ela é a propriedade que faz a busca vetorial
    # valer a pena, e só dá para vê-la onde existe um índice.
    antes = dict(CONSUMO)
    indice = construir_indice()
    gasto_indice = {k: CONSUMO[k] - antes[k] for k in CONSUMO}

    print("=" * 74)
    print(f"BUSCADOR — estratégia={ESTRATEGIA} · {len(indice)} chunks · k={K_PADRAO}")
    print("=" * 74)
    print(f"\npergunta: {pergunta!r}\n")

    antes_busca = dict(CONSUMO)
    for posicao, chunk in enumerate(buscar(pergunta, indice=indice), start=1):
        print(f"  {posicao}. [{chunk['id']}] score {chunk['score']:.4f}")
        for linha in chunk["texto"].strip().split("\n"):
            print(f"       {linha}")
        print()
    gasto_busca = {k: CONSUMO[k] - antes_busca[k] for k in CONSUMO}

    # ------------------------------------------------------------ a assimetria
    print("=" * 74)
    print("A ASSIMETRIA: O ÍNDICE UMA VEZ, A PERGUNTA SEMPRE")
    print("=" * 74)
    print(f"""
  construir o índice ... {gasto_indice['chamadas']} chamada(s) · {gasto_indice['tokens']} tokens · {len(indice)} chunks
  esta consulta ........ {gasto_busca['chamadas']} chamada   · {gasto_busca['tokens']} tokens

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

    print(f"\n{resumo_consumo('TOTAL DO SCRIPT')}")
