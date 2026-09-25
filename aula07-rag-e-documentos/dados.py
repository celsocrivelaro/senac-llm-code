# Aula 07 — RAG e Documentos
# Dados da aula. O laboratório é autocontido: o regulamento, as perguntas e a
# tabela de preços são cópias da aula 06, e não imports.
#
# A duplicação é deliberada. Na aula 06 o regulamento era o objeto de estudo,
# com três estratégias de corte medidas sobre ele em `recall@k`. Nesta aula
# ele é o corpus de partida e precisa ser modificado: o `CORPUS_COM_RUIDO`
# definido abaixo acrescenta um parágrafo revogado que não existe na aula 06.
# Manter cópias independentes permite a modificação sem invalidar a medição
# da outra aula.
#
# O domínio é a prestação de contas, o mesmo desde o exercício da aula 05.
# Preço da Mistral por milhão de tokens (mesma conta da aula 02, nota 04).
# O preço por token de embedding é uma ordem de grandeza menor que o de
# geração, o que altera a aritmética de custo desta aula.
PRECO_ENTRADA = 0.60
PRECO_SAIDA = 1.80
PRECO_EMBEDDING = 0.10


def custo(entrada: int, saida: int = 0) -> float:
    return entrada * PRECO_ENTRADA / 1e6 + saida * PRECO_SAIDA / 1e6


def custo_embedding(tokens: int) -> float:
    return tokens * PRECO_EMBEDDING / 1e6


# ============================================================ O REGULAMENTO
#
# Documento normativo fictício, redigido com a estrutura de um documento
# real: artigos, parágrafos e incisos numerados. A estrutura é funcional — é
# a informação que a estratégia de chunking por estrutura utiliza como
# fronteira de corte, e que a estratégia por contagem de caracteres descarta.

REGULAMENTO = """
POLÍTICA DE REEMBOLSO DE DESPESAS — Vigência a partir de 01/01/2026

Art. 1º — Do objeto.
Esta política estabelece as condições de reembolso de despesas incorridas
por colaboradores no exercício de suas atribuições, os limites aplicáveis
por categoria e as alçadas de aprovação.

Art. 2º — Das definições.
§1º Considera-se despesa reembolsável aquela realizada em razão do serviço,
comprovada por documento fiscal quando exigido, e submetida no prazo do
Art. 8º.
§2º Considera-se viagem a serviço o deslocamento com pernoite fora do
município de lotação do colaborador.
§3º Considera-se viagem internacional aquela cujo destino esteja fora do
território nacional, independentemente da duração.

Art. 3º — Da comprovação.
§1º A nota fiscal é obrigatória para as categorias alimentação, hospedagem
e material.
§2º Para a categoria transporte, o recibo do aplicativo ou o comprovante de
corrida substitui a nota fiscal.
§3º Divergência entre o valor declarado e o valor constante do comprovante
implica devolução do pedido ao colaborador, sem análise de mérito.

Art. 4º — Das despesas com alimentação.
§1º O reembolso de refeições em viagem a serviço fica limitado a R$ 120,00
por pessoa por refeição, exigida a nota fiscal.
§2º Em viagem internacional, o limite de que trata o §1º passa a R$ 260,00
por pessoa por refeição.
§3º Quando a refeição envolver representantes de cliente, o limite do §1º
aplica-se individualmente a cada participante, devendo constar do pedido a
relação nominal dos presentes.
§4º Bebida alcoólica não é reembolsável em nenhuma hipótese.

Art. 5º — Das despesas com transporte.
§1º O reembolso de deslocamento urbano fica limitado a R$ 90,00 por corrida.
§2º Corrida que exceda o limite do §1º pode ser reembolsada mediante
justificativa escrita do colaborador, sujeita à análise do gestor.
§3º Não são reembolsáveis multas, estacionamento em via irregular e
deslocamento entre a residência e o local de lotação.

Art. 6º — Das despesas com hospedagem.
§1º O reembolso de hospedagem fica limitado a R$ 380,00 por diária, exigida
a nota fiscal.
§2º Em viagem internacional, o limite do §1º passa a R$ 640,00 por diária.
§3º Despesas de frigobar, lavanderia e serviços de quarto não integram a
diária e não são reembolsáveis.

Art. 7º — Das despesas com material.
§1º O reembolso de material de escritório fica limitado a R$ 50,00 por item,
exigida a nota fiscal.
§2º Equipamento de informática não se enquadra nesta categoria e segue o
processo de compra, não o de reembolso.

Art. 8º — Dos prazos.
§1º O pedido de reembolso deve ser submetido em até 30 dias corridos
contados da data da despesa.
§2º Pedido submetido fora do prazo do §1º é indeferido, ressalvada
justificativa aceita pelo gestor da área.

Art. 9º — Das alçadas de aprovação.
§1º Despesas de até R$ 500,00 são aprovadas pelo analista de prestação de
contas.
§2º Despesas acima de R$ 500,00 e até R$ 5.000,00 dependem de aprovação do
gestor da área.
§3º Despesas acima de R$ 5.000,00 dependem de aprovação da diretoria.

Art. 10 — Das vedações gerais.
§1º É vedado o reembolso de despesa de terceiro que não seja colaborador,
salvo o disposto no Art. 4º §3º.
§2º É vedado o fracionamento de despesa com o objetivo de contornar os
limites desta política.
§3º A reincidência na conduta do §2º sujeita o colaborador às medidas
disciplinares cabíveis.
"""


# ============================================================ AS PERGUNTAS
#
# Dez perguntas com resposta conhecida. O conjunto é o primeiro dataset de
# avaliação do curso, e a aula 11 o retoma sob o nome de conjunto de eval.
#
# Construir o conjunto é a parte custosa do trabalho de avaliação; calcular a
# métrica sobre ele é trivial em comparação.
#
# O campo `artigo` registra o trecho do regulamento que responde a pergunta,
# e é o gabarito contra o qual o `recall@k` é calculado.

PERGUNTAS = [
    {"pergunta": "Qual o teto de reembolso para uma refeição em viagem?",
     "artigo": "Art. 4º §1º"},
    {"pergunta": "Quanto posso gastar em refeição numa viagem para Portugal?",
     "artigo": "Art. 4º §2º"},
    {"pergunta": "Jantar com três pessoas do cliente: o teto vale para o total?",
     "artigo": "Art. 4º §3º"},
    {"pergunta": "Posso pedir reembolso de vinho no jantar de negócios?",
     "artigo": "Art. 4º §4º"},
    {"pergunta": "Qual o limite por corrida de aplicativo?",
     "artigo": "Art. 5º §1º"},
    {"pergunta": "A corrida passou do limite mas era madrugada. Tem jeito?",
     "artigo": "Art. 5º §2º"},
    {"pergunta": "Preciso de nota fiscal para táxi?",
     "artigo": "Art. 3º §2º"},
    {"pergunta": "O recibo mostra valor diferente do que declarei. O que acontece?",
     "artigo": "Art. 3º §3º"},
    {"pergunta": "Uma despesa de R$ 1.240 é aprovada por quem?",
     "artigo": "Art. 9º §2º"},
    {"pergunta": "Perdi o prazo de envio. Ainda dá para pedir?",
     "artigo": "Art. 8º §2º"},
]


# ============================================================ MODO DE FALHA 4
#
# A versão revogada do Art. 4º §1º. A presença simultânea de versão vigente e
# versão revogada é a condição normal de um acervo documental: revisões
# antigas permanecem no repositório e são indexadas junto com as atuais.
#
# Os dois trechos diferem apenas na magnitude do teto, e portanto são quase
# idênticos para o vetor (cegueira de NÚMERO, script 01). Decidem, no
# entanto, casos diferentes.

REGULAMENTO_REVOGADO = """
POLÍTICA DE REEMBOLSO DE DESPESAS — Revisão 2024 (REVOGADA em 01/01/2026)

Art. 4º — Das despesas com alimentação.
§1º O reembolso de refeições em viagem a serviço fica limitado a R$ 90,00
por pessoa por refeição, exigida a nota fiscal.
"""

# O corpus usado pelos scripts: versão vigente e versão revogada juntas.
CORPUS_COM_RUIDO = REGULAMENTO + "\n" + REGULAMENTO_REVOGADO


# ============================================================ MODO DE FALHA 3
#
# Perguntas cuja resposta não consta do regulamento. Sem um campo de recusa
# no contrato de saída, o pipeline responde a todas e cita fonte, o que torna
# a falha indetectável por leitura da resposta.

SEM_RESPOSTA = [
    "Qual o teto de reembolso para curso de idiomas?",
    "Em quantos dias o reembolso é depositado na conta do colaborador?",
    "Quem aprova a compra de um notebook para o time de tecnologia?",
]


# ============================================================ O CASO DE LISBOA
#
# Pergunta que exige três trechos independentes e que, por isso, não é
# respondida por uma única consulta:
#
#   Art. 4º §1º   o teto da categoria
#   Art. 4º §2º   a exceção para viagem internacional
#   Art. 9º §2º   a alçada de aprovação da faixa de valor resultante
#
# Uma busca recupera um deles. O pipeline produz uma resposta incorreta com
# fonte citada, o que impede a detecção por leitura.
#
# É a mesma despesa do exemplo 4 da nota 03 da aula 05, onde falhou por perda
# de contexto na delegação a um sub-agente. Aqui a causa é outra —
# recuperação insuficiente — e o sintoma é o mesmo.

LISBOA = {
    "pergunta": ("Uma refeição de R$ 340,00 por pessoa em Lisboa, "
                 "durante viagem a serviço, está dentro da política? "
                 "E quem aprova?"),
    "artigos_necessarios": ["Art. 4º §1º", "Art. 4º §2º", "Art. 9º §2º"],
    "resposta_correta": ("Não. Em viagem internacional o teto é de R$ 260,00 "
                         "por pessoa (Art. 4º §2º), e R$ 340,00 o excede. "
                         "Por estar acima de R$ 500,00 no acumulado do pedido, "
                         "a decisão cabe ao gestor da área (Art. 9º §2º)."),
}


# ============================================================ MODO DE FALHA 2
#
# A mesma pergunta sobre os mesmos trechos, em duas ordens de apresentação.
# O recall é idêntico nas duas execuções por construção; se as respostas
# diferem, a causa é a posição do trecho na janela de contexto (`lost in the
# middle`, LIU et al., 2023; aula 02, nota 01 §4.3).

ORDEM = {
    "pergunta": "Qual o teto de refeição em viagem internacional?",
    "artigo_certo": "Art. 4º §2º",
}


# ============================================================ SCHEMAS

SCHEMA_RESPOSTA = {
    "type": "object",
    "properties": {
        "resposta": {"type": "string"},
        "fontes": {"type": "array", "items": {"type": "string"}},
        "suficiente": {"type": "boolean"},
    },
    "required": ["resposta", "fontes", "suficiente"],
    "additionalProperties": False,
}
