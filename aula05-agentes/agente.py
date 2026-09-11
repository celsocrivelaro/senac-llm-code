# Aula 05 — Arquitetura de agentes
# O AGENTE: o objeto de estado, o orçamento, as ferramentas e o laço.
#
# Compartilhado pelos scripts 03, 04, 05 e 06 — e só por eles. Os scripts 00,
# 01 e 02 não importam nada daqui: eles demonstram WORKFLOWS, e cada um se
# explica sozinho no próprio arquivo.
#
# A razão de estes quatro dividirem um módulo é oposta: eles não são quatro
# demonstrações, são O MESMO AGENTE visto quatro vezes. O 03 apresenta o
# estado, o 04 as formas de terminar, o 05 os erros, o 06 a compressão. A
# pergunta que o aluno faz em cada um é "o que mudou desde o anterior?" — e
# ela só tem resposta se o que NÃO mudou estiver num lugar só.
#
# Este arquivo é a nota 02 desta aula virando código. A ideia única:
#
#     mensagens[] é FORMATO DE TRANSPORTE, não é o estado do agente.
#
# O estado é um objeto; a lista de mensagens é DERIVADA dele a cada volta.
# Sem essa separação, nada do que vem nos scripts 04, 05 e 06 é implementável:
# orçamento, detecção de laço, checkpoint e compaction precisam de informação
# que simplesmente não existe dentro de uma lista de dicionários de mensagem.
#
# Compare com o `04-tool-calling.py` da aula 03. O laço é o mesmo ReAct;
# o que mudou é o que ele carrega.

import json
import os
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError, APIStatusError

from dados import PEDIDOS, CLIENTES, CHAMADOS, CATEGORIAS, HOJE

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://api.mistral.ai/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
)
MODELO = os.environ.get("LLM_MODELO", "mistral-small-latest")

CHECKPOINTS = Path(__file__).parent / "checkpoints"


# ============================================================ EXCEÇÕES
# A distinção mais importante da nota 03: quem classifica o erro é o SEU
# código, não o modelo.

class ErroRecuperavel(Exception):
    """O modelo pode contornar mudando a chamada. Volta como observação."""

    def __init__(self, mensagem, **contexto):
        super().__init__(mensagem)
        self.payload = {"erro": mensagem, **contexto}


class ErroFatal(Exception):
    """Nenhuma decisão do modelo resolve. Aborta o laço."""


class PausaParaHumano(Exception):
    """Ação irreversível: o agente para, grava e devolve o controle."""


# ============================================================ O ESTADO

class Termino(str, Enum):
    RESPONDEU = "respondeu"             # o modelo concluiu
    ORCAMENTO = "orcamento_esgotado"    # bateu um dos três tetos
    ERRO_FATAL = "erro_fatal"           # não dá para continuar
    HUMANO = "aguardando_humano"        # precisa de confirmação
    LACO = "laco_detectado"             # girando sem progresso


@dataclass
class Passo:
    indice: int
    ferramenta: str | None
    argumentos: dict
    resultado: dict | None = None
    erro: str | None = None
    tokens_entrada: int = 0
    tokens_saida: int = 0
    # preenchidos pelo tool clearing (script 06)
    resumo: str | None = None
    limpo: bool = False


@dataclass
class Estado:
    objetivo: str                                    # imutável: a âncora
    execucao_id: str = field(default_factory=lambda: uuid4().hex[:8])
    passos: list[Passo] = field(default_factory=list)
    tokens_gastos: int = 0
    ferramentas_ativas: list[str] = field(default_factory=list)
    termino: Termino | None = None
    motivo: str | None = None
    resposta: str | None = None
    pendencia: dict | None = None                    # ação aguardando humano
    contexto_por_passo: list[int] = field(default_factory=list)
    # o histórico como o modelo o vê — DERIVADO, e reescrevível
    historico: list[dict] = field(default_factory=list)

    @property
    def n_passos(self) -> int:
        return len(self.passos)

    def registrar(self, passo: Passo) -> None:
        self.passos.append(passo)


@dataclass
class Orcamento:
    """Três tetos. `max_passos` sozinho não é orçamento: um passo consome
    entre 300 e 40.000 tokens, então 'no máximo 10 passos' não é um limite."""
    max_passos: int = 12
    max_tokens: int = 60_000
    max_segundos: float = 120.0
    inicio: float = field(default_factory=time.monotonic)

    def excedido(self, estado: Estado) -> str | None:
        """Devolve QUAL teto estourou — bool seria mais simples e inútil."""
        if estado.n_passos >= self.max_passos:
            return f"passos {estado.n_passos}/{self.max_passos}"
        if estado.tokens_gastos >= self.max_tokens:
            return f"tokens {estado.tokens_gastos}/{self.max_tokens}"
        decorrido = time.monotonic() - self.inicio
        if decorrido >= self.max_segundos:
            return f"tempo {decorrido:.0f}s/{self.max_segundos:.0f}s"
        return None


# ============================================================ FERRAMENTAS

def consultar_pedido(numero: str) -> dict:
    if not numero.isdigit() or len(numero) != 5:
        raise ErroRecuperavel(
            "formato de número de pedido inválido",
            esperado="5 dígitos, ex: 48219", recebido=numero,
            sugestao="peça o número ao cliente ou use listar_pedidos")
    pedido = PEDIDOS.get(numero)
    if pedido is None:
        raise ErroRecuperavel(
            "pedido não encontrado", recebido=numero,
            sugestao="confirme o número com o cliente; use listar_pedidos")
    return {"numero": numero, **pedido}


def listar_pedidos() -> dict:
    return {"pedidos": sorted(PEDIDOS)}


def consultar_cliente(cliente_id: str) -> dict:
    """A ferramenta usada no script 05 para provocar um erro RECUPERÁVEL:
    o formato é C-001 (três dígitos), e o modelo tende a escrever C-1."""
    cliente = CLIENTES.get(cliente_id)
    if cliente is None:
        raise ErroRecuperavel(
            "cliente não encontrado",
            esperado="C seguido de 3 dígitos, ex: C-001", recebido=cliente_id,
            sugestao="obtenha o id do cliente em consultar_pedido")
    return {"id": cliente_id, **cliente}


def calcular_prazo(data_prevista: str, hoje: str = str(HOJE)) -> dict:
    """Aritmética é trabalho de código, não do modelo."""
    from datetime import date
    try:
        d_hoje = date.fromisoformat(hoje)
        d_prev = date.fromisoformat(data_prevista)
    except ValueError as e:
        raise ErroRecuperavel("data inválida", detalhe=str(e),
                              esperado="AAAA-MM-DD")
    dias = (d_prev - d_hoje).days
    return {"dias": dias, "atrasado": dias < 0}


def abrir_chamado(pedido: str, categoria: str, descricao: str,
                  chave: str) -> dict:
    """ESCRITA. Idempotente: `chave` identifica a OPERAÇÃO, não a tentativa.

    Se você gerar a chave com uuid4() a cada chamada, ela não é chave de
    idempotência — é um identificador novo por tentativa, que é exatamente
    o que se quer evitar."""
    if categoria not in CATEGORIAS:
        raise ErroRecuperavel("categoria inválida", recebido=categoria,
                              validas=CATEGORIAS)
    if (existente := CHAMADOS.get(chave)):
        # O `ja_existia` é informação PARA O MODELO: ele descobre que já agiu.
        return {**existente, "ja_existia": True}
    chamado = {"protocolo": f"CH-{len(CHAMADOS) + 1001}", "pedido": pedido,
               "categoria": categoria, "descricao": descricao}
    CHAMADOS[chave] = chamado
    return chamado


FERRAMENTAS = {
    "consultar_pedido": consultar_pedido,
    "listar_pedidos": listar_pedidos,
    "consultar_cliente": consultar_cliente,
    "calcular_prazo": calcular_prazo,
    "abrir_chamado": abrir_chamado,
}

ESCRITA = {"abrir_chamado"}          # exigem idempotência e, se irreversível,
                                     # confirmação humana

# A descrição É PROMPT (aula 03, nota 04 §4). Diga o que faz, quando usar e
# quando NÃO usar.
DECLARACOES = {
    "consultar_pedido": {
        "type": "function",
        "function": {
            "name": "consultar_pedido",
            "description": (
                "Consulta situação, previsão de entrega, transportadora e id "
                "do cliente de um pedido. Use quando a resposta depender do "
                "status real. Não use para dúvidas gerais de política."),
            "parameters": {
                "type": "object",
                "properties": {"numero": {"type": "string",
                                          "description": "5 dígitos, ex: 48219"}},
                "required": ["numero"], "additionalProperties": False,
            },
        },
    },
    "listar_pedidos": {
        "type": "function",
        "function": {
            "name": "listar_pedidos",
            "description": ("Lista os números de pedido existentes. Use quando "
                            "um número não for encontrado, para conferir."),
            "parameters": {"type": "object", "properties": {},
                           "additionalProperties": False},
        },
    },
    "consultar_cliente": {
        "type": "function",
        "function": {
            "name": "consultar_cliente",
            "description": ("Dados do cliente e quantos chamados ele já tem "
                            "abertos. Use antes de abrir um chamado novo."),
            "parameters": {
                "type": "object",
                "properties": {"cliente_id": {
                    "type": "string",
                    "description": "id do cliente, formato C-001"}},
                "required": ["cliente_id"], "additionalProperties": False,
            },
        },
    },
    "calcular_prazo": {
        "type": "function",
        "function": {
            "name": "calcular_prazo",
            "description": ("Dias entre hoje e a previsão de entrega, e se já "
                            "está atrasado. Use em vez de calcular de cabeça."),
            "parameters": {
                "type": "object",
                "properties": {
                    "data_prevista": {"type": "string",
                                      "description": "AAAA-MM-DD"},
                    "hoje": {"type": "string", "description": "AAAA-MM-DD"},
                },
                "required": ["data_prevista"], "additionalProperties": False,
            },
        },
    },
    "abrir_chamado": {
        "type": "function",
        "function": {
            "name": "abrir_chamado",
            "description": ("ESCRITA: registra um chamado de suporte. Use "
                            "apenas depois de confirmar o problema com dados "
                            "reais. Não use para dúvidas ou elogios."),
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido": {"type": "string"},
                    "categoria": {"type": "string", "enum": CATEGORIAS},
                    "descricao": {"type": "string"},
                    "chave": {"type": "string",
                              "description": ("chave de idempotência, derivada "
                                              "do conteúdo: pedido:categoria")},
                },
                "required": ["pedido", "categoria", "descricao", "chave"],
                "additionalProperties": False,
            },
        },
    },
}

# Ferramentas por fase (nota 02, §6). Na fase de análise, `abrir_chamado`
# NÃO EXISTE para o modelo — restrição por arquitetura vence restrição por
# prompt: instrução ele pode ignorar, ferramenta não declarada ele não tem
# como chamar.
FASES = {
    "analise": ["consultar_pedido", "listar_pedidos", "consultar_cliente",
                "calcular_prazo"],
    "tudo": list(FERRAMENTAS),
}

SYSTEM = (
    "Você é o assistente de atendimento de uma transportadora.\n"
    "Use as ferramentas para obter dados reais — nunca invente número de "
    "pedido, situação, data ou protocolo.\n"
    f"Hoje é {HOJE}.\n"
    "Quando tiver a conclusão, responda em português, de forma breve."
)

REANCORAR_A_CADA = 5


# ============================================================ O LAÇO

# Pistas por código de status. A mensagem crua da API diz o que aconteceu;
# estas dizem o que FAZER, que é a parte que falta quando o script para.
PISTAS = {
    401: "chave inválida ou ausente — confira OPENAI_API_KEY no .env",
    403: "a chave não tem permissão para este modelo",
    404: "modelo não encontrado — confira LLM_MODELO no .env",
    422: "a API recusou o corpo da requisição — olhe `tools` e `response_format`",
}

# O último conjunto de cabeçalhos de limite que o provedor mandou, atualizado
# a cada chamada. Reagir ao 429 é reagir tarde; a cota restante vem nos
# cabeçalhos de TODA resposta, e é por isso que `chamar()` usa
# `with_raw_response` — o `create()` direto devolve só o corpo.
#
# Fica VAZIO quando o provedor não manda cabeçalho de cota, e há vários que
# não mandam. Se este dicionário estiver vazio depois de uma execução, a
# conclusão não é "sobra cota": é que aqui só dá para reagir ao 429, e o
# ajuste é a constante PAUSA no topo de cada script.
LIMITES: dict[str, str] = {}

# Abaixo de quantas unidades restantes o script avisa na tela.
AVISAR_ABAIXO_DE = 20


def _limites(cabecalhos) -> dict[str, str]:
    """Os cabeçalhos de limite de uso, qualquer que seja o nome deles.

    Os nomes NÃO são padronizados: a OpenAI usa `x-ratelimit-remaining-requests`,
    a Mistral usa `ratelimitbysize-remaining`, e há provedor que não manda nada.
    Por isso o filtro é por substring, e não por chave exata — procurar a chave
    que você conhece é como descobrir que o seu provedor "não tem limite"."""
    try:
        itens = cabecalhos.items()
    except AttributeError:
        return {}
    return {k.lower(): v for k, v in itens
            if "ratelimit" in k.lower().replace("-", "")
            or k.lower() == "retry-after"}


def _restante(limites: dict[str, str]) -> int | None:
    """O menor valor entre os cabeçalhos de "remaining" — o que acaba primeiro."""
    valores = [int(v) for k, v in limites.items()
               if "remaining" in k and v.isdigit()]
    return min(valores) if valores else None


def chamar(**kwargs):
    """Uma chamada, e só. Se falhar, o script para dizendo por quê.

    Em produção isto teria backoff exponencial (aula 02, nota 01 §8.2). Aqui
    não tem, de propósito: num laboratório, a falha contornada por três
    tentativas silenciosas esconde a causa — e a causa quase sempre é
    configuração, não instabilidade.

    Continua valendo a distinção que o script 05 desenvolve: repetir serve
    para falha de TRANSPORTE. Falha de CONTEÚDO — um argumento inválido —
    não se resolve repetindo; quem tenta de novo, com informação nova, é o
    modelo.

    Usa `with_raw_response` para enxergar os CABEÇALHOS da resposta, e não só
    o corpo. É lá que vive a cota restante — e olhá-la a cada chamada é o que
    permite reagir ANTES do 429, em vez de depois."""
    try:
        bruta = client.chat.completions.with_raw_response.create(**kwargs)
    except RateLimitError as e:
        # O 429 também traz os cabeçalhos, e `retry-after` costuma vir junto:
        # é o provedor dizendo quanto tempo esperar.
        restantes = _limites(getattr(e.response, "headers", None))
        raise ErroFatal(
            "429 — a API recusou por excesso de requisições. Aumente a "
            "constante PAUSA no topo do script e rode de novo."
            + (f" Cabeçalhos de limite: {restantes}." if restantes else
               " O provedor não mandou cabeçalho de limite nesta resposta.")
            + f" ({e})") from e
    except APIConnectionError as e:
        raise ErroFatal(
            "não foi possível falar com a API. Verifique a rede e o "
            f"LLM_BASE_URL do .env. ({e})") from e
    except APIStatusError as e:
        pista = PISTAS.get(
            e.status_code,
            "erro do servidor da API — o problema não é seu; tente mais tarde"
            if e.status_code >= 500 else "consulte a documentação da API")
        raise ErroFatal(f"{e.status_code} — {pista}. ({e})") from e

    LIMITES.clear()
    LIMITES.update(_limites(bruta.headers))

    restante = _restante(LIMITES)
    if restante is not None and restante < AVISAR_ABAIXO_DE:
        print(f"      [limites] restam {restante} — aumente a PAUSA")

    return bruta.parse()


def declaracoes(ativas: list[str]) -> list[dict]:
    return [DECLARACOES[nome] for nome in ativas]


def montar_mensagens(estado: Estado) -> list[dict]:
    """A lista de mensagens é uma VISÃO do estado, montada a cada volta."""
    mensagens = [{"role": "system", "content": SYSTEM},
                 {"role": "user", "content": estado.objetivo}]
    mensagens.extend(estado.historico)

    # Reancoragem (nota 03, §7): em trajetória longa o objetivo fica no MEIO
    # do contexto, que é onde o modelo lê pior. Custa dezenas de tokens.
    if estado.n_passos and estado.n_passos % REANCORAR_A_CADA == 0:
        mensagens.append({"role": "user",
                          "content": f"Lembrete do objetivo: {estado.objetivo}"})
    return mensagens


def mensagem_de_tool(passo: Passo, tool_call_id: str) -> dict:
    conteudo = passo.resultado if passo.resultado is not None else {"erro": passo.erro}
    return {"role": "tool", "tool_call_id": tool_call_id,
            "name": passo.ferramenta,
            "content": json.dumps(conteudo, ensure_ascii=False)}


def executar(chamada, estado: Estado, exige_confirmacao: set[str] = frozenset()) -> Passo:
    """A ACTION do ReAct — e a classificação do erro."""
    nome = chamada.function.name
    passo = Passo(indice=estado.n_passos, ferramenta=nome, argumentos={})
    try:
        passo.argumentos = json.loads(chamada.function.arguments)
    except json.JSONDecodeError:
        passo.erro = "argumentos não são JSON válido"
        passo.resultado = {"erro": passo.erro}
        return passo

    if nome in exige_confirmacao:
        # Confirmação humana é uma das QUATRO FORMAS DE TERMINAR — não um
        # input() no meio do laço (que prende o processo e não sobrevive a
        # reinício).
        estado.termino = Termino.HUMANO
        estado.motivo = f"{nome} exige aprovação"
        estado.pendencia = {"ferramenta": nome, "argumentos": passo.argumentos}
        salvar_checkpoint(estado)
        raise PausaParaHumano(nome)

    funcao = FERRAMENTAS.get(nome)
    if funcao is None:                       # o modelo inventou o nome
        passo.erro = f"ferramenta desconhecida: {nome}"
        passo.resultado = {"erro": passo.erro,
                           "disponiveis": estado.ferramentas_ativas}
        return passo

    try:
        passo.resultado = funcao(**passo.argumentos)
    except ErroRecuperavel as e:
        # Volta para o modelo como OBSERVAÇÃO. O texto do erro é prompt.
        passo.erro = e.payload["erro"]
        passo.resultado = e.payload
    except TypeError as e:                   # alucinou um parâmetro
        passo.erro = f"argumentos inválidos: {e}"
        passo.resultado = {"erro": passo.erro}
    return passo


def assinatura(passo: Passo) -> tuple:
    """sort_keys=True não é detalhe: sem ele, {'a':1,'b':2} e {'b':2,'a':1}
    são assinaturas diferentes e o detector não detecta nada."""
    return (passo.ferramenta, json.dumps(passo.argumentos, sort_keys=True))


def detectar_laco(estado: Estado, limite: int = 3) -> bool:
    if estado.n_passos < limite:
        return False
    recentes = [assinatura(p) for p in estado.passos[-limite:]]
    return len(set(recentes)) == 1


def salvar_checkpoint(estado: Estado) -> None:
    """Sempre DEPOIS de executar, nunca antes: se gravar a intenção e o
    processo cair, a retomada reexecuta. É a idempotência que fecha a fresta."""
    CHECKPOINTS.mkdir(exist_ok=True)
    caminho = CHECKPOINTS / f"{estado.execucao_id}.json"
    caminho.write_text(json.dumps(asdict(estado), ensure_ascii=False,
                                  default=str, indent=2), encoding="utf-8")


def rodar(objetivo: str,
          orcamento: Orcamento | None = None,
          fase: str = "tudo",
          com_detector: bool = True,
          limite_laco: int = 3,
          exige_confirmacao: set[str] = frozenset(),
          gancho_contexto=None,
          verboso: bool = True) -> Estado:
    """O laço da aula 03, agora operando sobre o ESTADO.

    Três diferenças em relação ao original, e nenhuma é cosmética:
      1. devolve Estado, não str — quem chamou recebe a trajetória e a conta;
      2. `while True` com saídas NOMEADAS, no lugar de `for range(max_passos)`;
      3. `historico` é campo do estado, e por isso pode ser reescrito (06).
    """
    orcamento = orcamento or Orcamento()
    estado = Estado(objetivo=objetivo, ferramentas_ativas=list(FASES[fase]))

    try:
        while True:
            if (motivo := orcamento.excedido(estado)):
                estado.termino, estado.motivo = Termino.ORCAMENTO, motivo
                return estado

            if com_detector and detectar_laco(estado, limite_laco):
                # Intervir ANTES de abortar: injeta a observação e dá mais
                # uma chance. Só aborta se voltar a repetir.
                if estado.motivo == "laco: observacao injetada":
                    estado.termino = Termino.LACO
                    estado.motivo = "repetiu mesmo após a intervenção"
                    return estado
                ultimo = estado.passos[-1]
                if verboso:
                    print(f"      [laço] {ultimo.ferramenta} repetida "
                          f"{limite_laco}x — injetando observação")
                estado.historico.append({
                    "role": "user",
                    "content": (f"Você já chamou {ultimo.ferramenta} com estes "
                                f"argumentos e recebeu este resultado. Use a "
                                f"informação que já tem ou diga o que falta.")})
                estado.motivo = "laco: observacao injetada"

            if gancho_contexto:               # compaction / tool clearing (06)
                gancho_contexto(estado)

            mensagens = montar_mensagens(estado)
            resposta = chamar(
                model=MODELO, messages=mensagens,
                tools=declaracoes(estado.ferramentas_ativas),
                temperature=0,       # escolher ferramenta é decisão: variar é defeito
            )
            uso = resposta.usage
            estado.tokens_gastos += uso.total_tokens
            estado.contexto_por_passo.append(uso.prompt_tokens)

            msg = resposta.choices[0].message
            if verboso:
                print(f"   passo {estado.n_passos} · contexto enviado: "
                      f"{uso.prompt_tokens} tokens")

            if not msg.tool_calls:            # respondeu: terminou
                estado.termino = Termino.RESPONDEU
                estado.resposta = msg.content
                return estado

            estado.historico.append(msg)
            for chamada in msg.tool_calls:
                passo = executar(chamada, estado, exige_confirmacao)
                passo.tokens_entrada = uso.prompt_tokens
                passo.tokens_saida = uso.completion_tokens
                estado.registrar(passo)
                estado.historico.append(mensagem_de_tool(passo, chamada.id))
                if verboso:
                    marca = "ERRO " if passo.erro else "     "
                    print(f"      {marca}{passo.ferramenta}({passo.argumentos}) "
                          f"-> {json.dumps(passo.resultado, ensure_ascii=False)[:70]}")

    except PausaParaHumano:
        return estado                          # termino já marcado
    except ErroFatal as e:
        estado.termino, estado.motivo = Termino.ERRO_FATAL, str(e)
        return estado
    finally:
        # O trace é gravado em TODOS os caminhos. O except que registra só o
        # sucesso é o except que garante que você nunca vai achar a causa.
        salvar_checkpoint(estado)


def resumo(estado: Estado) -> str:
    return (f"TERMINO: {estado.termino.value}"
            f"{' (' + estado.motivo + ')' if estado.motivo else ''} | "
            f"{estado.n_passos} passos | {estado.tokens_gastos} tokens")
