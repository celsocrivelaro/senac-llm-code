# Aula 07 — 06: O CONTRATO DE SAÍDA — CITAÇÃO E RECUSA.
#
# CONTRATO DE SAÍDA é um schema que o modelo é obrigado a preencher. Aqui ele
# tem três campos, e dois deles existem para tornar falhas detectáveis:
#
#   resposta     o texto gerado
#   fontes       os identificadores dos trechos usados, conferíveis em código
#   suficiente   false quando a informação não está nos trechos recuperados
#
# O campo `suficiente` é a ROTA DE ESCAPE. Ele corresponde à rota `nenhuma`
# do roteador da aula 05 (nota 01, §3.2): um destino explícito para o caso em
# que nenhuma das opções se aplica. Sem ele, o modelo escolhe entre opções
# que não servem, porque o formato de saída não admite outra coisa.
#
# ESCOPO DESTE SCRIPT. Duas demonstrações. A primeira compara a mesma
# pergunta respondida com e sem o campo `suficiente`. A segunda verifica, em
# código, se as fontes citadas existem entre os trechos recuperados.

from dados import CORPUS_COM_RUIDO, PERGUNTAS, SEM_RESPOSTA
from geracao import responder
from indice_chroma import IndiceChroma
from metricas import citacao_verificavel

indice = IndiceChroma(CORPUS_COM_RUIDO)

print("=" * 74)
print("O CONTRATO DE SAÍDA")
print("=" * 74)
print("""
    {"resposta": str, "fontes": [str], "suficiente": bool}

`fontes`      -> a citação, verificável em código contra o que foi recuperado
`suficiente`  -> a rota de escape. false = a informação não está nos trechos
""")

# -------------------------------------------------- antes e depois da recusa
print("=" * 74)
print("A MESMA PERGUNTA, SEM E COM O CAMPO `suficiente`")
print("=" * 74)

for pergunta in SEM_RESPOSTA:
    trechos = indice.buscar(pergunta, k=3)
    print(f"\n  P: {pergunta}")

    sem = responder(pergunta, trechos, com_contrato=False)
    print(f"     SEM contrato: {sem['resposta'][:130]}")

    com = responder(pergunta, trechos, com_contrato=True)
    veredito = "RECUSOU" if com["suficiente"] is False else "RESPONDEU MESMO ASSIM"
    print(f"     COM contrato: [{veredito}] {com['resposta'][:130]}")
    print(f"                   fontes={com['fontes']}")

print("""
`suficiente: false` é um resultado intermediário, não o encerramento do
processo. Um sistema que devolve a recusa e para transferiu o problema ao
usuário. O campo precisa ter destino definido: fila de revisão humana,
pedido de reformulação, ou nova consulta com outra estratégia de busca.
""")

# --------------------------------------------------- a citação é verificável
print("=" * 74)
print("A CITAÇÃO PRECISA SER VERIFICÁVEL")
print("=" * 74)
print("""
A fonte precisa ser um identificador do corpus, não uma paráfrase do trecho.
A diferença é operacional: um identificador pode ser comparado com a lista do
que foi recuperado, e uma paráfrase não pode. A verificação é uma comparação
de strings — não exige chamada ao modelo.
""")

inventadas_total = 0
for caso in PERGUNTAS[:6]:
    trechos = indice.buscar(caso["pergunta"], k=3)
    r = responder(caso["pergunta"], trechos)
    check = citacao_verificavel(r["fontes"], trechos)
    inventadas_total += len(check["inventadas"])

    estado = "ok" if not check["inventadas"] else "FONTE INVENTADA"
    print(f"  [{estado}] {caso['pergunta'][:52]}")
    print(f"      citou={check['citadas']}")
    print(f"      disponíveis={check['disponiveis']}")
    if check["inventadas"]:
        print(f"      inventadas={check['inventadas']}")
    print()

print(f"  fontes inventadas no total: {inventadas_total}")
