# pass^k — "testei e funcionou" é uma amostra de tamanho um.
#
# A TÉCNICA: rodar a mesma entrada k vezes e exigir acerto em todas.
#
# Fundamento: o τ-bench (Yao et al., 2024) passou a medir se o agente
# acerta VÁRIAS VEZES SEGUIDAS, e não uma.
#
# O CASO: depois do ticket #331, alguém ajustou o prompt, rodou a D-4613
# (Lisboa) uma vez, viu "aprovado" e fechou o ticket. A pergunta é quantas
# vezes em vinte esse mesmo agente, com a mesma entrada e temperature=0,
# dá a mesma resposta.
#
#     pass@k   ao menos uma de k tentativas acerta   (quem escolhe a melhor)
#     pass^k   as k tentativas acertam               (k usuários, uma cada)
#
#     python 03-pass-k.py          # 20 execuções do agente

from collections import Counter

from casos import CASOS
from metricas import extrair_veredito
from sistema import MODELO, PROVEDOR, rodar

N = 20
CASO = next(c for c in CASOS if c["id"] == "C-005")
ESPERADO = CASO["esperado"]["veredito"]

print(f"[{PROVEDOR}:{MODELO}]")
print(f"{CASO['id']}: {CASO['entrada']}   (esperado: {ESPERADO})\n")

vereditos, trajetorias = [], []
for i in range(N):
    trace = rodar(CASO["entrada"])
    vereditos.append(extrair_veredito(trace.resposta))
    trajetorias.append(" -> ".join(p["ferramenta"] for p in trace.passos) or "(nenhuma)")
    print(f"  {i + 1:>2}/{N}  {str(vereditos[-1]):<10} {len(trace.passos)} passos  {trace.tokens} tokens")

acertos = vereditos.count(ESPERADO)

print("\nVEREDITOS")
for veredito, n in Counter(vereditos).most_common():
    marca = "  <- esperado" if veredito == ESPERADO else ""
    print(f"  {str(veredito):<10} {n:>3}  {'#' * int(40 * n / N)}{marca}")

print("\nTRAJETÓRIAS")
for trajetoria, n in Counter(trajetorias).most_common():
    print(f"  {n:>3}x  {trajetoria}")

# A taxa de acerto de uma execução é p. Acertar k vezes seguidas, supondo
# execuções independentes, é p multiplicado por ele mesmo k vezes.
p = acertos / N
print(f"\n  pass@1 = {p:.2f}          acertos / {N}")
for k in (3, 5, 8):
    print(f"  pass^{k} = {p ** k:.2f}          p ** {k}: as {k} execuções acertam")

# Se houve variação, ela veio com temperature=0: o provedor (réplicas,
# ponto flutuante, versão servida) não é controlável. O pass^5 acima é a
# chance de cinco funcionários receberem, os cinco, o parecer certo — é o
# número que o ticket fechado com uma execução não tinha.
