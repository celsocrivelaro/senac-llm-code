# Aula 08 — 02: A MEMÓRIA PROCEDURAL — regras de conduta.
#
# A MEMÓRIA PROCEDURAL registra regras de conduta: como agir diante de uma
# situação recorrente. A estrutura é uma lista de regras em texto.
#
# Ela difere das outras duas numa propriedade: NÃO É RECUPERADA. Não há
# consulta, não há índice, não há chave — as regras são injetadas
# integralmente no system prompt de todas as execuções seguintes.
#
# Essa propriedade define o valor e o risco, que são o mesmo fato visto de
# dois lados. O valor: o agente incorpora correções de comportamento sem
# alteração de código. O risco: uma regra incorreta passa a valer em todas as
# execuções, e nada no fluxo obriga a revisá-la.
#
# CUSTO DE CONSULTA: zero chamadas, mas custo FIXO de janela em toda execução
# — o texto ocupa contexto mesmo quando nenhuma regra se aplica ao caso.

from memoria_procedural import MemoriaProcedural

print("=" * 74)
print("PROCEDURAL — como agir  (texto, no system prompt)")
print("=" * 74)

procedural = MemoriaProcedural()
procedural.gravar("Quando o recibo diverge do valor declarado, devolver o "
                  "pedido antes de analisar o mérito (Art. 3º §3º).")
procedural.gravar("Ids de funcionário têm o formato F seguido de três "
                  "dígitos; F-88 é erro de digitação de F-088.")

print(f"\n{procedural.como_system_prompt()}")

print(f"""
  {len(procedural.regras())} regras · custo fixo de janela em TODA execução
""")

# --------------------------------------------------------- de onde ela vem
#
# As duas regras acima não foram escritas por um projetista: derivam de
# incidentes. A primeira, de um pedido devolvido tarde demais; a segunda, do
# erro de digitação `F-88` que a trajetória do script 00 registra.
#
# O par INCIDENTE -> REGRA é o que caracteriza este tipo de memória. Uma
# regra que não tem incidente de origem é configuração, e configuração
# pertence ao código.
print("=" * 74)
print("A ESCRITA É IDEMPOTENTE")
print("=" * 74)
print()

de_novo = procedural.gravar("Ids de funcionário têm o formato F seguido de "
                            "três dígitos; F-88 é erro de digitação de F-088.")
print(f"  gravar a mesma regra de novo: {de_novo}  (False = já existia)")
print(f"  total de regras: {len(procedural.regras())}")
