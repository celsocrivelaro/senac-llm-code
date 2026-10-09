# AS FERRAMENTAS DO AGENTE — funções Python comuns, sem LangChain e sem modelo.
#
# Ficam num arquivo próprio para poderem ser testadas sozinhas
# (01-tool-unit-tests.py). O `sistema.py` as importa e as entrega ao agente
# com `tool(...)`, que lê a assinatura e a docstring de cada uma.
#
#     PARECERES                     o "mundo": o que o agente já escreveu

from casos import REGULAMENTO

# O estado do mundo. A avaliação de RESULTADO (caso 04) compara este
# dicionário antes e depois da execução.
PARECERES: dict[str, dict] = {}

VEREDITOS = ["aprovado", "reprovado", "recusa"]


def limpar_pareceres() -> None:
    PARECERES.clear()


def consultar_despesa(despesa: str) -> dict:
    """Dados de uma despesa pelo identificador (D + 4 dígitos).

    Args:
        despesa: O identificador da despesa, ex: D-4612
    """
    DESPESAS = {
        "D-4612": {"categoria": "refeicao",   "valor": 138.00, "cidade": "Sao Paulo", "internacional": False},
        "D-4613": {"categoria": "hospedagem", "valor": 590.00, "cidade": "Lisboa",    "internacional": True},
        "D-4614": {"categoria": "transporte", "valor":  96.00, "cidade": "Sao Paulo", "internacional": False},
        "D-4615": {"categoria": "refeicao",   "valor":  84.00, "cidade": "Campinas",  "internacional": False},
        "D-4616": {"categoria": "outros",     "valor": 210.00, "cidade": "Campinas",  "internacional": False},
        "D-4617": {"categoria": "hospedagem", "valor": 610.00, "cidade": "Recife",    "internacional": False},
        "D-4618": {"categoria": "hospedagem", "valor": 600.00, "cidade": "Brasilia",  "internacional": False},
    }
    if despesa not in DESPESAS:
        # DE PROPÓSITO mal descrito: não diz o que recebeu nem o que seria
        # válido. O caso 01 reprova esta mensagem.
        return {"erro": "despesa inexistente"}
    return {"despesa": despesa, **DESPESAS[despesa]}


def consultar_politica(categoria: str) -> dict:
    """Teto de reembolso de uma categoria: refeicao, transporte, hospedagem ou outros.

    Args:
        categoria: A categoria da despesa
    """
    POLITICA = {
        "refeicao":   {"teto": 120.00, "artigo": "art-7",  "exige_nota": True},
        "transporte": {"teto": 250.00, "artigo": "art-23", "exige_nota": True},
        "hospedagem": {"teto": 480.00, "artigo": "art-12", "exige_nota": True},
        "outros":     {"teto":  90.00, "artigo": None,     "exige_nota": True},
    }
    if categoria not in POLITICA:
        return {"erro": "categoria desconhecida", "recebido": categoria,
                "validos": sorted(POLITICA),
                "sugestao": "chame de novo com um dos valores de 'validos'"}
    return {"categoria": categoria, **POLITICA[categoria]}


def buscar_regulamento(consulta: str) -> dict | list[dict]:
    """Recupera artigos do regulamento. Use para exceções (capital, viagem internacional).

    Args:
        consulta: O que procurar no regulamento
    """
    termos = set(consulta.lower().replace("?", "").split())
    achados = []
    for artigo, texto in REGULAMENTO.items():
        palavras = set(texto.lower().replace(",", "").replace(".", "").split())
        # que fração das palavras da consulta aparece no artigo
        cobertura = len(termos & palavras) / max(len(termos), 1)
        if cobertura >= 0.4:   # portão da aula 07
            achados.append({"artigo": artigo, "texto": texto, "cobertura": round(cobertura, 2)})
    if not achados:
        return {"recusa": "nada recuperado acima do limiar",
                "sugestao": "reformule com termos do regulamento, ou recuse"}
    achados.sort(key=lambda a: a["cobertura"], reverse=True)
    return achados[:3]


def registrar_parecer(despesa: str, veredito: str, chave: str) -> dict:
    """Registra o parecer de uma despesa. Idempotente pela chave.

    Args:
        despesa: O identificador da despesa
        veredito: aprovado, reprovado ou recusa
        chave: Identificador estável do parecer; repetir a chave não cria outro
    """
    if veredito not in VEREDITOS:
        return {"erro": "veredito inválido", "recebido": veredito,
                "validos": VEREDITOS}
    if (existente := PARECERES.get(chave)):
        return {**existente, "ja_existia": True}
    parecer = {"parecer": f"P-{1000 + len(PARECERES)}", "despesa": despesa,
               "veredito": veredito}
    PARECERES[chave] = parecer
    return {**parecer, "ja_existia": False}
