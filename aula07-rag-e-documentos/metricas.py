# Aula 07 — As duas métricas do RAG, e a conferência de citação.
#
# As duas métricas medem metades distintas do pipeline e são mantidas
# separadas deliberadamente. Combiná-las num índice único de qualidade produz um
# número que não indica em qual componente intervir.
#
#   recall@k      a busca trouxe o trecho correto entre os k primeiros?
#                 Não envolve geração.
#
#   fidelidade    a resposta se apoia nos trechos recuperados?
#                 Exige uma chamada de avaliação por resposta.
#
# A terceira função do módulo não é métrica, e sim verificação:
# `citacao_verificavel` confere em código se cada fonte citada existe entre
# os trechos recuperados. A conferência é comparação de strings e não exige
# chamada ao modelo.

import json

from geracao import chamar, montar_contexto
from indice_chroma import IndiceChroma


def recall_at_k(indice: IndiceChroma, casos: list[dict], k: int = 3) -> dict:
    """A busca trouxe o trecho certo? Não envolve geração."""
    acertos, falhas = 0, []
    for caso in casos:
        trechos = indice.buscar(caso["pergunta"], k=k)
        artigos = [t["artigo"] for t in trechos]
        if _contem(artigos, caso["artigo"]):
            acertos += 1
        else:
            falhas.append({**caso, "veio": artigos})
    return {"acertos": acertos, "total": len(casos),
            "recall": acertos / len(casos), "falhas": falhas}


PROMPT_FIDELIDADE = """Verifique se a RESPOSTA se sustenta integralmente nos
TRECHOS fornecidos.

TRECHOS:
{contexto}

RESPOSTA:
{resposta}

Liste em `afirmacoes_sem_lastro` toda afirmação da resposta que não pode ser
verificada nos trechos. `sustentada` é true apenas se a lista estiver vazia.
Não avalie se a resposta é boa; avalie apenas se ela está nos trechos."""


def fidelidade(resposta: str, trechos: list[dict]) -> dict:
    """A resposta usou o que veio? É outra pergunta, e outro defeito."""
    bruto = chamar(
        [{"role": "user", "content": PROMPT_FIDELIDADE.format(
            contexto=montar_contexto(trechos), resposta=resposta)}],
        schema={"type": "object",
                "properties": {"sustentada": {"type": "boolean"},
                               "afirmacoes_sem_lastro": {
                                   "type": "array",
                                   "items": {"type": "string"}}},
                "required": ["sustentada", "afirmacoes_sem_lastro"],
                "additionalProperties": False},
        nome="fidelidade")
    return json.loads(bruto)


def citacao_verificavel(fontes: list[str], trechos: list[dict]) -> dict:
    """A fonte citada existe entre os trechos recuperados?

    Verificação DETERMINÍSTICA, em código. Se o programa não consegue
    conferir a citação, ela não vale nada.
    """
    disponiveis = [t["artigo"] for t in trechos]
    validas = [f for f in fontes if _contem(disponiveis, f)]
    return {"citadas": fontes, "disponiveis": disponiveis,
            "validas": validas,
            "inventadas": [f for f in fontes if f not in validas]}


def _contem(artigos: list[str], alvo: str) -> bool:
    n = _normalizar(alvo)
    return any(n in _normalizar(a) or _normalizar(a) in n for a in artigos)


def _normalizar(s: str) -> str:
    return (s.replace("º", "").replace(".", "").replace(" ", "")
             .replace("§", "p").lower())
