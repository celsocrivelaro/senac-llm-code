# Aula 08 — Memória: o que o agente lembra entre execuções

Laboratório da aula 08. Encerra a fase Conhecimento e trata a primeira das
três pendências registradas na aula 03 (nota 04, §9): memória, MCP e
multiagente.

Sem dependência nova: Chroma vem da aula 07. O que muda é o **objeto
indexado**: em vez de documentos, **episódios** — o registro do que o agente
fez numa execução anterior, e no que deu.

**Este laboratório é autocontido.** Nenhum script importa de outra aula —
não há `sys.path` apontando para fora desta pasta. O `embedding.py` é
**cópia** da aula 06, de modo que alterações em uma aula não invalidam a
outra.

## A fronteira: checkpoint × memória

|  | checkpoint (script `00`) | memória (scripts `01` em diante) |
|---|---|---|
| escopo | uma execução | todas as execuções |
| propósito | **retomar** | **lembrar** |
| forma | estado íntegro | fragmento selecionado |
| leitura | uma vez, no início | por relevância, a cada volta |

Serializar o `Estado` de todas as execuções não produz memória: produz um
conjunto de arquivos sem critério de recuperação. Memória exige
**recuperar**, e recuperar exige um critério de relevância — que é o
mecanismo da aula 07 aplicado a outro objeto.

## Ordem sugerida

| Script | O que produz |
|---|---|
| `00-o-checkpoint.py` | **O estado de uma execução em disco.** A execução é interrompida no passo que exige aprovação, o estado é gravado e impresso por extenso, e a execução é retomada sem repetir os dois primeiros passos. Não chama a API. |
| `01-checkpoint-vs-memoria.py` | A mesma tarefa contra dez execuções serializadas e contra dez execuções indexadas. `21.360` tokens de arquivo morto — `~5.340` de contexto para incluir tudo — contra os poucos fragmentos que a recuperação escolhe. |
| `02-memoria-episodica.py` | O que aconteceu, e quando. Chroma, recuperado por similaridade — **e a consulta que falha**: `"refeição em viagem internacional"` traz duas viagens domésticas, porque o que distingue Lisboa de Curitiba é atributo, não assunto. O script confere isso em código e contrasta com o filtro por metadado, que entra **antes** da ordenação. |
| `02-memoria-semantica.py` | Fatos sobre entidades. JSON lido por chave, com custo de consulta zero, e a chave de idempotência derivada do conteúdo. |
| `02-memoria-procedural.py` | Regras de conduta. Texto injetado no system prompt: não é recuperada, e por isso tem custo **fixo** de janela em toda execução. |
| `03-quem-escreve.py` | As três políticas de escrita aplicadas à mesma execução, e a demonstração de que gravar memória é operação de escrita: chave de idempotência derivada do conteúdo, com `ja_existia` no retorno. |
| `04-esquecer-contradicao.py` | Dois fatos verdadeiros em datas diferentes. A recuperação devolve o mais semelhante, não o vigente, porque o vetor não representa anterioridade (cegueira TEMPO, aula 07). Aqui **nada é apagado**: o desempate ocorre na leitura. |
| `04-esquecer-decaimento.py` | O fato envelheceu sem ser contradito. Decair é **rebaixar** a prioridade, não deletar o registro. Junto com o `00`, não chama a API. |
| `04-esquecer-remocao.py` | Remoção solicitada pelo titular (LGPD). **A verificação falha na primeira passada**: o checkpoint armazena o identificador e não é uma das três memórias. O requisito é verificar a cobertura, não declará-la. |
| `05-o-ganho-em-passos.py` | A medição do ganho: 2 passos de 4 na segunda execução da mesma tarefa. Passos evitados são chamadas não emitidas, e é essa a grandeza comparável. |

## Os módulos

`dados.py` — o dado **compartilhado**, em duas peças: os dez episódios
anteriores do agente de prestação de contas (lidos pelos scripts `01`, `02`
e `05`) e o `CHECKPOINT`, um deles na forma íntegra — o `00` o grava e
retoma, e o `01` o compara com o fragmento que a memória guarda da mesma
execução. Os demais dados residem no script que os utiliza: os fatos
contraditórios no `04-esquecer-contradicao`, e a tarefa corrente nos três
scripts que a reexecutam, com texto idêntico. Nada é importado de fora da
pasta.

**Uma memória por arquivo.** A separação reflete a diferença de estrutura:
os três tipos têm padrões de acesso distintos, e as três implementações não
compartilham nenhuma linha.

| Módulo | O que é |
|---|---|
| `memoria_episodica.py` | o que aconteceu, quando — **Chroma**, recuperado por similaridade |
| `memoria_semantica.py` | fato estável sobre a entidade — **JSON**, lido por chave |
| `memoria_procedural.py` | como agir — **texto**, entra no system prompt |
| `escrita.py` | quem escreve, e quando: a extração pelo código e o prompt dela |
| `leitura.py` | qual fato vale (desempate por tempo) e quanto dele cabe (orçamento) |
| `embedding.py` | texto → vetor. Cópia da aula 06 |
| `cliente.py` | um cliente para as duas modalidades |
| `armazenamento.py` | a raiz que as três memórias dividem em disco |
| `checkpoint.py` | o estado de uma execução em disco — **não é memória de longo prazo**: o escopo é uma execução. Expõe `esquecer()` porque armazena dado pessoal |

`memoria_db/` é criado em tempo de execução e não é versionado.

## O gancho para a aula 13

Os scripts `04` identificam o risco e não o tratam. A memória é o dado mais
sensível do sistema por duas propriedades combinadas: é **acumulada** e
**não supervisionada**. Ela é alvo de ataque e também vetor — conteúdo
gravado hoje é lido semanas depois, em outro contexto, sem que a relação
entre as duas operações seja visível. O tratamento é assunto da aula de
segurança.

## O laboratório de compressão fica na Aula 05

As técnicas de compressão de trajetória — *tool clearing* e *compaction* — são
teoria desta aula (nota 03, §5 e §6), mas o script que as demonstra é o
[`aula05-agentes/07-compaction.py`](../aula05-agentes/07-compaction.py).

A separação é deliberada. Aquele script exige um agente com laço, estado e
orçamento para produzir uma trajetória longa o bastante para justificar
compressão, e esse agente é o `agente.py` da Aula 05. Duplicá-lo aqui
custaria mais do que a referência cruzada.

Execute-o a partir daqui, ao chegar na §5:

```bash
python aula05-agentes/07-compaction.py
```
