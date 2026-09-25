# Aula 07 — 05: OS QUATRO MODOS DE FALHA DE UM PIPELINE DE RAG.
#
# Um pipeline de RAG tem quatro modos de falha documentados, e eles se
# distinguem pelo COMPONENTE em que a causa está — o que determina onde o
# conserto se aplica:
#
#   FALHA  descrição                        causa em    sintoma
#   -----  -------------------------------  ----------  -------------------
#     1    recuperou o trecho errado        recuperação resposta correta
#                                                       sobre outro assunto
#     2    recuperou o certo e não usou     geração     a resposta muda com
#                                                       a ordem dos trechos
#     3    não havia resposta e respondeu   geração     conteúdo sem lastro
#                                                       no corpus
#     4    recuperou trechos contraditórios corpus      escolhe um dos dois
#                                                       sem sinalizar
#
# Nenhuma das quatro aparece em perguntas cujo trecho de resposta é único e
# existe no corpus. Cada bloco deste script constrói a condição que provoca
# uma delas.
#
# Taxonomia: BARNETT et al. (2024).

from dados import CORPUS_COM_RUIDO, ORDEM, SEM_RESPOSTA
from geracao import responder
from indice_chroma import IndiceChroma
from pipeline import pipeline

indice = IndiceChroma(CORPUS_COM_RUIDO)

# ------------------------------------------------------------------ falha 1
print("=" * 74)
print("FALHA 1 — RECUPEROU O TRECHO ERRADO")
print("=" * 74)
print("""
A pergunta é sobre EQUIPAMENTO DE INFORMÁTICA. O regulamento trata do
assunto no Art. 7º §2º apenas para dizer que ele NÃO se enquadra em
material — mas o vetor aproxima "notebook" de "material de escritório".
""")

r = pipeline("Qual o teto de reembolso para um notebook?", indice, k=3,
             com_portao=False)
print(f"  trechos recuperados: {[t['artigo'] for t in r['trechos']]}")
print(f"  resposta: {r['resposta'][:200]}")
print(f"  fontes: {r['fontes']}")
print("""
A resposta é fluente e o assunto é próximo, de modo que o erro não é
detectável pelo texto: só a lista de fontes o revela. Essa é a justificativa
funcional do campo `fontes` do contrato de saída, construído no script 06.
""")

# ------------------------------------------------------------------ falha 2
print("=" * 74)
print("FALHA 2 — RECUPEROU O CERTO E IGNOROU")
print("=" * 74)
print(f"""
Mesma pergunta, MESMOS trechos, duas ORDENS. Se a resposta muda, o problema
não é recuperação: é posição na janela (LIU et al., 2023; aula 02 §4.3).

pergunta: {ORDEM['pergunta']!r}
""")

trechos = indice.buscar(ORDEM["pergunta"], k=5)
for rotulo, ordenados in (("certo em PRIMEIRO", trechos),
                          ("certo no MEIO", trechos[1:3] + trechos[:1] + trechos[3:])):
    r = responder(ORDEM["pergunta"], ordenados)
    print(f"  [{rotulo}] ordem={[t['artigo'] for t in ordenados]}")
    print(f"     -> {r['resposta'][:140]}")
    print(f"        fontes={r['fontes']}\n")

print("""As duas execuções usam os mesmos trechos, logo o recall é idêntico por
construção. Se as respostas diferem, o defeito não está na recuperação: está
na montagem do contexto e no prompt. É essa distinção que a tabela de
diagnóstico do script 02 formaliza.
""")

# ------------------------------------------------------------------ falha 3
print("=" * 74)
print("FALHA 3 — NÃO HAVIA RESPOSTA, E O MODELO INVENTOU")
print("=" * 74)
print("""
As três perguntas abaixo não têm resposta no regulamento. Sem contrato de
saída, o formato da resposta não admite a alternativa "não sei": o modelo
produz uma resposta para todas, e cita fonte.

O conteúdo gerado é plausível e compatível com o domínio, o que torna a
falha difícil de detectar por leitura.
""")

for pergunta in SEM_RESPOSTA:
    trechos = indice.buscar(pergunta, k=3)
    r = responder(pergunta, trechos, com_contrato=False)
    print(f"  P: {pergunta}")
    print(f"  R: {r['resposta'][:200]}\n")

print("""Dos quatro modos de falha, este é o único que se resolve com uma
alteração de schema: um campo booleano que permita ao modelo declarar que os
trechos não contêm a resposta. O script 06 implementa esse campo.
""")

# ------------------------------------------------------------------ falha 4
print("=" * 74)
print("FALHA 4 — TRECHOS CONTRADITÓRIOS")
print("=" * 74)
print("""
O corpus contém a versão VIGENTE do Art. 4º §1º (R$ 120,00) e a REVOGADA de
2024 (R$ 90,00). Nenhum sistema real tem só a versão vigente indexada.
""")

pergunta = "Qual o teto de reembolso para refeição em viagem a serviço?"
trechos = indice.buscar(pergunta, k=5)
print(f"  trechos recuperados: {[t['artigo'] for t in trechos]}")
print("  conteúdo relevante:")
for t in trechos:
    if "120,00" in t["texto"] or "90,00" in t["texto"]:
        marca = "REVOGADA" if "REVOGADA" in t["texto"] or "90,00" in t["texto"] else "vigente"
        print(f"     [{t['artigo']}] ({marca}) "
              f"{t['texto'].strip().splitlines()[-1][:80]}")

r = responder(pergunta, trechos)
print(f"\n  resposta: {r['resposta'][:200]}")
print(f"  fontes: {r['fontes']}")
