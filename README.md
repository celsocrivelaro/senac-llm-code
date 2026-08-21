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

Há dois modelos de arquivo no repositório, e você copia **um** deles para `.env`:

| Arquivo | Para que |
|---|---|
| `.env.example` | a configuração padrão do curso: API da Mistral |
| `.env.ollama` | rodar local com o [Ollama](https://ollama.com), sem internet e sem custo |

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

## 5. Trocando de provedor ou de modelo

Os exemplos da **aula 02** não têm endereço de API nem nome de modelo escritos
no código: eles leem do `.env`, com um valor padrão embutido. Isso significa
que o `.env` com só a `OPENAI_API_KEY` continua funcionando — e que trocar de
provedor é mudar uma linha, não editar oito arquivos.

| Variável | Padrão | Para que serve |
|---|---|---|
| `LLM_BASE_URL` | `https://api.mistral.ai/v1` | qualquer endpoint compatível com a API da OpenAI |
| `LLM_MODELO` | `mistral-small-latest` | o modelo padrão dos exemplos |

Duas exceções: os scripts **`06-benchmark-modelos.py`** e **`07-raciocinio.py`**
têm os nomes dos modelos **fixos no código**. Ali os modelos não são
configuração — são o objeto do experimento, cada um com o preço ao lado, e a
tabela que eles produzem só significa algo se você souber exatamente quem
entrou na comparação. Para trocar, edite o topo daqueles dois arquivos.

Rodando tudo local, de graça, com o [Ollama](https://ollama.com): baixe o
modelo e troque o `.env`.

```bash
ollama pull qwen3.6:35b     # confirme a tag com `ollama list`
cp .env.ollama .env
```

O `.env.ollama` já vem com o endpoint, a chave de fachada e o modelo
preenchidos — e com as duas advertências que valem para essa configuração
(memória necessária para um modelo de 35B, e quais recursos da API o Ollama
não tem).

Essa portabilidade é o assunto da nota 01 da aula 02: o formato
`chat/completions` virou padrão de fato, então **isolar o endpoint e o nome do
modelo em um único lugar** é uma decisão de arquitetura que sai de graça. Se
você espalhar `model="mistral-small-latest"` por trinta arquivos, se amarrou ao
provedor sem precisar.

> Atenção: compatível não é idêntico. O Ollama não expõe tudo o que a API
> expõe (`response_format` com JSON Schema, por exemplo), e a contagem de
> tokens no streaming pode não vir. Para os experimentos de custo (`06`) e de
> saída estruturada (`05`), use a API.

## Problemas comuns

- **`AuthenticationError` / `401`**: a chave está errada ou o `.env` não foi criado. Confira o passo 1.
- **`api_key client option must be set`**: a variável `OPENAI_API_KEY` está vazia — o `.env` existe, mas sem valor preenchido.
- **`ModuleNotFoundError: No module named 'openai'`**: o virtual env não está ativo ou as dependências não foram instaladas. Repita os passos 2 e 3.
- **`429 rate limit`**: muitas chamadas em sequência. Espere alguns segundos entre execuções.
- **`model not found` / `404` rodando com o Ollama**: a tag em `LLM_MODELO` não
  bate com nenhum modelo baixado. Rode `ollama list` e corrija o `.env`.
- **Para rodar sem internet / sem chave**: os exemplos da aula 02 leem o
  endpoint e o modelo do `.env`, então o mesmo código roda com o
  [Ollama](https://ollama.com) local sem editar script nenhum — é só
  `cp .env.ollama .env` (passo 5).
