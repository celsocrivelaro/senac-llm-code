# Aula 13 — A imagem do agente.
#
# O contexto de build é ESTA PASTA:
#
#     docker build -t auditor-de-despesas:1.0.0 .
#
# No Dockerfile, comentário só vale em linha própria. Um `#` no fim de uma
# instrução vira argumento dela.

# ---------------------------------------------------------------- 1
# Imagem base com versão FIXADA até o patch. `python:3.11-slim` é uma
# etiqueta móvel: a mesma linha produz imagens diferentes em dias diferentes.
FROM python:3.11.13-slim-bookworm
WORKDIR /app

# ---------------------------------------------------------------- 2
# Dependências ANTES do código. A instalação é a camada mais cara, e o
# código é o que muda a cada commit: com o requirements.txt copiado sozinho,
# mudar uma linha do agente reaproveita esta camada do cache.
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------------------------------------------------------------- 3
# Só os módulos do agente, por nome. Um `COPY . .` dependeria apenas do
# .dockerignore para manter o .env fora da imagem; a lista explícita é a
# segunda barreira.
COPY agente.py cliente.py ./

# ---------------------------------------------------------------- 4
# ENTRYPOINT fixa o programa; os argumentos do `docker run` viram o objetivo.
# NENHUM SEGREDO AQUI: a chave chega em tempo de execução, por
# `docker run --env-file .env`.
ENTRYPOINT ["python", "agente.py"]
