# Aula 05 — Arquitetura de agentes
# 06 — CONTEXT ENGINEERING DINÂMICA: medir antes de otimizar.
#
# A propriedade que passa despercebida em execuções curtas e domina tudo nas
# longas:
#
#     a cada volta, o histórico inteiro é reenviado. Nada nunca sai.
#
# O custo ACUMULADO cresce com o quadrado do número de passos: dobrar os
# passos não dobra a conta, quadruplica. E a qualidade cai ANTES de a janela
# acabar, porque o objetivo vai para o meio do contexto — que é onde o
# modelo lê pior (lost in the middle, aula 02, nota 01 §4.3).
#
# Este script roda a MESMA tarefa longa duas vezes e imprime a curva de
# tokens por passo. A primeira coisa que ele faz é MEDIR: sem o número,
# qualquer otimização de contexto é chute.
#
# A tática aplicada aqui é TOOL CLEARING, e ela é a primeira da lista por
# três razões: é seletiva (mexe só no que já foi consumido), é REVERSÍVEL
# (o resultado completo continua em estado.passos — só saiu do que se envia)
# e preserva a estrutura da trajetória.
#
# O erro clássico da compressão ingênua: apagar a CHAMADA inteira faz o
# agente repeti-la. Ele não lembra de ter consultado, consulta de novo, e
# você criou um laço com a sua própria otimização.

import json

from agente import Orcamento, rodar, resumo

LINHA = "=" * 78

# Tarefa longa de propósito: 5 pedidos × (consultar + prazo + cliente).
OBJETIVO = ("Faça um levantamento dos pedidos 48219, 77310, 90455, 31002 e "
            "55870. Para cada um, informe a situação, quantos dias de atraso "
            "tem (ou quantos faltam) e o nome do cliente. Consulte as "
            "ferramentas para cada pedido — não deduza.")

MANTER_INTEGROS = 3          # os N resultados mais recentes ficam completos


def tool_clearing(estado) -> None:
    """Substitui o CORPO de resultados antigos por um marcador curto.

    Repare no que o marcador preserva: o nome da ferramenta e o fato de a
    chamada ter acontecido. É isso que impede o agente de chamá-la de novo.

    E repare no que NÃO se perde: `estado.passos` continua com o resultado
    inteiro. A compressão é do que se ENVIA, não do que se sabe — por isso
    o trace continua completo para auditoria."""
    indices_tool = [i for i, m in enumerate(estado.historico)
                    if isinstance(m, dict) and m.get("role") == "tool"]
    if len(indices_tool) <= MANTER_INTEGROS:
        return

    for i in indices_tool[:-MANTER_INTEGROS]:
        mensagem = estado.historico[i]
        if mensagem["content"].startswith("[resultado removido"):
            continue                                   # já limpo
        try:
            dados = json.loads(mensagem["content"])
        except json.JSONDecodeError:
            dados = {}
        chave = next((k for k in ("numero", "id", "dias", "protocolo")
                      if k in dados), None)
        essencial = f"{chave}={dados[chave]}" if chave else "ok"
        mensagem["content"] = (f"[resultado removido do contexto] "
                               f"{mensagem.get('name')} -> {essencial}")


def curva(estado, rotulo):
    print(f"\n{rotulo}")
    print(f"   {'passo':>5} {'contexto enviado':>18} {'acumulado':>12}")
    acumulado = 0
    for i, tokens in enumerate(estado.contexto_por_passo):
        acumulado += tokens
        barra = "#" * max(1, tokens // 400)
        print(f"   {i:>5} {tokens:>18} {acumulado:>12}  {barra}")
    return acumulado


print(f"objetivo (tarefa longa de propósito):\n   {OBJETIVO}\n")

# ------------------------------------------------------ A) sem tool clearing
print(LINHA + "\nA) SEM tool clearing — nada nunca sai do histórico\n")
a = rodar(OBJETIVO, orcamento=Orcamento(max_passos=20, max_tokens=120_000,
                                        max_reais=0.30, max_segundos=300),
          fase="analise", verboso=False)
print(f"   {resumo(a)}")
total_a = curva(a, "   curva de contexto:")

# ------------------------------------------------------ B) com tool clearing
print("\n" + LINHA + f"\nB) COM tool clearing (mantendo {MANTER_INTEGROS} "
      f"resultados íntegros)\n")
b = rodar(OBJETIVO, orcamento=Orcamento(max_passos=20, max_tokens=120_000,
                                        max_reais=0.30, max_segundos=300),
          fase="analise", gancho_contexto=tool_clearing, verboso=False)
print(f"   {resumo(b)}")
total_b = curva(b, "   curva de contexto:")

# ------------------------------------------------------------------ a conta
print("\n" + LINHA)
economia = (1 - total_b / total_a) * 100 if total_a else 0
print(f"""
                        passos   tokens de entrada   custo
   sem tool clearing    {a.n_passos:>6}   {total_a:>17}   R$ {a.custo_estimado:.4f}
   com tool clearing    {b.n_passos:>6}   {total_b:>17}   R$ {b.custo_estimado:.4f}
   economia                      {economia:>16.1f}%

O que levar daqui:

  - olhe a curva de A: ela CRESCE a cada passo, porque o histórico inteiro
    volta em toda chamada. Em B ela ESTABILIZA — os últimos {MANTER_INTEGROS} resultados
    inteiros mais um marcador de ~30 tokens por passo antigo;

  - tool clearing é CÓDIGO, não modelo: nenhuma chamada extra de LLM. A
    compaction (resumir o histórico com o modelo) custa uma chamada e
    destrói mais; use quando isto aqui não bastar;

  - a tática ZERO vale mais que as quatro: encurte o retorno das suas
    ferramentas. Uma ferramenta que devolve 900 tokens quando 60 bastam é
    defeito de projeto — nenhuma compressão conserta a origem;

  - e o preço, dito sem eufemismo: compressão é perda de informação com
    aparência de continuidade. O agente segue funcionando, com uma memória
    que alguém editou. Quando ele errar por causa disso, não vai parecer
    erro de memória — vai parecer burrice do modelo.

  - o que um resumo NUNCA pode perder: o objetivo, as decisões tomadas, as
    ESCRITAS EXECUTADAS com seus identificadores, os erros já cometidos e os
    fatos numéricos. Perder o id de uma escrita faz o agente escrever duas
    vezes — e aí quem salva é a chave de idempotência do script 05.
""")
