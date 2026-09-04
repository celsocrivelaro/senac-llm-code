# Aula 05 — Arquitetura de agentes
# 03 — O MESMO LAÇO, COM ESTADO EXPLÍCITO.
#
# Compare este script com o `04-tool-calling.py` da aula 03. O padrão é o
# mesmo ReAct, o modelo é o mesmo, as ferramentas são as mesmas.
#
# O que mudou é o que o programa CARREGA:
#
#     aula 03:  mensagens[]  é o estado E é o transporte
#     aula 05:  Estado       é o estado
#               mensagens[]  é DERIVADO do estado
#
# Isso não deixa o agente mais inteligente. Deixa o agente OBSERVÁVEL — que
# é a pré-condição de tudo o que vem nos scripts 04, 05 e 06.
#
# Rode e olhe o objeto no fim: ele responde, sem parsing, as sete perguntas
# que a lista de mensagens não responde.

import json
from dataclasses import asdict

from agente import Estado, Orcamento, rodar, resumo, FASES
from dados import HOJE

PERGUNTA = ("O cliente diz que o pedido 48219 não chegou. "
            "Verifique a situação e diga se há atraso.")

print(f"objetivo: {PERGUNTA}")
print(f"hoje: {HOJE} | ferramentas da fase `analise`: {FASES['analise']}")
print("(repare: `abrir_chamado` NÃO está declarada — restrição por "
      "arquitetura, não por prompt)\n")

estado = rodar(PERGUNTA,
               orcamento=Orcamento(max_passos=8, max_tokens=20_000,
                                   max_reais=0.05, max_segundos=90),
               fase="analise")

print("\n" + "=" * 78)
print(f"RESPOSTA: {estado.resposta}\n")
print(resumo(estado))

# ----------------------------------------- o que a lista de mensagens não sabe
print("\n" + "=" * 78)
print("O QUE O ESTADO RESPONDE (e `mensagens[]` não responderia):\n")
print(f"  quantos passos?          {estado.n_passos}")
print(f"  quantos tokens?          {estado.tokens_gastos}")
print(f"  quanto custou?           R$ {estado.custo_estimado:.4f}")
print(f"  qual era o objetivo?     {estado.objetivo[:50]}...")
print(f"  alguma ferramenta falhou? "
      f"{[p.ferramenta for p in estado.passos if p.erro] or 'nenhuma'}")
print(f"  alguma chamada repetiu?  "
      f"{len({(p.ferramenta, json.dumps(p.argumentos, sort_keys=True)) for p in estado.passos})}"
      f" assinaturas distintas em {estado.n_passos} passos")
print(f"  por que parou?           {estado.termino.value}")

print("\n" + "=" * 78)
print("A TRAJETÓRIA, como DADO (não como texto dentro de content):\n")
for p in estado.passos:
    marca = "ERRO" if p.erro else "ok  "
    print(f"  passo {p.indice}  {marca}  {p.ferramenta}({p.argumentos})")
    print(f"           -> {json.dumps(p.resultado, ensure_ascii=False)[:88]}")

print(f"""
{'=' * 78}
Este objeto foi gravado em checkpoints/{estado.execucao_id}.json.

Ele tem nome: é um TRACE. Você acabou de escrever o primeiro do curso, e
ele é a matéria-prima das aulas de observabilidade e de evals.

    Não se avalia o que não se rastreia.
""")
