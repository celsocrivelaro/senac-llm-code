# Aula 08 — 02: A MEMÓRIA EPISÓDICA — o que aconteceu, e quando.
#
# Memória divide-se em duas, antes de dividir-se em tipos:
#
#   short-term memory  a janela de contexto: system prompt, objetivo,
#                      trajetória da execução corrente. Persistida em disco,
#                      é o checkpoint (`checkpoint.py`, script 00).
#
#   long-term memory   o que atravessa execuções, e é de um de três tipos:
#                      episódica, semântica ou procedural.
#
# A MEMÓRIA EPISÓDICA registra o que ocorreu em execuções passadas: o que o
# agente fez e qual foi o resultado. A estrutura é um banco vetorial porque a
# consulta dirigida a ela — "já ocorreu algo parecido com isto?" — é uma
# pergunta sobre ASSUNTO, e assunto é o que a similaridade representa.
#
# É o mecanismo da aula 07 aplicado a outro objeto: em vez de indexar
# documentos, indexa EPISÓDIOS.
#
# ESCOPO DESTE SCRIPT. Indexa os dez episódios, executa uma consulta por
# similaridade e CONFERE o que voltou. A conferência é o motivo de o script
# existir na forma em que está: a consulta escolhida falha, e a falha é a da
# aula 07 num objeto novo.
#
# CUSTO DE CONSULTA: uma chamada de embedding para a consulta, mais a busca
# vetorial. É o mais caro dos três.

from dados import EPISODIOS
from memoria_episodica import MemoriaEpisodica

# Os destinos fora do país, no corpus desta aula. A lista existe para que a
# conferência abaixo seja feita em código, e não a olho.
INTERNACIONAIS = ("Lisboa",)


def e_internacional(resumo: str) -> bool:
    return any(destino in resumo for destino in INTERNACIONAIS)


print("=" * 74)
print("EPISÓDICA — o que aconteceu, quando  (Chroma, por similaridade)")
print("=" * 74)

episodica = MemoriaEpisodica(recriar=True)
episodica.gravar(EPISODIOS)

no_corpus = [t for t in EPISODIOS if e_internacional(t["resumo"])]
print(f"\n  {len(EPISODIOS)} episódios indexados, "
      f"{len(no_corpus)} deles em viagem internacional.\n")

CONSULTA = "refeição em viagem internacional"
K = 2
print(f"  consulta: {CONSULTA!r}   k={K}\n")

recuperados = episodica.recuperar(CONSULTA, k=K)
for e in recuperados:
    marca = "  <-- internacional" if e_internacional(e["resumo"]) else ""
    print(f"  [{e['data']}] {e['resumo'][:80]}{marca}")

# ============================================ A CONFERÊNCIA, E O QUE ELA ACHA
#
# Não basta a consulta devolver algo. A pergunta é se devolveu o que a
# consulta pedia — e aqui ela pede viagem internacional, que é um critério
# verificável em código.
acertos = [e for e in recuperados if e_internacional(e["resumo"])]

print(f"\n{'=' * 74}")
print("O QUE A CONSULTA PEDIU, E O QUE ELA TROUXE")
print("=" * 74)
print(f"""
  a consulta pede viagem INTERNACIONAL
  o corpus tem {len(no_corpus)} episódios internacionais entre {len(EPISODIOS)}
  dos {len(recuperados)} resultados recuperados, {len(acertos)} são internacionais
""")

if len(acertos) < min(K, len(no_corpus)):
    print("""  A palavra "internacional" está na consulta e não trouxe as viagens
  internacionais. É a cegueira da aula 07 (nota 02) aparecendo na memória:
  o vetor representa ASSUNTO — "refeição", "viagem", "teto", "reembolso" —,
  e todos os episódios do corpus tratam desse assunto. O que distingue
  Lisboa de Curitiba não é o assunto: é um ATRIBUTO da viagem.

  Atributo se filtra, não se busca.""")
else:
    print("""  A consulta trouxe as internacionais. O resultado depende do corpus e do
  modelo de embedding: com outro conjunto de episódios, a mesma consulta
  pode trazer as domésticas — porque o que distingue Lisboa de Curitiba não
  é o assunto do texto.""")

# ============================================ O FILTRO, E O QUE ELE ALCANÇA
#
# `recuperar` aceita filtro por metadado, e o filtro entra ANTES da
# ordenação: restringir o espaço de busca é mais barato e mais exato que
# recuperar por similaridade e descartar depois.
print(f"\n{'=' * 74}")
print("O FILTRO POR METADADO — o que é campo se resolve como campo")
print("=" * 74)
print()

for e in episodica.recuperar(CONSULTA, k=K, funcionario="F-088"):
    marca = "  <-- internacional" if e_internacional(e["resumo"]) else ""
    print(f"  [{e['data']}] {e['resumo'][:80]}{marca}")
