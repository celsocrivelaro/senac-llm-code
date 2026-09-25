# Aula 08 — A memória SEMÂNTICA: fato estável sobre uma entidade.
#
# A estrutura é uma tabela, armazenada em JSON. A consulta dirigida a ela tem
# chave: o destino frequente de um funcionário é `F-088:destinos_frequentes`,
# e uma chave se resolve por lookup. Recuperar isso por similaridade seria
# mais caro e menos exato.
#
# A comparação com `memoria_episodica.py` é informativa: os dois módulos
# implementam tipos de memória e não compartilham nenhuma linha, porque os
# padrões de acesso são diferentes.

import json

from armazenamento import BASE


class MemoriaSemantica:

    def __init__(self):
        self.caminho = BASE / "semantica.json"
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.fatos: dict[str, dict] = {}
        if self.caminho.exists():
            self.fatos = json.loads(self.caminho.read_text(encoding="utf-8"))

    def gravar(self, entidade: str, chave: str, valor, data: str) -> dict:
        """Chave de idempotência derivada do CONTEÚDO (aula 05, nota 02 §8):
        a mesma execução processada duas vezes não gera dois fatos."""
        id_fato = f"{entidade}:{chave}"
        anterior = self.fatos.get(id_fato)
        if anterior and anterior["valor"] == valor:
            return {**anterior, "ja_existia": True}

        registro = {"entidade": entidade, "chave": chave, "valor": valor,
                    "data": data, "substituiu": anterior["valor"] if anterior else None}
        self.fatos[id_fato] = registro
        self._persistir()
        return registro

    def ler(self, entidade: str, chave: str):
        f = self.fatos.get(f"{entidade}:{chave}")
        return f["valor"] if f else None

    def sobre(self, entidade: str) -> dict:
        return {f["chave"]: f["valor"] for f in self.fatos.values()
                if f["entidade"] == entidade}

    def esquecer(self, entidade: str) -> int:
        alvos = [k for k, f in self.fatos.items() if f["entidade"] == entidade]
        for k in alvos:
            del self.fatos[k]
        self._persistir()
        return len(alvos)

    def _persistir(self) -> None:
        self.caminho.write_text(
            json.dumps(self.fatos, ensure_ascii=False, indent=2),
            encoding="utf-8")
