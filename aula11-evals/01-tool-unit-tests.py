# TOOL UNIT TESTS — as ferramentas, testadas sem o modelo.
#
# Cada ferramenta é uma função Python comum (`ferramentas.py`): chama-se com
# um argumento e confere-se a resposta. Não há modelo, não há LangChain, não
# há custo, e o resultado é sempre o mesmo.
#
# O CASO: no ticket #355, o agente pediu a despesa "D4612" (sem o hífen) seis
# vezes seguidas. O erro devolvido não dizia o que estava errado, e o modelo
# não tinha como se corrigir. Por isso os testes de erro conferem se a
# resposta diz O QUE RECEBEU.
#
#     python 01-tool-unit-tests.py          # não chama modelo

from ferramentas import consultar_despesa, consultar_politica, registrar_parecer


def teste(nome, ok):
    print("  ok     " if ok else "  FALHOU ", nome)


print("\nCASOS DE ACERTO")
teste("despesa D-4612 custa 138", consultar_despesa(despesa="D-4612")["valor"] == 138.0)
teste("teto de refeição é 120", consultar_politica(categoria="refeicao")["teto"] == 120.0)
teste("parecer registrado como reprovado", registrar_parecer(despesa="D-4612", veredito="reprovado", chave="k1")["veredito"] == "reprovado")

print("\nCASOS DE ERRO — a resposta diz o que recebeu?")
teste("despesa 'D4612', sem hífen", "recebido" in consultar_despesa(despesa="D4612"))
teste("categoria 'almoço'", "recebido" in consultar_politica(categoria="almoço"))
teste("veredito 'negado'", "recebido" in registrar_parecer(despesa="D-4612", veredito="negado", chave="k2"))

print("\nO que o modelo recebeu no ticket #355:")
print(" ", consultar_despesa("D4612"))
print("E o que ele recebe quando erra a categoria:")
print(" ", consultar_politica("almoço"))

# A primeira mensagem não diz o que recebeu nem o que seria válido: o modelo
# só pode repetir. A segunda traz o valor recebido e a lista válida, e o
# modelo se corrige na chamada seguinte. Corrija a `consultar_despesa` em
# `ferramentas.py` e rode de novo.
