# Aula 07 — A geração.
#
# É a metade que a aula 06 não implementava: lá o pipeline terminava nos
# trechos recuperados; aqui eles são convertidos em resposta. Os modos de
# falha 2 e 3 do script 05 ocorrem nesta etapa e não existem sem um modelo
# gerando texto.
#
# O módulo expõe dois prompts. O primeiro pede a resposta em texto livre. O
# segundo impõe um contrato de saída com os campos `fontes` e `suficiente`,
# construído no script 06. A diferença operacional entre eles é que o
# segundo produz uma saída conferível em código.

import json
import time

from openai import APIConnectionError, RateLimitError

from cliente import MODELO, client
from consumo import registrar_geracao
from dados import SCHEMA_RESPOSTA


def chamar(mensagens, schema=None, nome="resposta", temperatura=0,
           tentativas=5):
    """A chamada de geração, com o mesmo retry usado no embedding.

    A função é pública porque `metricas.py` também a utiliza: a fidelidade é
    avaliada por um modelo, e essa avaliação é uma geração como qualquer
    outra — inclusive para efeito de contabilização de consumo.
    """
    formato = ({"type": "json_schema",
                "json_schema": {"name": nome, "schema": schema, "strict": True}}
               if schema else None)
    for tentativa in range(tentativas):
        try:
            kwargs = dict(model=MODELO, messages=mensagens,
                          temperature=temperatura)
            if formato:
                kwargs["response_format"] = formato
            r = client.chat.completions.create(**kwargs)
            break
        except (RateLimitError, APIConnectionError):
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)

    registrar_geracao(r.usage.prompt_tokens, r.usage.completion_tokens)
    return r.choices[0].message.content


def montar_contexto(trechos: list[dict]) -> str:
    """Os trechos recuperados viram contexto. Cada um vem ROTULADO com o
    artigo — é o rótulo que torna a citação verificável depois."""
    return "\n\n".join(f"[{t['artigo']}]\n{t['texto'].strip()}" for t in trechos)


PROMPT_INGENUO = """Responda a pergunta do colaborador usando os trechos da
política de reembolso abaixo.

TRECHOS:
{contexto}

PERGUNTA: {pergunta}"""


PROMPT_COM_CONTRATO = """Responda a pergunta do colaborador usando EXCLUSIVAMENTE
os trechos da política de reembolso abaixo.

TRECHOS:
{contexto}

PERGUNTA: {pergunta}

Responda no schema, observando:
- `fontes`: os rótulos entre colchetes dos trechos efetivamente usados na
  resposta, exatamente como aparecem. Não invente rótulo.
- `suficiente`: false quando os trechos não contêm a informação necessária
  para responder. Nesse caso `resposta` diz o que falta, e não tenta
  responder assim mesmo.

Não use conhecimento que não esteja nos trechos. Não conclua além do que
os trechos permitem."""


def responder(pergunta: str, trechos: list[dict],
              com_contrato: bool = True) -> dict:
    """O quarto passo do pipeline. Com contrato, devolve o dicionário do
    schema; sem contrato, devolve texto livre. A comparação entre as duas
    saídas é o objeto do script 06."""
    contexto = montar_contexto(trechos)
    if not com_contrato:
        texto = chamar([{"role": "user", "content": PROMPT_INGENUO.format(
            contexto=contexto, pergunta=pergunta)}])
        return {"resposta": texto, "fontes": [], "suficiente": None}

    bruto = chamar(
        [{"role": "user", "content": PROMPT_COM_CONTRATO.format(
            contexto=contexto, pergunta=pergunta)}],
        schema=SCHEMA_RESPOSTA, nome="resposta_com_fonte")
    return json.loads(bruto)
