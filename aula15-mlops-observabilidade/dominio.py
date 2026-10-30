# Aula 15 — O domínio e as ferramentas do auditor de despesas.
#
# Os dados, o SYSTEM e as ferramentas que o `agente.py` usa. Nada aqui é
# telemetria: o domínio é o das aulas anteriores, e fica fora do agente
# para que o `agente.py` mostre só o grafo e os spans.

from __future__ import annotations

import json
import re

from langchain.tools import tool

POLITICA = {"refeicao": 120.00, "transporte": 250.00,
            "hospedagem": 480.00, "outros": 90.00}

REGULAMENTO = {
    "art-7":  "Art. 7º Refeição: teto de R$ 120,00, mediante nota fiscal.",
    "art-12": "Art. 12. Hospedagem: teto de R$ 480,00. §1º Capitais: R$ 620,00.",
    "art-19": "Art. 19. Viagem internacional: tetos acrescidos de 60%, vedada a cumulação.",
    "art-23": "Art. 23. Transporte por aplicativo: teto de R$ 250,00.",
}

DESPESAS = {
    "D-4612": {"categoria": "refeicao",   "valor": 138.00, "cidade": "Sao Paulo"},
    "D-4613": {"categoria": "hospedagem", "valor": 590.00, "cidade": "Lisboa"},
    "D-4614": {"categoria": "transporte", "valor":  96.00, "cidade": "Recife"},
    "D-4615": {"categoria": "refeicao",   "valor":  84.00, "cidade": "Sorocaba"},
}

SYSTEM = ("Você analisa despesas segundo a política vigente. Use as ferramentas antes de concluir. Termine com o veredito: aprovado, reprovado ou recusa.")


@tool
def consultar_despesa(despesa: str) -> str:
    """Dados de uma despesa pelo identificador (D + 4 dígitos).

    Args:
        despesa: O identificador da despesa, ex: D-4612
    """
    if despesa not in DESPESAS:
        return json.dumps({"erro": "despesa inexistente", "recebido": despesa})
    return json.dumps({"despesa": despesa, **DESPESAS[despesa]}, ensure_ascii=False)


@tool
def consultar_politica(categoria: str) -> str:
    """Teto de reembolso: refeicao, transporte, hospedagem, outros.

    Args:
        categoria: A categoria da despesa
    """
    if categoria not in POLITICA:
        return json.dumps({"erro": "categoria desconhecida",
                           "validos": sorted(POLITICA)}, ensure_ascii=False)
    return json.dumps({"categoria": categoria, "teto": POLITICA[categoria]})


@tool
def buscar_regulamento(consulta: str) -> str:
    """Recupera artigos do regulamento. Use para exceções.

    Args:
        consulta: O que procurar no regulamento
    """
    termos = set(consulta.lower().split())
    achados = [{"artigo": a, "texto": t} for a, t in REGULAMENTO.items()
               if termos & set(t.lower().split())]
    if not achados:
        return json.dumps({"recusa": "nada recuperado"}, ensure_ascii=False)
    return json.dumps(achados[:2], ensure_ascii=False)


FERRAMENTAS = [consultar_despesa, consultar_politica, buscar_regulamento]
FERRAMENTAS_POR_NOME = {f.name: f for f in FERRAMENTAS}


def extrair_veredito(texto: str) -> str:
    """O SYSTEM pede que a resposta termine com o veredito. Vale o último
    que aparecer; se nenhum aparecer, o veredito é `ausente` — e isso é
    medido, porque uma resposta sem veredito chega como `respondeu`."""
    achados = re.findall(r"\b(aprovado|reprovado|recusa)\b", texto.lower())
    return achados[-1] if achados else "ausente"
