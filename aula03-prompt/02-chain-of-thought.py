# Aula 03 — Prompt engineering
# 02 — Chain-of-thought: três jeitos de montar o MESMO pedido.
#
# Este script é sobre CONSTRUÇÃO DE PROMPT. O problema é sempre o mesmo; o
# que muda é como você escreve o pedido:
#
#   A) direto        — só o enunciado e o formato da resposta
#   B) zero-shot CoT — acrescenta UMA frase: "Vamos pensar passo a passo"
#   C) few-shot CoT  — mostra um exemplo RESOLVIDO, com o raciocínio à vista
#
# Leia as três versões do prompt no código antes de rodar. Depois leia o que
# o modelo escreveu em cada uma: na A ele salta direto para o resultado; na
# B e na C ele escreve os passos primeiro — e é isso que faz a diferença.
#
# Por que funciona: o modelo gera um token por vez, condicionado a tudo o que
# JÁ escreveu. Ao escrever os passos intermediários, ele coloca no próprio
# contexto os resultados parciais de que vai precisar depois. O raciocínio
# escrito é memória de trabalho externalizada.
#
# Papers: Wei et al. (2022)    https://arxiv.org/abs/2201.11903
#         Kojima et al. (2022) https://arxiv.org/abs/2205.11916

import os
import re
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")
PAUSA = 0.5

# Problemas de VÁRIAS ETAPAS, com resposta numérica verificável.
# Repare que nenhum é difícil — são só multi-etapa, que é o critério que
# decide o uso de CoT. Numa classificação, ele não ajudaria em nada.
PROBLEMAS = [
    ("Uma loja vende canetas em caixas de 12 por R$ 30 a caixa e avulsas por "
     "R$ 3,50. Preciso de 100 canetas gastando o mínimo possível. Qual o "
     "valor total, em reais?", 254),

    ("Três transportadoras: A cobra R$ 80 fixo mais R$ 2,00 por kg; B cobra "
     "R$ 120 fixo mais R$ 1,20 por kg; C cobra R$ 3,00 por kg sem taxa fixa. "
     "Para um envio de 60 kg, quanto custa a opção mais barata, em reais?", 180),

    ("Qual é a soma dos números ímpares deste grupo: 15, 32, 5, 13, 82, 7, 1?",
     41),

    ("Um palete comporta 48 caixas. Preciso enviar 300 caixas em paletes "
     "cheios. Quantas caixas sobram fora dos paletes cheios?", 12),
]

# ---------------------------------------------------------------------------
# AS TRÊS FORMAS DE MONTAR O PROMPT — é aqui que está a aula.
# ---------------------------------------------------------------------------

# Comum às três: o contrato de saída. Sem isso, você não consegue nem
# verificar se o modelo acertou (nota 01, §4).
FORMATO = ("\n\nTermine a resposta com uma última linha exatamente assim:"
           "\nRESPOSTA: <número>")

# A) DIRETO — o prompt mínimo. Nada além do enunciado e do formato.
def prompt_direto(enunciado):
    return enunciado + FORMATO

# B) ZERO-SHOT CoT — uma frase a mais, e só. É a técnica de melhor
#    relação benefício/esforço da aula: não custa nenhum exemplo.
def prompt_zero_shot_cot(enunciado):
    return enunciado + "\n\nVamos pensar passo a passo." + FORMATO

# C) FEW-SHOT CoT — mostra UM exemplo resolvido, com o raciocínio à vista.
#    Repare no que o exemplo ensina: não é a resposta, é O FORMATO DO
#    RACIOCÍNIO — enumerar, calcular, comparar, concluir.
EXEMPLO_RESOLVIDO = """Exemplo de como resolver:

Pergunta: Um pacote traz 6 lápis por R$ 9. Preciso de 20 lápis gastando o
mínimo. Lápis avulso custa R$ 2. Qual o valor total, em reais?

Raciocínio: No pacote, cada lápis sai por 9 / 6 = 1,50, mais barato que os
2,00 do avulso. Então uso o máximo de pacotes: 3 pacotes dão 18 lápis por
3 x 9 = 27 reais. Faltam 2 lápis. Duas opções: 2 avulsos custam 2 x 2 = 4
(total 31), ou um quarto pacote custa mais 9 (total 36). Como 31 < 36, fico
com os avulsos.
RESPOSTA: 31
"""

def prompt_few_shot_cot(enunciado):
    return f"{EXEMPLO_RESOLVIDO}\nAgora resolva:\n\nPergunta: {enunciado}" + FORMATO


def extrair_resposta(texto):
    """Pega o número da última linha 'RESPOSTA: <n>'."""
    achados = re.findall(r"RESPOSTA:\s*R?\$?\s*([\d.,]+)", texto, re.IGNORECASE)
    if not achados:
        return None
    bruto = achados[-1].replace(".", "").replace(",", ".")
    try:
        return round(float(bruto))
    except ValueError:
        return None


def resolver(prompt):
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=800,     # o raciocínio precisa de espaço para caber
    )
    escolha = resposta.choices[0]
    if escolha.finish_reason == "length":
        # Truncou no meio do raciocínio: não é uma resposta, é um corte.
        return None, (escolha.message.content or "") + "\n[TRUNCADO]"
    texto = escolha.message.content or ""
    return extrair_resposta(texto), texto


def rodar(nome, construir_prompt, mostrar_texto=False):
    acertos = 0
    print(f"### {nome}")
    for enunciado, esperado in PROBLEMAS:
        valor, texto = resolver(construir_prompt(enunciado))
        ok = valor == esperado
        acertos += ok
        print(f"  {'ok  ' if ok else 'ERRO'} esperado={esperado:<5} obtido={valor}")
        if mostrar_texto:
            print("      --- o que o modelo escreveu ---")
            for linha in texto.strip().splitlines():
                print(f"      {linha}")
            print()
        time.sleep(PAUSA)
    print(f"  -> {acertos}/{len(PROBLEMAS)} corretos\n")
    return acertos


print(f"modelo: {MODELO} | {len(PROBLEMAS)} problemas de várias etapas\n")
print("Leia os três prompts no código antes de olhar os resultados.\n")

a = rodar("A) direto", prompt_direto)
b = rodar("B) zero-shot CoT — uma frase a mais", prompt_zero_shot_cot)
c = rodar("C) few-shot CoT — com um exemplo resolvido", prompt_few_shot_cot)

print("=" * 66)
print(f"{'A) direto':<42} {a}/{len(PROBLEMAS)}")
print(f"{'B) zero-shot CoT':<42} {b}/{len(PROBLEMAS)}")
print(f"{'C) few-shot CoT':<42} {c}/{len(PROBLEMAS)}")

print("\n" + "=" * 66)
print("Agora veja O QUE MUDA no texto da resposta — o mesmo problema, "
      "resolvido\ndas três formas:\n")

enunciado, esperado = PROBLEMAS[0]
for nome, construir in [("A) direto", prompt_direto),
                        ("B) zero-shot CoT", prompt_zero_shot_cot),
                        ("C) few-shot CoT", prompt_few_shot_cot)]:
    valor, texto = resolver(construir(enunciado))
    print(f"--- {nome}  (esperado: {esperado} | obtido: {valor})")
    for linha in texto.strip().splitlines():
        print(f"    {linha}")
    print()
    time.sleep(PAUSA)

print(
    "O que observar:\n"
    "  - Na A o modelo salta direto para um número. Quando ele erra, não há\n"
    "    onde procurar o erro — não existe raciocínio para conferir.\n"
    "  - Na B, UMA frase muda o comportamento: ele enumera, calcula e só\n"
    "    então conclui. É a mesma quantidade de trabalho que você teve para\n"
    "    escrever o prompt: uma linha.\n"
    "  - Na C, o exemplo resolvido ensina o FORMATO do raciocínio. Compare a\n"
    "    estrutura da resposta com a do exemplo — o modelo imita o caminho,\n"
    "    não a resposta.\n"
    "\n"
    "  Quando NÃO usar CoT:\n"
    "   - em classificação e extração (as tarefas do script 00). A tarefa é\n"
    "     de um passo só; o raciocínio não tem o que fazer e ainda dá espaço\n"
    "     para o modelo se contradizer antes de responder;\n"
    "   - em modelos de RACIOCÍNIO, que já fazem isso internamente. Pedir de\n"
    "     novo é redundante (aula 02, nota 01, §6.3).\n"
    "\n"
    "  Experimente: pegue uma mensagem do script 00 e classifique com e sem\n"
    "  'vamos pensar passo a passo'. O acerto não melhora — e a resposta\n"
    "  fica cheia de texto que você não pediu."
)
