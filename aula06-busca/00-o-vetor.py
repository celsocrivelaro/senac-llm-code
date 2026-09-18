# Aula 06 — 00: O VETOR.
#
# Primeiro contato com um modelo que NÃO GERA TEXTO. A aula 02 (nota 01 §5)
# já tinha apresentado embeddings como modalidade; a aula 01 (nota 01 §6.1)
# já tinha dito de onde eles vêm — a linhagem encoder, que lê o texto inteiro
# de uma vez e produz representação em vez de continuação.
#
# O script tem um assunto só, em dois tempos:
#
#   1. um vetor sozinho não diz NADA — é uma lista de números sem significado
#      individual, e ver isso é uma decepção útil;
#   2. dois vetores dizem TUDO — a comparação entre eles é o único número que
#      a aula inteira vai usar.
#
# O 01 pega daqui: como esse número se calcula, por que cosseno, e como
# ordenar por ele já é buscar.

import os
import time

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError


load_dotenv()

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

    Aqui ela é usada como caixa-preta, só para produzir o número do segundo
    bloco. Por que cosseno, e não distância euclidiana, é assunto do 01.
    """
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# Três textos: o primeiro é a regra, o segundo pergunta a mesma coisa com
# outras palavras, o terceiro não tem relação nenhuma com os dois.
REGRA = "O reembolso de refeições em viagem fica limitado a R$ 120,00."
PARAFRASE = "Quanto posso gastar almoçando numa viagem a trabalho?"
ALHEIO = "O campeonato de futebol começa no próximo domingo às dezesseis horas."

# Uma chamada, três vetores. A API aceita lista, e embutir em lote é o modo
# normal de usá-la — o 03 embute quarenta chunks assim.
vetor_regra, vetor_parafrase, vetor_alheio = embutir([REGRA, PARAFRASE, ALHEIO])

# --------------------------------------------------------------- um vetor
print("=" * 74)
print("UM VETOR SOZINHO NÃO DIZ NADA")
print("=" * 74)

print(f"\ntexto ......... {REGRA!r}")
print(f"dimensão ...... {vetor_regra.shape[0]}")
print(f"norma ......... {np.linalg.norm(vetor_regra):.4f}")
print(f"primeiros 8 ... {np.round(vetor_regra[:8], 4).tolist()}")
print(f"faixa ......... [{vetor_regra.min():.4f}, {vetor_regra.max():.4f}]")

print("""
Nenhuma dessas posições significa alguma coisa isoladamente. Não existe
"a dimensão 42 é o quanto o texto fala de dinheiro", nem a 43, nem nenhuma.
Procurar sentido dentro do vetor é procurar no lugar errado.
""")

# -------------------------------------------------------------- dois vetores
print("=" * 74)
print("DOIS VETORES DIZEM TUDO")
print("=" * 74)

sim_parafrase = cosseno(vetor_regra, vetor_parafrase)
sim_alheio = cosseno(vetor_regra, vetor_alheio)

print(f"\n  A  {REGRA}")
print(f"  B  {PARAFRASE}")
print(f"  C  {ALHEIO}\n")
print(f"  cosseno(A, B) = {sim_parafrase:.4f}   <- dizem a mesma coisa, sem "
      f"compartilhar quase nenhuma palavra")
print(f"  cosseno(A, C) = {sim_alheio:.4f}   <- não têm relação nenhuma")

print(f"""
É este o número que a aula inteira usa. O sentido não está DENTRO do vetor:
está ENTRE vetores, e aparece só quando há mais de um para comparar.

Repare que A e B quase não compartilham palavras — "refeições"/"almoçando",
"limitado"/"gastar" — e ainda assim ficam em {sim_parafrase:.2f}. É isso que a busca
por palavra-chave não faz, e é a razão de o embedding existir.

E repare no outro número: A e C não têm relação nenhuma e mesmo assim dão
{sim_alheio:.2f}, não zero. Por que o piso não é zero, e o que fazer com isso, é o
assunto do script 01.""")

print(f"\n{resumo_consumo('TOTAL DO SCRIPT')}")
