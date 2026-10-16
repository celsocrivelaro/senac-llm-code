# Aula 13 — O agente completo: dados fixos, RAG e memória, isolados por usuário.
#
# O mesmo auditor de despesas das pastas anteriores, agora com:
#
#   - DADOS FIXOS no Postgres: a política e as despesas, cada despesa de um
#     usuário (dados.py);
#   - RAG no Postgres: os artigos do regulamento, recuperados por busca
#     textual e entregues ao modelo como contexto (dados.py);
#   - MEMÓRIA no Redis: o histórico da sessão e os fatos do usuário
#     (memoria.py).
#
# O ISOLAMENTO é a peça central. O usuário vem do cabeçalho da requisição,
# e não do texto: as ferramentas são construídas POR REQUISIÇÃO, já presas a
# esse usuário. O modelo escolhe QUAL despesa consultar, mas nunca DE QUEM —
# perguntar pela despesa de outro usuário devolve "inexistente".

import json

from langchain.agents import create_agent
from langchain.tools import tool

import dados
import memoria
from cliente import modelo

SYSTEM = """Você analisa despesas de reembolso do usuário segundo a política vigente.
Use as ferramentas antes de concluir. Consulte o regulamento quando houver exceção (capital, viagem internacional, prazo).
Quando o usuário declarar algo duradouro sobre si (cargo, cidade-base, preferência), registre com anotar_fato.
Termine cada análise com o veredito: aprovado ou reprovado."""


def ferramentas_do_usuario(usuario: str) -> list:
    """As ferramentas desta requisição, com o usuário fixado pelo código."""

    @tool
    def consultar_despesa(despesa: str) -> str:
        """Dados de uma despesa do usuário pelo identificador (D + 4 dígitos).

        Args:
            despesa: O identificador da despesa, ex: D-4612
        """
        achada = dados.despesa_do_usuario(usuario, despesa)
        if achada is None:
            return json.dumps({"erro": "despesa inexistente para este usuário", "recebido": despesa})
        return json.dumps(achada, ensure_ascii=False)

    @tool
    def listar_minhas_despesas() -> str:
        """Os identificadores das despesas do usuário."""
        return json.dumps({"despesas": dados.despesas_do_usuario(usuario)})

    @tool
    def consultar_politica(categoria: str) -> str:
        """Teto de reembolso por categoria: refeicao, transporte, hospedagem, outros.

        Args:
            categoria: A categoria da despesa
        """
        teto = dados.teto(categoria)
        if teto is None:
            return json.dumps({"erro": "categoria desconhecida"})
        return json.dumps({"categoria": categoria, "teto": teto})

    @tool
    def buscar_regulamento(consulta: str) -> str:
        """Recupera os artigos do regulamento mais relevantes para a consulta.

        Args:
            consulta: O que procurar, ex: hospedagem em capital
        """
        artigos = dados.buscar_regulamento(consulta)
        return json.dumps(artigos or {"aviso": "nenhum artigo encontrado"}, ensure_ascii=False)

    @tool
    def anotar_fato(fato: str) -> str:
        """Registra um fato duradouro que o usuário declarou sobre si.

        Args:
            fato: O fato, numa frase curta, ex: trabalha baseado em Recife
        """
        memoria.anotar_fato(usuario, fato)
        return json.dumps({"anotado": fato}, ensure_ascii=False)

    return [consultar_despesa, listar_minhas_despesas, consultar_politica, buscar_regulamento, anotar_fato]


def rodar(usuario: str, sessao: str, pergunta: str) -> dict:
    """Uma execução: lê a memória, executa o agente, grava o turno."""
    usuario, sessao = memoria.validar(usuario), memoria.validar(sessao)

    # A memória de LONGO PRAZO entra no prompt de sistema; a de CURTO PRAZO,
    # como as mensagens anteriores da conversa.
    fatos = memoria.fatos(usuario)
    sistema = SYSTEM + ("\n\nO que se sabe deste usuário:\n- " + "\n- ".join(fatos) if fatos else "")
    mensagens = memoria.historico(usuario, sessao) + [{"role": "user", "content": pergunta}]

    agente = create_agent(modelo, tools=ferramentas_do_usuario(usuario), system_prompt=sistema)
    resposta = agente.invoke({"messages": mensagens})["messages"][-1].content

    # Grava DEPOIS de executar: uma execução que falha não deixa meio turno.
    tamanho = memoria.registrar_turno(usuario, sessao, pergunta, resposta)
    return {"resposta": resposta, "mensagens_na_sessao": tamanho, "fatos_do_usuario": len(memoria.fatos(usuario))}
