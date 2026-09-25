# Aula 08 — 04: ESQUECER — REMOÇÃO, solicitada pelo titular.
#
# São três causas distintas de esquecimento, e esta é obrigação legal:
#
#   contradição  o fato mudou
#   decaimento   o fato envelheceu
#   remoção      o titular solicitou (LGPD)
#
# O requisito da remoção é de COBERTURA: o dado precisa sair de todas as
# estruturas em que foi gravado. Uma remoção parcial não cumpre a obrigação,
# e a diferença entre cumprir e declarar cumprido é a existência de uma
# verificação independente.
#
# ESTE SCRIPT FALHA NA PRIMEIRA VERIFICAÇÃO, por construção. Ele apaga as
# três memórias, declara a remoção concluída, e a verificação localiza o
# titular numa quarta estrutura — os checkpoints. A falha demonstra por que a
# verificação é necessária.

from checkpoint import arquivos as checkpoints_existentes
from checkpoint import esquecer as esquecer_checkpoints
from checkpoint import procurar as procurar_em_checkpoints
from checkpoint import salvar as salvar_checkpoint
from dados import CHECKPOINT, EPISODIOS
from memoria_episodica import MemoriaEpisodica
from memoria_procedural import MemoriaProcedural
from memoria_semantica import MemoriaSemantica

CODIGO_FUNCIONARIO = "F-088"

episodica = MemoriaEpisodica(recriar=True)
episodica.gravar(EPISODIOS)

semantica = MemoriaSemantica()
semantica.gravar(CODIGO_FUNCIONARIO, "destinos_frequentes",
                 ["Lisboa", "Curitiba"], "2026-08-11")
semantica.gravar(CODIGO_FUNCIONARIO, "media_por_refeicao", 178.0, "2026-08-11")
semantica.gravar("F-091", "historico_reprovacao", "transporte", "2026-04-04")

procedural = MemoriaProcedural()
procedural.gravar("Ids de funcionário têm o formato F seguido de três dígitos.")

# A quarta estrutura, deliberadamente ausente da lista de remoção: o
# checkpoint do script 00, que contém {"funcionario": "F-088"} nos argumentos
# do passo 0.
salvar_checkpoint(CHECKPOINT)

# ---------------------------------------------------------- remoção sob pedido
print("=" * 74)
print(f"REMOÇÃO SOB PEDIDO — o titular {CODIGO_FUNCIONARIO} solicita o apagamento")
print("=" * 74)

antes = {
    "episodica": len(episodica),
    "semantica": len(semantica.sobre(CODIGO_FUNCIONARIO)),
    "procedural": len(procedural.regras()),
    "checkpoints": len(checkpoints_existentes()),
}
print(f"""
  ANTES: episódica={antes['episodica']} registros · """
      f"""semântica={antes['semantica']} fatos sobre {CODIGO_FUNCIONARIO} · """
      f"""procedural={antes['procedural']} regras · checkpoints={antes['checkpoints']}""")

# As três memórias. É o que a taxonomia do script 02 cobre, e é o que
# qualquer um lembraria de apagar.
removidos_ep = episodica.esquecer_funcionario(CODIGO_FUNCIONARIO)
removidos_sem = semantica.esquecer(CODIGO_FUNCIONARIO)

print(f"  DEPOIS: episódica={len(episodica)} · "
      f"semântica={len(semantica.sobre(CODIGO_FUNCIONARIO))} · "
      f"procedural={len(procedural.regras())}")
print(f"\n  removidos: {removidos_ep} episódios, {removidos_sem} fatos")
print("\n  \"Apaguei das três memórias.\" É o ponto em que a maioria para.")


# ------------------------------------------------------------------- a PROVA
def varrer() -> list[tuple[str, str]]:
    """Procura o titular nas QUATRO estruturas, cada uma do jeito dela."""
    achados = []

    for r in episodica.recuperar(f"despesas do funcionário {CODIGO_FUNCIONARIO}", k=5):
        if (r.get("funcionario") == CODIGO_FUNCIONARIO
                or CODIGO_FUNCIONARIO in r["resumo"]):
            achados.append(("episodica", r["id"]))

    if semantica.sobre(CODIGO_FUNCIONARIO):
        achados.append(("semantica", str(semantica.sobre(CODIGO_FUNCIONARIO))))

    for regra in procedural.regras():
        if CODIGO_FUNCIONARIO in regra:
            achados.append(("procedural", regra[:60]))

    # A quarta estrutura, ausente da lista de remoção.
    for caminho in procurar_em_checkpoints(CODIGO_FUNCIONARIO):
        achados.append(("checkpoint", caminho.name))

    return achados


print(f"\n{'=' * 74}")
print("A PROVA — verificar, não afirmar")
print("=" * 74)

vestigios = varrer()
print()
if vestigios:
    print(f"  FALHOU — {len(vestigios)} vestígio(s) de {CODIGO_FUNCIONARIO}:")
    for estrutura, o_que in vestigios:
        print(f"      [{estrutura}] {o_que}")
    print("""
  O checkpoint não é uma das três memórias, e foi por isso que escapou: a
  varredura foi feita contra a TAXONOMIA, e não contra os lugares em que o
  dado efetivamente caiu.

  Ele contém {"funcionario": "F-088"} nos argumentos do passo 0: dado
  pessoal, num arquivo que a taxonomia não classifica como memória.
""")
else:
    print(f"  OK — nenhum vestígio de {CODIGO_FUNCIONARIO}.")

# --------------------------------------------------- a segunda passada
print("=" * 74)
print("A CORREÇÃO, E A SEGUNDA PASSADA")
print("=" * 74)

removidos_ckpt = esquecer_checkpoints(CODIGO_FUNCIONARIO)
print(f"\n  removidos {removidos_ckpt} checkpoint(s) que mencionavam o titular.\n")

vestigios = varrer()
if vestigios:
    print(f"  FALHOU DE NOVO — {len(vestigios)} vestígio(s):")
    for estrutura, o_que in vestigios:
        print(f"      [{estrutura}] {o_que}")
else:
    print(f"  OK — nenhum vestígio de {CODIGO_FUNCIONARIO} nas quatro estruturas.")

# Esta verificação é o requisito, e não a chamada de delete. "Apaguei" é
# afirmação; "procurei nas quatro estruturas e não achei" é prova. A
# diferença entre as duas é literalmente o que aconteceu na tela acima: a
# primeira estava correta sobre o que fez, e errada sobre o resultado.
#
# Duas lições de projeto, e nenhuma é sobre LGPD:
#
# 1. A lista de lugares a varrer não se deriva da taxonomia. Ela se deriva
#    de um inventário de ONDE O DADO CAI — e esse inventário cresce toda
#    vez que alguém acrescenta uma estrutura ao sistema.
#
# 2. A varredura do checkpoint é TEXTUAL, e não por chave. O identificador
#    aparece dentro de `argumentos`, `objetivo` e `resposta`, em
#    profundidades diferentes. Uma busca por campo não o acharia em todos.
#
# A memória PROCEDURAL é o caso de detecção mais difícil dos quatro: a regra
# sobre o formato do id derivou de um erro do F-088 e não contém o
# identificador. Nessa forma ela não é dado pessoal. Se contivesse, a
# varredura textual implementada acima não a alcançaria, porque o system
# prompt não costuma ser incluído no escopo da busca.
