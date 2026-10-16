# Aula 13 — A gestão de memória, no Redis.
#
# Duas memórias, com políticas diferentes:
#
#   CURTO PRAZO — o histórico da SESSÃO. Chave `sessao:{usuario}:{sessao}`,
#   uma lista de mensagens. Guarda só os turnos (pergunta do usuário e
#   resposta final), e não as chamadas de ferramenta. Tem JANELA (só as
#   últimas N mensagens ficam) e EXPIRA (a sessão parada some sozinha).
#
#   LONGO PRAZO — os FATOS do usuário, que valem entre sessões. Chave
#   `fatos:{usuario}`, uma lista curta. Só o agente escreve, por uma
#   ferramenta, e só o que o usuário declarou sobre si.
#
# O ISOLAMENTO está no nome da chave: o usuário e a sessão vêm do cabeçalho
# da requisição, validados, e entram na chave. Nenhuma função aqui recebe
# uma chave pronta, e o modelo nunca escolhe de quem é a memória que lê.

import json
import os
import re

import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# A janela e o prazo são parâmetros de produto, e não constantes mágicas.
JANELA_MENSAGENS = int(os.environ.get("JANELA_MENSAGENS", "20"))
SESSAO_TTL_S = int(os.environ.get("SESSAO_TTL_S", "3600"))
MAX_FATOS = int(os.environ.get("MAX_FATOS", "10"))

# Identificador aceito: letras, dígitos, `-` e `_`. Sem isso, um `:` no
# identificador escreveria na chave de outro usuário.
IDENTIFICADOR = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

conexao = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def validar(identificador: str) -> str:
    if not IDENTIFICADOR.fullmatch(identificador or ""):
        raise ValueError(f"identificador inválido: {identificador!r}")
    return identificador


def _chave_sessao(usuario: str, sessao: str) -> str:
    return f"sessao:{validar(usuario)}:{validar(sessao)}"


def _chave_fatos(usuario: str) -> str:
    return f"fatos:{validar(usuario)}"


# ---------------------------------------------------------- curto prazo

def historico(usuario: str, sessao: str) -> list[dict]:
    """As mensagens da sessão, da mais antiga à mais recente."""
    return [json.loads(m) for m in conexao.lrange(_chave_sessao(usuario, sessao), 0, -1)]


def registrar_turno(usuario: str, sessao: str, pergunta: str, resposta: str) -> int:
    """Acrescenta o turno, corta a janela e renova o prazo. Devolve o tamanho."""
    chave = _chave_sessao(usuario, sessao)
    with conexao.pipeline() as p:
        p.rpush(chave, json.dumps({"role": "user", "content": pergunta}, ensure_ascii=False))
        p.rpush(chave, json.dumps({"role": "assistant", "content": resposta}, ensure_ascii=False))
        p.ltrim(chave, -JANELA_MENSAGENS, -1)
        p.expire(chave, SESSAO_TTL_S)
        p.llen(chave)
        return p.execute()[-1]


def esquecer_sessao(usuario: str, sessao: str) -> bool:
    return bool(conexao.delete(_chave_sessao(usuario, sessao)))


# ---------------------------------------------------------- longo prazo

def fatos(usuario: str) -> list[str]:
    return conexao.lrange(_chave_fatos(usuario), 0, -1)


def anotar_fato(usuario: str, fato: str) -> None:
    chave = _chave_fatos(usuario)
    with conexao.pipeline() as p:
        p.rpush(chave, fato.strip()[:200])
        p.ltrim(chave, -MAX_FATOS, -1)
        p.execute()


def esquecer_usuario(usuario: str) -> int:
    """Apaga TUDO do usuário: os fatos e todas as sessões dele."""
    chaves = [_chave_fatos(usuario), *conexao.scan_iter(f"sessao:{validar(usuario)}:*")]
    return conexao.delete(*chaves)


def ok() -> bool:
    try:
        return bool(conexao.ping())
    except redis.RedisError:
        return False
