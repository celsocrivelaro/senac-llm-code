# Aula 08 — 02: A MEMÓRIA SEMÂNTICA — fatos estáveis sobre entidades.
#
# A MEMÓRIA SEMÂNTICA registra fatos estáveis sobre entidades do domínio: o
# destino frequente de um funcionário, o formato de um identificador, o
# histórico de reprovação de um solicitante.
#
# A estrutura é uma TABELA, armazenada em JSON, porque a consulta dirigida a
# ela tem CHAVE: `F-088:destinos_frequentes` é um endereço, e endereço se
# resolve por lookup. Recuperar isso por similaridade seria mais caro e menos
# exato — e o vetor não distingue `F-088` de `F-091` (cegueira de ENTIDADE,
# aula 07, nota 02 §4).
#
# CUSTO DE CONSULTA: zero chamadas. É o mais barato dos três.
#
# A comparação com `02-memoria-episodica.py` é o ponto da divisão em
# arquivos: os dois implementam memória de longo prazo e não compartilham
# nenhuma linha, porque os padrões de acesso são diferentes.

from memoria_semantica import MemoriaSemantica

print("=" * 74)
print("SEMÂNTICA — fato estável sobre a entidade  (chave-valor, por lookup)")
print("=" * 74)

semantica = MemoriaSemantica()
semantica.gravar("F-088", "destinos_frequentes", ["Lisboa", "Curitiba"],
                 "2026-08-11")
semantica.gravar("F-088", "formato_id", "F + 3 dígitos", "2026-03-12")
semantica.gravar("F-091", "historico_reprovacao",
                 "transporte sem justificativa", "2026-04-04")

print(f"\n  sobre F-088: {semantica.sobre('F-088')}")
print(f"  lookup direto: {semantica.ler('F-088', 'destinos_frequentes')}")
print("\n  custo da consulta: ZERO chamadas")

# ------------------------------------------------------------- idempotência
#
# Gravar memória é uma operação de ESCRITA, e portanto exige chave de
# idempotência derivada do CONTEÚDO (aula 05, nota 02 §8). A mesma execução
# processada duas vezes não pode produzir dois fatos.
print(f"\n{'=' * 74}")
print("A ESCRITA É ESCRITA: a mesma gravação, duas vezes")
print("=" * 74)
print()

de_novo = semantica.gravar("F-088", "destinos_frequentes",
                           ["Lisboa", "Curitiba"], "2026-08-11")
print(f"  segunda gravação do mesmo fato: ja_existia={de_novo.get('ja_existia')}")
print(f"  total de fatos armazenados: {len(semantica.fatos)}")
