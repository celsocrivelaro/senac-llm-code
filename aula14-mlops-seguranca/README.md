# Aula 14 — Segurança: prompt injection, tool misuse e OWASP ASI

Laboratório da aula 14. O sistema já está no ar (aula 13) e já tem suíte
(aula 11); esta pasta o ataca, o defende e mede quanto a defesa custou. Os
dois riscos próprios de multiagente — ASI07 e ASI08 — são nomeados aqui e
tratados na aula 16.

## Regra de escopo — obrigatória

> Os ataques desta pasta valem **exclusivamente contra o sistema do próprio
> aluno, em ambiente local**. Aplicar o mesmo procedimento a sistema de
> terceiro sem autorização é ilícito.

A regra vale para todos os scripts desta pasta, e não é formalidade: o
objetivo é defender o que se construiu.

Nada sai da máquina. A ferramenta `enviar_relatorio` apenas anexa a uma lista
em memória, e os dados "privados" são fictícios.

## O caso de uso

> Dado o sistema construído ao longo da disciplina, descobrir por onde ele
> obedece a um atacante e fechar duas dessas portas.

## Os módulos

| Arquivo | O que é |
|---|---|
| `cliente.py` | o modelo, escolhido por `LLM_PROVEDOR` no `.env` entre Mistral, Ollama e Groq, o mesmo das aulas 09 a 14. Traz também os dados fictícios (despesas, política e dados "privados") e as três ferramentas de consulta que os leem: `consultar_politica`, `consultar_despesa` e `consultar_credenciais`. A de envio, `enviar_relatorio`, fica nos próprios `02.1` e `02.3` |

O agente vulnerável é o `create_agent` da aula 09, e cada script o monta à
vista. Os textos de cada ataque estão no próprio script, e a mensagem que o
modelo recebe é montada ali mesmo, para que se veja onde o texto do atacante
entra. Cada `03.x` traz uma defesa, como função curta no próprio script; cada `04.x`
traz a sua versão de uma configuração, ao lado dos casos da suíte.

A descrição envenenada da ferramenta é a mesma função com outra
`description`, trocada por `model_copy`. O que muda é só o texto que o
modelo lê.

Os *payloads* são **deliberadamente educados**, e é essa a propriedade que
os torna invisíveis para classificadores de toxicidade — limitação que não se
resolve com um classificador melhor.

## Ordem sugerida

| Script | O que produz |
|---|---|
| `00-injecao-direta.py` | A mesma pergunta, limpa e com uma instrução injetada pelo usuário: o agente deixa de consultar a política e aprova. |
| `01.1-injecao-documento.py` | Injeção indireta pelo documento recuperado: o art. 31 do corpus, sem e com o parágrafo do atacante. |
| `01.2-injecao-descricao-ferramenta.py` | Injeção indireta pela descrição de ferramenta: a mesma função, com a descrição original e com a envenenada. |
| `01.3-injecao-memoria.py` | Injeção indireta pela memória: os mesmos registros, sem e com o gravado pelo atacante. |
| `02.1-trifecta-tres-pernas.py` | A exfiltração completa: o agente lê o dado privado, recebe o art. 31 envenenado e envia. |
| `02.2-trifecta-sem-envio.py` | O mesmo ataque sem a ferramenta de envio: o dado privado é lido, mas não sai. |
| `02.3-trifecta-sem-dado-privado.py` | O mesmo ataque sem a ferramenta que lê dado privado: o envio acontece, sem nada privado. |
| `03.1-defesa-nenhuma.py` | O ataque do art. 31 contra o agente sem defesa, e a pergunta legítima, como referência para os três seguintes. |
| `03.2-defesa-minimizacao-de-contexto.py` | O mesmo ataque contra a minimização de contexto. A pergunta legítima mostra **o que o agente deixou de conseguir fazer**. |
| `03.3-defesa-planejar-entao-executar.py` | O mesmo ataque contra planejar-então-executar, com a mesma pergunta legítima. |
| `03.4-defesa-llm-duplo.py` | O mesmo ataque contra o LLM duplo, com a mesma pergunta legítima. |
| `04.1-red-team-sem-defesa.py` | A suíte hostil ao lado da representativa da aula 11, contra o agente sem defesa, nas **duas colunas**. |
| `04.2-red-team-minimizacao.py` | A mesma suíte contra o agente com minimização de contexto. |
| `04.3-red-team-llm-duplo.py` | A mesma suíte contra o agente com LLM duplo. |

Os comandos:

```
python 00-injecao-direta.py
python 01.1-injecao-documento.py
python 01.2-injecao-descricao-ferramenta.py
python 01.3-injecao-memoria.py
python 02.1-trifecta-tres-pernas.py
python 02.2-trifecta-sem-envio.py
python 02.3-trifecta-sem-dado-privado.py
python 03.1-defesa-nenhuma.py
python 03.2-defesa-minimizacao-de-contexto.py
python 03.3-defesa-planejar-entao-executar.py
python 03.4-defesa-llm-duplo.py
python 04.1-red-team-sem-defesa.py
python 04.2-red-team-minimizacao.py
python 04.3-red-team-llm-duplo.py
```

## As três coisas que esta pasta demonstra

**1. O problema não é o texto, é o privilégio.** O `00` mostra uma frase
educada, escrita no próprio campo da pergunta, mudando o que o agente faz. A
instrução maliciosa não precisa parecer maliciosa — basta parecer instrução.

**2. A memória é o canal que assusta.** No `01.3`, o registro
envenenado foi gravado numa conversa anterior e age agora. O atacante não está presente,
o usuário afetado não é o atacante, e nada na segunda execução aponta para a
primeira.

**3. Toda defesa custa capacidade, e o custo precisa ser declarado.** Os `03.x` e
os `04.x` reportam **utilidade e resistência em colunas separadas**. Reportá-las
juntas esconde a troca — e o custo da defesa é o dado que falta em quase toda
discussão da área.

## Os dois reencontros

| Padrão de defesa | Onde já apareceu no curso | O que mudou |
|---|---|---|
| *mapear-reduzir* | o sub-agente da Aula 05, como parede de contexto | a impossibilidade de o principal ver o que o subordinado leu deixa de ser **preço** e vira **defesa** |
| *planejar-então-executar* | o *workflow* da Aula 01, o degrau menos capaz | é o **mais seguro**, porque não decide em execução e não pode ser redirecionado |

A segunda linha fecha o espectro de autonomia do curso: **cada degrau de
autonomia é também um degrau de superfície**.

## O que a suíte hostil acrescenta ao carimbo

O **conjunto de casos hostis**, ao lado do *golden dataset* da aula 11. E a
suíte passa a reportar **duas taxas separadas**: sucesso em casos
representativos, e resistência em casos hostis. A aula 16 roda a mesma
suíte hostil sobre a versão multiagente.

## Custo

Todos os scripts chamam o modelo. Cada `03.x` roda duas perguntas; cada
`04.x` roda oito casos — são os mais caros da pasta. O LLM duplo faz uma chamada de quarentena por documento, mais as do
agente.
