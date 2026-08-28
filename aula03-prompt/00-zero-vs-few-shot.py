# Aula 03 — Prompt engineering
# 00 — Zero-shot × few-shot: o mesmo pedido, com e sem exemplos.
#
# Este é o primeiro script da aula, e o mais importante para quem está
# montando prompt pela primeira vez. Mesma tarefa, mesmo modelo, mesmos
# parâmetros. A ÚNICA diferença é a presença de 5 exemplos no prompt.
#
# Leia as duas funções que montam o prompt antes de rodar. Repare que o
# few-shot não explica mais nada ao modelo — ele MOSTRA. E mostra sempre no
# MESMO formato, que é de onde o modelo tira a estrutura da resposta.
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

# O CONTRATO DE SAÍDA (nota 01, §4). Três coisas, e cada uma elimina uma
# possibilidade: o domínio (quais rótulos existem), a regra de fronteira
# (o que fazer no caso ambíguo) e o formato (como responder).
INSTRUCAO = (
    f"Classifique a mensagem do cliente em uma destas categorias: "
    f"{', '.join(CATEGORIAS)}.\n"
    "Se houver mais de um problema, escolha o da reclamação.\n"
    "Responda apenas o rótulo, em minúsculas, sem pontuação."
)


def prompt_zero_shot(mensagem):
    """Só a instrução. Nenhum exemplo."""
    return f"{INSTRUCAO}\n\nMensagem: {mensagem}\nRótulo:"


def prompt_few_shot(mensagem):
    """A mesma instrução, mais 5 exemplos.

    O formato é IDÊNTICO em todos os exemplos e igual ao da pergunta final:
    'Mensagem: ...' seguido de 'Rótulo: ...'. Isso não é capricho — é o que
    o modelo copia (nota 01, §6.1).
    """
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
        return None                          # truncou: não é resposta válida
    return escolha.message.content.strip().lower().rstrip(".")


def rodar(nome, construir_prompt):
    acertos = 0
    fora_do_dominio = 0

    print(f"### {nome}")
    for mensagem, esperado in TESTE:
        rotulo = classificar(construir_prompt(mensagem))
        ok = rotulo == esperado
        acertos += ok
        if rotulo not in CATEGORIAS:
            fora_do_dominio += 1

        print(f"  {'ok  ' if ok else 'ERRO'} esperado={esperado:<18} "
              f"obtido={rotulo}")
        time.sleep(PAUSA)

    print(f"  -> {acertos}/{len(TESTE)} corretos | "
          f"{fora_do_dominio} fora do domínio\n")
    return acertos, fora_do_dominio


print(f"modelo: {MODELO} | {len(TESTE)} mensagens | {len(EXEMPLOS)} exemplos\n")
print("Antes de olhar o resultado, abra o código e leia os dois prompts.\n")

zero = rodar("A) zero-shot — só a instrução", prompt_zero_shot)
few = rodar("B) few-shot — a instrução + 5 exemplos", prompt_few_shot)

print("=" * 60)
print(f"{'':<12} {'corretos':>10} {'fora do domínio':>18}")
print(f"{'zero-shot':<12} {zero[0]:>7}/{len(TESTE)} {zero[1]:>18}")
print(f"{'few-shot':<12} {few[0]:>7}/{len(TESTE)} {few[1]:>18}")

print(
    "\nComo ler este resultado:\n"
    "  - Olhe primeiro a coluna 'fora do domínio': é comum o zero-shot\n"
    "    devolver 'O rótulo é: endereco_errado' ou 'Endereço errado.' em vez\n"
    "    do rótulo puro. O ganho do few-shot costuma ser de FORMATO, antes\n"
    "    de ser de acerto.\n"
    "  - E formato tem uma solução mais direta que exemplos: JSON Schema com\n"
    "    enum (aula 02, nota 02, §7). Vale comparar as duas abordagens.\n"
    "  - Se os dois empataram, a resposta certa é ficar com o zero-shot: é o\n"
    "    prompt mais simples que resolve. Comece sempre por ele e só escale\n"
    "    quando MEDIR que precisa.\n"
    "\n"
    "  Experimente: remova um dos 5 exemplos do dados.py — de preferência o\n"
    "  de uma categoria que aparece pouco no teste — e rode de novo. O que\n"
    "  acontece com as mensagens daquela categoria?"
)
