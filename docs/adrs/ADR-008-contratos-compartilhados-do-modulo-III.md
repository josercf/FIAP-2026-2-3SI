# ADR-008: Contratos compartilhados da plataforma no Módulo III

- **Data:** 2026-07-31
- **Status:** Aceita
- **Decisores:** Prof. José Romualdo da Costa Filho

## Contexto

O Módulo III tem três aulas com conteúdo e, pela segunda vez no semestre, elas
não são independentes:

- Aula 10 (06/10) escreve testes de unidade para as regras de negócio do
  Módulo II e cria o **Portal do Cliente em React**.
- Aula 11 (13/10) cria o **painel administrativo em Angular**, comparando a
  arquitetura opinada do framework com a liberdade do React da aula anterior.
- Aula 12 (20/10) liga **RAG com `pgvector`** e um **servidor MCP** à plataforma,
  consumindo a API de Pedidos da Aula 05.

A diferença em relação ao Módulo II é qualitativa e vale nomear: até aqui todo
consumidor de API era outro processo de servidor. A partir da Aula 10 o
consumidor é o **navegador**, e o navegador aplica a política de mesma origem.
Nenhum serviço das Aulas 02, 05 e 06 foi escrito com isso em mente.

Esse é o tipo de defeito que não aparece em teste de servidor: `curl` e cliente
HTTP de servidor ignoram CORS, então a suíte fica verde e a tela fica vazia. Se
o contrato não resolver isso antes, as Aulas 10 e 11 viram aulas de conserto de
CORS em vez de aulas de frontend.

## Decisão

Estender o contrato da `ADR-006` com os serviços de frontend, o serviço de RAG e
o servidor MCP, e **acrescentar CORS ao contrato de todo serviço de backend**.

### Serviços novos

| Serviço | Container | Stack | Porta | Nasce na | Consome |
|---|---|---|---|---|---|
| Portal do Cliente | `portal` | React 19, TypeScript, Vite | 5173 | Aula 10 | `pedidos`, `frete` |
| Painel administrativo | `painel-admin` | Angular, TypeScript, RxJS | 4200 | Aula 11 | `faturamento`, `painel` |
| Pipeline RAG | `rag` | Python, FastAPI | 8010 | Aula 12 | `postgres`, Ollama |
| Servidor MCP | `mcp-logitech` | Node 22, TypeScript | sem porta, stdio | Aula 12 | `pedidos`, `rag` |

O `mcp-logitech` **não expõe porta**. O transporte padrão do MCP é stdio: o
cliente sobe o servidor como processo filho e conversa por entrada e saída
padrão. Isso é conteúdo da aula, não detalhe de implantação, e explica por que
esse é o único serviço da plataforma que não tem `GET /health`.

### Quem cada frontend consome, e por quê

O planejamento fala em "gerenciar frotas e motoristas" no painel administrativo.
Frota e motorista não existem no contrato da `ADR-006`, e inventar dois serviços
novos para a Aula 11 seria conteúdo descartável. O que existe e serve é a
telemetria: o `painel` da Aula 02 já expõe `GET /api/v1/posicoes` e
`GET /api/v1/eventos`, que é exatamente posição de caminhão ao longo do tempo.

- **Portal do Cliente (React):** rastreia pedido em `pedidos` e cota frete em
  `frete`. É a visão de quem comprou.
- **Painel administrativo (Angular):** fatura em `faturamento`, o serviço .NET
  que o planejamento nomeia, e posição de frota em `painel`. É a visão de quem
  opera.

A divisão não é arbitrária: dá ao Angular um caso com **dois fluxos assíncronos
concorrentes e contínuos**, que é o que justifica RxJS. Uma tela de consulta
pontual não justificaria, e o `switchMap` da Pergunta de Verificação 3 ficaria
sendo decoração.

### CORS entra no contrato de todo serviço de backend

Todo serviço que um navegador chama passa a responder com CORS, lendo as origens
permitidas de `LOGITECH_CORS_ORIGINS`, lista separada por vírgula, com padrão
`http://localhost:5173,http://localhost:4200`.

Vale para `pedidos`, `faturamento`, `frete` e `painel`. Não vale para
`notificacoes` nem `ai-gateway`, que nenhum navegador chama.

**Consequência operacional:** os serviços congelados em `servicos/` dos lab kits
das Aulas 10, 11 e 12 já saem com CORS ligado. Os lab kits das Aulas 05, 06 e 07
**não** são reabertos para isso, porque lá o consumidor ainda é servidor e a
mudança seria ruído sem propósito na aula em que ele aparece.

### PostgreSQL passa a ser `pgvector`

A imagem do serviço `postgres` muda de `postgres:16` para
`pgvector/pgvector:pg16`. Nome do container, porta, banco, usuário e schemas
seguem os da `ADR-006`.

É a mesma imagem do PostgreSQL com a extensão compilada disponível; ativá-la
continua sendo `CREATE EXTENSION vector`, que é o primeiro passo do laboratório
da Aula 12 e não some da aula por causa da troca de imagem.

Schema novo `conhecimento`, com **duas** tabelas, e a normalização é deliberada:

```sql
conhecimento.contratos   -- um por documento: id, cliente, titulo, vigencia, arquivo
conhecimento.trechos     -- um por chunk: id, contrato_id -> contratos(id), ordem,
                         --               texto, embedding vector(768)
```

Uma tabela só bastaria para o RAG funcionar, e é justamente por isso que são
duas: o `JOIN` entre elas é o que permite responder "de qual contrato veio este
trecho", que é a pergunta que separa um RAG utilizável de uma demonstração. A
citação da fonte na resposta sai desse `JOIN`, não de metadado duplicado em cada
linha.

Segue a regra da `ADR-006`: um schema por contexto, e ninguém lê a tabela do
outro.

### SQL relacional é conteúdo da Aula 12, não pré-requisito dela

Levantamento feito ao escrever esta ADR: **não existe um único arquivo `.sql` no
acervo**. No serviço de Pedidos o schema nasce de `spring.jpa.hibernate.ddl-auto=update`;
no de Faturamento, do `ModelBuilder` do EF Core. Os dois estão corretos para o
que a Aula 05 ensina, que é Repository Pattern, mas a consequência é que o aluno
chega ao Módulo III tendo persistido em PostgreSQL o semestre inteiro **sem
nunca ter escrito uma linha de SQL**.

Pedir `CREATE EXTENSION vector`, `vector(768)` e o operador `<=>` de alguém
nessa situação produz cópia, não aprendizado.

A Aula 12 passa a ser **"PostgreSQL: do relacional ao vetorial"**, e a ordem
importa:

1. `psql` no container, e o aluno abre com `\dn`, `\dt` e `\d+` as tabelas que o
   ORM gerou nas Aulas 05 e 06. O primeiro contato com SQL é lendo a SQL que
   escreveram por ele.
2. DDL à mão para o schema `conhecimento`, porque nenhum ORM do curso declara
   uma coluna `vector`. É aqui que a chave estrangeira e a restrição aparecem.
3. `SELECT`, `JOIN`, `ORDER BY` e `LIMIT` sobre as duas tabelas, ainda sem
   vetor nenhum.
4. Só então a busca semântica, que entra como **mais um `ORDER BY`**, sobre
   distância em vez de sobre coluna. Essa é a tese da aula: busca vetorial não é
   outro banco nem outro paradigma, é um operador de ordenação a mais no
   PostgreSQL que já estava lá.
5. Índice e `EXPLAIN`, comparando varredura sequencial com `hnsw`. O `EXPLAIN`
   vale por si como fundamento relacional e serve de evidência do ganho.

O servidor MCP fica com o último terço do bloco prático. É uma escolha com
custo, declarada: o MCP entra com uma ferramenta e um recurso bem feitos em vez
de uma superfície ampla, e o CP3 cobra nesse nível.

### Embeddings vêm do Ollama local

A `ADR-005` já fixou o Ollama como único backend de IA. Para embeddings o modelo
de geração não serve, então o devcontainer da Aula 12 baixa um modelo de
embedding além do modelo de conversa, e a coluna vetorial é `vector(768)`.

**Emenda de 31/07/2026, após medição.** A primeira versão desta ADR fixava
`nomic-embed-text`. A construção do laboratório mediu `recall@3` sobre treze
perguntas de resposta conhecida, no mesmo acervo de contratos e com a mesma
consulta:

| Modelo | Dimensões | `recall@3` |
|---|---|---|
| `nomic-embed-text` | 768 | 9 de 13 |
| `nomic-embed-text` com o prefixo `search_query:` que a documentação recomenda | 768 | 7 de 13 |
| `paraphrase-multilingual` | 768 | 13 de 13 |

O `nomic-embed-text` é treinado predominantemente em inglês, e o acervo da aula
é contrato de transporte em português jurídico. **O modelo padrão passa a ser
`paraphrase-multilingual`.**

A troca sai barata justamente por causa do que esta ADR já tinha fixado: as 768
dimensões são as mesmas, então coluna, índice e DDL não mudam. Custa um
`ollama pull` e uma reingestão.

Vale registrar o resultado do meio da tabela, porque ele é o mais instrutivo:
seguir a recomendação de uso do próprio modelo, prefixando a consulta com
`search_query:`, **piorou** a recuperação, de 9 para 7. E piorou em silêncio, sem
erro nem aviso. É a evidência de que escolha de modelo de embedding se resolve
medindo no seu corpus, não lendo a documentação do fornecedor, e isso virou
conteúdo da aula em vez de nota de rodapé desta ADR.

A dimensão é do modelo, não uma escolha livre: trocar o modelo de embedding
obriga a recriar a coluna e reindexar. Isso é conteúdo da aula, não nota de
rodapé, porque é a primeira decisão de projeto irreversível que o aluno toma
neste laboratório.

### Variáveis de ambiente novas

Mantendo o prefixo `LOGITECH_`:

```
LOGITECH_CORS_ORIGINS        <- todo backend chamado por navegador
LOGITECH_RAG_URL             <- consumido pelo mcp-logitech
LOGITECH_EMBEDDING_MODELO    <- padrão paraphrase-multilingual
LOGITECH_OLLAMA_URL          <- padrão http://localhost:11434
```

No Vite, variável exposta ao navegador precisa do prefixo `VITE_`, e no Angular
a configuração de ambiente é arquivo, não variável de processo. Cada lab kit
mapeia `LOGITECH_PEDIDOS_URL` e companhia para a forma que a sua ferramenta
exige, e o nome canônico continua sendo o do contrato.

### O que a Aula 10 testa

"100% de cobertura" é meta de slide, não de laboratório: perseguir o número leva
a teste de getter. O laboratório cobre **as regras de negócio de frete**, em
PyTest sobre o serviço `frete` da Aula 06, e **o portal**, em Vitest com
Testing Library.

O mock com propósito aparece onde ele é inevitável e não decorativo: o cálculo
de frete consulta o serviço de `pedidos` para saber o peso, e o teste de unidade
não pode depender de outro processo no ar. É esse ponto que separa Stub de Mock
na Pergunta de Verificação 2.

### Extensões surgidas durante a construção, em 31/07/2026

Duas coisas que a construção da Aula 10 obrigou a decidir e que passam a valer
para o módulo:

**Rota nova em `frete`.** O contrato da `ADR-006` tinha só
`POST /api/v1/frete/cotacao`, que recebe os dados já resolvidos. O caso de uso
da Aula 10 é outro: cotar a partir de um pedido, que é o que obriga o `frete` a
consultar o `pedidos` e é exatamente o ponto onde o dublê de teste deixa de ser
decorativo.

```
frete   POST /api/v1/frete/cotacao/pedido
              entra {pedidoId, modalidade}
              sai   {pedidoId, modalidade, valor, prazoDias, pesoKg,
                     distanciaKm, cargaFechada}
```

**Serviço congelado pode trocar de linguagem, desde que cumpra o contrato.** O
`pedidos` que a Aula 10 entrega congelado é FastAPI em Python, não o Spring Boot
da Aula 05. Mesma porta, mesmas rotas, mesmo JSON.

O motivo é o custo: exigir JDK num devcontainer que já carrega Python e Node
gastaria minutos do bloco prático sem ensinar nada do assunto da aula. A Aula 07
abriu esse precedente ao escrever uma versão mínima do Pedidos, e a `ADR-007`
registra a mesma lógica.

A consequência precisa ser dita em voz alta, porque ela tem custo pedagógico:
**o aluno que escreveu Java na Aula 05 recebe um substituto em Python na Aula
10**, e pode concluir que o serviço dele foi descartado. Cada lab kit declara a
troca em `servicos/LEIA-ME.md`, e o que ela ensina, que interface é contrato e
não implementação, vale ser dito no slide em vez de escondido no README.

**Instrumentação de laboratório não é contrato.** O `faturamento` congelado da
Aula 11 ganhou `GET /api/v1/metricas`, `POST /api/v1/metricas/zerar` e a variável
`LOGITECH_FATURAMENTO_ATRASO_MS`, com padrão 800. Elas existem para o aluno
**medir o cancelamento** que o `switchMap` provoca, contando requisições
recebidas, concluídas e canceladas, e o atraso existe para a corrida ser
observável em rede local.

Não fazem parte do contrato da plataforma e nenhuma outra aula depende delas.
Ficam registradas aqui para que ninguém as tome por contrato ao construir o
Módulo IV, e para que a diferença entre instrumentação de ensino e superfície de
produção esteja escrita em algum lugar.

### Cada laboratório congela o que veio antes

Regra herdada da `ADR-006` e mantida: `servicos/` traz os serviços das aulas
anteriores prontos, congelados, com aviso de que não são tarefa. Quem faltou à
Aula 06 consegue fazer a Aula 10.

## Motivações

- CORS decidido no contrato custa uma variável de ambiente; descoberto em sala
  custa o bloco prático inteiro, e o sintoma (tela vazia, sem erro de rede
  aparente para quem não abriu o console) é dos piores para depurar ao vivo.
- Nomes estáveis são o que permite construir as três aulas em paralelo, que foi
  o que funcionou no Módulo II.
- Ancorar o painel administrativo na telemetria que já existe evita inventar
  domínio novo em uma aula cujo assunto é RxJS, não modelagem.
- Fixar o modelo de embedding antes evita que a Aula 12 e o CP3 discordem sobre
  a dimensão da coluna.
- Apresentar a busca vetorial como um `ORDER BY` a mais, e não como tecnologia
  separada, é o enquadramento que sobrevive à próxima moda de banco vetorial.
  Quem entendeu índice e plano de execução leva isso para qualquer stack.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| React e Angular na mesma quinzena, com `npm install` de cada um dentro de 60 minutos | Os dois lab kits sobem com dependências já instaladas no devcontainer, e o aluno preenche lacunas nomeadas em vez de criar projeto do zero |
| O modelo de embedding é mais um download no devcontainer da Aula 12 | Baixado na criação do container, como já se faz com o modelo de conversa; o `post-create` usa `curl` com `--connect-timeout` e `--max-time`, como ficou definido na Aula 03 |
| Trocar o modelo de embedding depois obriga a reingerir todo o acervo | Enquanto a dimensão for a mesma, a coluna e o índice sobrevivem e o custo é uma reingestão. Mudar de dimensão é que exige recriar a coluna, e é por isso que a dimensão está fixada aqui e não no código |
| O aluno subir o Compose da Aula 07 com a imagem antiga e o `CREATE EXTENSION` falhar | O lab kit da Aula 12 traz o Compose já com `pgvector/pgvector:pg16`, e o verificador checa a extensão ativa antes de checar a busca |
| O servidor MCP depender de um cliente que a turma não tem instalado | O laboratório entrega um cliente de teste próprio, em Node, que fala stdio; funciona sem depender de qual ferramenta de IA o aluno usa |
| Qualidade da resposta do RAG variar com o modelo local | O entregável mede **recuperação**, ou seja, se o trecho certo do contrato foi trazido, e não a redação da resposta gerada |
| SQL relacional, pgvector e MCP em uma noite só não caber nos 60 minutos do bloco prático | Ordem de corte declarada no README do lab: primeiro o `EXPLAIN` comparativo vira demonstração do professor, depois a segunda ferramenta do MCP; a DDL à mão e a busca por distância **nunca** saem, porque são a tese da aula. A cronometragem na primeira aplicação entra como pendência |
| O aluno concluir que ORM é dispensável, ou o contrário | O slide de fecho nomeia a divisão real: ORM para o caminho transacional do CRUD, SQL à mão para o que o ORM não modela, que nesta aula é literalmente a coluna `vector` |

## Consequências

**Positivas**
- As três aulas podem ser construídas em paralelo sem divergir.
- O CP3 tem escopo verificável, com contrato escrito para cobrar.
- A plataforma passa a ter frontend, o que fecha a promessa do case desde a
  Aula 01.
- O curso deixa de formar alguém que persiste em banco relacional sem saber
  consultá-lo. O `EXPLAIN` da Aula 12 é também o primeiro contato com custo de
  consulta, que o Módulo IV cobra em teste de carga.

**Negativas**
- O contrato cresce: agora são doze serviços, e mudar uma porta toca em mais
  laboratórios do que antes.
- Ligar CORS nos serviços congelados cria uma diferença entre o que o aluno
  escreveu na Aula 06 e o que ele recebe congelado na Aula 10. A diferença é
  pequena e está declarada no README de cada kit, mas existe.
- A troca da imagem do PostgreSQL torna o Compose da Aula 12 incompatível com o
  volume de dados criado na Aula 07 se houver diferença de versão maior; o
  roteiro manda recriar o volume.
- O `PLANO_DE_ENSINO.md` e o `PLANEJAMENTO_AULA_A_AULA.md` precisam ser
  atualizados: o título da Aula 12, a lista de conteúdo e o escopo do CP3 hoje
  não citam SQL relacional. Os dois documentos são a fonte da verdade e passam a
  divergir do deck enquanto não forem tocados.

## ADRs relacionadas

- `ADR-005`: Ollama como único backend de IA, que determina de onde vêm os
  embeddings.
- `ADR-006`: contrato do Módulo II, que esta ADR estende. Portas, rotas, banco,
  rede e prefixo de variável continuam valendo como estão lá.
- `ADR-007`: decisões de orquestração da Aula 07, incluindo o `healthcheck` que
  os serviços novos precisam respeitar para entrar no Compose.
