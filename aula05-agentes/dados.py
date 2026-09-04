# Aula 05 — Arquitetura de agentes
# Dados compartilhados por todos os scripts da aula.
#
# O domínio é o MESMO das aulas 01-03 (a transportadora) de propósito: o
# assunto de hoje é ARQUITETURA, e trocar de domínio ao mesmo tempo faria
# você gastar atenção com o problema em vez de com a solução.
#
# O exercício 04 usa um domínio diferente — prestação de contas — porque lá
# a escolha da arquitetura é sua, e um domínio novo impede que você resolva
# copiando daqui.

from datetime import date

HOJE = date(2026, 9, 15)          # data fixa: o laboratório precisa ser reproduzível

# --------------------------------------------------------------- os pedidos
PEDIDOS = {
    "48219": {"situacao": "em transporte",     "previsao": "2026-09-02",
              "transportadora": "RápidoLog",   "cliente": "C-001"},
    "77310": {"situacao": "entregue",          "previsao": "2026-08-19",
              "transportadora": "RápidoLog",   "cliente": "C-002"},
    "90455": {"situacao": "aguardando coleta", "previsao": "2026-09-22",
              "transportadora": "TransBrasil", "cliente": "C-001"},
    "31002": {"situacao": "em transporte",     "previsao": "2026-09-18",
              "transportadora": "TransBrasil", "cliente": "C-003"},
    "55870": {"situacao": "em transporte",     "previsao": "2026-09-05",
              "transportadora": "RápidoLog",   "cliente": "C-002"},
}

CLIENTES = {
    "C-001": {"nome": "Ana Souza",   "desde": "2021", "chamados_abertos": 0},
    "C-002": {"nome": "Bruno Lima",  "desde": "2019", "chamados_abertos": 2},
    "C-003": {"nome": "Célia Rocha", "desde": "2024", "chamados_abertos": 0},
}

CHAMADOS = {}                     # preenchido por abrir_chamado()

CATEGORIAS = ["entrega_atrasada", "endereco_errado", "produto_avariado",
              "duvida", "elogio"]

# ------------------------------------------------------- o lote de mensagens
# Usado pelo 00-roteador.py. A mistura é deliberada: a MAIORIA é consulta de
# status pura, que uma regra resolve sem chamar o modelo. Se você mandar tudo
# para o LLM, funciona — e custa dez vezes mais.
MENSAGENS = [
    "Qual o status do pedido 48219?",
    "onde está meu pedido 31002",
    "Status 90455 por favor",
    "quero saber do 55870",
    "O pedido 48219 está atrasado há duas semanas e ninguém me responde. "
    "Isso é um absurdo, quero uma solução hoje.",
    "Consta que o 77310 foi entregue mas eu não recebi nada. "
    "Falei com o porteiro e ele também não viu.",
    "A caixa do 55870 chegou rasgada e o produto está trincado",
    "vocês entregam em Portugal?",
    "Só queria dizer que a entrega do 31002 foi rapidíssima, parabéns!",
    "meu pedido não chegou",                      # sem número: falta informação
]

# --------------------------------------------------- preços (aula 02, nota 04)
# Ajuste para os preços reais do seu modelo. O ponto do laboratório não é o
# número exato — é EXISTIR um número, para o orçamento em reais ter sentido.
PRECO_ENTRADA = 0.60              # R$ por milhão de tokens de entrada
PRECO_SAIDA = 1.80                # R$ por milhão de tokens de saída


def custo(tokens_entrada: int, tokens_saida: int) -> float:
    return (tokens_entrada * PRECO_ENTRADA + tokens_saida * PRECO_SAIDA) / 1_000_000
