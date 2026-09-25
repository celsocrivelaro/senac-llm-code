# Aula 06 — 01: SIMILARIDADE, na mão.
#
# Quatro linhas de numpy e o primeiro buscador do curso. Nenhuma biblioteca
# de busca envolvida: ordenar por cosseno JÁ É buscar.
#
# Dois pontos que o script demonstra e que a intuição erra:
#   1. a faixa de valores reais NÃO é de 0 a 1;
#   2. similaridade não é relevância — o trecho mais parecido com a pergunta
#      costuma ser a repetição dela em outras palavras.


import numpy as np

from embedding import gerar_matrix_embbeddings, gerar_vetor_embeddings
from similaridade import cosseno, cosseno_lote

def ranquear(consulta_vec: np.ndarray, matriz: np.ndarray,
             rotulos: list[str], k: int = 5) -> list[tuple[str, float]]:
    """Ordena os rótulos por similaridade decrescente. ISTO JÁ É UM BUSCADOR:
    não há biblioteca de busca envolvida, só uma multiplicação de matriz.

    Mora neste script, e não no módulo compartilhado, porque é o único lugar
    que ranqueia uma lista solta de frases. Do 02 em diante quem ranqueia é
    o `IndiceMemoria`, que faz exatamente esta conta sobre chunks.
    """
    scores = cosseno_lote(consulta_vec, matriz)
    ordem = np.argsort(-scores)[:k]
    return [(rotulos[i], float(scores[i])) for i in ordem]


FRASES = [
    "O reembolso de refeições em viagem fica limitado a R$ 120,00 por pessoa.",
    "Corridas de aplicativo acima de R$ 90,00 exigem justificativa escrita.",
    "A diária de hotel está limitada a R$ 380,00, com nota fiscal.",
    "Despesas acima de R$ 500,00 dependem de aprovação do gestor da área.",
    "O pedido deve ser enviado em até 30 dias corridos da data da despesa.",
    "Bebida alcoólica não é reembolsável em nenhuma hipótese.",
    "Material de escritório tem limite de R$ 50,00 por item.",
    "Não são reembolsáveis multas nem estacionamento em via irregular.",
    "A previsão do tempo indica chuva no litoral norte nesta semana.",
    "O campeonato de futebol começa no próximo domingo às dezesseis horas.",
]

matriz = gerar_matrix_embbeddings(FRASES)
pergunta = "Quanto posso gastar em uma refeição durante uma viagem?"

print("=" * 74)
print(f"BUSCA: {pergunta!r}")
print("=" * 74)
print()

# Os rótulos que aparecem na saída: a frase cortada, só para caber na tela.
rotulos = [f[:62] for f in FRASES]

vetor_pergunta = gerar_vetor_embeddings(pergunta)

for rotulo, score in ranquear(vetor_pergunta, matriz, rotulos, k=len(FRASES)):
    barra = "█" * int(score * 50)
    print(f"  {score:.4f}  {barra:<50s}  {rotulo}")

print("""
A FAIXA é o que importa aqui. As frases sobre futebol e previsão do tempo
não têm relação alguma com a pergunta, e ainda assim não se aproximam de
zero. Textos em português compartilham estrutura, e o vetor a representa.

Consequência prática: um limiar absoluto escolhido no chute ("aceito acima
de 0,8") não funciona. O que funciona é o RANKING — e, quando for preciso um
corte, ele se calibra com dados, como o script 02 faz.
""")

# ============================================================ SIMILARIDADE ≠ RELEVÂNCIA
#
# Uma pergunta, três trechos. O mais PARECIDO com a pergunta é a repetição
# dela em outras palavras; o que a RESPONDE é outro.

RELEVANCIA = {
    "pergunta": "Qual o teto de reembolso para refeição em viagem?",
    "trechos": [
        ("A", "Dúvidas sobre o teto de reembolso para refeição em viagem "
              "devem ser encaminhadas ao setor de prestação de contas."),
        ("B", "Art. 4º §1º — O reembolso de refeições em viagem a serviço "
              "fica limitado a R$ 120,00 por pessoa por refeição."),
        ("C", "O colaborador deve apresentar a nota fiscal no prazo de "
              "30 dias corridos contados da data da despesa."),
    ],
    "responde": "B",
}

print("=" * 74)
print("SIMILARIDADE NÃO É RELEVÂNCIA")
print("=" * 74)

vec_pergunta = gerar_vetor_embeddings(RELEVANCIA["pergunta"])
print(f"\npergunta: {RELEVANCIA['pergunta']!r}\n")

resultados = []
for letra, trecho in RELEVANCIA["trechos"]:
    score = cosseno(vec_pergunta, gerar_vetor_embeddings(trecho))
    resultados.append((score, letra, trecho))

for score, letra, trecho in sorted(resultados, reverse=True):
    marca = "  <-- É O QUE RESPONDE" if letra == RELEVANCIA["responde"] else ""
    print(f"  {score:.4f}  [{letra}] {trecho[:58]}...{marca}")

vencedor = max(resultados)[1]
if vencedor != RELEVANCIA["responde"]:
    print(f"""
O trecho mais PARECIDO é o [{vencedor}] — que é a pergunta reescrita e não
responde nada. O que RESPONDE é o [{RELEVANCIA['responde']}], e ele não ficou em primeiro.

É a distinção que organiza o resto da aula: o buscador ordena por
SIMILARIDADE, e o que se quer é RELEVÂNCIA. As duas coincidem com
frequência, e é justamente por isso que a diferença passa despercebida
até o dia em que custa caro.""")
else:
    print(f"""
Neste corpus o trecho certo [{RELEVANCIA['responde']}] ficou em primeiro — mas repare na distância
para o [A], que é a pergunta reescrita e não responde nada. A margem é
estreita, e é a margem que a aula 07 vai atacar.""")
