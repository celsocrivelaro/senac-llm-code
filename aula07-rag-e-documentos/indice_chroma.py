# Aula 07 — O índice persistente.
#
# Diferença em relação à aula 06: lá o índice era mantido em memória e
# descartado ao fim do processo, o que é suficiente para 40 chunks. Aqui os
# vetores são gravados em arquivo, porque o corpus é reconstruído entre
# execuções e porque o trabalho da Parte 2 exige persistência.
#
# A interface é a mesma nas duas aulas — recebe corpus, devolve trechos
# ordenados —, e a diferença está apenas em onde os vetores residem entre uma
# execução e outra. Daí o par de nomes: `IndiceMemoria` na aula 06,
# `IndiceChroma` aqui.

import shutil
from pathlib import Path

import chromadb

from embedding import gerar_matrix_embbeddings, gerar_vetor_embeddings
from estrategias_chunking import ESTRATEGIA

BANCO = Path(__file__).parent / "indice"


class IndiceChroma:
    """Índice persistente. O `.db` fica em `indice/` e não é versionado."""

    def __init__(self, corpus: str, nome: str = "regulamento",
                 recriar: bool = True):
        if recriar and BANCO.exists():
            shutil.rmtree(BANCO)

        self.cliente = chromadb.PersistentClient(path=str(BANCO))
        if recriar:
            try:
                self.cliente.delete_collection(nome)
            except Exception:
                pass

        self.colecao = self.cliente.get_or_create_collection(
            name=nome, metadata={"hnsw:space": "cosine"})

        if self.colecao.count() == 0:
            chunks = ESTRATEGIA(corpus)
            # Os embeddings são calculados AQUI, com o mesmo modelo da aula
            # 06, e passados prontos. Chroma guarda e recupera; não embute
            # nada.
            self.colecao.add(
                ids=[f"{i:03d}" for i in range(len(chunks))],
                documents=[c["texto"] for c in chunks],
                metadatas=[{"artigo": c["id"]} for c in chunks],
                embeddings=gerar_matrix_embbeddings(
                    [c["texto"] for c in chunks]).tolist(),
            )

    def buscar(self, pergunta: str, k: int = 3) -> list[dict]:
        r = self.colecao.query(
            query_embeddings=[gerar_vetor_embeddings(pergunta).tolist()],
            n_results=k)
        return [{"artigo": m["artigo"], "texto": d, "distancia": dist}
                for d, m, dist in zip(r["documents"][0], r["metadatas"][0],
                                      r["distances"][0])]

    def __len__(self) -> int:
        return self.colecao.count()
