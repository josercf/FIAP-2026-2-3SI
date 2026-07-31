# Laboratório Prático - Aula 12

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 12, do relacional ao vetorial)

Você persistiu em PostgreSQL o semestre inteiro **sem escrever uma linha de
SQL**. Na Aula 05 o schema do serviço de Pedidos nasceu de
`spring.jpa.hibernate.ddl-auto=update`, e o de Faturamento nasceu do
`ModelBuilder` do EF Core. Os dois estão corretos para o que aquela aula
ensina, que é Repository Pattern. A consequência é que ninguém nunca viu o que
saiu do outro lado.

Hoje isso muda, e a ordem importa: primeiro você **lê** a SQL que escreveram
por você; depois escreve a sua, porque nenhum ORM do curso sabe declarar uma
coluna do tipo `vector`; e só então liga a busca semântica, que entra como
**mais um `ORDER BY`** na mesma tabela.

Essa é a tese da aula e vale repetir: **busca vetorial não é outro banco nem
outro paradigma**. É um operador de ordenação a mais no PostgreSQL que já
estava lá. Quem entende índice e plano de execução leva isso para qualquer
stack, e a próxima moda de banco vetorial não o pega desprevenido.

A dor de negócio: os atendentes da LogiTech gastam a tarde procurando cláusula
em contrato de transporte para responder "em quantos dias o cliente pode
reclamar de avaria". Ao fim desta noite eles perguntam em português e recebem o
trecho certo **com a fonte citada**, e um servidor MCP expõe essa busca para
qualquer cliente de IA.

**Atividade em dupla**, seis passos.

---

## O que já vem pronto, e o que vocês fazem

| Vem pronto, é modelo | Vocês escrevem |
|---|---|
| `contratos/`, quatro contratos de transporte da LogiTech em Markdown | `sql/02-conhecimento.sql`, a DDL do schema novo (`TODO-2a` a `TODO-2c`) |
| `servicos/orm-gerado.sql`, a saída literal de um `pg_dump` dos schemas que o Hibernate e o EF Core criaram | `sql/03-consultas.sql`, as duas consultas nomeadas (`TODO-3a`, `TODO-3b`) |
| `rag/chunking.py`, `rag/embeddings.py`, `rag/ingestao.py`, `rag/geracao.py`, `rag/app.py` | `rag/busca.py`, a consulta de busca por similaridade (`TODO-4`) |
| `mcp-logitech/src/protocolo.ts`, o transporte stdio e o enquadramento JSON-RPC | `sql/05-indice.sql`, o índice HNSW (`TODO-5`) |
| `mcp-logitech/src/cliente-teste.ts`, o cliente MCP de teste | `mcp-logitech/src/servidor.ts`, a ferramenta `buscar_em_contratos` (`TODO-6a`) |
| `docker-compose.yml` já com a imagem `pgvector/pgvector:pg16` | `docs/EVIDENCIAS.md`, com os marcadores medidos na sua máquina |
| `verificar.py` e `resgate/` | Os commits, um por passo |

**Nada em `servicos/` é tarefa.** Leia o `servicos/LEIA-ME.md`: o que está
congelado ali é o **schema** que as Aulas 05 e 06 deixaram, e não código de
serviço.

---

## Pré-requisitos

- Fork do repositório `josercf/mwe-2026-2-lab12-rag-mcp` (nunca clone direto).
- GitHub Codespaces, ou Docker Desktop local.
- A rede `logitech-net`, herdada da Aula 03. Se não existir:

```bash
docker network create logitech-net
```

> **O volume do banco precisa ser recriado.**
>
> Se você fez a Aula 07 nesta máquina, o volume `logitech-postgres` foi criado
> pela imagem `postgres:16`, que **não** tem a extensão de vetores disponível.
> O `CREATE EXTENSION vector` do Passo 2 falharia com uma mensagem que não
> ajuda em nada. O Passo 0 abaixo resolve.

---

## Passo 0, o ambiente

```bash
cp .env.exemplo .env
docker network create logitech-net          # se ainda nao existir

docker compose down -v                      # apaga o volume da Aula 07
docker compose up -d --wait
```

O `down -v` não é opcional. Ele apaga o volume, e é isso que faz o PostgreSQL
rodar `servicos/orm-gerado.sql` na subida: sem esse arquivo executado, o
Passo 1 abriria um banco sem tabela nenhuma para ler.

Confirme que o Ollama está no ar com os **dois** modelos:

```bash
ollama list        # paraphrase-multilingual e qwen2.5:1.5b
```

Modelo de geração não serve para embedding e vice-versa: são cabeças
diferentes, treinadas para tarefas diferentes. Esta é a primeira aula em que a
distinção aparece na prática.

---

## Passo 1, leia a SQL que escreveram por você

Sem lacuna de código. É leitura, e a evidência dela é o que você anota.

```bash
docker compose exec postgres psql -U logitech -d logitech
```

Dentro do `psql`, na ordem:

```
\dn                          -- que schemas existem
\dt pedidos.*                -- o que o Hibernate criou
\dt faturamento.*            -- o que o EF Core criou
\d+ faturamento.faturas      -- a anatomia de uma tabela que você não escreveu
\di faturamento.*            -- os índices que vieram de brinde
\dx                          -- a extensão vector ainda NÃO está aqui
```

Os comandos com barra invertida são do `psql`, e não SQL: são atalhos que o
cliente traduz em consultas ao catálogo. O arquivo `sql/01-explorar.sql` traz
cada um deles também na forma de `SELECT`, para você ver o que o atalho faz por
baixo.

Três coisas para reparar, e nenhuma é acidente:

| O que você lê | De onde veio |
|---|---|
| `"PedidoId" character varying(36)`, com aspas | O EF Core manteve o PascalCase do C#. Sem aspas, o PostgreSQL rebaixaria tudo para minúsculas. No `psql`, `SELECT PedidoId ...` falha e `SELECT "PedidoId" ...` funciona |
| `peso_kg numeric(38,2)` ao lado de `"Valor" numeric(12,2)` | Um `BigDecimal` sem precisão declarada, contra um `HasPrecision(12, 2)` explícito. A mesma ideia de negócio, dois resultados, porque um dos dois foi declarado |
| `CONSTRAINT pedidos_status_check CHECK (status = ANY (...))` | Um `enum` Java com `@Enumerated(EnumType.STRING)`. Regra de negócio gravada no banco, que passa a valer mesmo para quem escrever na tabela por fora |

Preencha `SCHEMAS_QUE_O_ORM_CRIOU`, `TIPO_DA_COLUNA_VALOR` e
`INDICES_QUE_NAO_ESCREVI` em `docs/EVIDENCIAS.md`.

```bash
python3 verificar.py --criterio 1
```

---

## Passo 2, a DDL à mão (`TODO-2a`, `TODO-2b`, `TODO-2c`)

Abra `sql/02-conhecimento.sql` e complete as lacunas. São duas tabelas, e a
normalização é deliberada:

```
conhecimento.contratos   um por documento: id, cliente, titulo, vigencia, arquivo
conhecimento.trechos     um por pedaço:    id, contrato_id -> contratos(id),
                                           ordem, texto, embedding vector(768)
```

Uma tabela só bastaria para o RAG funcionar, e é **por isso** que são duas: o
`JOIN` entre elas é o que responde "de qual contrato veio este trecho". Essa é a
pergunta que separa um RAG utilizável de uma demonstração, e a citação da fonte
sai desse `JOIN`, não de metadado repetido em cada linha.

O `768` de `vector(768)` **é do modelo**, não uma escolha sua. O
`paraphrase-multilingual` devolve 768 números. Trocar por um modelo de outra
dimensão obriga a recriar a coluna e a reindexar tudo: é a primeira decisão
irreversível deste laboratório.

```bash
docker compose exec -T postgres psql -U logitech -d logitech -v ON_ERROR_STOP=1 < sql/02-conhecimento.sql
python3 verificar.py --criterio 2
```

---

## Passo 3, a ingestão e as consultas relacionais (`TODO-3a`, `TODO-3b`)

Primeiro a ingestão, que já vem pronta:

```bash
python3 -m rag.ingestao
```

Ela lê `contratos/`, divide cada documento em trechos, pede ao Ollama o vetor
de cada trecho em um único lote e grava nas duas tabelas. Anote
`TRECHOS_INGERIDOS` e `SEGUNDOS_DE_INGESTAO`.

Depois as consultas, em `sql/03-consultas.sql`. Ainda **sem vetor nenhum**:
`SELECT`, `JOIN`, `GROUP BY`, `ORDER BY` e `LIMIT` sobre as duas tabelas.

Não é aquecimento. As duas consultas têm a **mesma estrutura** da busca
semântica do Passo 4; lá muda uma coisa só, a expressão do `ORDER BY`.

O `TODO-3b` merece atenção: junção sem condição não é erro de sintaxe. O
PostgreSQL aceita, executa e devolve o produto cartesiano, com centenas de
linhas plausíveis e quase todas erradas. É o tipo de defeito que passa
despercebido até alguém conferir a fonte, e o verificador foi escrito para
pegá-lo.

```bash
docker compose exec -T postgres psql -U logitech -d logitech < sql/03-consultas.sql
python3 verificar.py --criterio 3 && python3 verificar.py --criterio 4
```

No fim do arquivo há uma busca por palavra-chave com `ILIKE '%avaria%'`.
**Guarde o resultado dela**: no Passo 4 você compara com a busca por
significado.

---

## Passo 4, a busca por distância (`TODO-4`)

A lacuna central do laboratório está em `rag/busca.py`, e são três linhas.

Antes de escrever, rode `sql/04-busca.sql`, que não tem lacuna e mostra o
operador funcionando em SQL puro, sem Python e sem Ollama no caminho:

```bash
docker compose exec -T postgres psql -U logitech -d logitech < sql/04-busca.sql
```

Repare no resultado de `'[1,0,0]' <=> '[9,0,0]'`: **zero**. Os dois vetores
apontam para o mesmo lado e um é nove vezes maior que o outro, e a distância de
cosseno entre eles é nula. É por isso que o cosseno é o padrão em busca de
texto: o que importa é a direção do significado, não o tamanho do vetor. Pela
distância euclidiana, os mesmos dois vetores distam 8.

Agora complete o `TODO-4` e suba o serviço:

```bash
uvicorn rag.app:app --host 0.0.0.0 --port 8010 --reload
```

Em outro terminal:

```bash
curl -s --connect-timeout 5 --max-time 120 -X POST http://localhost:8010/api/v1/busca \
  -H 'Content-Type: application/json' \
  -d '{"pergunta":"O motorista precisa de algum curso especial para levar produto inflamável?","k":3}'
```

A pergunta **não contém nenhuma palavra** da cláusula que responde a ela: o
contrato fala em "curso MOPP". O `ILIKE` do Passo 3 não encontra isso, e a
busca por distância traz a Cláusula 2 da Petroquímica Litoral em primeiro
lugar. Registre esse contraste em `O_QUE_O_ILIKE_NAO_ACHOU`.

### Uma pergunta que a busca semântica não resolve sozinha

Depois de fechar o critério, faça esta:

```bash
curl -s --connect-timeout 5 --max-time 120 -X POST http://localhost:8010/api/v1/busca \
  -H 'Content-Type: application/json' \
  -d '{"pergunta":"Quanto tempo o cliente tem para pedir ressarcimento de mercadoria danificada?","k":3}'
```

Os três resultados são as cláusulas de avaria de **três contratos diferentes**,
e a recuperação está certa: a pergunta não diz de qual cliente se trata, e os
quatro contratos têm uma Cláusula 7 sobre o mesmo assunto. O problema é a
pergunta, não o modelo.

Só que os prazos são **90, 120 e 180 dias**. Responder o primeiro resultado sem
olhar de onde ele veio dá a resposta errada para três em cada quatro clientes.

É exatamente aqui que o `JOIN` do `TODO-4a` deixa de ser detalhe: ele é o que
mostra que o trecho veio da Frigolar e não da Aurora, e o que permite ao
atendente perceber que precisa perguntar de qual contrato o cliente é antes de
responder. **Recuperação semântica traz o assunto certo; a citação da fonte é o
que impede o assunto certo do documento errado de virar uma resposta errada.**

O RAG completo, com geração, é a rota `/api/v1/perguntar`. Ela existe, e **não
entra nos critérios**: o que a aula cobra é a recuperação, ou seja, se o trecho
certo foi trazido. A redação varia com o modelo local que a sua máquina
aguenta.

```bash
python3 verificar.py --criterio 5
```

---

## Passo 5, índice e EXPLAIN (`TODO-5`)

```bash
docker compose exec -T postgres psql -U logitech -d logitech < sql/05-indice.sql
```

O arquivo roda o `EXPLAIN ANALYZE` três vezes: antes do índice, depois do
índice, e depois do índice com `enable_seqscan = off`.

**A segunda saída provavelmente continua mostrando `Seq Scan`, e está certa.**
Com poucas dezenas de linhas cabendo em uma página de memória, o planejador
calcula que varrer tudo custa menos do que caminhar por um grafo. Índice não é
obrigação: é uma opção que o banco usa quando compensa. Por isso a terceira
execução força o outro plano, para você ver `Index Scan using
trechos_embedding_hnsw` com os próprios olhos.

Duas armadilhas que este passo existe para mostrar:

1. **Vetor de comparação vindo de subconsulta não usa índice.** O índice
   precisa de um ponto de partida constante. Por isso o arquivo guarda o vetor
   em uma variável do `psql` com `\gset` e o interpola com `:'alvo'`.
2. **Classe de operadores errada não dá erro.** `vector_cosine_ops` serve ao
   `<=>`, `vector_l2_ops` serve ao `<->`. Criar com a classe errada faz nascer
   um índice que ocupa disco e que o planejador ignora, para sempre.

Registre `EXPLAIN_SEM_INDICE`, `EXPLAIN_COM_INDICE` e `TAMANHO_DO_INDICE`.

```bash
python3 verificar.py --criterio 6
```

---

## Passo 6, o servidor MCP (`TODO-6a`)

O `mcp-logitech` é o único serviço da plataforma **sem porta e sem
`GET /health`**, e isso é conteúdo, não detalhe de implantação. O transporte
padrão do MCP é o **stdio**: o cliente sobe o servidor como processo filho e
conversa por entrada e saída padrão, uma mensagem JSON por linha. Não há socket
escutando, então não há endereço para um terceiro chamar.

O protocolo é JSON-RPC 2.0, que existe desde 2010. Aqui ele é escrito à mão,
como os sockets da Aula 02, porque o protocolo é o assunto. Em produção você
usaria o SDK oficial.

Leia primeiro o bloco do **Resource**, que vem pronto, e depois escreva a
**Tool**. A distinção não é sinônimo:

| | Quem decide buscar | Tem argumento | Tem efeito |
|---|---|---|---|
| **Resource** | o cliente | não, é identificado por URI | não |
| **Tool** | o modelo | sim | pode ter |
| **Prompt** | o usuário | sim | não |

A busca é Tool, e não Resource, porque o resultado depende de um argumento que
só existe no momento da conversa. Não há URI estável para "o trecho que
responde ao que o usuário acabou de digitar".

```bash
cd mcp-logitech
npm test                       # o roteiro completo
npm test -- --verboso          # mostrando as cinco mensagens cruas
```

> **A armadilha do stdio:** nada pode ser escrito em `stdout` além de mensagens
> do protocolo. Um `console.log` de depuração corrompe o fluxo e o cliente
> desconecta com um erro de parse que não menciona o seu log. Use `registrar()`,
> que escreve em `stderr`.

A ferramenta `consultar_pedido` (`TODO-6b`) é **opcional** e não entra nos
critérios. Ela consome `GET /api/v1/pedidos/{id}/status`, a mesma rota que o
agente da Aula 08 chamava por Function Calling. O paralelo vale ser pensado: lá
a integração era escrita à mão, para aquele agente, naquele formato; aqui a
mesma rota vira uma ferramenta que qualquer cliente MCP descobre sozinho.

```bash
cd .. && python3 verificar.py --criterio 7
```

---

## Ordem de corte

Sessenta minutos, seis passos. Se o tempo apertar, corte nesta ordem, que está
fixada na ADR-008 e não é negociável em sala:

| Ordem | O que sai | Vira o quê |
|---|---|---|
| 1 | O `EXPLAIN` comparativo do Passo 5 | Demonstração do professor no projetor. O `CREATE INDEX` continua sendo tarefa |
| 2 | A segunda ferramenta do MCP (`TODO-6b`) | Leitura de casa |
| 3 | As consultas de leitura do fim do Passo 3 | Leitura de casa |

**A DDL à mão do Passo 2 e a busca por distância do Passo 4 nunca saem**, em
nenhuma hipótese. São a tese da aula: sem elas o encontro vira uma
demonstração de biblioteca.

---

## Critérios de aceitação

| # | Critério | Verificado por |
|---|---|---|
| CA-01 | As tabelas dos ORMs existem no banco e os três marcadores de leitura do Passo 1 estão preenchidos | `verificar.py --criterio 1` |
| CA-02 | Extensão `vector` ativa; schema `conhecimento` com as duas tabelas; chave estrangeira de `trechos.contrato_id` para `contratos(id)` com `ON DELETE CASCADE`; coluna `embedding` do tipo `vector(768)`; restrição única sobre `(contrato_id, ordem)` | `verificar.py --criterio 2` |
| CA-03 | 4 contratos e pelo menos 30 trechos ingeridos, **todos** com `embedding` não nulo e nenhum órfão; `TRECHOS_INGERIDOS` e `SEGUNDOS_DE_INGESTAO` preenchidos | `verificar.py --criterio 3` |
| CA-04 | As duas consultas nomeadas executam, respeitam ordem e `LIMIT`, e os pares (trecho, contrato) batem com a origem real das linhas | `verificar.py --criterio 4` |
| CA-05 | O serviço `rag` responde; a busca devolve no máximo `k` trechos, em ordem crescente de distância, cada um com o contrato de origem; **4 de 4** perguntas, uma por contrato, trazem o trecho certo entre os três primeiros | `verificar.py --criterio 5` |
| CA-06 | Índice `hnsw` sobre `embedding` com a classe `vector_cosine_ops`; `EXPLAIN_SEM_INDICE` com `Seq Scan` e `EXPLAIN_COM_INDICE` com `Index Scan` | `verificar.py --criterio 6` |
| CA-07 | O servidor MCP responde `initialize`, `tools/list`, `resources/read` e `tools/call`; a ferramenta devolve trechos **citando o contrato de origem** | `verificar.py --criterio 7` |

```bash
python3 verificar.py                # roda os sete
python3 verificar.py --criterio 4   # roda só um
python3 verificar.py --lista        # o que cada um cobra
```

O verificador **checa o banco e o serviço `rag` antes de julgar** e imprime o
resultado. Um critério que falha porque o serviço nem subiu tem conserto
diferente de um critério que falha porque falta uma linha na sua SQL, e
misturar os dois manda você procurar no lugar errado.

### O que a máquina prova, e o que fica por sua conta

| Passo | Verificado por máquina | Declarado por você |
|---|---|---|
| 1 | As tabelas `pedidos.pedidos` e `faturamento.faturas` existem | Os três marcadores de leitura. O verificador confere que há texto, não que você leu |
| 2 | Catálogo do PostgreSQL: extensão, tabelas, tipo da coluna, chave estrangeira, tipo de cascata e restrição única | `DIMENSAO_DA_COLUNA` e `O_QUE_ACONTECE_SEM_CASCATA` |
| 3 | Contagem de contratos e trechos, ausência de `embedding` nulo e de órfãos; as duas consultas executadas e comparadas com uma referência calculada na hora | `TRECHOS_INGERIDOS` e `SEGUNDOS_DE_INGESTAO` |
| 4 | Três chamadas HTTP reais ao serviço, com conferência de ordem, de `LIMIT`, da presença da fonte e do trecho esperado | `MENOR_DISTANCIA` e `O_QUE_O_ILIKE_NAO_ACHOU` |
| 5 | Definição do índice lida de `pg_indexes`, incluindo método e classe de operadores | `EXPLAIN_SEM_INDICE` e `EXPLAIN_COM_INDICE`: o verificador confere que as linhas parecem plano de execução, não que saíram da sua máquina |
| 6 | O cliente MCP sobe o servidor por stdio e exercita quatro métodos do protocolo | `POR_QUE_SEM_HEALTH` |

Nas linhas onde a máquina não prova tudo, o professor confere na correção.
Preencher com valor fabricado engana a correção, não o `verificar.py`.

---

## O verificador tem testes

```bash
python3 -m unittest discover -v
```

23 testes cobrem as funções puras: leitura de marcador, separação das consultas
nomeadas, normalização de acento e as regras de divisão do contrato em trechos.
Nenhum precisa de banco, de Docker ou de Ollama no ar.

---

## Valores de referência, medidos

Todos os números abaixo foram **medidos** na validação deste laboratório, e não
estimados. Os seus vão diferir, e é isso que `ONDE_MEDI` registra.

Medidos em **macOS arm64, Docker Desktop, Ollama rodando no host**:

| Medida | Valor |
|---|---|
| `docker compose up -d --wait` até `healthy` | 5,87 s |
| Contratos ingeridos | 4 |
| Trechos gerados | 44 |
| Ingestão completa, com o modelo já carregado | 0,82 s |
| Ingestão completa, primeira execução do dia | 2,59 s |
| Recuperação pura (`POST /api/v1/busca`) | 0,109 s |
| RAG completo (`/api/v1/perguntar`), modelo já carregado | 1,24 s |
| RAG completo, primeira chamada depois de subir o Ollama | 21,2 s |
| `recall@3` do modelo padrão, em 13 perguntas de contrato | **13 de 13** |
| Índice HNSW sobre 44 trechos, em disco | 184 kB |
| Testes do verificador | 23, todos passando |
| `verificar.py` contra o esqueleto entregue | **0 de 7** |
| `verificar.py` contra o `resgate/` | **7 de 7** |

### Duas medições que valem mais do que parecem

**A geração é a parte frágil, a recuperação não é.** A mesma pergunta, com o
mesmo acervo e o mesmo `TODO-4`, respondeu em **1,24 s** com `qwen2.5:1.5b`. Com
`qwen3.5:2b`, que é um modelo de raciocínio, a mesma chamada levou **230,7 s** e
devolveu **texto vazio**: o modelo gastou o orçamento inteiro pensando e não
chegou a redigir. A recuperação levou **0,109 s** nos dois casos e trouxe
exatamente os mesmos três trechos, do mesmo contrato, na mesma ordem.

É por isso que o critério de aceitação mede recuperação: ela não depende de qual
modelo a sua máquina aguenta. E é por isso que a rota `/api/v1/busca` existe
separada da `/api/v1/perguntar`.

**A qualidade da recuperação depende do modelo de embedding, e muito.** O modelo
padrão deste laboratório **não foi escolhido por reputação: foi escolhido
medindo**. A tabela abaixo é um `recall@3` sobre as mesmas 13 perguntas de
contrato, com resposta conhecida, no mesmo acervo de 44 trechos:

| Modelo de embedding | Dimensão | `recall@3` |
|---|---|---|
| `paraphrase-multilingual` (o padrão deste laboratório) | 768 | **13 de 13** |
| `nomic-embed-text` | 768 | 9 de 13 |
| `nomic-embed-text` com o prefixo de tarefa `search_query:` | 768 | 7 de 13 |

Duas leituras, e a segunda é a que vale levar:

- O `nomic-embed-text` é um modelo excelente, e é **treinado predominantemente
  em inglês**. O acervo aqui é contrato em português jurídico. Ele erra
  principalmente ao distinguir **qual dos quatro contratos** responde, e não ao
  achar o assunto.
- O prefixo `search_query:`, que a **documentação do próprio fornecedor
  recomenda**, piorou o resultado de 9 para 7. Seguir a recomendação sem medir
  teria deixado a recuperação pior do que não fazer nada.

A lição não é "use este modelo": é que **escolha de modelo de embedding se
resolve medindo no seu corpus**, e não lendo a documentação de quem o vende.
Você tem o acervo, as perguntas e o `verificar.py`; montar a sua própria tabela
custa uma reingestão.

Os três têm 768 dimensões, e é por isso que a troca entre eles não mexe na
coluna nem no índice:

```bash
ollama pull nomic-embed-text
LOGITECH_EMBEDDING_MODELO=nomic-embed-text python3 -m rag.ingestao
python3 verificar.py --criterio 5
```

Experimente depois da aula, e repare no que **não** muda: nem uma linha de SQL,
nem a DDL, nem o índice. Trocar o modelo custa uma reingestão porque a dimensão
coincide; se não coincidisse, custaria recriar a coluna e reindexar tudo.

---

## O ganho do índice, medido em escala

Leitura de depois do Passo 6. Com 44 trechos o índice não ganha nada, e ninguém
aqui vai fingir que ganha. O ganho aparece com volume, e ele é fácil de
reproduzir: 50.000 vetores aleatórios de 768 dimensões, gerados pelo próprio
PostgreSQL.

```sql
CREATE TABLE conhecimento.escala (id bigserial PRIMARY KEY, embedding vector(768));

INSERT INTO conhecimento.escala (embedding)
SELECT (SELECT array_agg(random())::vector FROM generate_series(1, 768))
FROM generate_series(1, 50000);

ANALYZE conhecimento.escala;

SELECT embedding AS alvo FROM conhecimento.escala ORDER BY id LIMIT 1
\gset

EXPLAIN ANALYZE SELECT id FROM conhecimento.escala
ORDER BY embedding <=> :'alvo'::vector LIMIT 5;

CREATE INDEX escala_hnsw ON conhecimento.escala
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

ANALYZE conhecimento.escala;

EXPLAIN ANALYZE SELECT id FROM conhecimento.escala
ORDER BY embedding <=> :'alvo'::vector LIMIT 5;
```

O que saiu, medido:

| Medida | Valor |
|---|---|
| Inserção dos 50.000 vetores | 3,76 s |
| Consulta **sem** índice | `Seq Scan`, **389,933 ms** |
| Construção do índice HNSW | 24,46 s |
| Consulta **com** índice | `Index Scan using escala_hnsw`, **1,005 ms** |
| Índice em disco | 161 MB |
| Tabela (heap, sem os vetores em TOAST) | 2944 kB |

**388 vezes mais rápido**, e o preço está na mesma tabela: 24 s de construção e
161 MB de disco, que é aproximadamente o tamanho dos próprios vetores
(50.000 x 768 x 4 bytes são 146 MiB). Índice não é grátis, é uma troca. E
repare que, ao contrário do que se diria, **o planejador escolheu o índice
sozinho** aqui: com 50.000 linhas a conta virou.

Apague a tabela ao terminar:

```sql
DROP TABLE conhecimento.escala;
```

---

## O `rag` como container

Durante a aula o serviço roda direto no devcontainer, porque você vai editar
`rag/busca.py` várias vezes e um `docker compose build` por tentativa custa mais
do que ensina. O caminho containerizado existe e está pronto:

```bash
docker compose --profile completo up -d --build rag
```

Repare no `extra_hosts` do serviço no Compose: o Ollama roda no host, e de
dentro de um container `localhost` é o próprio container. É a mesma armadilha
que a Aula 07 mostrou com o AI Gateway.

---

## Como entregar

**Um commit por passo concluído**, no padrão Conventional Commits:

```bash
git add docs/EVIDENCIAS.md
git commit -m "docs(passo-1): a SQL que o Hibernate e o EF Core escreveram"

git add sql/02-conhecimento.sql
git commit -m "feat(passo-2): schema conhecimento com coluna vector(768)"

git add sql/03-consultas.sql docs/EVIDENCIAS.md
git commit -m "feat(passo-3): consultas com JOIN, ORDER BY e LIMIT"

git add rag/busca.py docs/EVIDENCIAS.md
git commit -m "feat(passo-4): busca por distância de cosseno"

git add sql/05-indice.sql docs/EVIDENCIAS.md
git commit -m "feat(passo-5): índice HNSW e leitura do plano"

git add mcp-logitech/src/servidor.ts docs/EVIDENCIAS.md
git commit -m "feat(passo-6): ferramenta buscar_em_contratos no servidor MCP"

git push
```

A progressão precisa ficar visível no histórico do seu fork: seis commits, não
um único commit final com tudo dentro.

Ao terminar, submeta a **URL do seu fork** no formulário da aula.

> **Formulário:** a URL será publicada pelo professor antes da aula.

Um envio por dupla, até o fim da aula.

---

## O diretório `resgate/`

Atividade em passos tem um risco que atividade única não tem: travar no Passo 2
mata os Passos 3, 4, 5 e 6. O `resgate/` tem os cinco arquivos completos e
comentados:

```bash
cp resgate/02-conhecimento.sql sql/02-conhecimento.sql
cp resgate/03-consultas.sql    sql/03-consultas.sql
cp resgate/busca.py            rag/busca.py
cp resgate/05-indice.sql       sql/05-indice.sql
cp resgate/servidor.ts         mcp-logitech/src/servidor.ts
```

Quem usar registra `USEI_O_RESGATE` em `docs/EVIDENCIAS.md`, dizendo a partir
de qual passo. Sem penalidade automática: é informação para a correção, não
armadilha.

---

## Onde isso vai dar

O **CP3**, na semana seguinte, cobra Testes de Unidade, Frontend e RAG ou MCP
no nível deste laboratório: uma ferramenta e um recurso bem feitos, e a busca
por distância funcionando com a fonte citada.

E fica a divisão que esta aula existe para nomear: **ORM para o caminho
transacional do CRUD, SQL à mão para o que o ORM não modela**. Nesta noite, o
que ele não modela é literalmente a coluna `vector`. Não é uma escolha entre os
dois: é saber onde cada um serve, e ter aberto o `psql` pelo menos uma vez para
poder decidir.
