# Aula 13 — A imagem do agente como API.
#
# Os blocos 1 a 3 são os mesmos de 01-agente-cli/Dockerfile. Muda o bloco 4:
# em vez de um programa que roda e termina, um servidor que fica de pé
# escutando uma porta.
#
#     docker build -t auditor-de-despesas-web:1.0.0 .
#     docker run --rm -p 8000:8000 --env-file .env auditor-de-despesas-web:1.0.0

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
COPY agente.py cliente.py api.py ./

# ---------------------------------------------------------------- 4
# O servidor. `--host 0.0.0.0` é obrigatório: com o padrão 127.0.0.1, o
# uvicorn escuta só dentro do container, e o `-p 8000:8000` do `docker run`
# não alcança nada. EXPOSE apenas documenta a porta; quem a abre para fora
# é o `-p`.
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
