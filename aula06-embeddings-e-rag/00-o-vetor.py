# Aula 06 — 00: O VETOR.
#
# Primeiro contato com um modelo que NÃO GERA TEXTO. A aula 02 (nota 01 §5)
# já tinha apresentado embeddings como modalidade; a aula 01 (nota 01 §6.1)
# já tinha dito de onde eles vêm — a linhagem encoder, que lê o texto inteiro
# de uma vez e produz representação em vez de continuação.
#
# O script tem um assunto só, em dois tempos:
#
#   1. um vetor sozinho não diz NADA — é uma lista de números sem significado
#      individual, e ver isso é uma decepção útil;
#   2. dois vetores dizem TUDO — a comparação entre eles é o único número que
#      a aula inteira vai usar.
#
# O 01 pega daqui: como esse número se calcula, por que cosseno, e como
# ordenar por ele já é buscar.


import numpy as np

from embedding import gerar_matrix_embbeddings
from similaridade import cosseno

# Três textos: o primeiro é a regra, o segundo pergunta a mesma coisa com
# outras palavras, o terceiro não tem relação nenhuma com os dois.
REGRA = "O reembolso de refeições em viagem fica limitado a R$ 120,00."
PARAFRASE = "Quanto posso gastar almoçando numa viagem a trabalho?"
ALHEIO = "O campeonato de futebol começa no próximo domingo às dezesseis horas."

# Uma chamada, três vetores. A API aceita lista, e embutir em lote é o modo
# normal de usá-la — o 02 embute quarenta chunks assim.
vetor_regra, vetor_parafrase, vetor_alheio = gerar_matrix_embbeddings(
    [REGRA, PARAFRASE, ALHEIO])

# --------------------------------------------------------------- um vetor
print("=" * 74)
print("UM TEXTO EM UM VETOR")
print("=" * 74)

print(f"\ntexto ......... {REGRA!r}")
print(f"dimensão ...... {vetor_regra.shape[0]}")
print(f"norma ......... {np.linalg.norm(vetor_regra):.4f}")
print(f"primeiros 8 ... {np.round(vetor_regra[:8], 4).tolist()}")
print(f"faixa ......... [{vetor_regra.min():.4f}, {vetor_regra.max():.4f}]")

# -------------------------------------------------------------- dois vetores
print("=" * 74)
print("COMPARAÇÃO ENTRE 2 TEXTOS")
print("=" * 74)

sim_parafrase = cosseno(vetor_regra, vetor_parafrase)
sim_alheio = cosseno(vetor_regra, vetor_alheio)

print(f"\n  A  {REGRA}")
print(f"  B  {PARAFRASE}")
print(f"  C  {ALHEIO}\n")
print(f"  cosseno(A, B) = {sim_parafrase:.4f}   <- dizem a mesma coisa, sem "
      f"compartilhar quase nenhuma palavra")
print(f"  cosseno(A, C) = {sim_alheio:.4f}   <- não têm relação nenhuma")

# É este o número que a aula inteira usa. O sentido não está DENTRO do vetor:
# está ENTRE vetores, e aparece só quando há mais de um para comparar.
#
# A e B quase não compartilham palavras — "refeições"/"almoçando",
# "limitado"/"gastar" — e ainda assim medem 0,85. É a operação que a busca
# por palavra-chave não realiza, e a razão de o embedding existir.
#
# E repare no outro número: A e C não têm relação nenhuma e mesmo assim dão
# 0,73, não zero. Por que o piso não é zero, e o que fazer com isso, é o
# assunto do script 01.
