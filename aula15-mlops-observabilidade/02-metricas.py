# Aula 15 — Métricas num programa comum: formar times de pokémon.
#
# O problema: o programa já não busca UM pokémon, e sim monta vários times,
# cada um com várias consultas à PokeAPI (https://pokeapi.co). Ninguém vai
# ler um trace por consulta; o que se quer saber é o AGREGADO — quantas
# chamadas houve, quantas falharam, quanto tempo levaram, e que tipos de
# pokémon entraram nos times.
#
# Nada aqui é LLM. Um sinal da nota 01:
#
#   MÉTRICA  um número agregado sobre MUITAS operações, decomposto por
#            atributos de poucos valores (método, status, tipo)
#
# Não há trace nem log neste arquivo, de propósito: a métrica perde o
# detalhe de cada consulta — e é por isso que é barata e serve a alertas.

import time

import requests
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.resources import Resource

API = "https://pokeapi.co/api/v2"


# =====================================================================
#  1. A configuração
# =====================================================================
# As métricas ficam em memória, para serem impressas no fim; num serviço de
# verdade, iriam por OTLP para a plataforma.
recurso = Resource.create({"service.name": "montador-de-times", "service.version": "1.0.0"})
leitor_de_metricas = InMemoryMetricReader()
metrics.set_meter_provider(MeterProvider(resource=recurso, metric_readers=[leitor_de_metricas]))
medidor = metrics.get_meter("montador-de-times")


# =====================================================================
#  2. As métricas: declaradas uma vez, alimentadas a cada operação
# =====================================================================
# Métrica TÉCNICA, com o nome e a unidade da convenção semântica de HTTP.
# Um histograma guarda a DISTRIBUIÇÃO das durações; é dele que a plataforma
# tira p50 e p95.
duracao_http = medidor.create_histogram("http.client.request.duration", unit="s", description="Duração das chamadas HTTP feitas pelo programa")

# Métrica de NEGÓCIO: quantos pokémon de cada tipo entraram nos times. O
# tipo tem poucos valores (18), por isso serve de atributo de métrica; o
# NOME do pokémon não serve — seria uma série por pokémon.
pokemon_por_tipo = medidor.create_counter("time.pokemon", unit="1", description="Pokémon incluídos em times, por tipo")


# =====================================================================
#  3. Formar um time: cada consulta alimenta as métricas
# =====================================================================

def formar_time(nomes: list[str]) -> list[str]:
    time_formado = []
    for nome in nomes:
        inicio = time.monotonic()
        resposta = requests.get(f"{API}/pokemon/{nome}", timeout=10)
        segundos = time.monotonic() - inicio

        # Uma medida por chamada, com atributos de poucos valores.
        duracao_http.record(segundos, {"http.request.method": "GET", "http.response.status_code": resposta.status_code})

        if resposta.status_code == 200:
            time_formado.append(nome)
            for tipo in resposta.json()["types"]:
                pokemon_por_tipo.add(1, {"pokemon.tipo": tipo["type"]["name"]})
    return time_formado


# =====================================================================
#  4. Execução: três times, um deles com um nome que não existe
# =====================================================================

formar_time(["pikachu", "charizard", "bulbasaur"])
formar_time(["squirtle", "gengar", "pikachuu"])   # "pikachuu" não existe: 404
formar_time(["eevee", "snorlax", "jigglypuff"])

# As MÉTRICAS: um agregado sobre os três times. Já não se sabe qual pokémon
# demorou nem qual falhou — sabe-se quantas chamadas houve, com que status,
# como as durações se distribuem e que tipos predominam.
print("MÉTRICAS (agregadas sobre os três times)")
dados = leitor_de_metricas.get_metrics_data()
for recurso_metricas in dados.resource_metrics:
    for escopo in recurso_metricas.scope_metrics:
        for metrica in escopo.metrics:
            print(f"\n  {metrica.name} ({metrica.unit})")
            for ponto in metrica.data.data_points:
                atributos = dict(ponto.attributes)
                if hasattr(ponto, "bucket_counts"):
                    print(f"      {atributos}  chamadas={ponto.count}  soma={ponto.sum:.2f}s  min={ponto.min * 1000:,.0f}ms  max={ponto.max * 1000:,.0f}ms")
                else:
                    print(f"      {atributos}  total={ponto.value}")
