# Aula 03 — Prompt engineering

Laboratório da aula 03. Mesma configuração das aulas anteriores: API da
Mistral pelo SDK da OpenAI, com `LLM_BASE_URL` e `LLM_MODELO` vindos do
`.env` da raiz. Nada novo para instalar.

## Ordem sugerida

| Script | O que você vai ver |
|---|---|
| `00-zero-vs-few-shot.py` | A mesma classificação sem e com 5 exemplos. Mede acurácia **e** o custo em tokens de entrada que os exemplos cobram em toda chamada. |
| `01-rotulos-errados.py` | O experimento do **Min et al. (2022)**: exemplos com rótulos corretos × embaralhados × sem exemplos. Rode este **antes** de ler a explicação e tente prever o resultado. |
| `02-cot-e-custo.py` | Chain-of-thought em problemas de várias etapas: quanto se acerta a mais e quantos tokens a mais se paga. |
| `03-self-consistency.py` | N raciocínios com temperatura e voto majoritário, para N = 1, 3 e 5. Mostra a distribuição dos votos. |
| `04-injection.py` | Quatro defesas contra a mesma mensagem hostil — três textuais e uma estrutural. |
| `05-tool-calling.py` | O laço completo em quatro tempos, com duas ferramentas e log de cada chamada. |

`dados.py` guarda o conjunto de teste e os exemplos usados pelos scripts
`00`, `01` e `04` — num lugar só, de propósito: é o mesmo conjunto em todos,
senão os experimentos não seriam comparáveis entre si.

## Antes de rodar

```bash
source .venv/bin/activate           # a partir da raiz do repositório
python aula03-prompt/00-zero-vs-few-shot.py
```

O `05-tool-calling.py` exige um modelo com suporte a **function calling**.
Confirme com o script `00-catalogo-modelos.py` da aula 02: o modelo precisa
declarar `function_calling` nas capacidades.

Os scripts `02` e `03` têm os preços num par de constantes no topo. Confira
em <https://mistral.ai/pricing> e anote a data.

## Custo e rate limit

O `03-self-consistency.py` é o mais caro do curso até aqui: com N = 5 sobre
4 problemas com CoT, são muitos tokens de saída — a tarifa cara. Rodar tudo
de ponta a ponta custa alguns centavos de dólar.

Se aparecer `429`, aumente a constante `PAUSA` no topo do script.

## O que levar do laboratório

- **Escalar técnica sem medir é o mesmo erro de escolher o modelo maior sem
  testar o menor.** Cada script existe para responder uma pergunta com
  número: *quanto de acerto a mais, por quanto de custo a mais?*
- **Uma medição não é uma medição.** Com 10 mensagens de teste, diferenças
  de 1 ou 2 acertos podem ser ruído. Antes de concluir, aumente o conjunto.
- O conjunto de teste do `dados.py` é o mesmo do exercício: ele é o **ativo**
  que permite comparar qualquer mudança futura de prompt, de parâmetro ou de
  modelo.
