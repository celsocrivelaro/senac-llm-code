# Aula 06 — As estratégias de chunking.
#
# O chunk é a UNIDADE DE RECUPERAÇÃO: é ele que volta da busca, e é ele que
# vai chegar ao leitor sem o texto em volta. Portanto precisa fazer sentido
# SOZINHO — e é esse o único critério que separa as três estratégias abaixo.
#
# As três residem no mesmo arquivo porque o objeto de estudo é a COMPARAÇÃO
# entre elas, e não cada uma isoladamente. Lidas lado a lado, a diferença de
# critério de corte é visível antes da medição.
#
# O `02-chunking.py` roda as três e mede `recall@k`. O `03-buscador.py` usa
# só a vencedora. Nenhuma das três chama a API — chunking é manipulação de
# texto, e o embedding só entra depois, no `indice_memoria.py`.

import re


# ------------------------------------------------- por contagem de caracteres
def por_caracteres(texto: str, tamanho: int = 400) -> list[dict]:
    """Cortar a cada N caracteres. A mais simples, e a que ignora
    completamente a estrutura que o autor do documento escreveu."""
    limpo = texto.strip()
    return [{"id": f"c{i//tamanho}", "texto": limpo[i:i + tamanho]}
            for i in range(0, len(limpo), tamanho)]


def por_caracteres_sobrepostos(texto: str, tamanho: int = 400,
                               sobreposicao: int = 100) -> list[dict]:
    """Cortar a cada N caracteres, com sobreposição.

    A sobreposição existe para que uma frase partida ao meio apareça inteira
    em pelo menos um dos chunks. Custa espaço no índice: o mesmo texto é
    embutido mais de uma vez.
    """
    limpo = texto.strip()
    passo = tamanho - sobreposicao
    return [{"id": f"s{i//passo}", "texto": limpo[i:i + tamanho]}
            for i in range(0, len(limpo), passo)]


# ----------------------------------------------------------- por estrutura
#
# O documento JÁ VEM CORTADO pelo autor, e esta estratégia aproveita esse
# corte. É a que vence a medição do 02 e a única que segue para o 03.

RE_ARTIGO = re.compile(r"^Art\. \d+[ºo]?\b", re.M)
RE_PARAGRAFO = re.compile(r"^§\d+[ºo]?", re.M)


def por_estrutura(texto: str) -> list[dict]:
    """Cortar por artigo e parágrafo.

    O documento JÁ VEM CORTADO pelo autor — artigos e parágrafos são a
    unidade de sentido que o legislador escolheu. Ignorar esse corte é jogar
    informação fora de graça.

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

# O registro das três, na ordem em que a aula as apresenta. Acrescentar uma
# quarta é acrescentar uma chave — e a comparação do 02 a inclui sozinha.
ESTRATEGIAS = {
    "caracteres": lambda t: por_caracteres(t, 400),
    "sobreposto": lambda t: por_caracteres_sobrepostos(t, 400, 100),
    "estrutura": por_estrutura,
}
