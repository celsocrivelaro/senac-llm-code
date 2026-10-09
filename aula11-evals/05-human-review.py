# HUMAN REVIEW — antes de automatizar o julgamento, os humanos concordam?
#
# A TÉCNICA: pessoas rotulam as saídas, e mede-se se concordam entre si.
#
# A partir de Shankar et al. (2024), "Who validates the validators?".
#
# O CASO: a equipe quer trocar a revisão humana de fidelidade por um juiz
# LLM (caso 06). O juiz vai ser calibrado contra rótulos humanos. Mas se
# duas pessoas rotulando os mesmos casos discordam, não existe padrão para
# calibrar: o problema está no CRITÉRIO, não no modelo.
#
# Dez pares (contexto, resposta) rotulados por duas pessoas, A e B.
#
#     python 05-human-review.py          # não chama modelo

from casos import ROTULOS_FIDELIDADE
from metricas import concordancia, imprimir_matriz

pares = [(r["id"], r["humano_a"], r["humano_b"]) for r in ROTULOS_FIDELIDADE]
resultado = concordancia(pares)

print("1 — HUMANO A × HUMANO B\n")
imprimir_matriz(resultado, ref="A", aval="B")

print("\n2 — ONDE OS HUMANOS DISCORDAM\n")
for r in ROTULOS_FIDELIDADE:
    if r["id"] in resultado["desacordos"]:
        print(f"  {r['id']}  {r['resposta']}")
        print(f"        contexto: {r['contexto']}")
        print(f"        {r['nota']}\n")

consenso = [r for r in ROTULOS_FIDELIDADE if r["humano_a"] == r["humano_b"]]
print("3 — O QUE ISSO IMPÕE AO JUIZ")
print(f"""
  teto de concordância de qualquer juiz: {resultado['taxa']:.0%}
  casos com padrão (consenso) ........: {len(consenso)}/{len(ROTULOS_FIDELIDADE)}
""")

# Os dois desacordos não são descuido: são duas perguntas que a rubrica não
# respondia. Resposta INCOMPLETA é fiel? RECUSA, quando o contexto
# respondia, é fiel? A rubrica do caso 06 decide as duas — "incompleta é
# fiel, recusa é fiel" —, e só depois disso os dois casos viram padrão.
