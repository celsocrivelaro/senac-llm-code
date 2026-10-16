# Configuração comum dos testes.
#
# O `cliente.py` constrói o modelo na importação. Nos testes unitários o
# modelo nunca é chamado, mas precisa poder ser construído: sem `.env` (como
# no CI), usa-se o Groq com uma chave falsa. No eval, a chave verdadeira vem
# do `.env` local ou do ambiente (no CI, de um secret) e prevalece sobre
# estes valores de reserva.

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PASTA = Path(__file__).resolve().parent.parent

# Primeiro o .env da pasta, se existir; depois os valores de reserva, que só
# valem para o que nem o .env nem o ambiente definiram.
load_dotenv(PASTA / ".env")
os.environ.setdefault("LLM_PROVEDOR", "groq")
os.environ.setdefault("GROQ_API_KEY", "chave-falsa-para-testes")

sys.path.insert(0, str(PASTA))
