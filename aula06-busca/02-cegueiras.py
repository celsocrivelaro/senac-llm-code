# Aula 06 — 02: O QUE O EMBEDDING NÃO VÊ.
#
# O script central da aula. Sem ele, a aula é "vetor, cosseno, pronto" e o
# aluno sai achando que busca semântica resolve tudo.
#
# COMO USAR EM SALA: para cada par, leia os dois textos em voz alta e peça
# que a turma PREVEJA a similaridade ANTES de apertar Enter. A previsão erra,
# e é o erro que fixa. Registre no quadro o previsto e o obtido.
#
# Rode com --sem-pausa para pular a interação.

import os
import sys
import time

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError



load_dotenv()


# ============================================================ AS CEGUEIRAS
#
# Pares de texto para o bloco 3. Cada par tem uma SIMILARIDADE ESPERADA pela
# intuição e uma similaridade REAL — e a distância entre as duas é a aula.
#
# O par de controle existe para calibrar: sem ele, ninguém sabe se 0,85 é
# alto. Textos reais quase nunca ficam abaixo de 0,5, e a intuição de que o
# cosseno varia de 0 a 1 na prática está errada.

CEGUEIRAS = [
    {"nome": "NEGAÇÃO",
     "a": "a despesa foi aprovada pelo analista",
     "b": "a despesa foi reprovada pelo analista",
     "previsao": "baixa — os textos afirmam o oposto",
     "licao": "o vetor não representa negação. 'aprovado' e 'reprovado' "
              "ocorrem nos mesmos contextos, e é isso que o embedding captura."},

    {"nome": "NÚMERO",
     "a": "o teto de reembolso é de R$ 120,00 por refeição",
     "b": "o teto de reembolso é de R$ 260,00 por refeição",
     "previsao": "baixa — os valores decidem coisas diferentes",
     "licao": "números são quase invisíveis para o vetor. Comparar valor é "
              "trabalho de `==` e de comparação numérica, não de cosseno."},

    {"nome": "ENTIDADE",
     "a": "análise da despesa D-4471 do funcionário F-088",
     "b": "análise da despesa D-4472 do funcionário F-091",
     "previsao": "baixa — são registros distintos",
     "licao": "identificador não é significado. Buscar um id por similaridade "
              "devolve todos os ids do mesmo formato."},

    {"nome": "TEMPO",
     "a": "em março de 2026, o teto de refeição passou a ser R$ 120,00",
     "b": "em agosto de 2026, o teto de refeição passou a ser R$ 150,00",
     "previsao": "baixa — um dos dois está revogado",
     "licao": "o vetor não tem noção de anterioridade. Guarde esta cegueira: "
              "ela volta na aula 08, quando dois fatos verdadeiros em datas "
              "diferentes disputarem a mesma pergunta."},

    {"nome": "CONTROLE",
     "a": "a despesa foi aprovada pelo analista",
     "b": "a previsão do tempo indica chuva no litoral norte",
     "previsao": "baixa — não têm relação nenhuma",
     "licao": "ESTE é o valor de referência. Compare os quatro anteriores com "
              "ele: a diferença entre 'opostos' e 'sem relação' é enorme para "
              "quem lê e quase nula para o vetor."},
]

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



PAUSA = "--sem-pausa" not in sys.argv

print("=" * 74)
print("O QUE O EMBEDDING NÃO VÊ")
print("=" * 74)

resultados = []

for caso in CEGUEIRAS:
    print(f"\n{'-' * 74}\n{caso['nome']}\n{'-' * 74}")
    print(f"  A: {caso['a']!r}")
    print(f"  B: {caso['b']!r}")
    print(f"\n  intuição: similaridade {caso['previsao']}")

    if PAUSA:
        input("\n  [Enter para revelar]")

    score = cosseno(embutir_um(caso["a"]), embutir_um(caso["b"]))
    resultados.append((caso["nome"], score))

    barra = "█" * int(score * 50)
    print(f"\n  OBTIDO: {score:.4f}  {barra}")
    print(f"\n  {caso['licao']}")

# ------------------------------------------------------------------ o quadro
print(f"\n{'=' * 74}")
print("O QUADRO COMPLETO")
print("=" * 74)
print()

controle = dict(resultados).get("CONTROLE")
for nome, score in resultados:
    barra = "█" * int(score * 50)
    marca = "  <-- referência: textos SEM RELAÇÃO" if nome == "CONTROLE" else ""
    print(f"  {nome:<10s} {score:.4f}  {barra}{marca}")

if controle is not None:
    piores = [(n, e) for n, e in resultados if n != "CONTROLE"]
    menor = min(piores, key=lambda x: x[1])
    print(f"""
A leitura que importa é a comparação com o CONTROLE.

Textos que afirmam o OPOSTO ficam em {dict(piores)['NEGAÇÃO']:.4f}. Textos sem relação nenhuma
ficam em {controle:.4f}. Para quem lê, a distância entre "aprovado" e "reprovado" é
total; para o vetor, é menor que a distância entre qualquer um dos dois e
uma frase sobre o tempo.

O par mais próximo do controle é {menor[0]} ({menor[1]:.4f}) — e mesmo esse não chega lá.""")

print("""
A CONCLUSÃO PRÁTICA, e é a mesma lição da aula 05 num lugar novo:

    REGRA DETERMINÍSTICA ONDE ELA EXISTE.

Valor se compara com `<=`. Identificador se compara com `==`. Data se compara
com `<`. Nenhum desses três é trabalho de cosseno, e usar o vetor para isso
é caro e errado ao mesmo tempo.

O vetor serve para o que sobra — e o que sobra é bastante: encontrar o
trecho que TRATA do assunto, entre quarenta que não tratam.
""")

print(resumo_consumo("TOTAL DO SCRIPT"))
