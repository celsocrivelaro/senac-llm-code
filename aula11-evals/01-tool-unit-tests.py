# TOOL UNIT TESTS — as ferramentas, testadas sem o modelo.
#
# A TÉCNICA: testar cada ferramenta como função comum, sem chamar o modelo.
#
# O CASO: no ticket #355, o agente perguntou pela despesa "D4612" (sem o
# hífen) seis vezes seguidas, até esgotar o orçamento de passos. O modelo
# não estava "raciocinando mal": a ferramenta devolveu um erro que não
# dizia o que estava errado, e ele não tinha como se corrigir.
#
# O que mais quebra em produção não é raciocínio, é ERRO MAL DESCRITO.
# Por isso o teste mais importante aqui não é o do caminho feliz: é o que
# confere se a MENSAGEM DE ERRO diz o que recebeu e o que seria válido.
#
#     python 01-tool-unit-tests.py          # não chama modelo

import json

from sistema import (PARECERES, buscar_regulamento, consultar_despesa,
                     consultar_politica, limpar_pareceres, registrar_parecer)


def chamar(ferramenta, **args) -> dict | list:
    return json.loads(ferramenta.invoke(args))


def erro_util(saida: dict, recebido: str) -> bool:
    """Um erro serve ao modelo se diz O QUE recebeu e O QUE seria válido."""
    texto = json.dumps(saida, ensure_ascii=False)
    return "erro" in saida and recebido in texto and ("validos" in saida or "esperado" in saida)


limpar_pareceres()
p1 = chamar(registrar_parecer, despesa="D-4612", veredito="reprovado", chave="D-4612-ana-0210")
p2 = chamar(registrar_parecer, despesa="D-4612", veredito="reprovado", chave="D-4612-ana-0210")

TESTES = [
    # ferramenta            o que se testa                      passou?
    ("consultar_despesa",  "caminho feliz",                    chamar(consultar_despesa, despesa="D-4612")["valor"] == 138.0),
    ("consultar_despesa",  "id inexistente devolve erro",      "erro" in chamar(consultar_despesa, despesa="D4612")),
    ("consultar_despesa",  "o erro diz o que recebeu e o válido", erro_util(chamar(consultar_despesa, despesa="D4612"), "D4612")),
    ("consultar_politica", "caminho feliz",                    chamar(consultar_politica, categoria="refeicao")["teto"] == 120.0),
    ("consultar_politica", "categoria inválida devolve erro",  "erro" in chamar(consultar_politica, categoria="almoço")),
    ("consultar_politica", "o erro diz o que recebeu e o válido", erro_util(chamar(consultar_politica, categoria="almoço"), "almoço")),
    ("buscar_regulamento", "exceção de capital acha o art. 12", chamar(buscar_regulamento, consulta="teto hospedagem capitais")[0]["artigo"] == "art-12"),
    ("buscar_regulamento", "fora do corpus recusa",            "recusa" in chamar(buscar_regulamento, consulta="férias coletivas")),
    ("registrar_parecer",  "primeira chamada cria",            p1["ja_existia"] is False),
    ("registrar_parecer",  "mesma chave não duplica",          p2["ja_existia"] is True and len(PARECERES) == 1),
    ("registrar_parecer",  "o erro diz o que recebeu e o válido", erro_util(chamar(registrar_parecer, despesa="D-4612", veredito="negado", chave="x"), "negado")),
]

print(f"  {'ferramenta':<20} {'teste':<40} resultado")
print("  " + "-" * 72)
for ferramenta, teste, ok in TESTES:
    print(f"  {ferramenta:<20} {teste:<40} {'ok' if ok else 'FALHOU'}")

falhas = [(f, t) for f, t, ok in TESTES if not ok]
print(f"\n  {len(TESTES) - len(falhas)}/{len(TESTES)} passaram")

print("\n  o que o modelo recebeu no ticket #355:")
print(f"    {consultar_despesa.invoke({'despesa': 'D4612'})}")
print("  e o que ele recebe quando erra a categoria:")
print(f"    {consultar_politica.invoke({'categoria': 'almoço'})}")

# A primeira mensagem não diz que faltou o hífen, nem quais ids existem: o
# modelo só pode repetir. A segunda traz o valor recebido e a lista válida,
# e o modelo se corrige na chamada seguinte. Corrija a `consultar_despesa`
# em `sistema.py` e rode de novo.
