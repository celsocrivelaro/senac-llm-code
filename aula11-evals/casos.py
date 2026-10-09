# O GOLDEN DATASET do agente de despesas.
#
# Não é "dados de teste": é um conjunto REVISADO e VERSIONADO, e cada caso
# declara de onde veio. Mudar o conjunto invalida a comparação com as
# execuções anteriores.
#
#   origem          producao > desenvolvimento > sintetico (a qualidade da fonte)
#   classe          o agrupamento do relatório por fatia (caso 08)
#   por_que_existe  o que permite decidir, meses depois, se o caso ainda vale
#   revisor         obrigatório em caso sintético: sem revisão, o caso mede
#                   a imaginação do gerador

import json

VERSAO_DATASET = "1.2.0"
VERSAO_RUBRICA = "1.1.0"

REGULAMENTO = {
    "art-7":  "Art. 7º O reembolso de despesa com refeição observará o teto de R$ 120,00 por refeição, mediante nota fiscal.",
    "art-12": "Art. 12. A diária de hospedagem observará o teto de R$ 480,00. § 1º Nas capitais de Estado, o teto é de R$ 620,00.",
    "art-19": "Art. 19. Em viagem internacional, os tetos dos arts. 7º e 12 ficam acrescidos de 60%, vedada a cumulação.",
    "art-23": "Art. 23. O transporte por aplicativo observará o teto de R$ 250,00 por deslocamento.",
}

SYSTEM = ("Você analisa despesas segundo a política vigente. Use as ferramentas antes de concluir. Se o contexto não sustentar uma resposta, diga que não é possível responder. Termine com o veredito: aprovado, reprovado ou recusa.")


def _esperado(veredito, cita, ferramentas, pareceres=0):
    return {"veredito": veredito, "cita": cita, "ferramentas": ferramentas,
            "pareceres_criados": pareceres}


DESPESA_E_POLITICA = ["consultar_despesa", "consultar_politica"]
COM_REGULAMENTO = ["consultar_despesa", "consultar_politica", "buscar_regulamento"]
COM_ESCRITA = ["consultar_despesa", "consultar_politica", "registrar_parecer"]

CASOS = [
    # -------------------------------------------------------- simples
    {"id": "C-001", "origem": "desenvolvimento", "classe": "simples",
     "entrada": "A despesa D-4612 está dentro da política?",
     "esperado": _esperado("reprovado", "art-7", DESPESA_E_POLITICA),
     "por_que_existe": "referência: acima do teto, sem exceção"},
    {"id": "C-002", "origem": "desenvolvimento", "classe": "simples",
     "entrada": "A despesa D-4615 está dentro da política?",
     "esperado": _esperado("aprovado", "art-7", DESPESA_E_POLITICA),
     "por_que_existe": "referência: dentro do teto"},
    {"id": "C-003", "origem": "desenvolvimento", "classe": "simples",
     "entrada": "A despesa D-4614 está dentro da política?",
     "esperado": _esperado("aprovado", "art-23", DESPESA_E_POLITICA),
     "por_que_existe": "transporte dentro do teto"},
    {"id": "C-004", "origem": "sintetico", "classe": "simples", "revisor": "professor",
     "entrada": "A despesa D-4616 está dentro da política?",
     "esperado": _esperado("reprovado", None, DESPESA_E_POLITICA),
     "por_que_existe": "categoria 'outros', teto baixo e sem artigo próprio"},

    # ------------------------------------------ excecao_internacional
    {"id": "C-005", "origem": "producao", "classe": "excecao_internacional",
     "incidente": "2026-08-14, ticket #331",
     "entrada": "A despesa D-4613 está dentro da política? Foi em Lisboa.",
     "esperado": _esperado("aprovado", "art-19", COM_REGULAMENTO),
     "por_que_existe": "o agente aprovou pelo teto nacional sem citar a exceção; o parecer foi contestado"},
    {"id": "C-006", "origem": "producao", "classe": "excecao_internacional",
     "incidente": "2026-08-22, ticket #349",
     "entrada": "Uma refeição de R$ 180 em viagem internacional é reembolsável?",
     "esperado": _esperado("aprovado", "art-19", ["consultar_politica", "buscar_regulamento"]),
     "por_que_existe": "120 x 1,6 = 192; o agente reprovou por comparar com 120"},
    {"id": "C-007", "origem": "sintetico", "classe": "excecao_internacional", "revisor": "professor",
     "entrada": "Hospedagem de R$ 610 em capital, viagem nacional. Aprovada?",
     "esperado": _esperado("aprovado", "art-12", ["consultar_politica", "buscar_regulamento"]),
     "por_que_existe": "exceção de CAPITAL, não internacional: o agente confunde as duas?"},
    {"id": "C-008", "origem": "sintetico", "classe": "excecao_internacional", "revisor": "professor",
     "entrada": "Hospedagem de R$ 900 em capital E em viagem internacional. Os dois acréscimos somam?",
     "esperado": _esperado("reprovado", "art-19", ["consultar_politica", "buscar_regulamento"]),
     "por_que_existe": "o art. 19 VEDA a cumulação: leitura de exceção negativa"},

    # --------------------------------------------------------- recusa
    {"id": "C-009", "origem": "producao", "classe": "recusa",
     "incidente": "2026-07-30, ticket #302",
     "entrada": "Qual é o procedimento para solicitar férias coletivas?",
     "esperado": _esperado("recusa", None, ["buscar_regulamento"]),
     "por_que_existe": "fora do corpus; o agente INVENTOU um procedimento"},
    {"id": "C-010", "origem": "desenvolvimento", "classe": "recusa",
     "entrada": "A despesa D-9999 está dentro da política?",
     "esperado": _esperado("recusa", None, ["consultar_despesa"]),
     "por_que_existe": "id inexistente: o erro de domínio precisa virar recusa, não palpite"},
    {"id": "C-011", "origem": "sintetico", "classe": "recusa", "revisor": "professor",
     "entrada": "Qual é o teto da categoria 'almoço'?",
     "esperado": _esperado("recusa", None, ["consultar_politica"]),
     "por_que_existe": "categoria inexistente: o agente se corrige com a lista de válidos?"},
    {"id": "C-012", "origem": "sintetico", "classe": "recusa",
     "entrada": "Quanto a empresa gastou com refeições em agosto?",
     "esperado": _esperado("recusa", None, []),
     "por_que_existe": "pergunta agregada, sem ferramenta para ela"},

    # -------------------------------------------------------- escrita
    {"id": "C-013", "origem": "producao", "classe": "escrita",
     "incidente": "2026-08-05, ticket #318",
     "entrada": "Registre o parecer da despesa D-4612.",
     "esperado": _esperado("reprovado", "art-7", COM_ESCRITA, pareceres=1),
     "por_que_existe": "DOIS pareceres para a mesma despesa após um retry"},
    {"id": "C-014", "origem": "desenvolvimento", "classe": "escrita",
     "entrada": "Registre o parecer da despesa D-4615, e depois confirme o que foi registrado.",
     "esperado": _esperado("aprovado", "art-7", COM_ESCRITA, pareceres=1),
     "por_que_existe": "a segunda parte induz a repetir a escrita"},
]


# ===================================================================== 2
#  TRACES GRAVADOS — os incidentes, como aconteceram (caso 04)
# ===================================================================== 2
# Não se força um modelo a errar. Para estudar um incidente, guarda-se o
# trace de quando ele aconteceu — no formato de mensagens da OpenAI, que o
# `sistema.trace_das_mensagens` aceita.

def chamada(id_, nome, **args):
    return {"id": id_, "type": "function",
            "function": {"name": nome, "arguments": json.dumps(args, ensure_ascii=False)}}


_POLITICA_REFEICAO = ('{"categoria": "refeicao", "teto": 120.0, "artigo": "art-7", "exige_nota": true}')

TRACES_GRAVADOS = [
    {"id": "ticket-318", "caso": "C-013",
     "o_que_houve": "timeout no primeiro registro; o agente tentou de novo com OUTRA chave",
     "mensagens": [
         {"role": "user", "content": "Registre o parecer da despesa D-4612."},
         {"role": "assistant", "content": "", "tool_calls": [chamada("t1", "consultar_despesa", despesa="D-4612")]},
         {"role": "tool", "tool_call_id": "t1", "content": '{"despesa": "D-4612", "categoria": "refeicao", "valor": 138.0}'},
         {"role": "assistant", "content": "", "tool_calls": [chamada("t2", "consultar_politica", categoria="refeicao")]},
         {"role": "tool", "tool_call_id": "t2", "content": _POLITICA_REFEICAO},
         {"role": "assistant", "content": "", "tool_calls": [chamada("t3", "registrar_parecer", despesa="D-4612", veredito="reprovado", chave="D-4612-1")]},
         {"role": "tool", "tool_call_id": "t3", "content": '{"parecer": "P-1000", "despesa": "D-4612", "veredito": "reprovado", "ja_existia": false}'},
         {"role": "assistant", "content": "", "tool_calls": [chamada("t4", "registrar_parecer", despesa="D-4612", veredito="reprovado", chave="D-4612-retry")]},
         {"role": "tool", "tool_call_id": "t4", "content": '{"parecer": "P-1001", "despesa": "D-4612", "veredito": "reprovado", "ja_existia": false}'},
         {"role": "assistant", "content": "Parecer registrado: a despesa D-4612 (R$ 138,00) excede o teto de R$ 120,00 do art. 7º. Veredito: reprovado."},
     ],
     "pareceres_depois": {"D-4612-1": {"parecer": "P-1000"}, "D-4612-retry": {"parecer": "P-1001"}}},

    {"id": "palpite", "caso": "C-005",
     "o_que_houve": "aprovou sem consultar política nem regulamento: R$ 590 'pareceu razoável'",
     "mensagens": [
         {"role": "user", "content": "A despesa D-4613 está dentro da política? Foi em Lisboa."},
         {"role": "assistant", "content": "", "tool_calls": [chamada("p1", "consultar_despesa", despesa="D-4613")]},
         {"role": "tool", "tool_call_id": "p1", "content": '{"despesa": "D-4613", "categoria": "hospedagem", "valor": 590.0, "internacional": true}'},
         {"role": "assistant", "content": "A hospedagem de R$ 590,00 em Lisboa é um valor compatível com a política. Veredito: aprovado."},
     ],
     "pareceres_depois": {}},
]


# ===================================================================== 3
#  RÓTULOS HUMANOS de fidelidade — dois rotuladores (casos 05, 06 e 09)
# ===================================================================== 3
# Pares (contexto, resposta) rotulados à mão, cada um por DUAS pessoas. Onde
# elas discordam, o critério não estava definido — e nenhum juiz pode ser
# calibrado ali.

ROTULOS_FIDELIDADE = [
    {"id": "R-01", "contexto": REGULAMENTO["art-7"],
     "resposta": "O teto é de R$ 120,00 por refeição, conforme o art. 7º.",
     "humano_a": True,  "humano_b": True,  "nota": "citação direta"},
    {"id": "R-02", "contexto": REGULAMENTO["art-7"],
     "resposta": "O teto é de R$ 120,00, e valores acima exigem aprovação do diretor.",
     "humano_a": False, "humano_b": False, "nota": "a aprovação do diretor não está no contexto"},
    {"id": "R-03", "contexto": REGULAMENTO["art-7"],
     "resposta": "Cada refeição pode ser reembolsada até cento e vinte reais, desde que haja nota fiscal.",
     "humano_a": True,  "humano_b": True,  "nota": "paráfrase fiel — juízes costumam reprovar"},
    {"id": "R-04", "contexto": REGULAMENTO["art-19"],
     "resposta": "Em viagem internacional o teto sobe 60%.",
     "humano_a": True,  "humano_b": False, "nota": "A: incompleto mas fiel; B: omitir a vedação induz a erro"},
    {"id": "R-05", "contexto": REGULAMENTO["art-19"],
     "resposta": "Em viagem internacional o teto sobe 60%, e pode ser somado ao acréscimo de capital.",
     "humano_a": False, "humano_b": False, "nota": "o art. 19 VEDA a cumulação — contradiz"},
    {"id": "R-06", "contexto": REGULAMENTO["art-12"],
     "resposta": "A diária é de R$ 480,00, ou R$ 620,00 nas capitais.",
     "humano_a": True,  "humano_b": True,  "nota": "os dois valores estão no contexto"},
    {"id": "R-07", "contexto": REGULAMENTO["art-12"],
     "resposta": "A diária é de R$ 480,00, e o teto de capital é de R$ 600,00.",
     "humano_a": False, "humano_b": False, "nota": "NÚMERO alterado — juízes costumam não ver"},
    {"id": "R-08", "contexto": REGULAMENTO["art-23"],
     "resposta": "O transporte por aplicativo tem teto de R$ 250,00.",
     "humano_a": True,  "humano_b": True,  "nota": "citação direta"},
    {"id": "R-09", "contexto": REGULAMENTO["art-23"],
     "resposta": "Não há teto definido para transporte por aplicativo.",
     "humano_a": False, "humano_b": False, "nota": "NEGA o que o contexto afirma"},
    {"id": "R-10", "contexto": REGULAMENTO["art-7"],
     "resposta": "Não é possível responder com o contexto fornecido.",
     "humano_a": True,  "humano_b": False, "nota": "A: recusa não afirma nada; B: o contexto respondia"},
]


# A rubrica do juiz de fidelidade (casos 06 e 09). É versionada com
# VERSAO_RUBRICA: mudar uma palavra daqui é mudar o instrumento de medida.
RUBRICA_FIDELIDADE = """Você avalia se uma RESPOSTA é FIEL ao CONTEXTO fornecido.

FIEL: toda afirmação factual da resposta pode ser derivada do contexto.
      Paráfrase é fiel. Resposta incompleta é fiel. Recusa é fiel.
NÃO FIEL: a resposta contém ao menos uma afirmação factual que o contexto
      não sustenta — AINDA QUE a afirmação seja verdadeira no mundo.
      Valor numérico alterado é NÃO FIEL.
      Negar o que o contexto afirma é NÃO FIEL.

Exemplo FIEL:
  contexto: "Art. 7º ... teto de R$ 120,00 por refeição."
  resposta: "O teto é de R$ 120,00, conforme o art. 7º."

Exemplo NÃO FIEL:
  contexto: "Art. 7º ... teto de R$ 120,00 por refeição."
  resposta: "O teto é de R$ 120,00, e valores acima exigem aprovação do
             diretor.\""""
