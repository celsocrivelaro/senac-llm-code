# Aula 08 — 05: A MEDIÇÃO DO GANHO, EM PASSOS EVITADOS.
#
# A justificativa econômica da memória é a redução do número de passos entre
# a primeira execução de uma tarefa e a segunda. Passos evitados são chamadas
# não emitidas, e é essa a grandeza comparável.
#
# A tarefa é idêntica à do script 01, o que torna as duas execuções
# comparáveis: a primeira ocorreu sem memória, e esta ocorre com ela.

from dados import EPISODIOS
from memoria_episodica import MemoriaEpisodica

# A tarefa corrente. O texto é idêntico nos scripts 01, 02 e neste: a aula
# executa a mesma tarefa repetidamente. Alterar este texto exige alterá-lo
# nos três arquivos.
TAREFA = ("Analisar a despesa D-4612 do funcionário F-088: refeição de R$ 245,00 por pessoa, em viagem a Lisboa, com nota fiscal.")

print("=" * 74)
print("A MEDIDA QUE FECHA A FASE")
print("=" * 74)

memoria = MemoriaEpisodica(recriar=True)
memoria.gravar(EPISODIOS)
uteis = memoria.recuperar(TAREFA, k=3)

print(f"""
  tarefa: {TAREFA}

  SEM memória, a segunda execução repete a primeira:
      passo 0  consultar_historico(F-88)   -> erro de formato
      passo 1  consultar_historico(F-088)  -> ok
      passo 2  consultar_politica(refeicao)
      passo 3  registrar_parecer
      = 4 passos

  COM memória, três dessas informações já estão no contexto:""")
for e in uteis:
    print(f"      [{e['data']}] {e['resumo'][:88]}")

print("""      = 2 passos (o erro de id não acontece, e a política já veio)

  ECONOMIA: 2 passos de 4, na segunda execução da mesma tarefa.
""")

# Passos evitados são chamadas não emitidas, e é essa a grandeza na qual o
# ganho da memória é comparável. É também o número que o exercício 08 pede.

# --------------------------------------------------- o que fica para a aula 13
#
# A aula 04 registrou o caso: mais de 30 mil instâncias do OpenClaw expostas
# na internet aberta, com a memória e o histórico de conversa legíveis por
# qualquer acesso.
#
# A memória é o dado mais sensível do sistema por duas propriedades
# combinadas: é ACUMULADA e NÃO SUPERVISIONADA — o conteúdo gravado ao longo
# de meses não passa por revisão.
#
# É também vetor de ataque, e não apenas alvo: conteúdo gravado hoje é lido
# semanas depois, em outro contexto, sem que a relação entre as duas
# operações seja visível. É injeção com persistência.
#
# O tratamento — OWASP ASI, tool misuse, isolamento — é assunto da aula 14.
