# Aula 07 — 00: A EXTRAÇÃO DE TEXTO A PARTIR DE PDF.
#
# Um arquivo PDF não armazena texto. Ele armazena INSTRUÇÕES DE DESENHO — a
# posição, a fonte e o corpo de cada glifo na página. Parágrafo, coluna e
# tabela não existem no arquivo: são regularidades que emergem das
# coordenadas. O que uma biblioteca de extração devolve é, portanto, uma
# RECONSTRUÇÃO inferida dessas posições, e a inferência pode falhar sem
# produzir erro.
#
# A extração é anterior a todo o resto do pipeline. Não há o que indexar
# antes de haver texto, o chunk não pode ser melhor que a extração que o
# produziu, e nenhuma métrica de recuperação detecta o que nunca entrou no
# índice.
#
# ESCOPO DESTE SCRIPT. Lê o mesmo regulamento usado nas aulas anteriores, a
# partir de um PDF de quatro páginas, imprime o texto extraído na íntegra e
# executa três verificações: páginas sem camada de texto, tabela extraída
# como texto contra tabela extraída como estrutura, e preservação dos
# marcadores de artigo.
#
# DEPENDÊNCIA: pdfplumber (MIT). Devolve a posição de cada caractere e, com
# base nela, extrai tabelas. A alternativa mais rápida, PyMuPDF, é AGPL-3 —
# ver a nota 00, §2: a licença é critério de escolha de dependência ao lado
# do desempenho.

import re
from pathlib import Path

import pdfplumber

from dados import REGULAMENTO

ARQUIVO = Path(__file__).parent / "regulamento.pdf"
PAGINA_TABELA = 3

with pdfplumber.open(ARQUIVO) as pdf:
    paginas = [(p.extract_text() or "") for p in pdf.pages]
    tabelas = pdf.pages[PAGINA_TABELA - 1].extract_tables()

# ================================================ 1. O TEXTO EXTRAÍDO, NA ÍNTEGRA
#
# A primeira verificação é a inspeção direta da saída. Os defeitos de
# extração mais comuns são identificáveis por leitura: palavra quebrada ao
# fim da linha, cabeçalho e rodapé repetidos a cada página, nota de rodapé
# inserida no meio do parágrafo, e página sem texto algum.
print("=" * 74)
print(f"1. O CONTEÚDO EXTRAÍDO — {ARQUIVO.name}, {len(paginas)} páginas")
print("=" * 74)

for numero, texto in enumerate(paginas, start=1):
    print(f"\n{'-' * 74}")
    print(f"--- página {numero} — {len(texto)} caracteres")
    print(f"{'-' * 74}")
    print(texto.strip() if texto.strip() else "  (vazia: nada de texto voltou)")

# ================================================== 2. PÁGINAS SEM CAMADA DE TEXTO
#
# A quarta página do arquivo é uma imagem, equivalente a uma página
# digitalizada. Para o extrator ela é uma página vazia: a extração não lança
# exceção nem emite aviso, e devolve string vazia. Contar caracteres por
# página é o que torna essa ausência detectável.
vazias = [n for n, t in enumerate(paginas, start=1) if not t.strip()]

print(f"\n{'=' * 74}")
print("2. A PÁGINA QUE VOLTOU EM SILÊNCIO")
print("=" * 74)
print()
for numero, texto in enumerate(paginas, start=1):
    marca = "   <-- SEM CAMADA DE TEXTO" if numero in vazias else ""
    print(f"  página {numero}: {len(texto):>5} caracteres{marca}")

if vazias:
    print(f"""
  {len(vazias)} de {len(paginas)} páginas sem texto extraível: {vazias}

  O PDF é HÍBRIDO: digital, com parte do conteúdo como imagem. É a classe
  perigosa, porque falha em silêncio — a extração devolve as páginas de
  texto, some com as de imagem, e ninguém nota até a busca não achar uma
  cláusula que "está no PDF". O tratamento é OCR, e ele tem custo e taxa de
  erro próprios, sobretudo em número e em tabela.""")

# ====================================== 3. TABELA COMO TEXTO E TABELA COMO DADO
#
# A página do anexo contém uma tabela com réguas desenhadas. Extraída como
# texto — que é o modo padrão, e o que a seção 1 imprimiu — ela produz linhas
# legíveis nas quais as fronteiras de coluna não estão marcadas.
print(f"\n{'=' * 74}")
print(f"3. A TABELA DA PÁGINA {PAGINA_TABELA}, COMO TEXTO")
print("=" * 74)
print()
for linha in paginas[PAGINA_TABELA - 1].strip().split("\n"):
    print(f"  {linha}")

print("""
  O texto está correto e a estrutura não. As fronteiras de coluna
  desapareceram: não há marcação de onde termina a categoria e começa o
  limite. Para a leitura humana o espaçamento basta; para o corte em chunks
  e para o cálculo de similaridade,
  "Hospedagem internacional R$ 640,00 por diária Art. 6º §2º" é uma sequência
  única, e o valor — que é o dado que decide a resposta — não é separável
  do resto.""")

print(f"\n{'=' * 74}")
print(f"   A MESMA PÁGINA, COMO ESTRUTURA")
print("=" * 74)
# `extract_tables` usa as RÉGUAS desenhadas na página. Sem elas — tabela
# alinhada só por espaçamento, que é comum — a detecção não acha nada, e é
# preciso passar uma estratégia por posição de texto.
print(f"\n  {len(tabelas)} tabela(s) detectada(s) pelas réguas da página.\n")
for tabela in tabelas:
    for linha in tabela:
        print(f"    {linha}")

print("""
  Com as colunas separadas, a tabela passa a ser dado estruturado, e há
  dois destinos possíveis. O primeiro é gerar um chunk por linha com o
  cabeçalho herdado, que é o corte por estrutura da aula 06. O segundo, mais
  adequado, é armazenar as colunas como metadado e resolver a faixa de valor
  com um operador de comparação — a consulta estruturada da nota 01, §2.""")

# ============================== 4. PRESERVAÇÃO DOS MARCADORES DE ESTRUTURA
#
# A presença do texto não é suficiente. A estratégia de chunking por
# estrutura corta nos marcadores de artigo; se a extração os perdeu ou
# alterou a ordem, a mesma função passa a cortar por contagem de caracteres,
# sem que nada no código mude e sem que nenhum erro seja emitido.
extraido = "\n".join(paginas)
no_pdf = re.findall(r"Art\. \d+", extraido)
na_origem = re.findall(r"Art\. \d+", REGULAMENTO)

print(f"\n{'=' * 74}")
print("4. A ESTRUTURA SOBREVIVEU?")
print("=" * 74)
print(f"\n  marcadores `Art. N` no original: {len(na_origem)}")
print(f"  marcadores `Art. N` no extraído: {len(no_pdf)}  "
      f"(inclui os do anexo, que não está no original)")
print(f"  caracteres — original: {len(REGULAMENTO.strip())} · "
      f"extraído: {len(extraido.strip())}")

if no_pdf[:len(na_origem)] == na_origem:
    print("\n  Os marcadores do corpo vieram na MESMA ORDEM. O corte por "
          "estrutura\n  da Aula 06 continua aplicável a este texto.")
else:
    print("\n  A ORDEM MUDOU. É o sintoma de leitura em múltiplas colunas: o "
          "extrator\n  percorreu a página em ordem visual, e não em ordem de "
          "leitura. A\n  correção é trocar o extrator, não ajustar o corte.")

# LIMITAÇÃO DESTE SCRIPT: ele não registra PROCEDÊNCIA. Arquivo, página e
# posição precisam ser armazenados como metadado do chunk. Sem o número da
# página, a resposta cita "o regulamento" e a citação não é conferível.
