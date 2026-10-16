# Testes da API, sem chamar o modelo: o `rodar` é substituído por um dublê.

import api
from fastapi.testclient import TestClient

cliente = TestClient(api.app)


def test_saude_nao_chama_o_modelo():
    resposta = cliente.get("/saude")
    assert resposta.status_code == 200
    assert resposta.json()["ok"] is True


def test_pergunta_devolve_a_resposta_do_agente(monkeypatch):
    monkeypatch.setattr(api, "rodar", lambda pergunta: f"resposta para: {pergunta}")
    resposta = cliente.post("/perguntas", json={"pergunta": "D-4612?"})
    assert resposta.status_code == 200
    assert resposta.json() == {"pergunta": "D-4612?", "resposta": "resposta para: D-4612?"}


def test_pergunta_sem_corpo_e_rejeitada():
    assert cliente.post("/perguntas", json={}).status_code == 422
