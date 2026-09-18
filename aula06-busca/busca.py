# Aula 06 — Embeddings e busca semântica
# Módulo do BUSCADOR, compartilhado pelo 03-chunking.py e pelo 04-buscador.py.
#
# Só esses dois importam daqui, e o motivo é que só esses dois são a mesma
# máquina: o 03 escolhe o corte medindo recall@k, o 04 entrega o buscador
# com o corte que ganhou. O 00, o 01 e o 02 são demonstrações conceituais
# independentes e carregam a própria cópia do `embutir` — cada um se lê
# inteiro sem abrir este arquivo.
#
# Repare no que NÃO existe aqui: nenhuma chamada de geração. Este módulo não
# escreve texto, e é a primeira vez no curso que o modelo é usado assim.

import os
import re
import time

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)
MODELO_EMBEDDING = os.environ.get("LLM_MODELO_EMBEDDING", "mistral-embed")

# Contador do processo: quantas chamadas e quantos tokens. Serve para ver a
# ASSIMETRIA — o corpus entra uma vez, a pergunta entra sempre.
CONSUMO = {"chamadas": 0, "tokens": 0}


# ============================================================ EMBEDDING

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


# ============================================================ SIMILARIDADE

def cosseno_lote(consulta: np.ndarray, matriz: np.ndarray) -> np.ndarray:
    """O mesmo cálculo, de um vetor contra N — em uma operação só."""
    normas = np.linalg.norm(matriz, axis=1) * np.linalg.norm(consulta)
    return (matriz @ consulta) / normas


# ============================================================ CHUNKING
#
# O chunk é a UNIDADE DE RECUPERAÇÃO: é ele que volta da busca, e é ele que
# vai chegar ao leitor sem o texto em volta. Portanto precisa fazer sentido
# sozinho — e é esse o critério que separa as estratégias de corte.
#
# Só o corte POR ESTRUTURA mora aqui, porque só ele roda em produção: é o
# que o 04-buscador.py usa. As outras duas
# estratégias existem para PERDER a comparação do 03-chunking.py, e é lá
# que elas moram.

RE_ARTIGO = re.compile(r"^Art\. \d+[ºo]?\b", re.M)
RE_PARAGRAFO = re.compile(r"^§\d+[ºo]?", re.M)


def por_estrutura(texto: str) -> list[dict]:
    """Cortar por artigo e parágrafo.

    O documento JÁ VEM CORTADO pelo autor — artigos e parágrafos são a
    unidade de sentido que o legislador escolheu. Ignorar esse corte é jogar
    informação fora de graça.

    Cada chunk carrega o cabeçalho do artigo a que pertence, para que o
    parágrafo faça sentido isolado: "§2º Em viagem internacional, o limite
    de que trata o §1º passa a R$ 260,00" não significa nada sem saber que
    o artigo é o das despesas com alimentação.
    """
    chunks: list[dict] = []
    artigo_atual = ""
    cabecalho = ""

    for bloco in [b.strip() for b in texto.strip().split("\n\n") if b.strip()]:
        linhas = bloco.split("\n")
        if RE_ARTIGO.match(linhas[0]):
            artigo_atual = linhas[0].split("—")[0].strip().rstrip(".")
            cabecalho = linhas[0].strip()
            corpo = "\n".join(linhas[1:]).strip()
        else:
            corpo = bloco

        paragrafos = _partir_paragrafos(corpo)
        if not paragrafos:                       # artigo sem § (o caput)
            chunks.append({"id": artigo_atual or "preambulo",
                           "texto": bloco.strip()})
            continue

        for marca, trecho in paragrafos:
            chunks.append({
                "id": f"{artigo_atual} {marca}" if marca else artigo_atual,
                "texto": f"{cabecalho}\n{trecho}" if cabecalho else trecho,
            })
    return chunks


def _partir_paragrafos(corpo: str) -> list[tuple[str, str]]:
    """Devolve [(marca, texto)] por parágrafo. Marca vazia = caput."""
    marcas = list(RE_PARAGRAFO.finditer(corpo))
    if not marcas:
        return [("", corpo)] if corpo else []

    partes = []
    if marcas[0].start() > 0:
        caput = corpo[:marcas[0].start()].strip()
        if caput:
            partes.append(("", caput))
    for i, m in enumerate(marcas):
        fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(corpo)
        partes.append((m.group().strip(), corpo[m.start():fim].strip()))
    return partes


# ============================================================ O ÍNDICE

class Indice:
    """Um índice em memória: os chunks, seus vetores e nada mais.

    Com 40 chunks, busca linear em numpy é instantânea — não há motivo para
    um banco vetorial ainda. Ele entra na aula 07, quando o índice precisa
    SOBREVIVER ao processo.
    """

    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.matriz = embutir([c["texto"] for c in chunks])

    def buscar(self, pergunta: str, k: int = 3) -> list[dict]:
        scores = cosseno_lote(embutir_um(pergunta), self.matriz)
        ordem = np.argsort(-scores)[:k]
        return [{**self.chunks[i], "score": float(scores[i])} for i in ordem]

    def __len__(self) -> int:
        return len(self.chunks)


# ============================================================ O CONSUMO

def resumo_consumo(rotulo: str = "consumo") -> str:
    return (f"{rotulo}: {CONSUMO['chamadas']} chamadas · "
            f"{CONSUMO['tokens']:,} tokens").replace(",", ".")
