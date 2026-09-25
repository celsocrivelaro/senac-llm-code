# Aula 08 — A memória EPISÓDICA: o que aconteceu, e quando.
#
# Emprega o mesmo mecanismo da aula 07 sobre outro objeto: em vez de indexar
# documentos, indexa EPISÓDIOS — o registro do que o agente fez numa
# execução anterior, e no que deu.
#
# A estrutura é um banco vetorial porque a consulta dirigida a ela — "já
# ocorreu algo parecido com isto?" — é uma pergunta sobre assunto, e não
# admite chave de acesso. Compare com `memoria_semantica.py`, cuja consulta
# admite.

import shutil

import chromadb

from armazenamento import BASE
from embedding import gerar_matrix_embbeddings, gerar_vetor_embeddings


class MemoriaEpisodica:

    def __init__(self, recriar: bool = True):
        caminho = BASE / "episodica"
        if recriar and caminho.exists():
            shutil.rmtree(caminho)
        self.cliente = chromadb.PersistentClient(path=str(caminho))
        self.colecao = self.cliente.get_or_create_collection(
            name="episodios", metadata={"hnsw:space": "cosine"})

    def gravar(self, episodios: list[dict]) -> None:
        if not episodios:
            return
        textos = [e["resumo"] for e in episodios]
        self.colecao.add(
            ids=[e["id"] for e in episodios],
            documents=textos,
            # A data vai como METADADO, não como texto. É o que permite
            # desempatar por tempo em código — o vetor não faria isso.
            metadatas=[{"data": e["data"], "funcionario": e.get("funcionario", ""),
                        "veredito": e.get("veredito", "")} for e in episodios],
            embeddings=gerar_matrix_embbeddings(textos).tolist(),
        )

    def recuperar(self, consulta: str, k: int = 3,
                  funcionario: str | None = None,
                  veredito: str | None = None) -> list[dict]:
        """Filtra por metadado ANTES de ordenar por similaridade.

        O filtro por `veredito` é a resposta à cegueira de NEGAÇÃO (nota 02
        da aula 06): "aprovado" e "reprovado" são quase idênticos para o
        vetor, e nenhum ajuste de busca corrige isso. Polaridade é campo
        com domínio fechado, e campo se filtra na consulta.
        """
        filtros = [{k_: v} for k_, v in
                   (("funcionario", funcionario), ("veredito", veredito))
                   if v]
        onde = filtros[0] if len(filtros) == 1 else (
            {"$and": filtros} if filtros else None)
        r = self.colecao.query(
            query_embeddings=[gerar_vetor_embeddings(consulta).tolist()],
            n_results=k, where=onde)
        return [{"id": i, "resumo": d, **m, "distancia": dist}
                for i, d, m, dist in zip(r["ids"][0], r["documents"][0],
                                         r["metadatas"][0], r["distances"][0])]

    def esquecer_funcionario(self, funcionario: str) -> int:
        antes = self.colecao.count()
        self.colecao.delete(where={"funcionario": funcionario})
        return antes - self.colecao.count()

    def __len__(self) -> int:
        return self.colecao.count()
