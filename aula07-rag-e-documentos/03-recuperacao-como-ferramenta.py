# Aula 07 — 03: A RECUPERAÇÃO EXPOSTA COMO FERRAMENTA.
#
# Existe uma classe de pergunta que um pipeline de RAG não responde: a que
# exige N trechos independentes, com N desconhecido antes da execução. O
# pipeline emite uma consulta e recebe um conjunto de trechos; se a resposta
# depende de três dispositivos distintos, uma consulta não os reúne.
#
# A alternativa é expor a busca como FERRAMENTA e deixar o modelo decidir
# quantas consultas emitir. Pela taxonomia da aula 05 (nota 01, §3.4), o
# resultado é o ORQUESTRADOR-TRABALHADOR: as subtarefas — quais consultas
# fazer — não estão no código e são determinadas em execução. O mercado
# denomina esse desenho `agentic RAG`.
#
# ESCOPO DESTE SCRIPT. Executa a mesma pergunta pelos dois caminhos e compara
# o que cada um recuperou e quantas chamadas de geração consumiu.
#
# O CASO. A despesa é a mesma do exemplo 4 da nota 03 da aula 05, em que ela
# falhou por perda de contexto na delegação a um sub-agente. Aqui ela falha
# por outra causa — recuperação insuficiente — e produz o mesmo sintoma: uma
# despesa legítima reprovada, sem indício de informação faltante.

import json

from dados import CORPUS_COM_RUIDO, LISBOA
from cliente import MODELO, client
from consumo import GERACAO
from geracao import montar_contexto
from indice_chroma import IndiceChroma
from pipeline import pipeline

indice = IndiceChroma(CORPUS_COM_RUIDO)
MAX_BUSCAS = 4          # orçamento em número de buscas (aula 05, nota 02 §1)

print("=" * 74)
print("A PERGUNTA QUE UMA CONSULTA SÓ NÃO RESPONDE")
print("=" * 74)
print(f"""
{LISBOA['pergunta']}

Ela exige TRÊS trechos:
  - {LISBOA['artigos_necessarios'][0]}  o teto da categoria
  - {LISBOA['artigos_necessarios'][1]}  a exceção de viagem internacional
  - {LISBOA['artigos_necessarios'][2]}  a alçada de aprovação

Uma busca devolve um deles.
""")

# ------------------------------------------------------------ o pipeline erra
print("=" * 74)
print("A — O PIPELINE (uma busca, uma resposta)")
print("=" * 74)

chamadas_antes = GERACAO["chamadas"]
r = pipeline(LISBOA["pergunta"], indice, k=3)
veio = [t["artigo"] for t in r["trechos"]]
faltou = [a for a in LISBOA["artigos_necessarios"] if a not in veio]
print(f"\n  recuperou: {veio}")
print(f"  faltou:    {faltou}")
print(f"\n  resposta: {r['resposta']}")
print(f"  fontes: {r['fontes']}   suficiente: {r['suficiente']}")
print(f"  chamadas de geração: {GERACAO['chamadas'] - chamadas_antes}")
print(f"""
  correto seria: {LISBOA['resposta_correta']}
""")

# --------------------------------------------------------- o agente acerta
print("=" * 74)
print("B — A RECUPERAÇÃO COMO FERRAMENTA (o laço decide quantas buscas)")
print("=" * 74)

FERRAMENTAS = [{
    "type": "function",
    "function": {
        "name": "buscar_politica",
        "description": ("Busca trechos da política de reembolso. Use uma "
                        "consulta por assunto: chamadas separadas para teto "
                        "da categoria, exceções e alçada de aprovação "
                        "recuperam mais que uma consulta longa."),
        "parameters": {
            "type": "object",
            "properties": {"consulta": {"type": "string"}},
            "required": ["consulta"],
            "additionalProperties": False,
        },
    },
}]

SYSTEM = ("Você analisa despesas contra a política de reembolso. Use a "
          "ferramenta de busca quantas vezes precisar, uma consulta por "
          "assunto, antes de concluir. Só responda quando tiver o teto "
          "aplicável, as exceções que incidem e a alçada de aprovação. "
          "Cite os artigos usados.")

mensagens = [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": LISBOA["pergunta"]}]
recuperados: list[str] = []
chamadas_antes = GERACAO["chamadas"]

for passo in range(MAX_BUSCAS + 1):
    r_api = client.chat.completions.create(
        model=MODELO, messages=mensagens, tools=FERRAMENTAS, temperature=0)
    msg = r_api.choices[0].message
    GERACAO["chamadas"] += 1
    GERACAO["entrada"] += r_api.usage.prompt_tokens
    GERACAO["saida"] += r_api.usage.completion_tokens

    if not msg.tool_calls:
        print(f"\n  resposta: {msg.content}")
        break

    mensagens.append(msg)
    for chamada in msg.tool_calls:
        # O teto existe porque o número de buscas é decidido em execução. Sem
        # ele, uma pergunta ambígua produz consultas sucessivas sem
        # convergência, e cada busca acrescenta trechos ao contexto que é
        # reenviado a cada volta — custo quadrático no acumulado.
        if len(recuperados) >= MAX_BUSCAS:
            conteudo = {"erro": "teto de buscas atingido",
                        "sugestao": "responda com o que já foi recuperado"}
        else:
            consulta = json.loads(chamada.function.arguments)["consulta"]
            trechos = indice.buscar(consulta, k=2)
            recuperados.extend(t["artigo"] for t in trechos)
            print(f"  passo {passo}: buscar_politica({consulta!r})"
                  f" -> {[t['artigo'] for t in trechos]}")
            conteudo = {"trechos": montar_contexto(trechos)}

        mensagens.append({"role": "tool", "tool_call_id": chamada.id,
                          "name": chamada.function.name,
                          "content": json.dumps(conteudo, ensure_ascii=False)})
else:
    print("\n  encerrou por teto de buscas sem concluir")

encontrados = [a for a in LISBOA["artigos_necessarios"]
               if any(a.replace("º", "") in r.replace("º", "")
                      for r in recuperados)]
print(f"""
  artigos recuperados no total: {sorted(set(recuperados))}
  dos três necessários, encontrou: {encontrados}
  chamadas de geração: {GERACAO['chamadas'] - chamadas_antes}
""")
