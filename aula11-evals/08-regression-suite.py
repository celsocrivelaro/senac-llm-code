# REGRESSION SUITE — o prompt B "corrige" a exceção internacional. Sobe?
#
# A TÉCNICA: rodar a suíte inteira nas duas versões antes de promover.
#
# O CASO: os tickets #331 e #349 são exceção de viagem internacional, e o
# #412 (caso 02), de capital. Alguém escreveu o prompt B, rodou os três, viu
# os três passarem e quer promover. A suíte responde a duas perguntas que o teste
# manual não responde: a diferença é maior que o RUÍDO? E alguma outra
# fatia PIOROU?
#
# Quem escolhe os casos acaba ajustando o sistema para eles. Por isso parte
# do conjunto vai para um HOLDOUT, que ninguém olha ao ajustar o prompt e
# que só roda na decisão de promover.
#
# A regra é escrita ANTES do resultado. Decidir depois é escolher o
# critério que confirma o que já se queria fazer.
#
#     python 08-regression-suite.py          # o caso mais caro: ver CUSTO

from collections import Counter

from casos import CASOS, SYSTEM
from metricas import nivel_deterministico, nivel_resultado, passou
from sistema import MODELO, PARECERES, PROVEDOR, limpar_pareceres, rodar

# CUSTO: execuções do agente = casos de desenvolvimento x REPETICOES x 3
# (A, A de novo para o ruído, e B) + holdout x 2. Com 9 casos e
# REPETICOES=2, são ~64. Em sala, REPETICOES=1 corta pela metade.
REPETICOES = 2

PROMPT_A = SYSTEM
PROMPT_B = SYSTEM + (
    "\n\nATENÇÃO: antes de comparar um valor com o teto, verifique se há exceção aplicável no regulamento — viagem internacional (art. 19) e capital (art. 12 §1) alteram os tetos. Use buscar_regulamento."
)

# A REGRA, declarada antes de rodar. B só sobe se:
#   1. o ganho médio for maior que o ruído de base (A contra A);
#   2. nenhuma classe cair mais que PIORA_MAXIMA;
#   3. no holdout, B não for pior que A.
PIORA_MAXIMA = 0.05

# O HOLDOUT, escolhido uma vez e nunca mais trocado: estes casos ninguém
# olha ao ajustar o prompt.
HOLDOUT_IDS = ["C-003", "C-006", "C-007", "C-008", "C-012"]

DESENVOLVIMENTO = [c for c in CASOS if c["id"] not in HOLDOUT_IDS]
HOLDOUT = [c for c in CASOS if c["id"] in HOLDOUT_IDS]


def avaliar(caso: dict, prompt: str) -> dict:
    limpar_pareceres()
    antes = dict(PARECERES)
    trace = rodar(caso["entrada"], prompt)
    return {"id": caso["id"], "classe": caso["classe"],
            "deterministico": nivel_deterministico(trace, caso),
            "resultado": nivel_resultado(antes, dict(PARECERES), caso)}


def suite(casos: list[dict], prompt: str, repeticoes: int) -> dict:
    """Roda os casos `repeticoes` vezes e devolve a taxa de aprovação,
    no total e por classe."""
    resultados = [avaliar(c, prompt) for _ in range(repeticoes) for c in casos]
    por_classe = {}
    for r in resultados:
        por_classe.setdefault(r["classe"], []).append(passou(r))
    return {"taxa": sum(passou(r) for r in resultados) / len(resultados),
            "por_classe": {k: sum(v) / len(v) for k, v in por_classe.items()}}


print(f"[{PROVEDOR}:{MODELO}]")
print(f"desenvolvimento: {len(DESENVOLVIMENTO)} casos {dict(Counter(c['classe'] for c in DESENVOLVIMENTO))}")
print(f"holdout:         {len(HOLDOUT)} casos (só roda na confirmação)")
print(f"repetições:      {REPETICOES}\n")

print("  rodando A ...")
a = suite(DESENVOLVIMENTO, PROMPT_A, REPETICOES)
print("  rodando A de novo, para medir o ruído ...")
a2 = suite(DESENVOLVIMENTO, PROMPT_A, REPETICOES)
print("  rodando B ...")
b = suite(DESENVOLVIMENTO, PROMPT_B, REPETICOES)

ruido = abs(a["taxa"] - a2["taxa"])
delta = b["taxa"] - a["taxa"]

print("\n1 — POR FATIA (conjunto de desenvolvimento)")
print(f"  {'classe':<24} {'A':>6} {'A de novo':>10} {'B':>6} {'B - A':>7}")
pioras = []
for classe in sorted(a["por_classe"]):
    ta, ta2, tb = a["por_classe"][classe], a2["por_classe"][classe], b["por_classe"][classe]
    if tb < ta - PIORA_MAXIMA:
        pioras.append(classe)
    print(f"  {classe:<24} {ta:>6.0%} {ta2:>10.0%} {tb:>6.0%} {(tb - ta) * 100:>+6.0f}"
          + ("   <- PIOROU" if classe in pioras else ""))
print(f"  {'MÉDIA':<24} {a['taxa']:>6.0%} {a2['taxa']:>10.0%} {b['taxa']:>6.0%} {delta * 100:>+6.0f}")
print(f"\n  ruído de base (A contra A): {ruido * 100:.0f} pontos")

print("\n2 — A REGRA")
passa_ganho = delta > ruido
print(f"  ganho acima do ruído ...... {'sim' if passa_ganho else 'NÃO'} ({delta * 100:+.0f} contra {ruido * 100:.0f})")
print(f"  nenhuma fatia piorou ...... {'sim' if not pioras else 'NÃO: ' + ', '.join(pioras)}")

promove = passa_ganho and not pioras
if promove:
    print("\n3 — CONFIRMAÇÃO NO HOLDOUT")
    ha = suite(HOLDOUT, PROMPT_A, 1)
    hb = suite(HOLDOUT, PROMPT_B, 1)
    print(f"  A {ha['taxa']:.0%}   B {hb['taxa']:.0%}")
    promove = hb["taxa"] >= ha["taxa"]
else:
    print("\n3 — HOLDOUT NÃO RODADO: a regra já reprovou no desenvolvimento")

print(f"\n  VEREDITO: {'PROMOVER B' if promove else 'MANTER A'}")

