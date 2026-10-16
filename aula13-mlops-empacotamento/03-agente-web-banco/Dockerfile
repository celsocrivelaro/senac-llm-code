# Aula 13 — A imagem do agente como API, com a política no banco.
#
# O mesmo Dockerfile de 02-agente-web: a imagem não sabe que existe um banco.
# O endereço dele chega em tempo de execução, por DATABASE_URL, e quem sobe
# o banco ao lado é o docker-compose.yml.
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
# Só os módulos da API, por nome. O script do banco NÃO entra aqui: ele é
# da imagem do Postgres, montado pelo compose.
COPY agente.py cliente.py api.py ./

# ---------------------------------------------------------------- 4
# O servidor, escutando em todas as interfaces do container.
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
