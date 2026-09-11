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
