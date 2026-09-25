# Aula 07 — 01: AS QUATRO CEGUEIRAS DO EMBEDDING.
#
# Um modelo de embedding representa o CONTEXTO DE OCORRÊNCIA de um termo.
# Quatro propriedades ficam fora dessa representação, e cada uma decide uma
# classe de consulta:
#
#   NEGAÇÃO    polaridade de uma afirmação
#   NÚMERO     magnitude de um valor
#   ENTIDADE   identidade de um registro
#   TEMPO      anterioridade entre duas datas
#
# O script mede o cosseno de um par de textos por cegueira. Cada par difere
# APENAS na propriedade em questão; tudo o mais é idêntico. Um cosseno alto
# significa, portanto, que a propriedade não foi representada.
#
# O PAR DE CONTROLE reúne dois textos sem relação alguma entre si, e
# estabelece o piso da escala. Ele é necessário porque um cosseno isolado não
# é interpretável: textos em português compartilham estrutura, e o piso
# prático fica bem acima de zero.

from embedding import gerar_vetor_embeddings
from similaridade import cosseno

# ============================================================ AS CEGUEIRAS
#
# Cada entrada registra o par de textos, a similaridade que a leitura humana
# atribuiria (`previsao`) e a propriedade que o resultado demonstra (`licao`).
#
# O campo `previsao` não é decorativo: a divergência entre ele e o valor
# medido é o que a medição quantifica.

CEGUEIRAS = [
    {"nome": "NEGAÇÃO",
     "a": "a despesa foi aprovada pelo analista",
     "b": "a despesa foi reprovada pelo analista",
     "previsao": "baixa — os textos afirmam o oposto",
     "licao": "o vetor não representa negação. 'aprovado' e 'reprovado' "
              "ocorrem nos mesmos contextos, e é isso que o embedding captura."},

    {"nome": "NÚMERO",
     "a": "o teto de reembolso é de R$ 120,00 por refeição",
     "b": "o teto de reembolso é de R$ 260,00 por refeição",
     "previsao": "baixa — os valores decidem coisas diferentes",
     "licao": "números são quase invisíveis para o vetor. Comparar valor é "
              "trabalho de `==` e de comparação numérica, não de cosseno."},

    {"nome": "ENTIDADE",
     "a": "análise da despesa D-4471 do funcionário F-088",
     "b": "análise da despesa D-4472 do funcionário F-091",
     "previsao": "baixa — são registros distintos",
     "licao": "identificador não é significado. Buscar um id por similaridade "
              "devolve todos os ids do mesmo formato."},

    {"nome": "TEMPO",
     "a": "em março de 2026, o teto de refeição passou a ser R$ 120,00",
     "b": "em agosto de 2026, o teto de refeição passou a ser R$ 150,00",
     "previsao": "baixa — um dos dois está revogado",
     "licao": "o vetor não representa anterioridade. Que março preceda "
              "agosto é aritmética sobre o calendário, não propriedade do "
              "contexto textual. A aula 08 retoma esta cegueira na memória "
              "de um agente."},

    {"nome": "CONTROLE",
     "a": "a despesa foi aprovada pelo analista",
     "b": "a previsão do tempo indica chuva no litoral norte",
     "previsao": "baixa — não têm relação nenhuma",
     "licao": "este é o piso da escala. Os quatro valores acima devem ser "
              "lidos em relação a ele, e não em relação a zero."},
]

print("=" * 74)
print("O QUE O EMBEDDING NÃO VÊ")
print("=" * 74)

resultados = []

for caso in CEGUEIRAS:
    print(f"\n{'-' * 74}\n{caso['nome']}\n{'-' * 74}")
    print(f"  A: {caso['a']!r}")
    print(f"  B: {caso['b']!r}")
    print(f"\n  intuição: similaridade {caso['previsao']}")

    score = cosseno(gerar_vetor_embeddings(caso["a"]),
                    gerar_vetor_embeddings(caso["b"]))
    resultados.append((caso["nome"], score))

    barra = "█" * int(score * 50)
    print(f"\n  OBTIDO: {score:.4f}  {barra}")
    print(f"\n  {caso['licao']}")

# ------------------------------------------------------------------ o quadro
print(f"\n{'=' * 74}")
print("O QUADRO COMPLETO")
print("=" * 74)
print()

# O CONTROLE é o último par da lista, e é dele que sai a régua de leitura.
controle = dict(resultados)["CONTROLE"]
negacao = dict(resultados)["NEGAÇÃO"]

for nome, score in resultados:
    barra = "█" * int(score * 50)
    marca = "  <-- referência: textos SEM RELAÇÃO" if nome == "CONTROLE" else ""
    print(f"  {nome:<10s} {score:.4f}  {barra}{marca}")

cegueiras = [(n, s) for n, s in resultados if n != "CONTROLE"]
menor = min(cegueiras, key=lambda par: par[1])

print(f"""
Os valores devem ser lidos em relação ao CONTROLE, não em relação a zero.

Textos que afirmam o oposto um do outro medem {negacao:.4f}. Textos sem relação
alguma medem {controle:.4f}. A distância entre "aprovado" e "reprovado" é, para o
vetor, menor que a distância entre qualquer um dos dois e uma frase sobre
meteorologia.

O menor dos quatro valores é {menor[0]} ({menor[1]:.4f}), e ainda assim está acima do
piso. Nenhuma das quatro propriedades foi representada.""")
