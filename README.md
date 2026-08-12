# senac-llm-code

Exemplos de código do curso de LLMs do Senac. Os exemplos rodam **100% localmente**, usando o [Ollama](https://ollama.com) para servir o modelo — nenhuma chave de API é necessária.

## Pré-requisitos

- **Python 3.10+** (o projeto foi testado com 3.14)
- **Ollama** instalado e rodando

## 1. Instalar o Ollama e baixar o modelo

Instale o Ollama:

- **macOS / Windows**: baixe o instalador em https://ollama.com/download
- **macOS via Homebrew**: `brew install ollama`
- **Linux**: `curl -fsSL https://ollama.com/install.sh | sh`

Confirme a instalação:

```bash
ollama --version
```

Baixe o modelo usado nos exemplos (`qwen2.5:0.5b` — cerca de 400 MB, leve o suficiente para rodar em CPU):

```bash
ollama pull qwen2.5:0.5b
```

Teste se o modelo responde:

```bash
ollama run qwen2.5:0.5b "Olá, tudo bem?"
```

O Ollama precisa estar rodando em background para os scripts funcionarem. No macOS e Windows o app já faz isso; se necessário, suba o servidor manualmente:

```bash
ollama serve
```

## 2. Criar o virtual env

Na raiz do projeto:

```bash
python3 -m venv .venv
```

Ative o ambiente:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Com o ambiente ativo, o prompt do terminal passa a mostrar `(.venv)`. Para sair, use `deactivate`.

## 3. Instalar as dependências

```bash
pip3 install -r requirements.txt
```

> As dependências incluem `torch` e `transformers`, então o download é grande (alguns GB) na primeira vez.

## 4. Rodar os exemplos

Com o virtual env ativo e o Ollama rodando:

```bash
python aula01-hello-world/00-prompt.py
```

## Problemas comuns

- **`ConnectionError` / `connection refused`**: o servidor do Ollama não está rodando. Execute `ollama serve`.
- **`model "qwen2.5:0.5b" not found`**: falta baixar o modelo. Execute `ollama pull qwen2.5:0.5b`.
- **`ModuleNotFoundError: No module named 'ollama'`**: o virtual env não está ativo ou as dependências não foram instaladas. Repita os passos 2 e 3.
- **Respostas estranhas ou fora de formato**: o `qwen2.5:0.5b` é um modelo bem pequeno, escolhido pela velocidade. Para respostas melhores, troque o modelo nos scripts por um maior (ex.: `ollama pull qwen2.5:3b`).
