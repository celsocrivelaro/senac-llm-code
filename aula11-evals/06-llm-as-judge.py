# LLM AS JUDGE — trocar a revisão humana por um juiz, e calibrá-lo antes.
#
# A TÉCNICA: um modelo avalia a saída de outro, seguindo uma rubrica.
#
# O CASO: revisar fidelidade à mão não escala. A equipe escreve um juiz —
# rubrica explícita, critério binário, saída estruturada — e, antes de
# usá-lo, mede a concordância dele com os rótulos humanos. Só os oito casos
# de CONSENSO entre os humanos servem de padrão (caso 05).
#
# Um juiz não validado produz números que sobem enquanto o sistema piora.
#
#     python 06-llm-as-judge.py          # ~10 chamadas curtas ao modelo

from pydantic import BaseModel, Field

from casos import ROTULOS_FIDELIDADE, RUBRICA_FIDELIDADE, VERSAO_RUBRICA
from cliente import MODELO, MODELO_JUIZ, PROVEDOR
from cliente import juiz as modelo_juiz
from metricas import concordancia, imprimir_matriz

LIMIAR = 0.85   # declarado antes de rodar


class Fidelidade(BaseModel):
    fiel: bool = Field(description="A resposta é fiel ao contexto?")
    afirmacao_nao_sustentada: str | None = Field(
        description="O trecho da resposta que o contexto não sustenta, ou null se for fiel.")


juiz = modelo_juiz.with_structured_output(Fidelidade)


def julgar(resposta: str, contexto: str) -> Fidelidade | None:
    try:
        return juiz.invoke([
            {"role": "system", "content": RUBRICA_FIDELIDADE},
            {"role": "user", "content": f"CONTEXTO:\n{contexto}\n\nRESPOSTA:\n{resposta}"},
        ])
    except Exception:
        return None   # saída fora do schema: medida perdida, contada à parte


print(f"[{PROVEDOR}:{MODELO}]  juiz: {PROVEDOR}:{MODELO_JUIZ}  rubrica v{VERSAO_RUBRICA}")
if MODELO_JUIZ == MODELO:
    print("  (juiz e sistema são o mesmo modelo: viés de auto-preferência não mitigado)")

vereditos = {r["id"]: julgar(r["resposta"], r["contexto"]) for r in ROTULOS_FIDELIDADE}

consenso = [r for r in ROTULOS_FIDELIDADE if r["humano_a"] == r["humano_b"]]
pares = [(r["id"], r["humano_a"], v.fiel if (v := vereditos[r["id"]]) else None)
         for r in consenso]
resultado = concordancia(pares)

print(f"\n1 — JUIZ × HUMANOS ({len(consenso)} casos de consenso)\n")
imprimir_matriz(resultado, ref="humano", aval="juiz")
m = resultado["matriz"]
print(f"  falsos positivos: {m['fp']}  (o juiz APROVA o que os humanos reprovam)")

print(f"\n  limiar declarado: {LIMIAR:.0%}   ->   "
      + ("ADOTAR" if resultado["taxa"] >= LIMIAR else "NÃO ADOTAR: corrigir rubrica ou juiz"))

print("\n2 — OS DESACORDOS, UM A UM")
for r in consenso:
    if r["id"] not in resultado["desacordos"]:
        continue
    v = vereditos[r["id"]]
    juiz_disse = "sem veredito" if v is None else "FIEL" if v.fiel else "NÃO FIEL"
    print(f"\n  {r['id']}  humano={'FIEL' if r['humano_a'] else 'NÃO FIEL'}  juiz={juiz_disse}")
    print(f"        {r['resposta']}")
    print(f"        gabarito: {r['nota']}")
    if v and v.afirmacao_nao_sustentada:
        print(f"        o juiz apontou: {v.afirmacao_nao_sustentada}")
if not resultado["desacordos"]:
    print("\n  nenhum")

print("\n3 — E NOS DOIS CASOS SEM PADRÃO (os humanos discordaram)")
for r in ROTULOS_FIDELIDADE:
    if r["humano_a"] != r["humano_b"]:
        v = vereditos[r["id"]]
        print(f"  {r['id']}  juiz: {'sem veredito' if v is None else 'FIEL' if v.fiel else 'NÃO FIEL'}   ({r['nota']})")

# O que o juiz disse no item 3 não é acerto nem erro: é a rubrica decidindo
# no lugar de quem não decidiu. Falso positivo é o desacordo caro — número
# errado aprovado vira parecer errado.
