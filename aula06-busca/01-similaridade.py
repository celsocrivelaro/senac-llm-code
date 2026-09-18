# Aula 06 — 01: SIMILARIDADE, na mão.
#
# Quatro linhas de numpy e o primeiro buscador do curso. Nenhuma biblioteca
# de busca envolvida: ordenar por cosseno JÁ É buscar.
#
# Dois pontos que o script demonstra e que a intuição erra:
#   1. a faixa de valores reais NÃO é de 0 a 1;
#   2. similaridade não é relevância — o trecho mais parecido com a pergunta
#      costuma ser a repetição dela em outras palavras.

import os
import time

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError



load_dotenv()


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

# --------------------------------------------------------------- O EMBEDDING
#
# Este script é AUTOCONTIDO: o cliente e o `embutir` abaixo aparecem iguais
# no 00, no 01 e no 02. É repetição de propósito — cada um dos três demonstra
# um fenômeno diferente e precisa poder ser lido inteiro, sem abrir outro
# arquivo. O 03 e o 04 compartilham o `busca.py`, porque não são três
# demonstrações: são a mesma máquina em dois momentos.
#
# Repare no que NÃO existe aqui: nenhuma chamada de geração. Este modelo não
# escreve texto, e é a primeira vez no curso que o modelo é usado assim.

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)
MODELO_EMBEDDING = os.environ.get("LLM_MODELO_EMBEDDING", "mistral-embed")

# Contador do processo: quantas chamadas e quantos tokens. Serve para ver a
# ASSIMETRIA — o corpus entra uma vez, a pergunta entra sempre.
CONSUMO = {"chamadas": 0, "tokens": 0}


def embutir(textos: list[str], tentativas: int = 5) -> np.ndarray:
    """Transforma uma lista de textos numa matriz (n_textos, n_dimensoes).

    O retry é o mesmo da aula 02 (nota 01 §8.2): backoff exponencial para
    falha de TRANSPORTE. Erro de conteúdo não tem retry.
    """
    for tentativa in range(tentativas):
        try:
            resposta = client.embeddings.create(
                model=MODELO_EMBEDDING, input=textos)
            break
        except (RateLimitError, APIConnectionError):
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)

    uso = resposta.usage
    CONSUMO["chamadas"] += 1
    CONSUMO["tokens"] += uso.total_tokens

    # A API devolve os vetores na ordem da entrada, mas o campo `index`
    # existe justamente para não se depender disso.
    vetores = sorted(resposta.data, key=lambda d: d.index)
    return np.array([v.embedding for v in vetores], dtype=np.float32)


def embutir_um(texto: str) -> np.ndarray:
    return embutir([texto])[0]


def resumo_consumo(rotulo: str = "consumo") -> str:
    return (f"{rotulo}: {CONSUMO['chamadas']} chamadas · "
            f"{CONSUMO['tokens']:,} tokens").replace(",", ".")


def cosseno(a: np.ndarray, b: np.ndarray) -> float:
    """Similaridade de cosseno entre dois vetores.

    Por que cosseno e não distância euclidiana: o comprimento do texto vira
    NORMA do vetor, e comprimento não deveria pesar na comparação de
    significado. O cosseno olha só o ângulo — divide a norma fora.
    """
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def cosseno_lote(consulta: np.ndarray, matriz: np.ndarray) -> np.ndarray:
    """O mesmo cálculo, de um vetor contra N — em uma operação só."""
    normas = np.linalg.norm(matriz, axis=1) * np.linalg.norm(consulta)
    return (matriz @ consulta) / normas


def ranquear(consulta_vec: np.ndarray, matriz: np.ndarray,
             rotulos: list[str], k: int = 5) -> list[tuple[str, float]]:
    """Ordena os rótulos por similaridade decrescente. ISTO JÁ É UM BUSCADOR:
    não há biblioteca de busca envolvida, só uma multiplicação de matriz.

    Mora neste script, e não no módulo compartilhado, porque é o único lugar
    que ranqueia uma lista solta de frases. Do 03 em diante quem ranqueia é
    o `Indice`, que faz exatamente esta conta sobre chunks.
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

print("=" * 74)
print("O CÁLCULO")
print("=" * 74)
print("""
    cosseno(a, b) = (a · b) / (||a|| * ||b||)

Por que cosseno e não distância euclidiana: o COMPRIMENTO do texto vira a
norma do vetor, e comprimento não deveria pesar na comparação de significado.
O cosseno olha só o ângulo — divide a norma fora.
""")

matriz = embutir(FRASES)
pergunta = "Quanto posso gastar em uma refeição durante uma viagem?"

print("=" * 74)
print(f"BUSCA: {pergunta!r}")
print("=" * 74)
print()

for rotulo, score in ranquear(embutir_um(pergunta), matriz,
                               [f[:62] for f in FRASES], k=len(FRASES)):
    barra = "█" * int(score * 50)
    print(f"  {score:.4f}  {barra:<50s}  {rotulo}")

print("""
Repare na FAIXA. As frases sobre futebol e previsão do tempo não têm relação
nenhuma com a pergunta, e ainda assim não chegam perto de zero. Textos em
português compartilham estrutura, e o vetor captura isso.

Consequência prática: um limiar absoluto escolhido no chute ("aceito acima
de 0,8") não funciona. O que funciona é o RANKING — e, quando for preciso um
corte, ele se calibra com dados, como o script 03 faz.
""")

# ------------------------------------------------- similaridade ≠ relevância
print("=" * 74)
print("SIMILARIDADE NÃO É RELEVÂNCIA")
print("=" * 74)

vec_pergunta = embutir_um(RELEVANCIA["pergunta"])
print(f"\npergunta: {RELEVANCIA['pergunta']!r}\n")

resultados = []
for letra, trecho in RELEVANCIA["trechos"]:
    score = cosseno(vec_pergunta, embutir_um(trecho))
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

print(f"\n{resumo_consumo('TOTAL DO SCRIPT')}")
