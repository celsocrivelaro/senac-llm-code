# Aula 13 — O agente como API HTTP.
#
# CASO DE USO: dado o agente da linha de comando, deixá-lo disponível para
# outro programa, que envia a pergunta por HTTP e recebe a resposta.
#
# O desenho é o mais simples possível: requisição e resposta SÍNCRONAS — a
# conexão fica aberta enquanto o agente trabalha. Serve a um agente de
# poucos passos, como este. Para execuções que levam minutos, nenhum
# intermediário HTTP espera, e a entrega passa a ser por fila, webhook ou
# SSE (nota da aula, seção sobre atender por rede).
#
#     uvicorn api:app --port 8000
#
#     curl -X POST localhost:8000/perguntas \
#          -H 'content-type: application/json' \
#          -d '{"pergunta": "A despesa D-4613 está dentro da política?"}'
#
# O nome do arquivo é `api.py`, e não `02-api.py`: o uvicorn IMPORTA o
# módulo pelo nome, e um nome que começa por dígito não é identificador
# Python válido.

from fastapi import FastAPI
from pydantic import BaseModel

from agente import rodar
from cliente import MODELO, PROVEDOR

app = FastAPI(title="auditor-de-despesas")


class Pergunta(BaseModel):
    pergunta: str


@app.post("/perguntas")
def perguntar(pedido: Pergunta) -> dict:
    """Recebe a pergunta, executa o agente e devolve a resposta."""
    return {"pergunta": pedido.pergunta, "resposta": rodar(pedido.pergunta)}


@app.get("/saude")
def saude() -> dict:
    """Responde sem chamar o modelo: diz que o processo está de pé, e com qual modelo."""
    return {"ok": True, "modelo": f"{PROVEDOR}/{MODELO}"}
