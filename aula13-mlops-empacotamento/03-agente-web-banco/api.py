# Aula 13 — O agente como API, com a política no banco.
#
# A mesma API de `02-agente-web/`. O que muda é o ambiente em que ela roda:
# o docker compose sobe dois containers — o banco e esta API — e os liga
# numa rede própria.
#
#     docker compose up --build
#
#     curl localhost:8000/saude
#     curl -X POST localhost:8000/perguntas \
#          -H 'content-type: application/json' \
#          -d '{"pergunta": "A despesa D-4613 está dentro da política?"}'

from fastapi import FastAPI
from pydantic import BaseModel

from agente import banco_ok, rodar
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
    """Responde sem chamar o modelo: o processo está de pé, e o banco responde?"""
    return {"ok": True, "banco": banco_ok(), "modelo": f"{PROVEDOR}/{MODELO}"}
