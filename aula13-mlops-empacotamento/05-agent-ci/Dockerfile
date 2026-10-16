# Aula 13 — A imagem do agente como API, verificada, testada e publicada pelo CI.
#
# Os mesmos quatro blocos de 02-agente-web. O workflow em
# .github/workflows/ci.yml verifica este arquivo (hadolint e Trivy) antes de
# construir e publicar a imagem.
#
#     docker build -t agent-ci:dev .
#     docker run --rm -p 8000:8000 --env-file .env agent-ci:dev

# ---------------------------------------------------------------- 1
# Imagem base com versão FIXADA até o patch.
FROM python:3.11.13-slim-bookworm
WORKDIR /app

# ---------------------------------------------------------------- 2
# Dependências ANTES do código. Só o requirements.txt: o de testes
# (requirements-dev.txt) não entra na imagem.
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------------------------------------------------------------- 3
# Só os módulos da API, por nome. Os testes não entram na imagem.
COPY agente.py cliente.py api.py ./

# ---------------------------------------------------------------- 4
# O servidor, escutando em todas as interfaces do container.
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
