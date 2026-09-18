# Aula 06 — Embeddings e RAG
# O CORPUS da aula, e só ele.
#
# Está aqui porque dois scripts o usam — o 02 o corta de três formas e o 03
# o indexa. O resto dos dados mora no script que o consome: o trio de
# relevância no 01, as dez perguntas com resposta conhecida no 02, os
# exemplares de rota no 04 e as três perguntas do RAG no 05.
#
# O domínio é a PRESTAÇÃO DE CONTAS, o mesmo do exercício da aula 05. Nas
# aulas 01-05 o conhecimento do agente vinha de um dict escrito à mão; aqui
# ele passa a vir de um documento que ninguém vai estruturar.

# ============================================================ O REGULAMENTO
#
# Documento normativo fictício, escrito com a estrutura de um de verdade:
# artigos, parágrafos e incisos numerados. Essa estrutura NÃO é decoração —
# é a informação que a estratégia de chunking por estrutura aproveita e a
# estratégia por contagem de caracteres joga fora.

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

