# Aula 08 — A LEITURA: a seleção do fato vigente.
#
# A recuperação devolve candidatos, e uma decisão permanece: dois fatos
# contraditórios voltaram — qual está vigente?
#
# A resposta é regra determinística, `max()` sobre o carimbo de tempo.
# Delegá-la ao modelo tem três desvantagens: a decisão passa a errar, consome
# uma chamada, e deixa de ser testável.


def mais_recente(candidatos: list[dict], campo: str = "data") -> dict | None:
    return max(candidatos, key=lambda c: c[campo]) if candidatos else None


def desempatar_por_tempo(recuperados: list[dict]) -> dict:
    """Devolve o vencedor e o que foi descartado, para o log registrar.

    O descarte é registrado porque um agente que ignora silenciosamente um
    fato contraditório é indistinguível, no log, de um que nunca o
    recuperou."""
    vencedor = mais_recente(recuperados)
    return {"vigente": vencedor,
            "descartados": [r for r in recuperados if r is not vencedor]}
