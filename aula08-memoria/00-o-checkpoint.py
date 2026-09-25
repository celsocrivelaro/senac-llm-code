# Aula 08 — 00: O CHECKPOINT.
#
# CHECKPOINT é o estado de UMA execução, serializado em disco: um arquivo por
# execução, nomeado pelo identificador dela. A implementação não exige banco
# nem serviço — é um `write_text` com o objeto serializado.
#
# O checkpoint viabiliza três capacidades:
#
#   1. confirmação humana ASSÍNCRONA — o processo não permanece bloqueado
#      aguardando a decisão
#   2. retomada após queda — sem repetir efeitos colaterais já aplicados
#   3. depuração por reprodução — carregar um estado defeituoso e retomar a
#      execução a partir dele
#
# ESCOPO DESTE SCRIPT: demonstra a primeira. A execução é interrompida numa
# ferramenta que exige aprovação, o estado é gravado, e a execução é retomada
# em outro momento a partir do arquivo.
#
# Não há chamada à API. O script é serialização e manipulação de dicionário,
# e produz o mesmo resultado em toda execução.

import json

from checkpoint import CHECKPOINTS, carregar, salvar
from dados import CHECKPOINT

# O `salvar()` e o `carregar()` vivem no `checkpoint.py`, ao lado das três
# memórias e separados delas — o módulo explica por quê.

# `registrar_parecer` é ESCRITA, e escrita irreversível exige confirmação
# humana (Aula 01, nota 03 §3). É no passo 2, portanto, que a execução do
# `CHECKPOINT` pausou — e é essa pausa que este script reconstrói.
FERRAMENTA_QUE_EXIGE_APROVACAO = "registrar_parecer"


# ------------------------------------------------------------ A: a execução para
print("=" * 74)
print("A — A EXECUÇÃO PARA, E NÃO É ERRO")
print("=" * 74)

# A execução andou dois passos e chegou num terceiro que ESCREVE. Escrita
# irreversível exige confirmação humana (Aula 01, nota 03 §3), e a decisão
# de projeto que vem com isso é: NADA DE `input()` no meio do laço. Um
# processo que fica preso esperando alguém não sobrevive a um reinício, e
# não escala para mil execuções pendentes. A confirmação é uma FORMA DE
# TERMINAR — o agente para, grava e devolve o controle.
executados = CHECKPOINT["passos"][:2]
pendente = CHECKPOINT["passos"][2]
assert pendente["ferramenta"] == FERRAMENTA_QUE_EXIGE_APROVACAO

pausado = {
    "execucao_id": CHECKPOINT["execucao_id"],
    "objetivo": CHECKPOINT["objetivo"],
    "passos": executados,
    "tokens_gastos": sum(p["tokens_entrada"] + p["tokens_saida"]
                         for p in executados),
    "ferramentas_ativas": CHECKPOINT["ferramentas_ativas"],
    "termino": "HUMANO",
    "motivo": f"{pendente['ferramenta']} exige aprovação",
    "pendencia": {"ferramenta": pendente["ferramenta"],
                  "argumentos": pendente["argumentos"]},
    "historico": CHECKPOINT["historico"],
}

caminho = salvar(pausado)

print(f"""
  A execução {pausado['execucao_id']} deu {len(executados)} passos e parou:

      término: {pausado['termino']}
      motivo:  {pausado['motivo']}
      pendência: {pausado['pendencia']['ferramenta']}({pausado['pendencia']['argumentos']})

  E gravou o estado em {caminho.parent.name}/{caminho.name}.
""")

print("-" * 74)
print("  O ARQUIVO, POR EXTENSO — o estado inteiro, em disco:")
print("-" * 74)
print(caminho.read_text(encoding="utf-8"))

print("""
  O processo encerrou. Nenhum recurso permanece alocado aguardando a
  resposta, e a aprovação pode ocorrer em outro momento, em outro processo
  e em outra máquina.
""")

# ------------------------------------------------------------- B: a retomada
print("=" * 74)
print("B — A RETOMADA: aprovar não é recomeçar")
print("=" * 74)

# Outro processo, em outro momento. A única informação disponível para ele é
# o identificador da execução.
estado = carregar(pausado["execucao_id"])
passos_antes = len(estado["passos"])

print(f"""
  carregado de {caminho.name}: {passos_antes} passos já executados,
  {estado['tokens_gastos']} tokens já gastos, e uma pendência aguardando.
""")

# Aprovação concedida. Apenas o passo pendente é executado; os anteriores não
# são repetidos, e portanto seus efeitos colaterais não são reaplicados.
estado["passos"].append(pendente)
estado["tokens_gastos"] += pendente["tokens_entrada"] + pendente["tokens_saida"]
estado["termino"] = "CONCLUIDO"
estado["motivo"] = None
estado["pendencia"] = None
estado["resposta"] = CHECKPOINT["resposta"]
salvar(estado)

print(f"""  aprovado -> executa o passo {pendente['indice']}, e só ele:

      {pendente['ferramenta']}({pendente['argumentos']})
          -> {pendente['resultado']}

  término: {estado['termino']}
  passos:  {passos_antes} antes + 1 agora = {len(estado['passos'])}
  tokens:  {estado['tokens_gastos']}
""")

# A conta que justifica tudo: o que NÃO foi refeito.
custo_refazer = sum(p["tokens_entrada"] + p["tokens_saida"] for p in executados)
print(f"""  O QUE NÃO ACONTECEU: os {passos_antes} primeiros passos não foram refeitos.

      {custo_refazer} tokens que não foram gastos de novo — e, mais importante,
      nenhuma consulta repetida e nenhuma escrita duplicada.

  Sem o checkpoint, "aprovar" significaria reexecutar a tarefa do zero, e
  aí a aprovação do humano recairia sobre uma execução DIFERENTE da que
  ele analisou.
""")
