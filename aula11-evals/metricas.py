# As métricas, escritas à mão. Nenhuma chama modelo.
#
# Estão aqui para que o mecanismo fique visível antes de virar dependência:
# o caso 09 refaz duas delas com `agentevals` e `openevals`, e o aluno
# consegue dizer o que a biblioteca faz porque já escreveu a versão curta.

from __future__ import annotations

import hashlib


# ------------------------------------------------------- determinístico

def extrair_veredito(resposta: str) -> str | None:
    texto = (resposta or "").lower()
    if "não é possível" in texto or "nao e possivel" in texto or "recusa" in texto:
        return "recusa"
    for v in ("reprovado", "aprovado"):
        if v in texto:
            return v
    return None


def nivel_deterministico(trace, caso: dict) -> dict:
    esperado = caso["esperado"]
    obtido = extrair_veredito(trace.resposta)
    contexto = " ".join(trace.contexto)
    return {
        "veredito_correto": obtido == esperado["veredito"],
        "veredito_obtido": obtido,
        # o artigo esperado precisa estar no que as ferramentas DEVOLVERAM,
        # e não só parecer plausível na resposta (aula 07)
        "citacao_verificavel": esperado["cita"] is None or esperado["cita"] in contexto,
    }


# ------------------------------------------------------------ trajetória

def e_subsequencia(esperado: list[str], obtido: list[str]) -> bool:
    it = iter(obtido)
    return all(f in it for f in esperado)


def nivel_trajetoria(trace, caso: dict) -> dict:
    esperado = caso["esperado"]["ferramentas"]
    obtido = [p["ferramenta"] for p in trace.passos]
    return {
        "obtido": obtido,
        "cobertura": len(set(esperado) & set(obtido)) / len(esperado) if esperado else 1.0,
        "superfluas": [f for f in obtido if f not in esperado],
        "ordem_ok": e_subsequencia(esperado, obtido),
        "argumentos_invalidos": [p["ferramenta"] for p in trace.passos if p["erro"]],
    }


# ------------------------------------------------------------- resultado

def nivel_resultado(antes: dict, depois: dict, caso: dict) -> dict:
    """O estado do mundo, não a prosa: quantos pareceres a execução criou."""
    criados = len([k for k in depois if k not in antes])
    esperados = caso["esperado"]["pareceres_criados"]
    return {"criados": criados, "esperados": esperados,
            "correto": criados == esperados,
            "duplicado": criados > esperados,
            "ausente": criados < esperados}


def passou(r: dict) -> bool:
    """Aprovação de um caso. Não usa juiz: juiz mede o que não tem
    gabarito, e não decide aprovação."""
    return (r["deterministico"]["veredito_correto"]
            and r["deterministico"]["citacao_verificavel"]
            and r["resultado"]["correto"])


# ------------------------------------------------------------- repetição

def pass_at_k(acertos: int, total: int) -> float:
    return acertos / total if total else 0.0


def pass_pow_k(acertos: int, total: int, k: int) -> float:
    """Probabilidade de acertar as k vezes, supondo independência."""
    return pass_at_k(acertos, total) ** k


# ----------------------------------------------------------- concordância

def concordancia(pares: list[tuple]) -> dict:
    """`pares` = [(id, referência, avaliado), ...] com valores booleanos.

    Serve a humano x humano (05) e a juiz x humano (06, 09). `None` no
    avaliado — juiz que não devolveu veredito — fica fora da matriz e é
    contado à parte."""
    matriz = {"vp": 0, "fp": 0, "vn": 0, "fn": 0}
    desacordos, sem_veredito = [], []
    for id_, ref, aval in pares:
        if aval is None:
            sem_veredito.append(id_)
            continue
        chave = ("v" if ref == aval else "f") + ("p" if aval else "n")
        matriz[chave] += 1
        if ref != aval:
            desacordos.append(id_)
    total = sum(matriz.values())
    return {"matriz": matriz, "total": total,
            "taxa": (matriz["vp"] + matriz["vn"]) / total if total else 0.0,
            "desacordos": desacordos, "sem_veredito": sem_veredito}


def imprimir_matriz(c: dict, ref: str, aval: str) -> None:
    m = c["matriz"]
    print(f"                    {ref}: FIEL   {ref}: NÃO FIEL")
    print(f"  {aval + ': FIEL':<18} {m['vp']:>8} {m['fp']:>14}")
    print(f"  {aval + ': NÃO FIEL':<18} {m['fn']:>8} {m['vn']:>14}")
    print(f"\n  concordância {m['vp'] + m['vn']}/{c['total']} ({c['taxa']:.0%})"
          + (f"   sem veredito: {c['sem_veredito']}" if c["sem_veredito"] else ""))


# --------------------------------------------------------------- holdout

def particao(caso_id: str, fracao_holdout: float = 0.3) -> str:
    """'holdout' ou 'desenvolvimento', decidido pelo hash do id.

    `hash()` do Python muda a cada processo; o SHA-256 não. A divisão
    precisa ser a mesma hoje e daqui a um mês, ou o holdout vaza."""
    balde = int(hashlib.sha256(caso_id.encode()).hexdigest(), 16) % 100
    return "holdout" if balde < fracao_holdout * 100 else "desenvolvimento"
