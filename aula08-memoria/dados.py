# Aula 08 — Memória
# O dado compartilhado da aula, em duas peças:
#
#   EPISODIOS    as dez execuções antigas a indexar — a massa sobre a qual
#                toda a aula trabalha, o que o agente já fez e no que deu
#   CHECKPOINT   uma dessas execuções na forma ÍNTEGRA — o estado inteiro,
#                serializável — que é o assunto dos dois primeiros scripts
#
# Os demais dados residem no script que os utiliza: os fatos contraditórios
# no 04, a atividade de classificação no 01, a data de referência no 04, e a
# tarefa corrente nos três scripts que a reexecutam, com texto idêntico.
#
# O laboratório é autocontido: nada aqui é importado de outra aula. A
# duplicação evita que a alteração do dado de uma aula invalide a outra. No
# caso específico, o import sequer seria possível: `from dados import ...`
# dentro de um arquivo chamado `dados.py` reimporta o próprio módulo, e
# Python interrompe com "partially initialized module".
#
# =============================================================== OS EPISÓDIOS
#
# EPISÓDIO é o termo da literatura para a unidade que a memória episódica
# guarda: o registro de um acontecimento, com o que foi feito, quando, e
# qual foi o resultado.
#
# São dez execuções anteriores do agente de prestação de contas, com acertos
# erros. É o que a memória EPISÓDICA indexa: não documentos, e sim o que o
# próprio agente fez.
#
# `data` existe porque similaridade não desempata data (aula 06, cegueira
# TEMPO). O bloco 5 depende deste campo.

EPISODIOS = [
    {"id": "exec-0a1f", "data": "2026-03-12", "funcionario": "F-088",
     "despesa": "D-4102", "veredito": "aprovado",
     "resumo": "Refeição de R$ 84,00 em viagem a Curitiba. Dentro do teto "
               "de R$ 120,00 do Art. 4º §1º, com nota fiscal.",
     "passos": 3, "tokens": 1820},

    {"id": "exec-3b7c", "data": "2026-03-28", "funcionario": "F-088",
     "despesa": "D-4188", "veredito": "aprovado",
     "resumo": "Jantar de R$ 312,00 para três pessoas em Lisboa. Aplicado o "
               "Art. 4º §2º (viagem internacional, teto R$ 260,00 por pessoa) "
               "combinado com o §3º (limite individual por participante).",
     "passos": 6, "tokens": 4310},

    {"id": "exec-5d20", "data": "2026-04-04", "funcionario": "F-091",
     "despesa": "D-4210", "veredito": "reprovado",
     "resumo": "Corrida de R$ 130,00 sem justificativa escrita. Excede o teto "
               "do Art. 5º §1º e não atende ao §2º.",
     "passos": 4, "tokens": 2240},

    {"id": "exec-7e93", "data": "2026-04-19", "funcionario": "F-091",
     "despesa": "D-4233", "veredito": "aprovado",
     "resumo": "Corrida de R$ 118,00 com justificativa de trajeto noturno. "
               "Art. 5º §2º aplicado, com análise do gestor registrada.",
     "passos": 5, "tokens": 3100},

    {"id": "exec-9a44", "data": "2026-05-08", "funcionario": "F-103",
     "despesa": "D-4301", "veredito": "humano",
     "resumo": "Hospedagem de R$ 1.240,00 encaminhada ao gestor por exceder "
               "a alçada do analista (Art. 9º §1º).",
     "passos": 2, "tokens": 890},

    {"id": "exec-b112", "data": "2026-05-22", "funcionario": "F-088",
     "despesa": "D-4360", "veredito": "aprovado",
     "resumo": "Material de escritório de R$ 48,00 com nota. Dentro do teto "
               "do Art. 7º §1º.",
     "passos": 2, "tokens": 760},

    {"id": "exec-c8d1", "data": "2026-06-15", "funcionario": "F-091",
     "despesa": "D-4402", "veredito": "devolvido",
     "resumo": "Divergência entre valor declarado (R$ 96,00) e recibo "
               "(R$ 196,00). Devolvido sem análise de mérito, Art. 3º §3º.",
     "passos": 4, "tokens": 2510},

    {"id": "exec-d3f8", "data": "2026-07-02", "funcionario": "F-103",
     "despesa": "D-4455", "veredito": "aprovado",
     "resumo": "Refeição de R$ 110,00 em viagem a São Paulo, dentro do teto.",
     "passos": 3, "tokens": 1640},

    {"id": "exec-e770", "data": "2026-08-11", "funcionario": "F-088",
     "despesa": "D-4501", "veredito": "aprovado",
     "resumo": "Refeição de R$ 240,00 por pessoa em Lisboa. Art. 4º §2º.",
     "passos": 4, "tokens": 2380},

    {"id": "exec-f091", "data": "2026-09-03", "funcionario": "F-091",
     "despesa": "D-4560", "veredito": "reprovado",
     "resumo": "Bebida alcoólica incluída na conta do jantar. Art. 4º §4º "
               "veda em qualquer hipótese.",
     "passos": 3, "tokens": 1710},
]


# ============================================================ O CHECKPOINT
#
# O estado de uma execução, serializado: tudo o que ela produziu, inteiro —
# objetivo, passos com argumentos e resultados, ferramentas, término.
#
# Está aqui porque dois scripts o leem: o `00` o constrói passo a passo,
# pausa, grava e retoma; o `01` o contrasta com o fragmento que a memória
# guarda da MESMA execução.
#
# É a execução `exec-0a1f`, a mesma que abre os EPISODIOS acima — e a
# comparação entre as duas formas é o assunto do script 01.

CHECKPOINT = {
    "execucao_id": "exec-0a1f",
    "objetivo": ("Analisar a despesa D-4102 do funcionário F-088: refeição "
                 "de R$ 84,00 por pessoa, em viagem a Curitiba, com nota."),
    "passos": [
        {"indice": 0, "ferramenta": "consultar_historico",
         "argumentos": {"funcionario": "F-088"},
         "resultado": {"viagens_2026": 2, "reprovacoes": 0},
         "tokens_entrada": 380, "tokens_saida": 110},
        {"indice": 1, "ferramenta": "consultar_politica",
         "argumentos": {"categoria": "refeicao"},
         "resultado": {"artigo": "Art. 4º §1º", "teto": 120.0},
         "tokens_entrada": 520, "tokens_saida": 140},
        {"indice": 2, "ferramenta": "registrar_parecer",
         "argumentos": {"despesa": "D-4102", "veredito": "aprovado"},
         "resultado": {"parecer": "P-0993"},
         "tokens_entrada": 540, "tokens_saida": 130},
    ],
    "tokens_gastos": 1820,
    "ferramentas_ativas": ["consultar_historico", "consultar_politica",
                           "registrar_parecer"],
    "termino": "CONCLUIDO",
    "resposta": "Aprovado: R$ 84,00 dentro do teto de R$ 120,00 (Art. 4º §1º).",
    "historico": ["...12 mensagens, omitidas por espaço..."],
}
