# Aula 08 — 04: ESQUECER — DECAIMENTO, o fato que envelheceu.
#
# São três causas distintas de esquecimento, e a terceira é obrigação legal:
#
#   contradição  o fato mudou
#   decaimento   o fato envelheceu
#   remoção      o titular solicitou (LGPD)
#
# É o único dos três que não chama a API: a idade de um fato é aritmética
# sobre datas, e o parâmetro que define o corte é decisão de projeto.

from datetime import date

from dados import EPISODIOS

HOJE = date(2026, 10, 6)          # data fixa: o laboratório precisa ser reproduzível

# O corte é um parâmetro exposto no topo do módulo, e não um literal no meio
# de uma função. O valor adequado depende do domínio: cinco meses pode ser
# curto ou longo conforme a taxa de mudança dos fatos armazenados.
DIAS_PARA_DECAIR = 150


def idade_em_dias(data_iso: str) -> int:
    a, m, d = (int(x) for x in data_iso.split("-"))
    return (HOJE - date(a, m, d)).days


print("=" * 74)
print("DECAIMENTO — o fato envelheceu sem ser contradito")
print("=" * 74)

print(f"\n  hoje: {HOJE.isoformat()}\n")
for t in sorted(EPISODIOS, key=lambda t: t["data"]):
    idade = idade_em_dias(t["data"])
    marca = "  <-- candidato a decair" if idade > DIAS_PARA_DECAIR else ""
    print(f"  {t['data']}  {idade:>3d} dias  {t['id']}{marca}")

# Decaimento não é apagar por idade: é REBAIXAR. Um episódio de sete meses
# atrás ainda pode ser o único relevante para a pergunta de agora, e a
# execução de Lisboa de março é exatamente esse caso — ela está marcada
# acima como candidata a decair, e é uma das que o script 01 recupera.
#
# A implementação usual é ponderar a distância pela recência na hora de
# recuperar — recência, importância e relevância, como em PARK et al. (2023).
# O que NÃO se faz é deletar por idade sem olhar o conteúdo.
