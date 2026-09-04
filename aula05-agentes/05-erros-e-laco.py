# Aula 05 — Arquitetura de agentes
# 05 — ERRO RECUPERÁVEL × FATAL, E O DETECTOR DE LAÇO.
#
# O script central da aula. Ele mostra duas coisas, nesta ordem de
# importância:
#
#   1. A MENSAGEM DE ERRO É PROMPT. A aula 03 estabeleceu que a DESCRIÇÃO da
#      ferramenta é prompt; o corolário quase nunca é dito: o retorno de erro
#      é o único texto que o modelo lê para decidir COMO SE CORRIGIR.
#
#   2. O detector de laço é a rede de segurança para quando (1) não bastar.
#      Repare, no fim: com um erro bem escrito, o detector NEM DISPARA.
#      A maior parte do ganho está em não precisar dele.
#
# SUGESTÃO DE USO EM SALA: rode primeiro só a parte A, com o detector
# desligado, e peça à turma que preveja quantos passos o agente vai dar.
# Deixe o contador de tokens e o custo na tela até bater o teto.

import agente
from agente import Orcamento, ErroRecuperavel, rodar, resumo
from dados import CLIENTES

LINHA = "=" * 78

# O agente vai precisar do id do cliente. O formato real é C-001; o modelo
# tende a escrever C-1. É o erro RECUPERÁVEL que queremos provocar.
OBJETIVO = ("Descubra quantos chamados abertos tem o cliente do pedido "
            "48219 e diga o nome dele.")

original = agente.consultar_cliente


def cliente_erro_inutil(cliente_id: str) -> dict:
    """A versão que quase todo mundo escreve sem pensar. Verdadeira e sem
    ação possível: o modelo não sabe o que fazer com isto."""
    if cliente_id not in CLIENTES:
        raise ErroRecuperavel("não encontrado")
    return {"id": cliente_id, **CLIENTES[cliente_id]}


def rodar_condicao(rotulo, ferramenta, com_detector, max_passos):
    print(f"\n{LINHA}\n{rotulo}\n")
    agente.FERRAMENTAS["consultar_cliente"] = ferramenta
    try:
        estado = rodar(OBJETIVO,
                       orcamento=Orcamento(max_passos=max_passos,
                                           max_reais=0.10),
                       fase="analise", com_detector=com_detector,
                       limite_laco=3)
    finally:
        agente.FERRAMENTAS["consultar_cliente"] = original
    print(f"\n   {resumo(estado)}")
    if estado.resposta:
        print(f"   resposta: {estado.resposta[:100]}")
    repetidas = len(estado.passos) - len({
        (p.ferramenta, str(sorted(p.argumentos.items())))
        for p in estado.passos})
    print(f"   chamadas repetidas: {repetidas}")
    return estado


print(f"objetivo: {OBJETIVO}")
print("(o formato do id é C-001; o modelo quase sempre tenta C-1 primeiro)")

# A) erro inútil + detector DESLIGADO -> o agente gira até o teto
a = rodar_condicao(
    "A) erro inútil ({'erro': 'não encontrado'}), detector DESLIGADO",
    cliente_erro_inutil, com_detector=False, max_passos=10)

# B) erro inútil + detector LIGADO -> o detector intervém e depois aborta
b = rodar_condicao(
    "B) o MESMO erro inútil, detector LIGADO",
    cliente_erro_inutil, com_detector=True, max_passos=10)

# C) erro que ENSINA -> o modelo se corrige sozinho, na volta seguinte
c = rodar_condicao(
    "C) erro que ENSINA (o que errou, qual era o certo, o que fazer agora)",
    original, com_detector=True, max_passos=10)

print(f"\n{LINHA}")
print(f"{'condição':<34} {'término':<22} {'passos':>7} {'tokens':>8} {'custo':>10}")
for nome, e in [("A erro inútil, sem detector", a),
                ("B erro inútil, com detector", b),
                ("C erro que ensina", c)]:
    print(f"{nome:<34} {e.termino.value:<22} {e.n_passos:>7} "
          f"{e.tokens_gastos:>8} R$ {e.custo_estimado:>7.4f}")

print(f"""
O que levar daqui:

  - compare A e C. Mesmo modelo, mesma ferramenta, mesma tarefa. A única
    diferença é o TEXTO do erro:

        {{"erro": "não encontrado"}}

        {{"erro": "cliente não encontrado",
         "esperado": "C seguido de 3 dígitos, ex: C-001",
         "recebido": "C-1",
         "sugestao": "obtenha o id do cliente em consultar_pedido"}}

    O segundo responde as três perguntas que o modelo precisa responder para
    agir: o que estava errado, qual era o certo, o que fazer agora;

  - em A, o diagnóstico que você recebe é "orçamento esgotado" — que é o
    diagnóstico ERRADO para o problema certo. `max_passos` limita o dano do
    laço; ele não DETECTA o laço;

  - em B o detector intervém antes de abortar: injeta a observação e dá mais
    uma chance. Só aborta se voltar a repetir;

  - em C o detector provavelmente nem disparou. Quando você escreve bons
    retornos de erro, a rede de segurança fica sem uso — e é esse o objetivo.

  - e a regra que separa os dois mecanismos de recuperação:

        retry automático  ->  falha de TRANSPORTE (429, 500, timeout)
        volta ao modelo   ->  falha de CONTEÚDO   (argumento inválido)

    repetir uma chamada determinística com os mesmos argumentos é retry sem
    informação nova: uma forma lenta de falhar.
""")
