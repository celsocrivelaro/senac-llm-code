# Aula 03 — Prompt engineering
# 00 — Zero-shot × few-shot: o exemplo custa. Ele paga?
#
# Mesma tarefa, mesmo modelo, mesmos parâmetros. A ÚNICA diferença é a
# presença de 5 exemplos no prompt.
#
# O que medir não é só acurácia: exemplos entram na ENTRADA de TODA
# requisição (aula 03, nota 01, §6.2). A pergunta que decide é sempre a
# mesma: quanto de acerto a mais, por quanto de custo a mais?
#
# Documentação: https://docs.mistral.ai/api/

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
    "Se houver mais de um problema, escolha o da reclamação.\n"
    "Responda apenas o rótulo, em minúsculas, sem pontuação."
)


def prompt_zero_shot(mensagem):
    return f"{INSTRUCAO}\n\nMensagem: {mensagem}\nRótulo:"


def prompt_few_shot(mensagem):
    # Formato IDÊNTICO em todos os exemplos — é dele que o modelo tira a
    # estrutura da resposta (nota 01, §6.1).
    blocos = "\n".join(f"Mensagem: {m}\nRótulo: {r}\n" for m, r in EXEMPLOS)
    return f"{INSTRUCAO}\n\n{blocos}\nMensagem: {mensagem}\nRótulo:"


def classificar(prompt):
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,      # classificação: variação é defeito (aula 02, nota 02, §9)
        max_tokens=15,      # o rótulo mais longo tem ~8 tokens; folga de segurança
    )
    escolha = resposta.choices[0]
    if escolha.finish_reason == "length":
        return None, resposta.usage      # truncou: não é resposta válida
    rotulo = escolha.message.content.strip().lower().rstrip(".")
    return rotulo, resposta.usage


def rodar(nome, construir_prompt):
    acertos = 0
    entrada = saida = 0
    fora_do_dominio = 0

    print(f"### {nome}")
    for mensagem, esperado in TESTE:
        rotulo, uso = classificar(construir_prompt(mensagem))
        entrada += uso.prompt_tokens
        saida += uso.completion_tokens

        ok = rotulo == esperado
        acertos += ok
        if rotulo not in CATEGORIAS:
            fora_do_dominio += 1

        marca = "ok  " if ok else "ERRO"
        print(f"  {marca} esperado={esperado:<18} obtido={rotulo}")
        time.sleep(PAUSA)

    print(f"  -> {acertos}/{len(TESTE)} corretos | "
          f"{fora_do_dominio} fora do domínio | "
          f"entrada {entrada} tokens | saída {saida} tokens\n")
    return acertos, entrada, saida


print(f"modelo: {MODELO} | {len(TESTE)} mensagens | {len(EXEMPLOS)} exemplos\n")

zero = rodar("A) zero-shot", prompt_zero_shot)
few = rodar("B) few-shot", prompt_few_shot)

print("=" * 66)
print(f"{'':<12} {'acertos':>8} {'entrada':>9} {'saída':>7}")
print(f"{'zero-shot':<12} {zero[0]:>6}/{len(TESTE)} {zero[1]:>9} {zero[2]:>7}")
print(f"{'few-shot':<12} {few[0]:>6}/{len(TESTE)} {few[1]:>9} {few[2]:>7}")

delta_acerto = few[0] - zero[0]
delta_entrada = few[1] - zero[1]
por_chamada = delta_entrada / len(TESTE)

print(f"\nOs exemplos custaram +{delta_entrada} tokens de entrada no total, "
      f"ou ~{por_chamada:.0f} por chamada,")
print(f"e renderam {delta_acerto:+d} acerto(s).")

print(
    "\nComo ler este resultado:\n"
    "  - +N tokens POR CHAMADA, para sempre. Com 10 mil chamadas/dia, faça a\n"
    "    conta da aula 02 (nota 04, §2) antes de decidir.\n"
    "  - Olhe a coluna 'fora do domínio': é comum o few-shot ganhar aqui\n"
    "    mesmo empatando em acurácia — o ganho dele costuma ser de FORMATO.\n"
    "    E formato tem solução mais barata: JSON Schema com enum (aula 02).\n"
    "  - Se os dois empataram, a resposta certa é ficar com o zero-shot.\n"
    "    Escalar técnica sem medir é o mesmo erro de escolher o modelo maior\n"
    "    sem testar o menor."
)
