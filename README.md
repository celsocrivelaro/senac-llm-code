# senac-llm-code

Exemplos de código do curso de LLMs do Senac. Os exemplos usam o SDK da **OpenAI** apontado para a **API da Mistral** (`base_url="https://api.mistral.ai/v1"`), com o modelo `mistral-small-latest`.

## Pré-requisitos

- **Python 3.10+** (o projeto foi testado com 3.14)
- Uma **chave de API da Mistral**

## 1. Criar a chave de API e o arquivo `.env`

Acesse **https://admin.mistral.ai/** e faça login (ou crie uma conta gratuita). No painel, vá em **API Keys** → **Create new key**, dê um nome para a chave e copie o valor gerado.

> A chave é exibida **uma única vez**. Se você fechar a janela sem copiar, será preciso criar outra.

Na raiz do projeto, copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Abra o `.env` e cole a sua chave:

```
OPENAI_API_KEY=sua-chave-aqui
```

A variável se chama `OPENAI_API_KEY` (e não `MISTRAL_API_KEY`) porque usamos o SDK da OpenAI apontado para a Mistral — é o nome que o SDK e as bibliotecas do ecossistema procuram por padrão. O valor, porém, é a chave da Mistral.

Os scripts carregam esse arquivo com `load_dotenv()`, então a chave nunca fica escrita no código. O `.env` está no `.gitignore` — **nunca comite a sua chave**.

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

Com o virtual env ativo:

```bash
python aula01-hello-world/00-prompt.py
```

## Problemas comuns

- **`AuthenticationError` / `401`**: a chave está errada ou o `.env` não foi criado. Confira o passo 1.
- **`api_key client option must be set`**: a variável `OPENAI_API_KEY` está vazia — o `.env` existe, mas sem valor preenchido.
- **`ModuleNotFoundError: No module named 'openai'`**: o virtual env não está ativo ou as dependências não foram instaladas. Repita os passos 2 e 3.
- **`429 rate limit`**: muitas chamadas em sequência. Espere alguns segundos entre execuções.
- **Para rodar sem internet / sem chave**: o mesmo código funciona com o [Ollama](https://ollama.com) local, trocando o cliente por
  `OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")` e o modelo por um baixado com `ollama pull` (ex.: `qwen2.5:0.5b`).
