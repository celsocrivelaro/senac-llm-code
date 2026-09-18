# Aula 06 — 02: CHUNKING, medido.
#
# Três estratégias sobre o MESMO regulamento e as MESMAS dez perguntas. A
# afirmação "em documento normativo, estrutura ganha" não é para ser aceita:
# é para ser medida aqui.
#
# O conjunto de dez perguntas com resposta conhecida (definido abaixo) é o
# primeiro dataset de avaliação do curso. A aula 11 volta nele com outro nome.
#
# Rode com um número para mudar o k:  python 02-chunking.py 1

import sys

import numpy as np

from indice_memoria import IndiceMemoria
from dados import REGULAMENTO
from embedding import gerar_matrix_embbeddings
from estrategias_chunking import ESTRATEGIAS

# Quantos trechos a busca devolve. Passe outro na linha de comando para ver o
# efeito: `python 02-chunking.py 1` mostra o que se perde apostando no
# primeiro colocado.
K = int(sys.argv[1]) if len(sys.argv) > 1 else 3


# ============================================================ AS PERGUNTAS
#
# Dez perguntas com resposta CONHECIDA. Construir este conjunto é o trabalho;
# medir é fácil depois. É também o primeiro dataset de avaliação do curso —
# a aula 11 volta nele com outro nome.
#
# `artigo` é a resposta certa: qual trecho do regulamento responde a pergunta.

PERGUNTAS = [
    {"pergunta": "Qual o teto de reembolso para uma refeição em viagem?",
     "artigo": "Art. 4º §1º"},
    {"pergunta": "Quanto posso gastar em refeição numa viagem para Portugal?",
     "artigo": "Art. 4º §2º"},
    {"pergunta": "Jantar com três pessoas do cliente: o teto vale para o total?",
     "artigo": "Art. 4º §3º"},
    {"pergunta": "Posso pedir reembolso de vinho no jantar de negócios?",
     "artigo": "Art. 4º §4º"},
    {"pergunta": "Qual o limite por corrida de aplicativo?",
     "artigo": "Art. 5º §1º"},
    {"pergunta": "A corrida passou do limite mas era madrugada. Tem jeito?",
     "artigo": "Art. 5º §2º"},
    {"pergunta": "Preciso de nota fiscal para táxi?",
     "artigo": "Art. 3º §2º"},
    {"pergunta": "O recibo mostra valor diferente do que declarei. O que acontece?",
     "artigo": "Art. 3º §3º"},
    {"pergunta": "Uma despesa de R$ 1.240 é aprovada por quem?",
     "artigo": "Art. 9º §2º"},
    {"pergunta": "Perdi o prazo de envio. Ainda dá para pedir?",
     "artigo": "Art. 8º §2º"},
]


# ------------------------------------------------------------------ a medida

def _normalizar(s: str) -> str:
    return (s.replace("º", "").replace("o.", "").replace(".", "")
             .replace(" ", "").lower())



def acertou(chunks: list[dict], artigo_esperado: str) -> bool:
    """O chunk recuperado contém o artigo que responde a pergunta?

    Comparação por CONTEÚDO, não por id: as estratégias por caracteres não
    produzem ids com nome de artigo, e mesmo assim podem conter o texto certo.
    """
    alvo = _normalizar(artigo_esperado)
    return any(alvo in _normalizar(c["texto"]) or alvo in _normalizar(c["id"])
               for c in chunks)


def recall_at_k(indice: IndiceMemoria, perguntas: list[dict],
                vetores: np.ndarray, k: int = 3) -> dict:
    """recall@k: em quantas perguntas o trecho certo apareceu entre os k
    primeiros. Devolve também as falhas, que valem mais que a média.

    Recebe os VETORES das perguntas prontos, e por isso não chama a API
    nenhuma vez. Ver o comentário de VETORES_PERGUNTA, abaixo.
    """
    acertos, falhas = 0, []
    for caso, vetor in zip(perguntas, vetores):
        recuperados = indice.buscar_vetor(vetor, k=k)
        if acertou(recuperados, caso["artigo"]):
            acertos += 1
        else:
            falhas.append({**caso, "veio": recuperados[0]["id"],
                           "score": recuperados[0]["score"]})
    return {"k": k, "acertos": acertos, "total": len(perguntas),
            "recall": acertos / len(perguntas), "falhas": falhas}


print("=" * 74)
print(f"CHUNKING — três estratégias, {len(PERGUNTAS)} perguntas, recall@{K}")
print("=" * 74)

# --------------------------------------------- o que cada estratégia produz
print("\nO MESMO TRECHO, CORTADO DE TRÊS FORMAS\n")
for nome, estrategia in ESTRATEGIAS.items():
    chunks = estrategia(REGULAMENTO)
    amostra = chunks[len(chunks) // 2]
    print(f"  [{nome}] {len(chunks)} chunks · "
          f"média {sum(len(c['texto']) for c in chunks) // len(chunks)} caracteres")
    print(f"      id: {amostra['id']}")
    print(f"      {amostra['texto'][:100].strip()!r}...\n")

# ------------------------------------------------------------------ a medida
print("=" * 74)
print("A MEDIDA")
print("=" * 74)
print()

# As dez perguntas são embutidas UMA VEZ. O vetor de uma pergunta não muda
# entre estratégias nem entre valores de k, e este script a consulta SETE
# vezes: três para comparar os cortes, quatro para varrer o k.
#
# Reembuti-las a cada medição custaria 70 chamadas idênticas — e seria este
# script violando a lição que o 03 ensina: indexar uma vez, consultar sempre.
# Com os vetores prontos, a aula inteira cabe em 4 chamadas.
VETORES_PERGUNTA = gerar_matrix_embbeddings([c["pergunta"] for c in PERGUNTAS])

# Os índices ficam guardados: construir um custa uma chamada, e a varredura
# do k mais abaixo reusa o da estratégia vencedora.
indices, relatorios = {}, {}
for nome, estrategia in ESTRATEGIAS.items():
    indice = IndiceMemoria(estrategia(REGULAMENTO))
    indices[nome] = indice
    relatorio = recall_at_k(indice, PERGUNTAS, VETORES_PERGUNTA, k=K)
    relatorios[nome] = relatorio
    barra = "█" * int(relatorio["recall"] * 40)
    print(f"  {nome:<12s} {len(indice):>3d} chunks   "
          f"recall@{K} = {relatorio['acertos']}/{relatorio['total']} "
          f"({relatorio['recall']:.0%})  {barra}")

melhor = max(relatorios, key=lambda n: relatorios[n]["recall"])
print(f"\n  melhor: {melhor}")

# ------------------------------------------------------- as falhas importam
print(f"\n{'=' * 74}")
print("AS PERGUNTAS QUE FALHARAM")
print("=" * 74)
print("""
O recall médio esconde o caso difícil. As falhas abaixo valem mais que a
média, porque cada uma tem um diagnóstico diferente: é o corte que separou
a pergunta da resposta, é a pergunta que está mal formulada, ou é o vetor
que não representa o que a pergunta exige — e este último caso é assunto
da aula 07.
""")

for nome, relatorio in relatorios.items():
    if not relatorio["falhas"]:
        print(f"  [{nome}] nenhuma falha em k={K}\n")
        continue
    print(f"  [{nome}]")
    for f in relatorio["falhas"]:
        print(f"      pergunta ... {f['pergunta']}")
        print(f"      esperado ... {f['artigo']}")
        print(f"      veio ....... {f['veio']} (score {f['score']:.4f})\n")

# ------------------------------------------------------------- o efeito do k
print("=" * 74)
print("O EFEITO DO k")
print("=" * 74)
print("""
k alto esconde defeito de índice — e enche a janela na aula 07, onde cada
chunk recuperado ocupa a janela em toda pergunta. Escolher k é decisão de
projeto, não detalhe.
""")

for k in (1, 3, 5, 10):
    r = recall_at_k(indices[melhor], PERGUNTAS, VETORES_PERGUNTA, k=k)
    print(f"  k={k:<3d} recall = {r['acertos']}/{r['total']} ({r['recall']:.0%})")
