# Aula 08 — 04: ESQUECER — CONTRADIÇÃO, o fato que mudou.
#
# São três causas distintas de esquecimento, e a terceira é obrigação legal:
#
#   contradição  o fato mudou
#   decaimento   o fato envelheceu
#   remoção      o titular solicitou (LGPD)
#
# A contradição difere das outras duas no momento em que a decisão ocorre.
# Aqui nada é apagado: os dois fatos permanecem no índice, e o desempate
# escolhe na LEITURA qual deles prevalece. Nos outros dois casos o dado é
# removido do armazenamento, em operação de ciclo de vida que ocorre fora do
# caminho da resposta.
#
# O desempate é necessário porque a recuperação por similaridade não ordena
# os dois fatos: o vetor não representa anterioridade (cegueira de TEMPO,
# aula 07, nota 02 §5).

from leitura import desempatar_por_tempo
from memoria_episodica import MemoriaEpisodica

# Dois fatos VERDADEIROS, em datas diferentes. O de agosto revoga o de
# março, e nada no texto diz isso.

FATOS_CONTRADITORIOS = [
    {"id": "fato-teto-mar", "data": "2026-03-01",
     "texto": "O teto de reembolso para refeição em viagem nacional é de "
              "R$ 120,00 por pessoa."},
    {"id": "fato-teto-ago", "data": "2026-08-01",
     "texto": "O teto de reembolso para refeição em viagem nacional passou "
              "a ser de R$ 150,00 por pessoa."},
]

PERGUNTA_CONTRADICAO = "Qual o teto de refeição em viagem nacional?"

print("=" * 74)
print("DOIS FATOS VERDADEIROS, EM DATAS DIFERENTES")
print("=" * 74)
print()
for f in FATOS_CONTRADITORIOS:
    print(f"  [{f['data']}]  {f['texto']}")

print(f"""
  O de agosto REVOGA o de março, e nada no texto diz isso.

  pergunta: {PERGUNTA_CONTRADICAO!r}
""")

print("  Qual dos dois o agente vai citar?")

# A memória episódica indexa os dois fatos como episódios datados.
memoria = MemoriaEpisodica(recriar=True)
memoria.gravar([{"id": f["id"], "data": f["data"], "resumo": f["texto"],
                 "funcionario": "", "veredito": ""}
                for f in FATOS_CONTRADITORIOS])

recuperados = memoria.recuperar(PERGUNTA_CONTRADICAO, k=2)

print(f"\n{'=' * 74}")
print("O QUE A BUSCA DEVOLVE")
print("=" * 74)
print()
for posicao, r in enumerate(recuperados, start=1):
    print(f"  {posicao}º  [{r['data']}]  distância {r['distancia']:.4f}")
    print(f"      {r['resumo']}")

primeiro = recuperados[0]
mais_novo = max(recuperados, key=lambda r: r["data"])

print()
if primeiro["data"] != mais_novo["data"]:
    print(f"""  O PRIMEIRO COLOCADO É O DE {primeiro['data']}, E O VIGENTE É O DE {mais_novo['data']}.

  A busca ordenou por SIMILARIDADE, e a pergunta usa a palavra "é", que
  combina melhor com "é de R$ 120,00" do que com "passou a ser de R$ 150,00".""")
else:
    print(f"""  Neste corpus o vigente ficou em primeiro — por acidente de fraseado,
  não por mérito. A DISTÂNCIA entre os dois é de apenas {abs(recuperados[0]['distancia'] - recuperados[1]['distancia']):.4f}. Uma reescrita
  da pergunta inverte a ordem.""")


# Em nenhum dos dois casos o vetor SABE qual é o mais recente. Ele não tem
# noção de anterioridade — é a cegueira TEMPO da aula 06, e ela custa aqui.

# ------------------------------------------------------------------ a correção
print(f"\n{'=' * 74}")
print("A CORREÇÃO: carimbo de tempo, e desempate NO CÓDIGO")
print("=" * 74)

resultado = desempatar_por_tempo(recuperados)
print(f"""
  vigente:     [{resultado['vigente']['data']}] {resultado['vigente']['resumo']}
  descartados: {[d['data'] for d in resultado['descartados']]}
""")

# Duas decisões de projeto, e nenhuma envolve o modelo:
#
# 1. TODO fato guardado carrega carimbo de tempo, como METADADO — não como
#    texto. Data em texto é para o modelo ler; data em metadado é para o
#    código comparar.
#
# 2. O desempate é `max(candidatos, key=data)`. Uma linha, determinística,
#    de graça. Delegar isso ao modelo é o antipadrão: ele erra, custa uma
#    chamada, e não há como testar.
#
# É a mesma lição do roteador (aula 05) e das cegueiras (aula 06):
# REGRA DETERMINÍSTICA ONDE ELA EXISTE.
#
# E o descarte é REGISTRADO. Um agente que silenciosamente ignora um fato
# contraditório é indistinguível de um que nunca o teve.

# ------------------------------------------------------------- o que isso abre
#
# Desempate por tempo resolve o caso em que um fato REVOGA outro. Não resolve
# o caso em que os dois continuam válidos em contextos diferentes — teto
# nacional e teto internacional, por exemplo.
#
# Para esse, o carimbo não basta: é preciso guardar a CONDIÇÃO de aplicação
# junto com o fato. É o mesmo problema da despesa de Lisboa da aula 07, e a
# mesma solução: a pergunta delegada precisa carregar o critério inteiro.
