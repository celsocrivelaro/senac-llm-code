# AS FERRAMENTAS DO AGENTE — funções Python comuns, sem LangChain e sem modelo.
#
# Ficam num arquivo próprio para poderem ser testadas sozinhas
# (01-tool-unit-tests.py). O `sistema.py` as importa e as entrega ao agente
# com `tool(...)`, que lê a assinatura e a docstring de cada uma.
#
#     PARECERES                     o "mundo": o que o agente já escreveu

import json

from casos import DESPESAS, POLITICA, REGULAMENTO

# O estado do mundo. A avaliação de RESULTADO (caso 04) compara este
# dicionário antes e depois da execução.
PARECERES: dict[str, dict] = {}

VEREDITOS = ["aprovado", "reprovado", "recusa"]


def limpar_pareceres() -> None:
    PARECERES.clear()


def _json(dados) -> str:
    return json.dumps(dados, ensure_ascii=False)


def consultar_despesa(despesa: str) -> str:
    """Dados de uma despesa pelo identificador (D + 4 dígitos).

    Args:
        despesa: O identificador da despesa, ex: D-4612
    """
    if despesa not in DESPESAS:
        # DE PROPÓSITO mal descrito: não diz o que recebeu nem o que seria
        # válido. O caso 01 reprova esta mensagem.
        return _json({"erro": "despesa inexistente"})
    return _json({"despesa": despesa, **DESPESAS[despesa]})


def consultar_politica(categoria: str) -> str:
    """Teto de reembolso de uma categoria: refeicao, transporte, hospedagem ou outros.

    Args:
        categoria: A categoria da despesa
    """
    if categoria not in POLITICA:
        return _json({"erro": "categoria desconhecida", "recebido": categoria,
                      "validos": sorted(POLITICA),
                      "sugestao": "chame de novo com um dos valores de 'validos'"})
    return _json({"categoria": categoria, **POLITICA[categoria]})


def _busca(consulta: str, k: int = 3) -> list[dict]:
    termos = set(consulta.lower().split())
    pontuados = [{"artigo": a, "texto": t,
                  "distancia": 1 - len(termos & set(t.lower().split())) / max(len(termos), 1)}
                 for a, t in REGULAMENTO.items()]
    pontuados.sort(key=lambda d: d["distancia"])
    return pontuados[:k]


def buscar_regulamento(consulta: str) -> str:
    """Recupera artigos do regulamento. Use para exceções (capital, viagem internacional).

    Args:
        consulta: O que procurar no regulamento
    """
    resultados = _busca(consulta)
    if not resultados or resultados[0]["distancia"] > 0.6:   # portão da aula 07
        return _json({"recusa": "nada recuperado acima do limiar",
                      "sugestao": "reformule com termos do regulamento, ou recuse"})
    return _json(resultados)


def registrar_parecer(despesa: str, veredito: str, chave: str) -> str:
    """Registra o parecer de uma despesa. Idempotente pela chave.

    Args:
        despesa: O identificador da despesa
        veredito: aprovado, reprovado ou recusa
        chave: Identificador estável do parecer; repetir a chave não cria outro
    """
    if veredito not in VEREDITOS:
        return _json({"erro": "veredito inválido", "recebido": veredito,
                      "validos": VEREDITOS})
    if (existente := PARECERES.get(chave)):
        return _json({**existente, "ja_existia": True})
    parecer = {"parecer": f"P-{1000 + len(PARECERES)}", "despesa": despesa,
               "veredito": veredito}
    PARECERES[chave] = parecer
    return _json({**parecer, "ja_existia": False})
