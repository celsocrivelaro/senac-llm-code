# Aula 06 — 04: O ROUTER POR EMBEDDING.
#
# Esta linha existe no `01-router.py` da aula 05:
#
#     router_embedding = None   # Aula 06
#
# com o comentário "é lá que esta linha vira código". É aqui.
#
# A aula 05 nomeou três formas de rotear — regra, embedding, semântica — e
# implementou a primeira e a terceira. A do meio ficou de fora porque depende
# de embeddings, e embeddings eram esta aula.
#
# O que o script demonstra, em ordem:
#
#   1. classificar e buscar são A MESMA OPERAÇÃO. O router é o `ranquear` do
#      script 01 com o corpus trocado por exemplares de rota;
#   2. ele decide sem gerar texto — uma chamada de embedding contra uma
#      chamada de geração do router semântico;
#   3. e ele quebra num caso específico: duas mensagens que diferem em UMA
#      palavra caem na mesma rota. A aula 07 volta a esse caso.


import numpy as np

from embedding import gerar_matrix_embbeddings, gerar_vetor_embeddings
from similaridade import cosseno

# ============================================================ OS EXEMPLARES
#
# As rotas são as do `01-router.py` da aula 05, e o domínio também: um lote
# de mensagens que chega à transportadora.
#
# O que substitui o classificador é esta tabela. Cada rota é representada por
# algumas frases que a exemplificam — e é só isso que o router "sabe". Não há
# treino, não há prompt, não há geração: há um punhado de frases por rota.

EXEMPLARES = {
    "consulta_status": [
        "qual o status do meu pedido",
        "onde está minha encomenda",
        "quero saber da entrega do pedido",
        "meu pedido já saiu para entrega?",
    ],
    "reclamacao": [
        "meu pedido está atrasado e ninguém resolve",
        "isso é um absurdo, quero uma solução",
        "a encomenda chegou danificada",
        "já é a terceira vez que isso acontece",
    ],
    "fora_de_escopo": [
        "vocês têm vaga de emprego",
        "quero falar sobre uma parceria comercial",
        "qual o horário de funcionamento da loja",
    ],
}

# Uma chamada para todos os exemplares, na largada. A partir daqui, cada
# mensagem classificada custa UMA chamada — a dela. É a assimetria do
# script 03 de novo: a tabela é construída uma vez, e consultada sempre.
# Duas listas paralelas: a frase de exemplo, e a rota a que ela pertence.
# `_matriz[i]` é o vetor da frase `i`, e `_rotas[i]` é a rota dela.
_frases, _rotas = [], []
for rota, exemplos in EXEMPLARES.items():
    for frase in exemplos:
        _frases.append(frase)
        _rotas.append(rota)

_matriz = gerar_matrix_embbeddings(_frases)


def router_embedding(mensagem: str, piso: float = 0.0) -> dict:
    """Classifica pela rota do exemplar mais próximo.

    É o `ranquear` do script 01 com o corpus trocado por exemplares de rota.
    Nenhum mecanismo novo: busca e classificação são a mesma operação, e a
    diferença está só no que se indexou.

    `piso` é o limiar abaixo do qual o router DECLINA — a rota `nenhuma` da
    aula 05, que existe para o sistema poder dizer que não sabe.
    """
    # UMA chamada, a da mensagem — e ela sai FORA da comparação. Embutir
    # dentro do laço custaria uma chamada por exemplar, que é o mesmo erro
    # que o 02 comete se reembutir as perguntas a cada medição.
    vetor = gerar_vetor_embeddings(mensagem)
    scores = np.array([cosseno(vetor, v) for v in _matriz])
    ordem = np.argsort(-scores)

    melhor, segundo = ordem[0], ordem[1]
    rota = _rotas[melhor]

    # A margem é a distância para o exemplar mais próximo de OUTRA rota —
    # decisão frágil vale mais que score alto. Percorremos a ordem até achar
    # o primeiro exemplar que pertence a outra rota.
    outra = segundo
    for i in ordem:
        if _rotas[i] != rota:
            outra = i
            break

    if scores[melhor] < piso:
        return {"rota": "nenhuma", "score": float(scores[melhor]),
                "margem": 0.0, "motivo": f"nada acima do piso {piso:.2f}"}
    return {"rota": rota, "score": float(scores[melhor]),
            "margem": float(scores[melhor] - scores[outra]),
            "motivo": f"exemplar {melhor}"}


# --------------------------------------------------------------- o lote
print("=" * 74)
print("ROTEANDO SEM GERAR TEXTO")
print("=" * 74)

LOTE = [
    "Qual o status do pedido 48219?",
    "onde está meu pedido 31002",
    "O pedido 48219 está atrasado há duas semanas e ninguém me responde.",
    "a caixa chegou toda amassada, quero reembolso",
    "vocês estão contratando?",
]

print()
for m in LOTE:
    r = router_embedding(m)
    print(f"  {r['rota']:<16s} score {r['score']:.4f}  margem {r['margem']:+.4f}")
    print(f"  {'':16s} {m[:54]!r}\n")

print("""Nenhuma chamada de geração. O router semântico da aula 05 gastaria uma
por mensagem; este gasta uma chamada de embedding, que é a modalidade
barata, e devolve a rota sem escrever uma palavra.

A MARGEM é a distância para o exemplar mais próximo de outra rota. Margem
estreita indica decisão frágil, e é mais informativa que o score absoluto:
um score de 0,80 com margem de 0,01 é um empate.
""")

# ------------------------------------------------------- onde ele quebra
print("=" * 74)
print("ONDE ELE QUEBRA")
print("=" * 74)

# Duas mensagens que diferem em uma palavra e exigem tratamentos opostos:
# uma é um agradecimento, a outra é uma entrega perdida.
PAR = [
    "o pedido 48219 chegou certinho, obrigado",
    "o pedido 48219 não chegou",
]

print()
for m in PAR:
    r = router_embedding(m)
    print(f"  {r['rota']:<16s} score {r['score']:.4f}  margem {r['margem']:+.4f}  {m!r}")

sim = cosseno(gerar_vetor_embeddings(PAR[0]), gerar_vetor_embeddings(PAR[1]))
print(f"""
  cosseno entre as duas .... {sim:.4f}

A reclamação vai para a fila errada. E não adianta mexer nos exemplares: o
problema não está neles, está em como o vetor representa as duas frases.

O contexto em que isso ocorre não tem corpus, não tem trechos recuperados e
não tem modelo gerando texto. O defeito é de representação, e a aula 07
retoma o caso para mostrar que ele não é isolado.
""")

# ------------------------------------------------------------- a cascata
print("=" * 74)
print("A SAÍDA É A CASCATA DA AULA 05")
print("=" * 74)


def regra(mensagem: str) -> str | None:
    """Polaridade se resolve com palavra-chave, não com vetor. Três termos
    em código valem mais que qualquer ajuste de exemplar."""
    baixo = mensagem.lower()
    if any(t in baixo for t in ("não chegou", "nao chegou", "não recebi")):
        return "reclamacao"
    return None


print()
for m in PAR:
    if (r := regra(m)):
        print(f"  {r:<16s} [REGRA]      zero chamadas  {m!r}")
    else:
        e = router_embedding(m)
        print(f"  {e['rota']:<16s} [EMBEDDING]  1 chamada      {m!r}")

print("""
A ordem é a mesma da aula 05, e agora a forma do meio existe:

    REGRA        ->  zero chamadas. Resolve o que é determinístico:
                     polaridade, número, identificador, data.
    EMBEDDING    ->  uma chamada barata. Resolve variação de redação,
                     que é justamente o que a regra não generaliza.
    SEMÂNTICO    ->  uma chamada de geração. Resolve o caso não previsto.

Cada degrau existe porque o anterior tem um limite conhecido. Um router que
começa no degrau mais caro não está economizando nada — e um que nunca sobe
está errando nos casos que não previu.
""")

print("=" * 74)
print("O LIMIAR, E A ROTA QUE DIZ NÃO SEI")
print("=" * 74)

FORA = "gostaria de saber sobre o índice de reajuste da tabela de fretes"
print(f"\n  mensagem: {FORA!r}\n")
for piso in (0.0, 0.75, 0.82):
    r = router_embedding(FORA, piso=piso)
    print(f"  piso {piso:.2f} -> {r['rota']:<16s} score {r['score']:.4f}  ({r['motivo']})")

print("""
Sem piso, o router SEMPRE devolve uma rota — a menos ruim. É o mesmo defeito
que a aula 05 apontou no router semântico: sem escape, o classificador é
obrigado a escolher, e escolhe.

O piso não se chuta. Calibra-se com o conjunto de mensagens conhecidas, do
mesmo jeito que o `k` do script 02 — e a nota 01 §5 já tinha avisado por que
um limiar absoluto escolhido no chute não funciona: o piso real entre textos
sem relação nenhuma fica bem acima de zero.
""")
