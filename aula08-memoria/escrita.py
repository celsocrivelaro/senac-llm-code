# Aula 08 — A ESCRITA EM MEMÓRIA.
#
# São três as políticas de escrita, e este módulo implementa a segunda:
#
#   o agente decide   uma decisão por passo; grava o irrelevante
#   o código extrai   uma chamada por execução; não grava o que o schema
#                     não previu
#   o humano corrige  a mais confiável; não escala
#
# Gravar memória é uma operação de ESCRITA, e portanto está sujeita à
# fronteira leitura/escrita da aula 01 (§3) e à chave de idempotência da aula
# 05 (nota 02 §8). É por essa razão que `MemoriaSemantica.gravar` deriva o id
# do conteúdo do fato, e não da tentativa de gravação.
#
# Esta é a única chamada de geração de texto da aula, o que explica `_chamar`
# residir neste módulo em vez de num `geracao.py` próprio.

import json
import time

from openai import APIConnectionError, RateLimitError

from cliente import MODELO, client


def _chamar(prompt: str, schema: dict | None = None, nome: str = "saida",
            tentativas: int = 5) -> str:
    for tentativa in range(tentativas):
        try:
            kwargs = dict(model=MODELO, temperature=0,
                          messages=[{"role": "user", "content": prompt}])
            if schema:
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {"name": nome, "schema": schema,
                                    "strict": True}}
            r = client.chat.completions.create(**kwargs)
            break
        except (RateLimitError, APIConnectionError):
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)
    return r.choices[0].message.content


SCHEMA_EXTRACAO = {
    "type": "object",
    "properties": {
        "fatos": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string",
                         "enum": ["episodica", "semantica", "procedural",
                                  "nao_guardar"]},
                "conteudo": {"type": "string"},
            },
            "required": ["tipo", "conteudo"],
            "additionalProperties": False}},
    },
    "required": ["fatos"],
    "additionalProperties": False,
}

PROMPT_EXTRACAO = """A execução abaixo terminou. Classifique cada informação
que ela produziu para decidir o que sobrevive a ela.

TIPOS:
- episodica: o que aconteceu e quando, com identificadores
- semantica: fato estável sobre uma entidade (funcionário, categoria)
- procedural: regra de como agir, aplicável a execuções futuras
- nao_guardar: ruído de execução — latência, contagem de tokens, número de
  passos, tentativas descartadas

PRESERVE OBRIGATORIAMENTE como `episodica` toda AÇÃO DE ESCRITA executada,
com o identificador que ela devolveu (ex: "registrou o parecer P-1188 para
a despesa D-4612"). Perder essa informação faz o agente repetir a escrita
numa execução futura — é a mesma exigência do prompt de compaction da
aula 05, aqui entre execuções em vez de dentro de uma.

A maior parte do que uma execução produz é `nao_guardar`. Não force
classificação: memória cheia de ruído é pior que memória vazia, porque o
ruído compete por espaço na janela.

EXECUÇÃO:
{execucao}"""


def extrair_pelo_codigo(execucao: str) -> list[dict]:
    """Política 2: o CÓDIGO extrai, num passo sobre o resultado final.

    Custo: uma chamada por execução. Previsível, e perde o que a extração
    não previu."""
    bruto = _chamar(PROMPT_EXTRACAO.format(execucao=execucao),
                    schema=SCHEMA_EXTRACAO, nome="extracao")
    return json.loads(bruto)["fatos"]
