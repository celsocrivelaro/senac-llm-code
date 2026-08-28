# Aula 03 — Prompt engineering
# 05 — Versionar o prompt, e a suíte que pega a regressão.
#
# Este script junta as três ideias do bloco "prompt como código":
#
#   1. O PROMPT VIVE EM ARQUIVO, não numa string no meio do .py.
#      Olhe a pasta prompts/ — e rode `diff prompts/extracao-v1.md
#      prompts/extracao-v2.md` para ver a diferença entre as versões.
#      É UMA PALAVRA.
#
#   2. A UNIDADE VERSIONADA É A COMBINAÇÃO prompt x modelo x parâmetros.
#      Versionar o texto sozinho não permite reproduzir bug: se o resultado
#      piorou, pode ter sido o prompt, o modelo (que o provedor atualizou
#      sob o alias -latest) ou um parâmetro que alguém ajustou.
#
#   3. A SUÍTE DE REGRESSÃO É O QUE PEGA A QUEBRA.
#      Não existe análise estática de prompt: acrescentar ou remover uma
#      palavra pode quebrar um caso que a palavra nem menciona. Só medindo.
#
# A v2 é uma edição que qualquer revisor humano aprovaria num PR de
# "limpeza de texto". Rode e veja o que ela faz com a suíte.

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)

PROMPTS = Path(__file__).parent / "prompts"
PAUSA = 0.4

# Quantas vezes cada caso roda. O teste é FLAKY POR NATUREZA: temperature=0
# não garante saída idêntica (aula 02, nota 02, §6), então o critério não é
# "passou", é "passou k de N".
N = 3
LIMIAR = 0.90          # definido ANTES de ver o resultado — senão não testa nada


# --------------------------------------------------------------------------
# AS DUAS VERSÕES. Repare que cada uma nomeia a COMBINAÇÃO inteira, não só
# o texto: é isso que o `versao` identifica, e é isso que vai no log.
# --------------------------------------------------------------------------
VERSOES = {
    "v1": {
        "versao": 1,
        "prompt": "extracao-v1",
        "modelo": os.environ.get("LLM_MODELO", "mistral-small-latest"),
        "parametros": {"temperature": 0, "max_tokens": 30},
    },
    "v2": {
        "versao": 2,
        "prompt": "extracao-v2",
        "modelo": os.environ.get("LLM_MODELO", "mistral-small-latest"),
        "parametros": {"temperature": 0, "max_tokens": 30},
    },
}

# Os casos de teste, com o resultado esperado. Este conjunto é o ATIVO:
# é ele que permite comparar qualquer mudança futura.
CASOS = [
    ("Meu pedido 48219 era pra chegar terça e até hoje nada!",        "48219"),
    ("A caixa do pedido 77310 chegou toda amassada",                  "77310"),
    ("Pedido 90021 cancelado e recomprado como 90455, o 90455 "
     "não chegou",                                                    "90455"),
    ("PEDIDO 12 MIL 340 ENTREGUE NO ENDERECO ERRADO",                 "12340"),
    ("Recebi o pedido n 55.102 com a tela rachada",                   "55102"),
    ("o pedido 33871 sumiu, ninguém sabe informar",                   "33871"),
    ("boa tarde, sobre o 60014, tem previsão de entrega?",            "60014"),
    ("meu pedido é o 71255 e ainda não chegou",                       "71255"),
]


def carregar_prompt(nome, **variaveis):
    """Dez linhas que já entregam diff, review e `git revert`."""
    texto = (PROMPTS / f"{nome}.md").read_text(encoding="utf-8")
    return texto.format(**variaveis)


def extrair(config, mensagem):
    resposta = client.chat.completions.create(
        model=config["modelo"],
        messages=[{"role": "user",
                   "content": carregar_prompt(config["prompt"], mensagem=mensagem)}],
        **config["parametros"],
    )
    escolha = resposta.choices[0]
    if escolha.finish_reason == "length":
        return None
    return (escolha.message.content or "").strip()


def avaliar(saida, esperado):
    """Teste POR PROPRIEDADE, não por igualdade de texto.

    Duas propriedades, e as duas importam:
      1. a saída é SOMENTE dígitos — é o que o código a seguir espera;
      2. os dígitos são os certos.
    """
    if saida is None:
        return False, "truncou"
    if not saida.isdigit():
        return False, "não é só dígitos"
    if saida != esperado:
        return False, "número errado"
    return True, "ok"


def rodar_suite(nome, config):
    # O CARIMBO: em produção, estas três linhas vão no log de CADA requisição.
    # É o que transforma "a resposta de terça estava errada" numa consulta.
    print(f"### {nome}")
    print(f"    prompt={config['prompt']} versao={config['versao']} "
          f"modelo={config['modelo']} params={config['parametros']}")

    total_ok = 0
    total = 0

    for mensagem, esperado in CASOS:
        acertos = 0
        ultimo_motivo = ""
        ultima_saida = ""
        for _ in range(N):
            saida = extrair(config, mensagem)
            ok, motivo = avaliar(saida, esperado)
            acertos += ok
            if not ok:
                ultimo_motivo, ultima_saida = motivo, saida or ""
            time.sleep(PAUSA)

        total_ok += acertos
        total += N
        marca = "ok  " if acertos == N else "FALHA"
        detalhe = "" if acertos == N else f"  <- {ultimo_motivo}: {ultima_saida[:40]!r}"
        print(f"  {marca} {acertos}/{N}  esperado={esperado}{detalhe}")

    taxa = total_ok / total
    veredito = "PASSOU" if taxa >= LIMIAR else "REGRESSÃO"
    print(f"  -> {total_ok}/{total} = {taxa:.0%}  [{veredito}, limiar {LIMIAR:.0%}]\n")
    return taxa


print(f"{len(CASOS)} casos × {N} execuções por versão\n")
print("Antes de rodar, veja a diferença entre as duas versões do prompt:")
print("  diff prompts/extracao-v1.md prompts/extracao-v2.md\n")

taxa_v1 = rodar_suite("VERSÃO 1 — em produção", VERSOES["v1"])
taxa_v2 = rodar_suite("VERSÃO 2 — o PR de 'limpeza de texto'", VERSOES["v2"])

print("=" * 62)
print(f"v1: {taxa_v1:.0%}   v2: {taxa_v2:.0%}   diferença: {taxa_v2 - taxa_v1:+.0%}")

if taxa_v2 < LIMIAR <= taxa_v1:
    print("\n>>> A suíte BLOQUEARIA esse PR.")
elif taxa_v2 < taxa_v1:
    print("\n>>> A v2 piorou, mas ficou acima do limiar. Você mergearia?")
else:
    print("\n>>> Nesta execução as duas passaram. Rode de novo — e veja o\n"
          ">>> comentário sobre flakiness no fim.")

print(
    "\n" + "=" * 62 + "\n"
    "O que este script mostra:\n"
    "\n"
    "  1. A DIFERENÇA ENTRE AS VERSÕES É UMA PALAVRA: 'apenas'.\n"
    "     Nenhum revisor humano apontaria isso num diff de PR. A suíte\n"
    "     aponta em segundos. Revisar prompt lendo o texto é como revisar\n"
    "     código sem rodar os testes.\n"
    "\n"
    "  2. O QUE QUEBRA NÃO É A ACURÁCIA, É O CONTRATO. Olhe os motivos das\n"
    "     falhas: o modelo continua ACHANDO o número certo, mas devolve\n"
    "     'O número do pedido é 48219.' — e o seu json.loads, ou o seu\n"
    "     int(), quebra lá na frente, longe da causa.\n"
    "\n"
    "  3. O TESTE É POR PROPRIEDADE. Não comparamos a resposta com um texto\n"
    "     esperado — verificamos que ela é só dígitos e que os dígitos estão\n"
    "     certos. Comparar strings falharia sem nada estar quebrado.\n"
    "\n"
    "  4. O TESTE É FLAKY. Por isso o critério é k de N, e não 'passou'.\n"
    "     Rode duas vezes seguidas: os números provavelmente vão diferir.\n"
    "     Isso não é defeito da suíte — é propriedade do sistema sob teste.\n"
    "\n"
    "  5. O CARIMBO. As linhas 'prompt=... versao=... modelo=...' impressas\n"
    "     no topo de cada suíte são o que, em produção, vai no log de cada\n"
    "     requisição. Sem elas, 'a resposta de terça estava errada' não tem\n"
    "     resposta: o git log te diz como o ARQUIVO mudou, não qual\n"
    "     combinação estava rodando naquela hora.\n"
    "\n"
    "  Experimente: crie uma prompts/extracao-v3.md tentando consertar a v2\n"
    "  sem usar a palavra 'apenas' — por exemplo, com um exemplo negativo\n"
    "  ('não escreva explicação'). Acrescente ao dicionário VERSOES e rode.\n"
    "  Você acabou de fazer um ciclo completo: mudou, mediu, comparou."
)
