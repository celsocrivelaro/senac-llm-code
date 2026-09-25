# Aula 08 — A memória PROCEDURAL: regras de conduta.
#
# A estrutura é uma lista de regras em texto, injetada no system prompt. Não
# tem índice nem chave: não é recuperada por consulta, e sim aplicada
# integralmente a todas as execuções seguintes.
#
# Essa propriedade define tanto o valor quanto o risco. O valor: o agente
# incorpora correções de comportamento sem alteração de código. O risco: uma
# regra incorreta passa a valer para todas as execuções, e nada no fluxo
# obriga a revisá-la.
#
# É também o tipo de memória que mais escapa a uma remoção sob pedido
# (`04-esquecer-remocao.py`): uma regra derivada do erro de um titular pode
# não conter o identificador dele.

from armazenamento import BASE


class MemoriaProcedural:

    def __init__(self):
        self.caminho = BASE / "procedural.txt"
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        if not self.caminho.exists():
            self.caminho.write_text("", encoding="utf-8")

    def regras(self) -> list[str]:
        return [l.strip() for l in
                self.caminho.read_text(encoding="utf-8").splitlines() if l.strip()]

    def gravar(self, regra: str) -> bool:
        atuais = self.regras()
        if regra in atuais:                       # idempotente
            return False
        self.caminho.write_text("\n".join(atuais + [regra]), encoding="utf-8")
        return True

    def como_system_prompt(self) -> str:
        regras = self.regras()
        if not regras:
            return ""
        return "Procedimentos aprendidos em execuções anteriores:\n" + \
               "\n".join(f"- {r}" for r in regras)
