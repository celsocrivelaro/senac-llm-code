# Aula 07 — 02: AS DUAS MÉTRICAS DO RAG, MEDIDAS SEPARADAS.
#
# Um pipeline de RAG tem duas metades independentes, e cada uma falha por
# causa própria. Medi-las juntas produz um número que não indica onde mexer.
#
#   RECALL@K     a busca trouxe o trecho certo entre os k primeiros?
#                Métrica da aula 06. Não envolve geração, e por isso custa
#                apenas os embeddings das perguntas.
#
#   FIDELIDADE   a resposta se apoia nos trechos recuperados, ou afirma o
#                que não está neles? Exige uma chamada de avaliação por
#                resposta.
#
# A separação é o que torna o diagnóstico possível: recall baixo é defeito de
# índice, fidelidade baixa com recall alto é defeito de prompt, e as duas
# altas com resposta errada é defeito de corpus. A tabela ao final do script
# formaliza esses três casos.

from dados import CORPUS_COM_RUIDO, PERGUNTAS
from indice_chroma import IndiceChroma
from metricas import fidelidade, recall_at_k
from pipeline import pipeline

K = 3
indice = IndiceChroma(CORPUS_COM_RUIDO)

# ------------------------------------------------------------- metade 1
print("=" * 74)
print(f"METADE 1 — A BUSCA ACERTOU?  (recall@{K}, sem geração)")
print("=" * 74)

r_busca = recall_at_k(indice, PERGUNTAS, k=K)
print(f"\n  recall@{K} = {r_busca['acertos']}/{r_busca['total']} "
      f"({r_busca['recall']:.0%})\n")
for f in r_busca["falhas"]:
    print(f"  falhou: {f['pergunta'][:56]}")
    print(f"          esperado={f['artigo']}  veio={f['veio']}")

# ------------------------------------------------------------- metade 2
print(f"\n{'=' * 74}")
print("METADE 2 — A RESPOSTA USOU O QUE VEIO?  (fidelidade)")
print("=" * 74)
print()

sustentadas, sem_lastro = 0, []
for caso in PERGUNTAS:
    r = pipeline(caso["pergunta"], indice, k=K)
    if r.get("barrado_no_portao"):
        print(f"  [portão] {caso['pergunta'][:56]}")
        continue
    aval = fidelidade(r["resposta"], r["trechos"])
    if aval["sustentada"]:
        sustentadas += 1
        print(f"  [ok]     {caso['pergunta'][:56]}")
    else:
        sem_lastro.append((caso["pergunta"], aval["afirmacoes_sem_lastro"]))
        print(f"  [FALHA]  {caso['pergunta'][:56]}")
        for a in aval["afirmacoes_sem_lastro"][:2]:
            print(f"           sem lastro: {a[:60]}")

fid = sustentadas / len(PERGUNTAS)
print(f"\n  fidelidade = {sustentadas}/{len(PERGUNTAS)} ({fid:.0%})")

# ------------------------------------------------------------- diagnóstico
print(f"\n{'=' * 74}")
print("A TABELA DE DIAGNÓSTICO")
print("=" * 74)
print("""
  recall@k   fidelidade   o defeito está em
  ---------  -----------  ------------------------------------------------
  baixo      qualquer     ÍNDICE — chunking, modelo de embedding, k
  alto       baixa        PROMPT — contrato, ordem dos trechos, contexto
  alto       alta         CORPUS — a informação não está lá, ou está velha
             (e errado)
""")

if r_busca["recall"] < 0.7:
    veredito = "ÍNDICE — o trecho certo não está chegando"
elif fid < 0.8:
    veredito = "PROMPT — o trecho chega e a resposta não se apoia nele"
else:
    veredito = "nem índice nem prompt — o que sobrar é CORPUS"

print(f"  recall@{K}={r_busca['recall']:.0%} · fidelidade={fid:.0%}")
print(f"  -> {veredito}")
