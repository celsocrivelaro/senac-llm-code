# Aula 15 — O agente, instrumentado.
#
# O agente é o das aulas anteriores, sem alteração de lógica: o grafo do
# `04-langgraph.py` da aula de frameworks, escrito nó a nó. O que esta aula acrescenta
# é a TELEMETRIA: cada execução sai como uma árvore de spans do
# OpenTelemetry, nas convenções semânticas GenAI, e é enviada por OTLP para
# a plataforma configurada no .env (ver .env.example).
#
#     python agente.py        # uma execução, e os spans que ela enviou
#
#                        ┌───────┐
#                        │ START │
#                        └───┬───┘
#                            ▼
#                   ┌─────────────────┐
#         ┌────────►│  chamar_modelo  │──► span "chat"
#         │         └────────┬────────┘
#         │           deve_continuar()
#         │            ┌─────┴─────┐
#         │     pediu ferramenta   não pediu
#         │            ▼           ▼
#         │  ┌─────────────────┐ ┌─────┐
#         └──┤  no_ferramentas │ │ END │
#            └─────────────────┘ └─────┘
#                    └──► span "execute_tool"
#
# Tudo isso dentro do span raiz "invoke_agent", aberto em `rodar()`.

from __future__ import annotations

import json
import operator
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Annotated, Literal, TypedDict

from langchain.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from opentelemetry import trace as otel
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# O `cliente` carrega o .env desta pasta: modelo E telemetria.
from cliente import MODELO, PROVEDOR, modelo
# O domínio — dados, SYSTEM e ferramentas — fica no `dominio.py`.
from dominio import FERRAMENTAS, FERRAMENTAS_POR_NOME, SYSTEM, extrair_veredito

AGENTE = "auditor-de-despesas"

# A VERSÃO IMPLANTADA vai em todo span. Sem ela, o painel soma sistemas
# distintos num mesmo número (nota 03, §5).
VERSAO = os.environ.get("VERSAO_SISTEMA", "1.5.0")

# Preço por milhão de tokens. Trocar o provedor troca estes números.
PRECO_ENTRADA = float(os.environ.get("PRECO_ENTRADA_MI", "0.20"))
PRECO_SAIDA = float(os.environ.get("PRECO_SAIDA_MI", "0.60"))


# ===================================================================== 1
#  A TELEMETRIA — para onde os spans vão
# ===================================================================== 1
# O RESOURCE descreve QUEM emite (OTEL_SERVICE_NAME + versão) e vai junto
# de todos os spans. O exportador lê endpoint, protocolo e o cabeçalho de
# autenticação das variáveis OTEL_EXPORTER_OTLP_*: o código não cita a
# plataforma, e trocar de plataforma é trocar o .env. Sem endpoint, os
# spans são produzidos e não saem do processo.
provedor = TracerProvider(resource=Resource.create({"service.version": VERSAO}))
if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
    # Em lote e em segundo plano: o agente não espera o envio.
    provedor.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
otel.set_tracer_provider(provedor)
tracer = otel.get_tracer(AGENTE, VERSAO)


# ===================================================================== 2
#  O modelo, com as ferramentas do domínio
# ===================================================================== 2

PREFIXO = [SystemMessage(content=SYSTEM)]
TEMPERATURA = 0.0
LLM = modelo.model_copy(update={"temperature": TEMPERATURA}).bind_tools(FERRAMENTAS)


# ===================================================================== 3
#  O registro da execução
# ===================================================================== 3

@dataclass
class Trace:
    id: str = field(default_factory=lambda: f"e-{uuid.uuid4().hex[:8]}")
    versao: str = VERSAO
    agente: str = AGENTE
    objetivo: str = ""
    passos: list[str] = field(default_factory=list)
    tokens_entrada: int = 0
    tokens_saida: int = 0
    termino: str = ""
    resposta: str = ""
    veredito: str = ""
    ms: float = 0.0

    @property
    def custo(self) -> float:
        return (self.tokens_entrada * PRECO_ENTRADA
                + self.tokens_saida * PRECO_SAIDA) / 1_000_000

    def dict(self) -> dict:
        return asdict(self) | {"custo": round(self.custo, 6)}


# ===================================================================== 4
#  O grafo, com um span por chamada ao modelo e por ferramenta
# ===================================================================== 4

class Estado(TypedDict):
    mensagens: Annotated[list[AnyMessage], operator.add]
    trace: Trace


def chamar_modelo(estado: Estado) -> dict:
    with tracer.start_as_current_span(f"chat {MODELO}") as span:
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.provider.name", PROVEDOR)
        span.set_attribute("gen_ai.request.model", MODELO)
        span.set_attribute("gen_ai.request.temperature", TEMPERATURA)
        resposta = LLM.invoke(PREFIXO + estado["mensagens"])
        uso = resposta.usage_metadata or {}
        span.set_attribute("gen_ai.usage.input_tokens", uso.get("input_tokens", 0))
        span.set_attribute("gen_ai.usage.output_tokens", uso.get("output_tokens", 0))
        # Cada provedor nomeia estes campos de um jeito; a convenção, não.
        meta = resposta.response_metadata or {}
        modelo_respondeu = meta.get("model_name") or meta.get("model")
        if modelo_respondeu:
            span.set_attribute("gen_ai.response.model", modelo_respondeu)
        motivo = meta.get("finish_reason") or meta.get("done_reason")
        if motivo:
            span.set_attribute("gen_ai.response.finish_reasons", [motivo])
    estado["trace"].tokens_entrada += uso.get("input_tokens", 0)
    estado["trace"].tokens_saida += uso.get("output_tokens", 0)
    return {"mensagens": [resposta]}


def no_ferramentas(estado: Estado) -> dict:
    resultado = []
    for chamada in estado["mensagens"][-1].tool_calls:
        with tracer.start_as_current_span(f"execute_tool {chamada['name']}") as span:
            ferramenta = FERRAMENTAS_POR_NOME.get(chamada["name"])
            saida = (ferramenta.invoke(chamada["args"]) if ferramenta
                     else json.dumps({"erro": "ferramenta desconhecida"}))
            erro = '"erro"' in saida
            span.set_attribute("gen_ai.operation.name", "execute_tool")
            span.set_attribute("gen_ai.tool.name", chamada["name"])
            # Liga a execução da ferramenta ao pedido do modelo que a originou.
            span.set_attribute("gen_ai.tool.call.id", chamada["id"])
            # Erro de domínio não derruba a execução: volta ao modelo como
            # observação. O status ERROR é o que o torna contável no painel.
            if erro:
                span.set_status(otel.StatusCode.ERROR)
        estado["trace"].passos.append(chamada["name"])
        resultado.append(ToolMessage(content=saida, tool_call_id=chamada["id"]))
    return {"mensagens": resultado}


def deve_continuar(estado: Estado) -> Literal["no_ferramentas", END]:
    return "no_ferramentas" if estado["mensagens"][-1].tool_calls else END


_construtor = StateGraph(Estado)
_construtor.add_node("chamar_modelo", chamar_modelo)
_construtor.add_node("no_ferramentas", no_ferramentas)
_construtor.add_edge(START, "chamar_modelo")
_construtor.add_conditional_edges("chamar_modelo", deve_continuar, ["no_ferramentas", END])
_construtor.add_edge("no_ferramentas", "chamar_modelo")
grafo = _construtor.compile()


def rodar(objetivo: str, max_passos: int = 8) -> Trace:
    trace = Trace(objetivo=objetivo)
    inicio = time.monotonic()

    # O span RAIZ é o corrente durante o grafo: os spans dos nós nascem como
    # filhos dele, e a plataforma desenha uma árvore só por execução.
    with tracer.start_as_current_span(f"invoke_agent {AGENTE}") as raiz:
        raiz.set_attribute("gen_ai.operation.name", "invoke_agent")
        raiz.set_attribute("gen_ai.agent.name", AGENTE)
        raiz.set_attribute("gen_ai.provider.name", PROVEDOR)
        despesa = re.search(r"\bD-\d{4}\b", objetivo)
        if despesa:
            raiz.set_attribute("agente.despesa", despesa.group())
        # Cada passo são dois nós: `2 * max_passos` deixa o modelo ser
        # chamado `max_passos` vezes, como no laço da aula de arquitetura de agentes.
        try:
            estado = grafo.invoke(
                {"mensagens": [HumanMessage(content=objetivo)], "trace": trace},
                {"recursion_limit": 2 * max_passos})
            trace.termino = "respondeu"
            trace.resposta = estado["mensagens"][-1].text
        except GraphRecursionError:
            # Termina por ORÇAMENTO e devolve 200 com resposta pior: a taxa
            # de erro não se mexe. É a degradação SILENCIOSA da nota 03.
            trace.termino = "orcamento_esgotado"
        except Exception as erro:
            # Falha do provedor (cota, rede, chave) vira MOTIVO DE TÉRMINO, e
            # não queda do processo: a execução é registrada e contada. O
            # `error.type` é de baixa cardinalidade — o código HTTP quando há.
            codigo = getattr(getattr(erro, "response", None), "status_code", None)
            trace.termino = "erro_api" if codigo else "erro"
            raiz.set_attribute("error.type", str(codigo) if codigo else type(erro).__name__)
            raiz.record_exception(erro)
            raiz.set_status(otel.StatusCode.ERROR)

        # O VEREDITO é o resultado do negócio: `respondeu` sem veredito é
        # outra forma de degradação silenciosa, e só se vê se for medida.
        trace.veredito = extrair_veredito(trace.resposta)

        # O MOTIVO DE TÉRMINO não está na convenção: é atributo da aplicação,
        # e só existe porque o término foi modelado como dado na aula de arquitetura de agentes.
        raiz.set_attribute("agente.termino", trace.termino)
        raiz.set_attribute("agente.veredito", trace.veredito)
        raiz.set_attribute("agente.passos", len(trace.passos))
        raiz.set_attribute("agente.custo_brl", round(trace.custo, 6))

    trace.ms = (time.monotonic() - inicio) * 1000
    return trace


# ===================================================================== 5
#  Execução direta: uma pergunta, e os spans que ela enviou
# ===================================================================== 5

if __name__ == "__main__":
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import \
        InMemorySpanExporter

    # Uma cópia em memória dos MESMOS spans, só para imprimi-los aqui.
    copia = InMemorySpanExporter()
    provedor.add_span_processor(SimpleSpanProcessor(copia))

    trace = rodar("A despesa D-4613 está dentro da política? Foi em Lisboa.")
    print(f"\n{trace.termino} · veredito: {trace.veredito}\n{trace.resposta}\n")

    spans = sorted(copia.get_finished_spans(), key=lambda s: s.start_time)
    print(f"resource: {dict(provedor.resource.attributes)}")
    print(f"trace_id: {spans[0].context.trace_id:032x}\n")
    for s in spans:
        recuo = "" if s.parent is None else "    "
        ms = (s.end_time - s.start_time) / 1_000_000
        erro = "  [ERROR]" if s.status.status_code == otel.StatusCode.ERROR else ""
        print(f"{recuo}{s.name}  ({ms:,.0f} ms){erro}")
        for chave, valor in s.attributes.items():
            print(f"{recuo}    {chave} = {valor!r}")

    # Envio em segundo plano: esvaziar a fila antes de sair, ou os spans se
    # perdem. Falha de rede ou de credencial aparece como "Failed to export".
    provedor.force_flush()
