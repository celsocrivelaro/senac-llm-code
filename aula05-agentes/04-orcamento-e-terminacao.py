# Aula 05 — Arquitetura de agentes
# 04 — AS QUATRO FORMAS DE TERMINAR, disparadas de propósito.
#
# Um agente termina de exatamente quatro maneiras. No laço da aula 03, a
# primeira era `return`, a segunda era `raise RuntimeError`, a terceira
# derrubava o processo por exceção não tratada e a quarta não existia.
#
#     1. RESPONDEU     o modelo devolveu sem tool_calls        ✓ sucesso
#     2. ORCAMENTO     estourou um dos quatro tetos            ✗ inconcluso
#     3. ERRO_FATAL    não há como continuar                   ✗ falha
#     4. HUMANO        pausou aguardando confirmação           ⏸ suspenso
#
# Aqui as quatro viram DADO no estado. Um agente que "acabou" sem dizer por
# quê é indepurável às onze da noite com o sistema em produção.
#
# E repare no orçamento: `max_passos` sozinho não é orçamento. Passo não é
# unidade de custo — um passo custa entre 300 e 40.000 tokens.

import agente
from agente import Orcamento, Termino, ErroFatal, rodar, resumo

LINHA = "=" * 78


def cabecalho(n, titulo, explicacao):
    print(f"\n{LINHA}\n{n}) {titulo}\n   {explicacao}\n")


# ------------------------------------------------------------ 1. RESPONDEU
cabecalho(1, "RESPONDEU", "orçamento folgado, tarefa que cabe nele")
e1 = rodar("Qual a situação do pedido 90455?",
           orcamento=Orcamento(max_passos=6, max_reais=0.05), fase="analise")
print(f"\n   {resumo(e1)}")
print(f"   resposta: {(e1.resposta or '')[:90]}")

# ------------------------------------------------------------ 2. ORCAMENTO
cabecalho(2, "ORCAMENTO", "a MESMA tarefa, com teto de 1 passo")
e2 = rodar("Compare a situação dos pedidos 48219, 77310 e 90455 e diga qual "
           "está em pior estado.",
           orcamento=Orcamento(max_passos=1), fase="analise")
print(f"\n   {resumo(e2)}")
print("   note: o motivo diz QUAL teto estourou. `bool` seria mais simples")
print("   e inútil — morrer por tempo e morrer por tokens são diagnósticos")
print("   diferentes, que pedem correções opostas.")

# ----------------------------------------------------------- 3. ERRO_FATAL
cabecalho(3, "ERRO_FATAL", "o banco 'caiu' — nenhuma decisão do modelo resolve")

original = agente.consultar_pedido


def consultar_pedido_quebrado(numero: str) -> dict:
    raise ErroFatal("banco de pedidos indisponível (simulado)")


agente.FERRAMENTAS["consultar_pedido"] = consultar_pedido_quebrado
try:
    e3 = rodar("Qual a situação do pedido 48219?",
               orcamento=Orcamento(max_passos=6), fase="analise")
finally:
    agente.FERRAMENTAS["consultar_pedido"] = original
print(f"\n   {resumo(e3)}")
print("   note: devolver ISTO ao modelo como observação seria o erro. Ele")
print("   reformularia o argumento educadamente quatro vezes, contra uma")
print("   parede, até o orçamento acabar.")

# --------------------------------------------------------------- 4. HUMANO
cabecalho(4, "HUMANO", "ação de escrita: o agente para, grava e devolve o controle")
e4 = rodar("O pedido 48219 está atrasado. Abra um chamado de entrega "
           "atrasada para ele.",
           orcamento=Orcamento(max_passos=8), fase="tudo",
           exige_confirmacao={"abrir_chamado"})
print(f"\n   {resumo(e4)}")
print(f"   pendência gravada: {e4.pendencia}")
print(f"   checkpoint: checkpoints/{e4.execucao_id}.json")
print("   note: NÃO houve input() no meio do laço. A confirmação é uma FORMA")
print("   DE TERMINAR — o estado foi gravado e a aprovação pode chegar amanhã,")
print("   por outro processo, sem repetir nenhum passo já dado.")

# ------------------------------------------------------------------ resumo
print(f"\n{LINHA}")
print(f"{'execução':<12} {'término':<22} {'passos':>7} {'tokens':>8} {'custo':>10}")
for nome, e in [("1 responde", e1), ("2 orçamento", e2),
                ("3 fatal", e3), ("4 humano", e4)]:
    print(f"{nome:<12} {e.termino.value:<22} {e.n_passos:>7} "
          f"{e.tokens_gastos:>8} R$ {e.custo_estimado:>7.4f}")

print(f"""
O que levar daqui:
  - as quatro formas são CÓDIGO EXPLÍCITO, e o motivo fica no estado;
  - o trace é gravado no `finally` — em todos os caminhos, inclusive nos de
    falha, que é justamente onde ele vale mais;
  - orçamento é PARÂMETRO, não constante no meio do arquivo. Uma triagem e
    uma investigação não têm o mesmo direito de gastar;
  - a linha "silêncio" da tabela de falhas da aula 01 morre aqui.
""")
