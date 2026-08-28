# Aula 03 — Prompt engineering
# 01 — O experimento do Min et al. (2022): e se os exemplos estiverem ERRADOS?
#
# A intuição de todo mundo: "o modelo aprende com os exemplos o mapeamento
# entrada -> saída". Se for verdade, embaralhar os rótulos dos exemplos deve
# destruir o resultado.
#
# Min et al. mostraram que não destrói. O que o few-shot ensina é o ESPAÇO DE
# RÓTULOS, a DISTRIBUIÇÃO da entrada e o FORMATO — não o mapeamento.
#
# Três condições, para separar as duas contribuições:
#   A) exemplos com rótulos CORRETOS
#   B) exemplos com rótulos EMBARALHADOS (errados de propósito)
#   C) SEM exemplos
#
# A queda de A para B mede o valor do mapeamento.
# A queda de B para C mede o valor de todo o resto.
#
# Paper: https://arxiv.org/abs/2202.12837
#        (PDF em material_auxiliar/prompt_engineering/papers/)

import os
import time
from dotenv import load_dotenv
from openai import OpenAI

from dados import CATEGORIAS, TESTE, EXEMPLOS

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")
PAUSA = 0.4

INSTRUCAO = (
    f"Classifique a mensagem do cliente em uma destas categorias: "
    f"{', '.join(CATEGORIAS)}.\n"
    "Responda apenas o rótulo, em minúsculas, sem pontuação."
)

# Embaralhamento FIXO, escrito à mão: cada exemplo recebe o rótulo do
# seguinte. Nenhum fica com o rótulo certo, e o conjunto de rótulos usados
# continua sendo exatamente o mesmo — que é a condição do experimento.
# (Fixo e não aleatório para a turma inteira ver o mesmo resultado.)
EXEMPLOS_EMBARALHADOS = [
    (mensagem, EXEMPLOS[(i + 1) % len(EXEMPLOS)][1])
    for i, (mensagem, _) in enumerate(EXEMPLOS)
]


def montar(mensagem, exemplos):
    if not exemplos:
        return f"{INSTRUCAO}\n\nMensagem: {mensagem}\nRótulo:"
    blocos = "\n".join(f"Mensagem: {m}\nRótulo: {r}\n" for m, r in exemplos)
    return f"{INSTRUCAO}\n\n{blocos}\nMensagem: {mensagem}\nRótulo:"


def classificar(prompt):
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=15,
    )
    escolha = resposta.choices[0]
    if escolha.finish_reason == "length":
        return None
    return escolha.message.content.strip().lower().rstrip(".")


def rodar(nome, exemplos):
    acertos = 0
    fora = 0
    for mensagem, esperado in TESTE:
        rotulo = classificar(montar(mensagem, exemplos))
        acertos += rotulo == esperado
        fora += rotulo not in CATEGORIAS
        time.sleep(PAUSA)
    print(f"  {nome:<28} {acertos:>2}/{len(TESTE)}  "
          f"({fora} fora do domínio)")
    return acertos


print(f"modelo: {MODELO} | {len(TESTE)} mensagens de teste\n")

print("Os exemplos embaralhados que serão usados na condição B:")
for (m, certo), (_, errado) in zip(EXEMPLOS, EXEMPLOS_EMBARALHADOS):
    print(f"  {m[:44]:<46} {certo}  ->  {errado}")
print()

print("### Resultados")
a = rodar("A) rótulos corretos", EXEMPLOS)
b = rodar("B) rótulos EMBARALHADOS", EXEMPLOS_EMBARALHADOS)
c = rodar("C) sem exemplos", [])

print("\n" + "=" * 66)
print(f"  mapeamento correto vale:  A - B = {a - b:+d} acerto(s)")
print(f"  todo o resto vale:        B - C = {b - c:+d} acerto(s)")

print(
    "\nO que isso significa:\n"
    "  A queda de A para B costuma ser PEQUENA: trocar os rótulos por rótulos\n"
    "  errados quase não atrapalha. A queda de B para C costuma ser GRANDE.\n"
    "\n"
    "  Ou seja: os exemplos valem muito — mas não pelo motivo que você\n"
    "  imaginava. Eles ensinam QUAIS rótulos existem, QUE TIPO de texto entra\n"
    "  e QUAL o formato da resposta. O mapeamento certo é a menor parte.\n"
    "\n"
    "  O que fazer com isso (nota 01, §6.2):\n"
    "   - cubra TODOS os rótulos nos exemplos, principalmente os raros;\n"
    "   - use entradas parecidas com as reais, com erro de digitação e tudo;\n"
    "   - mantenha o formato rigorosamente idêntico;\n"
    "   - e não gaste horas caçando os exemplos 'perfeitos'.\n"
    "\n"
    "  CUIDADO com a conclusão fácil: isto NÃO quer dizer 'os exemplos não\n"
    "  servem para nada, pode remover'. A condição C existe justamente para\n"
    "  impedir essa leitura. Corrija os rótulos assim mesmo — custa nada.\n"
    "\n"
    "  Com poucas mensagens de teste, a diferença entre A e B pode dar zero\n"
    "  ou até negativa. Isso é ruído, não refutação: aumente o conjunto de\n"
    "  teste antes de concluir qualquer coisa (aula 02, nota 04, §6)."
)
