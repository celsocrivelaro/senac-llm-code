# Aula 13 — O agente como API, a imagem que o CI publica.
#
#     uvicorn api:app --port 8000

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
