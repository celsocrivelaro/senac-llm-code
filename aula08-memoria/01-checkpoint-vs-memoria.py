# Aula 08 — 01: CHECKPOINT E MEMÓRIA SÃO ESTRUTURAS DISTINTAS.
#
# CHECKPOINT  estado de UMA execução, serializado.
#             Responde: "onde esta execução parou".
#             Escopo: uma execução.  Acesso: por identificador.
#
# MEMÓRIA     o que foi observado ao longo de VÁRIAS execuções, indexado.
#             Responde: "o que já se sabe sobre isto".
#             Escopo: o histórico.   Acesso: por relevância.
#
# Serializar o estado de todas as execuções não produz memória: produz um
# conjunto de arquivos sem critério de recuperação. Memória exige recuperar,
# e recuperar exige um critério de relevância.
#
# ESCOPO DESTE SCRIPT. Consulta as duas estruturas com as mesmas duas
# perguntas. Cada estrutura responde uma e falha na outra, porque os escopos
# não se sobrepõem — e portanto uma não substitui a outra.
#
# O CHECKPOINT vem do `dados.py`, e é o mesmo objeto que o script 00
# construiu, pausou e retomou. Aqui ele aparece já concluído.

import json

from dados import CHECKPOINT, EPISODIOS
from memoria_episodica import MemoriaEpisodica

# A tarefa corrente. O texto é idêntico nos scripts 01, 02 e 05: a aula
# executa a mesma tarefa repetidamente, e o script 05 mede a diferença de
# passos entre a primeira execução e a segunda. Alterar este texto exige
# alterá-lo nos três arquivos.
TAREFA = ("Analisar a despesa D-4612 do funcionário F-088: refeição de "
          "R$ 245,00 por pessoa, em viagem a Lisboa, com nota fiscal.")

# A tabela da fronteira — escopo, propósito, forma, leitura, crescimento e
# descarte — está na nota 02 §1 e no slide 02. Não se repete aqui: o que
# este script tem a acrescentar não é a tabela, é a execução.

def falta_para_retomar(estrutura: dict) -> list[str]:
    """Quais requisitos de retomada a estrutura NÃO atende.

    O `passos` não basta EXISTIR: no fragmento da memória ele é o número 3,
    e não se retoma uma execução a partir de uma contagem. É a armadilha
    que torna o teste interessante — os dois têm um campo com esse nome.
    """
    faltas = []
    if not isinstance(estrutura.get("passos"), list):
        faltas.append("passos (a lista, não a contagem)")
    faltas += [campo for campo in ("ferramentas_ativas", "historico", "termino")
               if campo not in estrutura]
    return faltas


def em_tokens(objeto) -> int:
    """~4 caracteres por token em PT-BR. Grosseiro e suficiente."""
    texto = objeto if isinstance(objeto, str) else json.dumps(objeto,
                                                              ensure_ascii=False)
    return len(texto) // 4


def mil(n: int) -> str:
    """21360 -> '21.360'. O separador de milhar do português."""
    return f"{n:,}".replace(",", ".")


# ------------------------------------------------------------- A: o checkpoint
print("=" * 74)
print("A — O CHECKPOINT: uma execução, inteira")
print("=" * 74)
print()
print(json.dumps(CHECKPOINT, ensure_ascii=False, indent=2))

tokens_checkpoint = em_tokens(CHECKPOINT)
print(f"""
  ~{tokens_checkpoint} tokens, e um trabalho só: RETOMAR a exec-0a1f exatamente onde
  ela parou. Para isso ele precisa estar ÍNTEGRO — qualquer campo que
  falte inviabiliza a retomada.
""")

total_tokens = sum(t["tokens"] for t in EPISODIOS)
print("=" * 74)
print(f"E existem {len(EPISODIOS)} destes gravados")
print("=" * 74)
print(f"""
  {len(EPISODIOS)} execuções · {sum(t['passos'] for t in EPISODIOS)} passos · {mil(total_tokens)} tokens

  Tudo isso está no disco. E a pergunta de agora é:

      {TAREFA}

  Qual dos dez checkpoints é relevante para esta tarefa? Sem um critério de
  recuperação há duas respostas possíveis, e ambas são inúteis: "todos", que
  significa ~{mil(total_tokens // 4)} tokens de contexto, ou "nenhum", que é o resultado
  prático quando nada consulta os arquivos.

  Serializar dez checkpoints não produziu memória. Produziu um conjunto de
  arquivos sem critério de recuperação.
""")

# ---------------------------------------------------------------- B: a memória
print("=" * 74)
print("B — A MEMÓRIA: as mesmas dez, indexadas")
print("=" * 74)

episodica = MemoriaEpisodica(recriar=True)
episodica.gravar(EPISODIOS)

# A MESMA execução, nas duas formas. É a linha "estado íntegro × fragmento
# selecionado" da tabela, com número.
fragmento = next(t for t in EPISODIOS if t["id"] == CHECKPOINT["execucao_id"])
tokens_fragmento = em_tokens(fragmento)
primeiro = CHECKPOINT["passos"][0]
descartado = 100 - (tokens_fragmento * 100 // tokens_checkpoint)

print(f"""
  a MESMA exec-0a1f, nas duas formas:

      checkpoint  ~{tokens_checkpoint:>4} tokens   {', '.join(list(CHECKPOINT)[:4])},
                                 {', '.join(list(CHECKPOINT)[4:])}

      memória     ~{tokens_fragmento:>4} tokens   {', '.join(list(fragmento)[:4])},
                                 {', '.join(list(fragmento)[4:])}

  A memória descartou ~{descartado}% do checkpoint, e descartou DE PROPÓSITO.

  O campo `passos` aparece nos dois, e NÃO é a mesma coisa:

      no checkpoint ... a lista dos {len(CHECKPOINT['passos'])}, com argumentos e resultados.
                        O primeiro é
                            {primeiro['ferramenta']}({primeiro['argumentos']})
                                -> {primeiro['resultado']}
      na memória ...... {fragmento['passos']}
                        só o número

  É a linha "estado íntegro × fragmento selecionado" da tabela: um guarda
  O QUE aconteceu, o outro guarda QUE aconteceu.
""")

relevantes = episodica.recuperar(TAREFA, k=3)
print(f"  indexadas: {len(episodica)} execuções. Recuperadas para a tarefa de agora:\n")
for e in relevantes:
    print(f"  [{e['data']}] {e['id']}  (distância {e['distancia']:.4f})")
    print(f"      {e['resumo'][:110]}")

tokens_memoria = sum(em_tokens(e["resumo"]) for e in relevantes)
print(f"""
  ~{tokens_memoria} tokens em vez de ~{mil(total_tokens // 4)}, e as três recuperadas são as de
  Lisboa e a do teto internacional — as que a tarefa de agora precisa.
""")

# --------------------------------------------------------- C: as duas perguntas
print("=" * 74)
print("C — A MESMA PERGUNTA ÀS DUAS ESTRUTURAS. DUAS VEZES.")
print("=" * 74)

# Pergunta 1 — retomar. Não é afirmação: é uma checagem sobre as duas
# estruturas que estão na memória do processo, agora.
faltam_no_checkpoint = falta_para_retomar(CHECKPOINT)
faltam_no_fragmento = falta_para_retomar(fragmento)

print(f"""
  PERGUNTA 1 — "retome a exec-0a1f exatamente onde ela parou"

      checkpoint ... {'RESPONDE' if not faltam_no_checkpoint else 'NÃO RESPONDE'}
                     {len(CHECKPOINT['passos'])} passos registrados, término {CHECKPOINT['termino']},
                     histórico preservado

      memória ...... {'RESPONDE' if not faltam_no_fragmento else 'NÃO RESPONDE'}
                     falta: {faltam_no_fragmento[0]}
                            {', '.join(faltam_no_fragmento[1:])}
                     o fragmento não guarda onde a execução parou, e nem
                     deveria — guardar isso de dez execuções é o arquivo
                     morto da seção A""")

# Pergunta 2 — lembrar. Aqui é o checkpoint que não serve, e o motivo é
# quantitativo: para responder ele teria que entrar inteiro no contexto.
print(f"""
  PERGUNTA 2 — "o que já se sabe que ajude na despesa de agora?"

      checkpoint ... NÃO RESPONDE
                     não há por onde perguntar: seria ler os {len(EPISODIOS)} inteiros,
                     ~{mil(total_tokens // 4)} tokens, para descobrir quais {len(relevantes)} interessavam

      memória ...... RESPONDE
                     {len(relevantes)} fragmentos, ~{tokens_memoria} tokens, escolhidos por relevância
""")

# ISTO é memória: recuperação sobre o passado. É a aula 07 apontada para
# dentro — mesmo mecanismo, objeto diferente.
#
# O QUE MUDA NA SEGUNDA EXECUÇÃO
#
# Sem memória, a segunda execução da mesma tarefa repete as mesmas consultas
# e comete o mesmo erro de id que a primeira cometeu — porque começa do zero.
#
# Com memória, ela começa sabendo que:
#   - F-088 já viajou a Lisboa duas vezes;
#   - o Art. 4º §2º foi o artigo aplicado nas duas;
#   - o formato do id é F seguido de TRÊS dígitos.
#
# O script 05 quantifica esse efeito em passos evitados, que é a grandeza na
# qual o ganho da memória é comparável.
