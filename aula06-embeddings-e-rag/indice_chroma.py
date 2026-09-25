# Aula 06 — O índice que sobrevive ao processo.
#
# O `indice_memoria.py` guarda os vetores num arranjo de numpy que morre
# junto com o script. Para 40 chunks isso basta, e é por isso que ele
# atravessa as três primeiras partes da aula.
#
# A troca por um BANCO DE VETORES não é motivada por desempenho — com 40
# chunks a busca exaustiva é imperceptível. É motivada por PERSISTÊNCIA:
# reconstruir o índice a cada execução custa uma chamada de embedding sobre
# o corpus inteiro, toda vez.
#
# O Chroma não embute nada. Os vetores são calculados aqui, pelo mesmo
# `embedding.py` das demais aulas, e entregues prontos. Manter o cálculo
# fora do banco impede que ele passe a usar um segundo modelo de embedding
# sem que a mudança apareça no código.

from pathlib import Path

import chromadb

from embedding import gerar_matrix_embbeddings, gerar_vetor_embeddings
from estrategias_chunking import por_estrutura

BANCO = Path(__file__).parent / "indice"


class IndiceChroma:
    """A mesma interface do `IndiceMemoria`: recebe corpus, devolve trechos.

    O que muda é onde os vetores ficam entre uma execução e outra — e o par
    de nomes é a diferença inteira.
    """

    def __init__(self, corpus: str, nome: str = "regulamento"):
        self.cliente = chromadb.PersistentClient(path=str(BANCO))
        self.colecao = self.cliente.get_or_create_collection(
            name=nome, metadata={"hnsw:space": "cosine"})

        # Apagar antes de inserir: o `add` acrescenta, e o banco é
        # persistente. Sem isto, cada execução somaria mais uma cópia do
        # regulamento ao índice. O script 05 explica por quê.
        existentes = self.colecao.get()["ids"]
        if existentes:
            self.colecao.delete(ids=existentes)

        chunks = por_estrutura(corpus)
        self.colecao.add(
            ids=[f"{i:03d}" for i in range(len(chunks))],
            documents=[c["texto"] for c in chunks],
            # O id do artigo vai como METADADO. É ele que a aula 07 usa
            # para conferir a citação.
            metadatas=[{"artigo": c["id"]} for c in chunks],
            embeddings=gerar_matrix_embbeddings(
                [c["texto"] for c in chunks]).tolist(),
        )

    def buscar(self, pergunta: str, k: int = 3) -> list[dict]:
        """Devolve DISTÂNCIA, não similaridade.

        Chroma com `hnsw:space: cosine` devolve d = 1 - cosseno. Distância
        baixa é bom, ao contrário do score da parte 1 — e confundir os dois
        é o erro mais fácil de cometer aqui.
        """
        r = self.colecao.query(
            query_embeddings=[gerar_vetor_embeddings(pergunta).tolist()],
            n_results=k)
        return [{"artigo": m["artigo"], "texto": d, "distancia": dist}
                for d, m, dist in zip(r["documents"][0], r["metadatas"][0],
                                      r["distances"][0])]

    def __len__(self) -> int:
        return self.colecao.count()
