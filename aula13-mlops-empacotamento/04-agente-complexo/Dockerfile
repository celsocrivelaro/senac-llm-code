# Aula 13 — A imagem do agente completo.
#
# Os mesmos quatro blocos das pastas anteriores. A imagem não sabe que
# existem um banco e um Redis: os endereços chegam em tempo de execução, por
# DATABASE_URL e REDIS_URL, e quem os sobe ao lado é o docker-compose.yml.
#
#     docker compose up --build

# ---------------------------------------------------------------- 1
# Imagem base com versão FIXADA até o patch.
FROM python:3.11.13-slim-bookworm
WORKDIR /app

# ---------------------------------------------------------------- 2
# Dependências ANTES do código.
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------------------------------------------------------------- 3
# Só os módulos da API, por nome.
COPY agente.py api.py cliente.py dados.py memoria.py ./

# ---------------------------------------------------------------- 4
# O servidor, escutando em todas as interfaces do container.
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
