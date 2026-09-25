# Aula 07 — O corte em chunks.
#
# Cópia de `estrategias_chunking.por_estrutura` da aula 06.
#
# Na aula 06 a estratégia de corte era o objeto de estudo: três estratégias
# foram medidas em recall@k e o corte por estrutura obteve o melhor
# resultado. Nesta aula ela entra como premissa, e o objeto de estudo passa a
# ser o que ocorre depois da recuperação.
#
# A duplicação tem um custo — as cópias podem divergir — e uma contrapartida:
# o corte é decisão de projeto desta aula, que precisa poder alterá-lo. O
# parágrafo revogado do `CORPUS_COM_RUIDO` é um caso que pode exigir ajuste,
# e alterá-lo aqui não invalida a medição de recall que a aula 06 faz sobre o
# corte original.

import re

RE_ARTIGO = re.compile(r"^Art\. \d+[ºo]?\b", re.M)
RE_PARAGRAFO = re.compile(r"^§\d+[ºo]?", re.M)


def por_estrutura(texto: str) -> list[dict]:
    """Cortar por artigo e parágrafo.

    O documento normativo já traz um corte definido pelo autor: artigo e
    parágrafo são as unidades de sentido escolhidas por quem o redigiu.
    Cortar por contagem de caracteres descarta essa informação.

    Cada chunk carrega o cabeçalho do artigo a que pertence, para que o
    parágrafo faça sentido isolado: "§2º Em viagem internacional, o limite
    de que trata o §1º passa a R$ 260,00" não significa nada sem saber que
    o artigo é o das despesas com alimentação.
    """
    chunks: list[dict] = []
    artigo_atual = ""
    cabecalho = ""

    for bloco in [b.strip() for b in texto.strip().split("\n\n") if b.strip()]:
        linhas = bloco.split("\n")
        if RE_ARTIGO.match(linhas[0]):
            artigo_atual = linhas[0].split("—")[0].strip().rstrip(".")
            cabecalho = linhas[0].strip()
            corpo = "\n".join(linhas[1:]).strip()
        else:
            corpo = bloco

        paragrafos = _partir_paragrafos(corpo)
        if not paragrafos:                       # artigo sem § (o caput)
            chunks.append({"id": artigo_atual or "preambulo",
                           "texto": bloco.strip()})
            continue

        for marca, trecho in paragrafos:
            chunks.append({
                "id": f"{artigo_atual} {marca}" if marca else artigo_atual,
                "texto": f"{cabecalho}\n{trecho}" if cabecalho else trecho,
            })
    return chunks


def _partir_paragrafos(corpo: str) -> list[tuple[str, str]]:
    """Devolve [(marca, texto)] por parágrafo. Marca vazia = caput."""
    marcas = list(RE_PARAGRAFO.finditer(corpo))
    if not marcas:
        return [("", corpo)] if corpo else []

    partes = []
    if marcas[0].start() > 0:
        caput = corpo[:marcas[0].start()].strip()
        if caput:
            partes.append(("", caput))
    for i, m in enumerate(marcas):
        fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(corpo)
        partes.append((m.group().strip(), corpo[m.start():fim].strip()))
    return partes


# O corte em uso, exposto como constante nomeada. Alterá-lo altera o recall,
# e por isso ele integra o carimbo de versão do índice (aula 03, nota 03).
ESTRATEGIA = por_estrutura
