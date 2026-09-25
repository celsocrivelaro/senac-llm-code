# Aula 08 — 03: AS TRÊS POLÍTICAS DE ESCRITA EM MEMÓRIA.
#
# Decidir O QUE gravar é uma decisão de projeto independente de onde gravar.
# Há três políticas em uso, e elas diferem em custo e em cobertura:
#
#   POLÍTICA          custo                    falha característica
#   ----------------  -----------------------  ------------------------------
#   o agente decide   uma decisão por passo    grava o irrelevante
#   o código extrai   uma chamada por execução não grava o que não foi
#                                              previsto no schema
#   o humano corrige  trabalho humano          não escala
#
# ESCOPO DESTE SCRIPT. Aplica as três políticas à mesma execução e compara o
# conteúdo resultante.
#
# Gravar memória é uma operação de ESCRITA, e está sujeita às regras que a
# disciplina já estabeleceu para escrita: a fronteira leitura/escrita da aula
# 01 (§3) e a chave de idempotência da aula 05 (nota 02 §8). Processar a
# mesma execução duas vezes não pode produzir dois fatos.

from escrita import extrair_pelo_codigo
from memoria_semantica import MemoriaSemantica

EXECUCAO = """
Execução exec-f2a0, 06/10/2026. Objetivo: analisar a despesa D-4612 do
funcionário F-088 (refeição de R$ 245,00 por pessoa, Lisboa, com nota).

passo 0  consultar_historico(F-88)  -> erro: funcionário inexistente
         (esperado: F seguido de três dígitos, ex: F-088)
passo 1  consultar_historico(F-088) -> duas viagens a Lisboa em 2026
passo 2  consultar_politica(refeicao) -> Art. 4º §1º teto R$ 120,00;
         §2º viagem internacional teto R$ 260,00
passo 3  registrar_parecer(D-4612, aprovado) -> P-1188

Resultado: aprovado, R$ 245,00 dentro do teto de R$ 260,00 do Art. 4º §2º.
Consumo: 4 passos, 2.410 tokens, 1.180 ms, R$ 0,0061.
"""

# ------------------------------------------------- política 1: o agente decide
print("=" * 74)
print("POLÍTICA 1 — O AGENTE DECIDE  (ferramenta `lembrar`)")
print("=" * 74)
print("""
  custo ......... uma decisão por passo, dentro do orçamento da execução
  vantagem ...... captura o que a extração não previria
  o que falha ... ele lembra de bobagem, e a memória vira lixo acumulado
""")

# O agente ganha uma ferramenta `lembrar(conteudo, tipo)` e a chama quando
# julgar pertinente.
#
# Numa execução de 4 passos, o agente costuma chamar `lembrar` 2 a 4 vezes —
# e boa parte do que grava é ruído de execução: latência, contagem de passos,
# a tentativa descartada do passo 0.

# -------------------------------------------------- política 2: o código extrai
print("=" * 74)
print("POLÍTICA 2 — O CÓDIGO EXTRAI  (um passo sobre o resultado final)")
print("=" * 74)
print(f"\nexecução analisada:\n{EXECUCAO}")

fatos = extrair_pelo_codigo(EXECUCAO)

por_tipo: dict[str, list[str]] = {}
for f in fatos:
    por_tipo.setdefault(f["tipo"], []).append(f["conteudo"])

print(f"  {len(fatos)} informações classificadas, em 1 chamada:\n")
for tipo in ("episodica", "semantica", "procedural", "nao_guardar"):
    itens = por_tipo.get(tipo, [])
    print(f"  [{tipo}] {len(itens)}")
    for item in itens:
        print(f"      {item[:88]}")
    print()

guardados = sum(len(v) for t, v in por_tipo.items() if t != "nao_guardar")
print(f"  guardados: {guardados} de {len(fatos)}")

# A pergunta a fazer olhando esta lista: o que a extração PERDEU? Ela só
# captura o que o prompt mandou capturar — e o prompt de extração é um
# prompt de produção, versionado e testado como o de compaction da aula 05
# (nota 04, §6). Vale comparar as duas listas de "preservar
# obrigatoriamente": são quase a mesma lista.

# ------------------------------------------------- política 3: o humano corrige
print(f"\n{'=' * 74}")
print("POLÍTICA 3 — O HUMANO CORRIGE")
print("=" * 74)
print("""
  custo ......... trabalho humano por execução
  vantagem ...... a mais confiável das três
  o que falha ... não escala, e é a primeira coisa que se abandona
""")

# Na prática, o desenho que se sustenta é misto: o código extrai por padrão,
# e o humano corrige a memória PROCEDURAL — que é a que se aplica a todas as
# execuções seguintes e, portanto, a que erra mais caro.

# ---------------------------------------------------------- escrita é escrita
print("=" * 74)
print("ESCREVER MEMÓRIA É ESCRITA")
print("=" * 74)

semantica = MemoriaSemantica()
primeira = semantica.gravar("F-088", "destinos_frequentes", ["Lisboa"], "2026-10-06")
segunda = semantica.gravar("F-088", "destinos_frequentes", ["Lisboa"], "2026-10-06")

print(f"\n  1ª gravação: {primeira}")
print(f"  2ª gravação: {segunda}\n")

# A chave é derivada do CONTEÚDO (`entidade:chave`), não da tentativa. A
# mesma execução processada duas vezes não gera dois fatos — e o retorno
# avisa `ja_existia`, que é informação para quem chamou.
#
# Sem isso, uma execução reprocessada duplica a memória. E memória
# duplicada é memória contraditória, que é o assunto do próximo script.
