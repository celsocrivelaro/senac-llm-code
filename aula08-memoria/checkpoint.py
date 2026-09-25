# Aula 08 — O CHECKPOINT: o estado de uma execução, em disco.
#
# Um arquivo por execução, nomeado pelo identificador dela. Não é banco, não
# é serviço: é um `write_text` com o objeto serializado.
#
# O checkpoint não é memória de longo prazo, e por isso ocupa um arquivo
# separado. As três memórias compartilham a raiz de `armazenamento.py` porque
# respondem a perguntas sobre o passado; o checkpoint responde a "onde esta
# execução parou". Escopo, ciclo de vida e padrão de acesso são distintos.
#
# Na nomenclatura da literatura ele tem nome: é a persistência da MEMÓRIA DE
# CURTO PRAZO (short-term / working memory) — o estado no nível da execução,
# descartado quando ela termina. Quando esta aula escreve "memória" sem
# qualificar, leia-se memória de longo prazo, que é o objeto dos scripts 02
# em diante.
#
# O checkpoint armazena DADO PESSOAL: os argumentos de cada passo contêm o
# identificador do titular analisado na execução. Por isso o módulo expõe
# `esquecer()`. Uma remoção sob pedido que percorra apenas as três memórias
# não alcança o checkpoint — falha que o script `04-esquecer-remocao.py`
# reproduz.

import json
from pathlib import Path

CHECKPOINTS = Path(__file__).parent / "checkpoints"


def salvar(estado: dict) -> Path:
    """Quatro linhas, e a regra que as acompanha.

    SEMPRE DEPOIS DE EXECUTAR, NUNCA ANTES. Se o checkpoint registrar a
    intenção e o processo cair entre o registro e a execução, a retomada
    reexecuta a ação — e se a ação for escrita, ela acontece duas vezes.

    Sobra uma fresta: cair ENTRE executar e gravar. Quem a fecha é a chave
    de idempotência — derivar o id da escrita do seu conteúdo, para que a
    segunda tentativa encontre a primeira em vez de duplicá-la. As duas
    salvaguardas trabalham juntas e nenhuma basta sozinha.
    """
    CHECKPOINTS.mkdir(exist_ok=True)
    caminho = CHECKPOINTS / f"{estado['execucao_id']}.json"
    caminho.write_text(json.dumps(estado, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    return caminho


def carregar(execucao_id: str) -> dict:
    caminho = CHECKPOINTS / f"{execucao_id}.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def arquivos() -> list[Path]:
    return sorted(CHECKPOINTS.glob("*.json")) if CHECKPOINTS.exists() else []


def procurar(termo: str) -> list[Path]:
    """Quais checkpoints mencionam o termo, em qualquer campo.

    É varredura TEXTUAL, e não por chave: o identificador aparece dentro de
    `argumentos`, `objetivo` e `resposta`, em profundidades diferentes. Uma
    busca por campo não o encontraria em todos.
    """
    return [c for c in arquivos()
            if termo in c.read_text(encoding="utf-8")]


def esquecer(termo: str) -> int:
    """Remove os checkpoints que mencionam o termo. Devolve quantos.

    A granularidade é o ARQUIVO, e não o campo: um checkpoint com o
    identificador removido não retoma mais nada, então editá-lo produziria
    um arquivo inútil que ainda ocupa espaço. Execução que envolve o
    titular sai inteira.
    """
    alvos = procurar(termo)
    for caminho in alvos:
        caminho.unlink()
    return len(alvos)
