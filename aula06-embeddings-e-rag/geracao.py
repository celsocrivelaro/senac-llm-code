# Aula 06 — A geração.
#
# A METADE QUE FALTAVA. As partes 1 a 3 desta aula constroem um buscador
# inteiro sem chamar o modelo generativo uma única vez; aqui os trechos
# recuperados viram resposta, e é isso que fecha o RAG.
#
# É um prompt só, deliberadamente. O contrato de saída — o campo `fontes`, a
# recusa quando nada serve, a citação conferida em código — é assunto da
# aula 07. Aqui o escopo é a última etapa do pipeline, isolada.

from cliente import MODELO, client


def chamar(mensagens: list[dict], temperatura: float = 0) -> str:
    """Uma chamada de geração, e só. Se a API recusar, o script para e
    mostra o erro dela."""
    r = client.chat.completions.create(
        model=MODELO, messages=mensagens, temperature=temperatura)
    return r.choices[0].message.content


def montar_contexto(trechos: list[dict]) -> str:
    """Os trechos recuperados viram contexto. Cada um vem ROTULADO com o
    artigo — e é o rótulo que a aula 07 transforma em citação verificável."""
    return "\n\n".join(f"[{t['artigo']}]\n{t['texto'].strip()}"
                       for t in trechos)


PROMPT_RAG = """Responda a pergunta do colaborador usando EXCLUSIVAMENTE os
trechos da política de reembolso abaixo. Se os trechos não contiverem a
informação necessária, diga isso em vez de responder assim mesmo.

TRECHOS:
{contexto}

PERGUNTA: {pergunta}"""


def responder(pergunta: str, trechos: list[dict]) -> str:
    """A última etapa: contexto + pergunta -> texto."""
    return chamar([{"role": "user",
                    "content": PROMPT_RAG.format(
                        contexto=montar_contexto(trechos),
                        pergunta=pergunta)}])
