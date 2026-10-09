# RUBRIC SCORING — qual de duas respostas de atendimento vai para o chatbot?
#
# A TÉCNICA: julgar contra critérios explícitos, cada um sim ou não.
#
# Com os dois vieses do juiz: POSIÇÃO e COMPRIMENTO.
#
# O CASO: a loja tem duas versões de resposta para seis situações de
# atendimento e precisa escolher qual entra no chatbot. Não há gabarito —
# "boa resposta" é tom, correção, não prometer demais, dizer o próximo
# passo. A equipe usa um juiz, e mede três coisas:
#
#   1. a rubrica por DIMENSÃO, cada uma sim/não, sem tirar média
#      (modelo é ruim dando nota e bom respondendo sim ou não);
#   2. a comparação por PARES, nas duas ordens — se trocar A e B de lugar
#      muda o veredito, o juiz está escolhendo a posição;
#   3. a melhor resposta contra a pior INFLADA — mesmo conteúdo, o dobro de
#      texto. Se a inflada passa a ganhar, o juiz premia comprimento.
#
#     python 07-rubric-scoring.py          # ~36 chamadas curtas ao modelo

from typing import Literal

from pydantic import BaseModel, Field

from atendimento import DIMENSOES, POLITICA_LOJA, SITUACOES
from sistema import MODELO, PROVEDOR, sistema

print(f"[{PROVEDOR}:{MODELO}]")


# --------------------------------------------------------- 1. dimensões
class Rubrica(BaseModel):
    correcao: bool = Field(description=DIMENSOES["correcao"])
    tom: bool = Field(description=DIMENSOES["tom"])
    seguranca: bool = Field(description=DIMENSOES["seguranca"])
    resolve: bool = Field(description=DIMENSOES["resolve"])


juiz_rubrica = sistema.with_structured_output(Rubrica)


def pontuar(pergunta: str, resposta: str) -> Rubrica | None:
    try:
        return juiz_rubrica.invoke(
            f"Política da loja: {POLITICA_LOJA}\n\nPergunta do cliente: {pergunta}\n\n"
            f"Resposta do atendimento: {resposta}\n\nResponda sim ou não a cada critério.")
    except Exception:
        return None


print("\n1 — RUBRICA POR DIMENSÃO (S = sim, - = não, ? = sem veredito)\n")
print(f"  {'':<10}" + "".join(f"{d:>11}" for d in DIMENSOES) + "   melhor")
for s in SITUACOES:
    for lado in ("a", "b"):
        nota = pontuar(s["pergunta"], s[f"resposta_{lado}"])
        celulas = [("?" if nota is None else "S" if getattr(nota, d) else "-") for d in DIMENSOES]
        print(f"  {s['id']} {lado.upper():<5}" + "".join(f"{c:>11}" for c in celulas)
              + ("      *" if s["melhor"] == lado else ""))

# Uma resposta com tom "S" e segurança "-" não é uma resposta "média": é
# uma resposta que promete o que a loja não cumpre. Média entre dimensões
# esconde exatamente isso.


# ------------------------------------------------------------ 2. pares
class Preferencia(BaseModel):
    melhor: Literal["1", "2"] = Field(description="Qual resposta atende melhor o cliente, 1 ou 2?")


juiz_pares = sistema.with_structured_output(Preferencia)


def vencedora(pergunta: str, r1: str, r2: str) -> str | None:
    """Pergunta ao juiz qual das duas respostas é melhor, e devolve o TEXTO
    da escolhida — r1 ou r2 —, ou None se o juiz não respondeu."""
    try:
        escolha = juiz_pares.invoke(
            f"Política da loja: {POLITICA_LOJA}\n\nPergunta do cliente: {pergunta}\n\n"
            f"Resposta 1: {r1}\n\nResposta 2: {r2}\n\nQual resposta atende melhor o cliente?").melhor
    except Exception:
        return None
    return r1 if escolha == "1" else r2


def venceu(ok: bool) -> str:
    return "venceu" if ok else "perdeu"


print("\n2 — POR PARES, NAS DUAS ORDENS (viés de posição)\n")
inversoes, acertos = 0, 0
for s in SITUACOES:
    melhor = s[f"resposta_{s['melhor']}"]
    pior = s["resposta_b" if s["melhor"] == "a" else "resposta_a"]
    # A mesma pergunta duas vezes, trocando só a ordem das respostas.
    melhor_em_1 = vencedora(s["pergunta"], melhor, pior) == melhor
    melhor_em_2 = vencedora(s["pergunta"], pior, melhor) == melhor
    inverteu = melhor_em_1 != melhor_em_2
    inversoes += inverteu
    acertos += melhor_em_1 + melhor_em_2
    print(f"  {s['id']}  a melhor, na posição 1: {venceu(melhor_em_1)}"
          f"   na posição 2: {venceu(melhor_em_2)}"
          + ("   <- INVERTEU" if inverteu else ""))
print(f"\n  acerto: {acertos}/{2 * len(SITUACOES)}   inversões: {inversoes}/{len(SITUACOES)}")


# ------------------------------------------------------- 3. comprimento
print("\n3 — A MELHOR CONTRA A PIOR INFLADA (viés de comprimento)\n")
vitorias_inflada = 0
for s in SITUACOES:
    melhor = s[f"resposta_{s['melhor']}"]
    inflada = s["resposta_inflada"]
    ganhou = ((vencedora(s["pergunta"], melhor, inflada) == inflada)
              + (vencedora(s["pergunta"], inflada, melhor) == inflada))
    vitorias_inflada += ganhou
    print(f"  {s['id']}  {len(melhor):>4} contra {len(inflada):>4} caracteres"
          f"   a inflada venceu {ganhou}/2")
print(f"\n  a inflada venceu {vitorias_inflada}/{2 * len(SITUACOES)}   (compare com o item 2, onde a mesma resposta era curta)")

# Inversão de ordem e vitória da inflada medem o JUIZ, não as respostas. Com
# qualquer uma acima de zero, o veredito por pares só vale nas duas ordens.
