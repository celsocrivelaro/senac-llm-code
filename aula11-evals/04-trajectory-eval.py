# TRAJECTORY EVAL — a resposta estava certa, e o sistema estava errado.
#
# A TÉCNICA: avaliar o caminho (ferramentas e ordem) e o estado final.
#
# Inclui a avaliação do estado final no espírito do τ-bench.
#
# OS CASOS, dois incidentes cuja resposta final estava CORRETA:
#
#   ticket #318  "Parecer registrado: reprovado." E estava — duas vezes.
#                Um timeout, um retry com outra chave, dois pareceres.
#   palpite      "Aprovado." Correto, para Lisboa. Mas o agente não
#                consultou política nem regulamento: R$ 590 lhe pareceu
#                razoável, e na próxima despesa vai parecer de novo.
#
# Avaliar só o texto aprova os dois. A tabela abaixo põe lado a lado o que
# cada nível vê.
#
#     python 04-trajectory-eval.py          # 2 execuções do agente

from casos import CASOS, TRACES_GRAVADOS
from metricas import nivel_deterministico, nivel_resultado, nivel_trajetoria
from sistema import MODELO, PARECERES, PROVEDOR, limpar_pareceres, rodar, trace_das_mensagens

CASOS_POR_ID = {c["id"]: c for c in CASOS}


def linha(nome: str, trace, caso: dict, antes: dict, depois: dict) -> None:
    det = nivel_deterministico(trace, caso)
    traj = nivel_trajetoria(trace, caso)
    res = nivel_resultado(antes, depois, caso)
    print(f"\n  {nome}  ({caso['id']})")
    print(f"    texto ....... veredito {det['veredito_obtido']!s:<10} {'ok' if det['veredito_correto'] else 'ERRADO'}")
    print(f"    citação ..... {'verificável' if det['citacao_verificavel'] else 'NÃO está no que as ferramentas devolveram'}")
    print(f"    trajetória .. {' -> '.join(traj['obtido']) or '(nenhuma)'}")
    print(f"                  cobertura {traj['cobertura']:.0%}, ordem {'ok' if traj['ordem_ok'] else 'FORA'}"
          + (f", erros em {traj['argumentos_invalidos']}" if traj["argumentos_invalidos"] else ""))
    print(f"    mundo ....... {res['criados']} parecer(es) criado(s), esperado {res['esperados']}"
          + ("   DUPLICADO" if res["duplicado"] else "   AUSENTE" if res["ausente"] else ""))


print("1 — OS INCIDENTES, COMO FORAM GRAVADOS")
for gravado in TRACES_GRAVADOS:
    trace = trace_das_mensagens(gravado["mensagens"])
    print(f"\n  [{gravado['o_que_houve']}]", end="")
    linha(gravado["id"], trace, CASOS_POR_ID[gravado["caso"]], {}, gravado["pareceres_depois"])

print(f"\n\n2 — OS MESMOS CASOS, NO AGENTE DE HOJE  [{PROVEDOR}:{MODELO}]")
for gravado in TRACES_GRAVADOS:
    caso = CASOS_POR_ID[gravado["caso"]]
    limpar_pareceres()
    antes = dict(PARECERES)
    trace = rodar(caso["entrada"])
    linha("ao vivo", trace, caso, antes, dict(PARECERES))

# Texto diz SE acertou; trajetória diz POR QUÊ; o estado do mundo diz o que
# ficou feito. A trajetória exigida é só o que não pode faltar — exigir o
# caminho exato reprovaria soluções válidas (ver o caso 09).
