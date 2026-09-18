# Aula 06 — 05: O BANCO VETORIAL.
#
# Os scripts 02 e 03 guardaram os vetores numa matriz de numpy. Funciona, e
# a aula defendeu essa escolha com número. Este script troca a matriz por um
# BANCO DE VETORES e mostra as quatro coisas que se precisa saber sobre um:
#
#   1. como ele funciona por dentro, e por que a busca não é exaustiva;
#   2. quanto tempo ele leva — medido, não afirmado;
#   3. como se INSERE (id, documento, metadado, vetor);
#   4. como se BUSCA, em quatro situações diferentes;
#   5. como se LÊ o que volta.
#
# O banco aqui é o Chroma, escolhido por ser o mais simples: roda embutido,
# num diretório local, sem serviço para subir. O que se aprende aqui vale
# para Pinecone, Weaviate, Qdrant e Milvus — a API muda, o modelo não.

import shutil
import time
from pathlib import Path

import chromadb
import numpy as np

from dados import REGULAMENTO
from embedding import gerar_matrix_embbeddings, gerar_vetor_embeddings
from estrategias_chunking import por_estrutura
from similaridade import cosseno_lote

BANCO = Path(__file__).parent / "indice-demo"


def numero_do_artigo(id_chunk: str) -> int:
    """'Art. 4º §1º' -> 4. Vira metadado, e é o que permite filtrar."""
    digitos = "".join(c for c in id_chunk.split("§")[0] if c.isdigit())
    return int(digitos) if digitos else 0


# ============================================================ COMO SE INSERE
print("=" * 74)
print("1. COMO SE INSERE")
print("=" * 74)

chunks = por_estrutura(REGULAMENTO)
vetores = gerar_matrix_embbeddings([c["texto"] for c in chunks])

if BANCO.exists():
    shutil.rmtree(BANCO)
cliente = chromadb.PersistentClient(path=str(BANCO))
colecao = cliente.get_or_create_collection(
    name="regulamento", metadata={"hnsw:space": "cosine"})

# Quatro listas paralelas, e é sempre assim em qualquer banco vetorial:
colecao.add(
    ids=[f"{i:03d}" for i in range(len(chunks))],          # a chave
    documents=[c["texto"] for c in chunks],                # o texto original
    metadatas=[{"artigo": c["id"],                         # o que dá para filtrar
                "numero": numero_do_artigo(c["id"]),
                "tamanho": len(c["texto"])} for c in chunks],
    embeddings=vetores.tolist(),                           # o vetor, pronto
)

print(f"""
  chunks inseridos ..... {colecao.count()}
  dimensão do vetor .... {vetores.shape[1]}
  chamadas de API ...... 1 (uma, com os {len(chunks)} textos juntos)

As quatro listas acima são o modelo de dados inteiro de um banco vetorial:

  ids         a chave primária. Reinserir o mesmo id SUBSTITUI.
  documents   o texto original. O banco guarda, não interpreta.
  metadatas   os campos estruturados — é por eles que se FILTRA.
  embeddings  o vetor. Repare que ele vai PRONTO: o banco não embute nada.

Esse último ponto é decisão de projeto, não detalhe. Muitos bancos aceitam
embutir por você; fazer isso esconde qual modelo produziu os vetores, e o
dia em que ele mudar o índice inteiro muda de significado sem aviso.""")

# ============================================================ COMO SE BUSCA
print("\n" + "=" * 74)
print("2. COMO SE BUSCA — quatro situações")
print("=" * 74)

# ---- situação 1: a busca comum
PERGUNTA = "qual o teto de refeição em viagem?"
v_pergunta = gerar_vetor_embeddings(PERGUNTA)
r = colecao.query(query_embeddings=[v_pergunta.tolist()], n_results=3)

print(f"\n  [1] BUSCA COMUM — os k mais próximos\n      {PERGUNTA!r}\n")
for artigo, dist in zip([m["artigo"] for m in r["metadatas"][0]],
                        r["distances"][0]):
    print(f"        {artigo:<14s} distância {dist:.4f}")

# ---- situação 2: busca com filtro de metadado
r_filtrada = colecao.query(query_embeddings=[v_pergunta.tolist()], n_results=3,
                           where={"numero": 9})

print(f"\n  [2] BUSCA FILTRADA — a mesma pergunta, só no Art. 9º\n")
for artigo, dist in zip([m["artigo"] for m in r_filtrada["metadatas"][0]],
                        r_filtrada["distances"][0]):
    print(f"        {artigo:<14s} distância {dist:.4f}")
print("""
      O filtro roda ANTES da comparação de vetores, e é a resposta para
      metade das cegueiras: faixa de valor, data e identificador se
      resolvem aqui, com `==` e `<=`, não com cosseno.""")

# ---- situação 3: o texto procurando a si mesmo
# O primeiro chunk é o preâmbulo e não tem id de artigo; pego o primeiro que
# tem, para a saída ficar legível.
alvo = next(c for c in chunks if c["id"].startswith("Art."))
r_igual = colecao.query(
    query_embeddings=[gerar_vetor_embeddings(alvo["texto"]).tolist()],
    n_results=1)
print(f"\n  [3] O TEXTO PROCURANDO A SI MESMO — o piso de baixo\n")
print(f"        {r_igual['metadatas'][0][0]['artigo']:<14s} "
      f"distância {r_igual['distances'][0][0]:.4f}   <- praticamente zero")

# ---- situação 4: a pergunta fora do domínio
FORA = "qual o índice de reajuste da tabela de fretes marítimos?"
r_fora = colecao.query(
    query_embeddings=[gerar_vetor_embeddings(FORA).tolist()], n_results=1)
d_fora = r_fora["distances"][0][0]
print(f"\n  [4] PERGUNTA FORA DO DOMÍNIO — o piso de cima\n      {FORA!r}\n")
print(f"        {r_fora['metadatas'][0][0]['artigo']:<14s} "
      f"distância {d_fora:.4f}   <- NÃO é um número alto")

# ============================================================ COMO SE LÊ
print("\n" + "=" * 74)
print("3. COMO SE ENTENDE O RESULTADO")
print("=" * 74)

print(f"""
O retorno do Chroma é um dicionário de LISTAS DE LISTAS, porque a API aceita
várias consultas de uma vez. Com uma consulta só, tudo mora no índice [0]:

  r["ids"][0]         {r["ids"][0]}
  r["distances"][0]   {[round(d, 4) for d in r["distances"][0]]}
  r["metadatas"][0]   {[m["artigo"] for m in r["metadatas"][0]]}
  r["documents"][0]   os textos, na mesma ordem

E o número que volta é DISTÂNCIA, não score. Com métrica de cosseno:

    distância = 1 - cosseno        ->   BAIXO é bom

  situação                    distância   cosseno
  ------------------------------------------------
  texto igual a si mesmo       {r_igual['distances'][0][0]:.4f}     {1 - r_igual['distances'][0][0]:.4f}
  pergunta pertinente          {r['distances'][0][0]:.4f}     {1 - r['distances'][0][0]:.4f}
  pergunta fora do domínio     {d_fora:.4f}     {1 - d_fora:.4f}

Repare na última linha: a pergunta que o regulamento NÃO responde não veio
com distância alta. Veio em {1 - d_fora:.4f} de cosseno, que é o piso que o script 01
mediu entre textos sem relação nenhuma.

    O BANCO NÃO SABE DIZER "NÃO TENHO ISSO". Ele devolve os k mais
    próximos, sempre, mesmo que os k sejam todos irrelevantes.

Quem decide se o mais próximo é próximo o bastante é o seu código — e é o
portão do script 06.""")

# ============================================================ QUAIS TEMPOS
print("\n" + "=" * 74)
print("4. QUAIS TEMPOS")
print("=" * 74)

REPETICOES = 200
v = v_pergunta

t0 = time.perf_counter()
for _ in range(REPETICOES):
    scores = cosseno_lote(v, vetores)
    _ = np.argsort(-scores)[:3]
t_numpy = (time.perf_counter() - t0) / REPETICOES * 1000

t0 = time.perf_counter()
for _ in range(REPETICOES):
    colecao.query(query_embeddings=[v.tolist()], n_results=3)
t_chroma = (time.perf_counter() - t0) / REPETICOES * 1000

print(f"""
Mesma pergunta, mesmos {len(chunks)} chunks, {REPETICOES} repetições, sem contar a
chamada de API:

  numpy, comparando com TODOS ..... {t_numpy:7.3f} ms
  Chroma .......................... {t_chroma:7.3f} ms

Com {len(chunks)} vetores, o banco não ganha nada — e pode até perder, porque paga
overhead de serialização para economizar comparações que custam quase nada.

O ganho está na ESCALA, e vem de não comparar com todos:

  busca exaustiva       compara com os n vetores        O(n)
  busca aproximada      navega um grafo de vizinhos     ~O(log n)

O algoritmo que o Chroma usa é o HNSW — um grafo de várias camadas, com
ligações longas em cima e vizinhança densa embaixo, percorrido de cima para
baixo. É "aproximado" num sentido preciso: ele pode não devolver o vizinho
mais próximo de verdade. Em troca, atende milhões de vetores em
milissegundos.

  n = 28          exaustivo é instantâneo       o banco é desnecessário
  n = 100 mil     exaustivo ainda é viável      o banco começa a compensar
  n = 10 milhões  exaustivo é inviável          o banco é obrigatório

    A PERGUNTA NÃO É "BANCO OU NUMPY". É QUANTOS VETORES VOCÊ TEM.

E, nesta aula, o argumento para usar um banco NÃO é velocidade: é
PERSISTÊNCIA. O índice em numpy morre com o processo, e reconstruí-lo custa
uma chamada de embedding sobre o corpus inteiro, toda vez.""")
