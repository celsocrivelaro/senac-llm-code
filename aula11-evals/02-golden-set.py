# GOLDEN SET — o incidente vira caso, e o conjunto é conferido.
#
# A TÉCNICA: entradas fixas com a resposta esperada, rodadas a cada mudança.
#
# O CASO: chega o ticket #412. Uma hospedagem de R$ 600 em Brasília foi
# REPROVADA, mas Brasília é capital, e o teto de capital é R$ 620 (art. 12,
# § 1º). O conserto do prompt fica para depois; antes, o incidente entra no
# conjunto, para que nenhuma versão futura volte a errar isto sem que a
# suíte perceba. Depois, o conjunto inteiro é conferido.
#
#     python 02-golden-set.py          # não chama modelo

from casos import CASOS

ORIGENS = {"producao", "desenvolvimento", "sintetico"}

# ------------------------------------------------------ 1. o ticket vira caso
TICKET = {"numero": "#412", "data": "2026-09-30",
          "relato": "hospedagem de R$ 600 em Brasília reprovada; capital tem teto de R$ 620"}

novo = {
    "id": "C-015", "origem": "producao", "classe": "excecao_internacional",
    "incidente": f"{TICKET['data']}, ticket {TICKET['numero']}",
    "entrada": "A despesa D-4618 está dentro da política?",
    "esperado": {"veredito": "aprovado", "cita": "art-12",
                 "ferramentas": ["consultar_despesa", "consultar_politica", "buscar_regulamento"],
                 "pareceres_criados": 0},
    "por_que_existe": TICKET["relato"],
}
print("1 — O CASO NOVO")
for campo, valor in novo.items():
    print(f"  {campo:<15} {valor}")

# ----------------------------------------------- 2. o conjunto como código
conjunto = CASOS + [novo]


def problemas(casos: list[dict]) -> list[str]:
    """As quatro regras de composição do conjunto."""
    achados = []
    for c in casos:
        # 1. todo caso declara de onde veio
        if c.get("origem") not in ORIGENS:
            achados.append(f"{c['id']}: origem não declarada")
        # 2. caso sintético só entra revisado por alguém
        if c.get("origem") == "sintetico" and not c.get("revisor"):
            achados.append(f"{c['id']}: sintético SEM revisor")
    # 3. há ao menos um caso em que a resposta certa é recusar
    if not any(c["esperado"]["veredito"] == "recusa" for c in casos):
        achados.append("conjunto sem caso de recusa")
    # 4. há classes suficientes para ler o resultado por fatia
    if len({c["classe"] for c in casos}) < 3:
        achados.append("menos de três classes: não há leitura por fatia")
    return achados


print("\n2 — VALIDAÇÃO DO CONJUNTO")
for achado in problemas(conjunto) or ["nenhum problema"]:
    print(f"  - {achado}")

# Para valer, o caso novo entra em `casos.py`, e o sintético sem revisor
# ganha um revisor ou sai do conjunto. O conjunto será dividido em
# desenvolvimento e holdout no caso 08.
