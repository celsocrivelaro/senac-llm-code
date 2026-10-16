# Aula 13 — A API do agente completo.
#
# Toda requisição traz QUEM pergunta e EM QUAL CONVERSA, nos cabeçalhos:
#
#     X-Usuario-Id: ana
#     X-Sessao-Id: viagem-lisboa
#
# Num sistema real, o usuário vem de autenticação (um token verificado), e
# não de um cabeçalho que o cliente escreve livremente. Aqui o cabeçalho
# faz o papel dessa identidade, para que o isolamento fique visível.
#
#     docker compose up --build
#
#     curl -X POST localhost:8000/perguntas \
#          -H 'content-type: application/json' \
#          -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s1' \
#          -d '{"pergunta": "A despesa D-4613 está dentro da política?"}'
#
#     curl localhost:8000/memoria -H 'X-Usuario-Id: ana' -H 'X-Sessao-Id: s1'

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

import dados
import memoria
from agente import rodar
from cliente import MODELO, PROVEDOR

app = FastAPI(title="auditor-de-despesas")


class Pergunta(BaseModel):
    pergunta: str


def _identidade(usuario: str, sessao: str | None = None) -> tuple[str, str | None]:
    try:
        return memoria.validar(usuario), (memoria.validar(sessao) if sessao is not None else None)
    except ValueError as erro:
        raise HTTPException(400, str(erro)) from erro


@app.post("/perguntas")
def perguntar(pedido: Pergunta, x_usuario_id: str = Header(), x_sessao_id: str = Header()) -> dict:
    """Executa o agente para este usuário, nesta sessão."""
    usuario, sessao = _identidade(x_usuario_id, x_sessao_id)
    return {"usuario": usuario, "sessao": sessao, **rodar(usuario, sessao, pedido.pergunta)}


@app.get("/memoria")
def ver_memoria(x_usuario_id: str = Header(), x_sessao_id: str = Header()) -> dict:
    """O que o agente lembra: o histórico DESTA sessão e os fatos DESTE usuário."""
    usuario, sessao = _identidade(x_usuario_id, x_sessao_id)
    return {"usuario": usuario, "sessao": sessao, "historico": memoria.historico(usuario, sessao), "fatos": memoria.fatos(usuario)}


@app.delete("/memoria/sessao")
def esquecer_sessao(x_usuario_id: str = Header(), x_sessao_id: str = Header()) -> dict:
    usuario, sessao = _identidade(x_usuario_id, x_sessao_id)
    return {"apagada": memoria.esquecer_sessao(usuario, sessao)}


@app.delete("/memoria")
def esquecer_usuario(x_usuario_id: str = Header()) -> dict:
    """Apaga tudo o que o agente guarda do usuário: fatos e todas as sessões."""
    usuario, _ = _identidade(x_usuario_id)
    return {"chaves_apagadas": memoria.esquecer_usuario(usuario)}


@app.get("/saude")
def saude() -> dict:
    """Responde sem chamar o modelo: o processo, o banco e a memória."""
    return {"ok": True, "banco": dados.ok(), "memoria": memoria.ok(), "modelo": f"{PROVEDOR}/{MODELO}"}
