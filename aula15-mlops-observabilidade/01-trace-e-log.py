# Aula 15 — Trace e log num programa comum: buscar um pokémon.
#
# O problema: um programa consulta uma API de terceiros (a PokeAPI,
# https://pokeapi.co) e é preciso saber, sem ler o código, o que aconteceu
# em CADA consulta — quanto tempo cada etapa levou, onde falhou e por quê.
#
# Nada aqui é LLM. Dois sinais da nota 01:
#
#   TRACE  uma busca inteira, como uma árvore de SPANS (as etapas dela)
#   LOG    um evento em texto livre, carimbado com o trace e o span em que
#          aconteceu
#
#   buscar_pokemon                       <- span raiz: o trace é esta árvore
#   ├── GET /api/v2/pokemon/{nome}       <- span CLIENT: a chamada HTTP
#   └── ler_resposta                     <- span interno, sem rede
#
# O agente da aula (`agente.py`) faz o mesmo: lá o trace é uma execução do
# agente, e os spans são as chamadas ao modelo e às ferramentas.

import logging
import os
import time

import requests
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, InMemoryLogRecordExporter, SimpleLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

API = "https://pokeapi.co/api/v2"

# O mesmo .env do `agente.py`: as variáveis OTEL_EXPORTER_OTLP_* dizem para
# onde a telemetria vai.
load_dotenv()
ENVIAR = bool(os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"))


# =====================================================================
#  1. A configuração: quem emite, e para onde vai
# =====================================================================
# O RESOURCE identifica o programa que emite: vai junto de todo span e de
# todo log. O `service.name` escrito aqui prevalece sobre o OTEL_SERVICE_NAME
# do .env, e o programa aparece na plataforma com nome próprio, separado do
# agente. Os dois sinais ficam em memória, para serem impressos no fim, e,
# com endpoint no .env, também vão por OTLP para a plataforma, como no
# `agente.py`.
recurso = Resource.create({"service.name": "buscador-de-pokemon", "service.version": "1.0.0"})

spans_em_memoria = InMemorySpanExporter()
provedor_de_traces = TracerProvider(resource=recurso)
provedor_de_traces.add_span_processor(SimpleSpanProcessor(spans_em_memoria))
if ENVIAR:
    # O exportador acrescenta /v1/traces ao endpoint.
    provedor_de_traces.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provedor_de_traces)
tracer = trace.get_tracer("buscador-de-pokemon")

# A aplicação escreve log com o `logging` do Python, como sempre. O handler
# do OpenTelemetry converte cada linha num registro de log, com o trace_id e
# o span_id do span que estava aberto naquele momento. O sinal de log ainda
# não é estável no SDK de Python (módulos `_logs`): os nomes podem mudar.
logs_em_memoria = InMemoryLogRecordExporter()
provedor_de_logs = LoggerProvider(resource=recurso)
provedor_de_logs.add_log_record_processor(SimpleLogRecordProcessor(logs_em_memoria))
if ENVIAR:
    # O exportador acrescenta /v1/logs ao endpoint.
    provedor_de_logs.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))

log = logging.getLogger("buscador-de-pokemon")
log.setLevel(logging.INFO)
log.addHandler(LoggingHandler(logger_provider=provedor_de_logs))
log.propagate = False   # só o handler do OpenTelemetry: nada vai direto ao terminal


# =====================================================================
#  2. Uma busca: o span raiz e os spans das etapas
# =====================================================================

def buscar_pokemon(nome: str) -> dict | None:
    with tracer.start_as_current_span("buscar_pokemon") as raiz:
        raiz.set_attribute("pokemon.nome", nome)
        log.info("buscando %s", nome)

        # Etapa 1: a chamada HTTP. O NOME do span é a rota com o parâmetro
        # como molde, para que todas as buscas se agrupem; o valor concreto
        # vai em atributo, nos nomes da convenção semântica de HTTP.
        with tracer.start_as_current_span("GET /api/v2/pokemon/{nome}", kind=trace.SpanKind.CLIENT) as chamada:
            url = f"{API}/pokemon/{nome}"
            chamada.set_attribute("http.request.method", "GET")
            chamada.set_attribute("url.full", url)
            resposta = requests.get(url, timeout=10)
            chamada.set_attribute("http.response.status_code", resposta.status_code)

            if resposta.status_code != 200:
                # A falha não derruba o programa, mas fica marcada no span
                # (status ERROR) e contada em texto no log — que, por estar
                # dentro deste span, sai preso a ele.
                chamada.set_attribute("error.type", str(resposta.status_code))
                chamada.set_status(trace.StatusCode.ERROR)
                log.warning("pokémon não encontrado: %s (status %d)", nome, resposta.status_code)
                return None

        # Etapa 2: ler a resposta. Trabalho sem rede também tem duração.
        with tracer.start_as_current_span("ler_resposta") as leitura:
            dados = resposta.json()
            tipos = [t["type"]["name"] for t in dados["types"]]
            leitura.set_attribute("pokemon.tipos", tipos)

        log.info("%s encontrado: %s", nome, ", ".join(tipos))
        return {"nome": nome, "tipos": tipos}


# =====================================================================
#  3. Execução: uma busca que dá certo, e uma que não
# =====================================================================

buscar_pokemon("pikachu")
buscar_pokemon("pikachuu")   # não existe: 404

# Os TRACES: um por busca, cada um como árvore de spans.
spans = sorted(spans_em_memoria.get_finished_spans(), key=lambda s: s.start_time)
for raiz in spans:
    if raiz.parent is not None:
        continue
    print(f"\nTRACE {raiz.context.trace_id:032x}")
    for s in spans:
        if s.context.trace_id != raiz.context.trace_id:
            continue
        recuo = "" if s.parent is None else "    "
        ms = (s.end_time - s.start_time) / 1_000_000
        erro = "  [ERROR]" if s.status.status_code == trace.StatusCode.ERROR else ""
        print(f"  {recuo}{s.name}  ({ms:,.0f} ms){erro}  {dict(s.attributes)}")

# Os LOGS: cada linha diz em que trace e em que span foi escrita. O aviso do
# "pikachuu" aparece preso à chamada HTTP que falhou.
print("\nLOGS")
nome_do_span = {}
for s in spans:
    nome_do_span[s.context.span_id] = s.name
for registro in logs_em_memoria.get_finished_logs():
    linha = registro.log_record
    print(f"  {linha.severity_text:<7} trace {linha.trace_id:032x}  span {nome_do_span.get(linha.span_id, '?'):<28}  {linha.body}")

# O envio é em lote e em segundo plano: o shutdown esvazia a fila antes de
# sair. Falha de rede ou de credencial aparece como "Failed to export".
provedor_de_traces.shutdown()
provedor_de_logs.shutdown()
