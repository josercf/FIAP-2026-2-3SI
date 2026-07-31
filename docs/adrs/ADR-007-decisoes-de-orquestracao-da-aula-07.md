# ADR-007: Decisões de orquestração e do AI Gateway na Aula 07

- **Data:** 2026-07-31
- **Status:** Aceita
- **Decisores:** Prof. José Romualdo da Costa Filho

## Contexto

A construção do laboratório da Aula 07 subiu os oito serviços da plataforma de
verdade e, no caminho, tomou quatro decisões que não estavam previstas na
`ADR-006` e que mudam o comportamento do que o aluno roda. Três delas nasceram
de defeitos reais observados na subida, não de preferência de estilo. Uma quinta
decisão, sobre quais serviços o Compose orquestra por padrão, tem custo
pedagógico e precisa ficar registrada.

## Decisão

### 1. Healthcheck usa `127.0.0.1`, nunca `localhost`

Com `localhost` no `healthcheck`, **quatro dos oito serviços ficaram
`unhealthy`** numa subida limpa. Dentro das imagens Alpine o `localhost` resolve
primeiro para `::1` (IPv6), enquanto os serviços escutam em IPv4. Todo
`healthcheck` do Compose passa a usar `127.0.0.1`, e o `docker-compose.yml` traz
o comentário explicando o porquê, porque é armadilha que o aluno vai reencontrar
fora da aula.

### 2. Rede e volume de telemetria são `external`; o volume do banco é gerenciado

`logitech-net` e `logitech-telemetria` foram criados à mão na Aula 03 e entram no
Compose como `external`. É o reencontro deliberado: o aluno vê o recurso que ele
criou por comando ser referenciado, e não recriado, pelo orquestrador. Já o
volume do banco (`logitech-postgres`) nasce na Aula 07 e é declarado no próprio
Compose, para o aluno ver as duas formas.

Consequência operacional: o `post-create.sh` do laboratório precisa criar a rede
e o volume herdados, senão o `compose up` falha com mensagem obscura.

### 3. Nenhum serviço declara `container_name`

Deixar o Compose nomear os containers pelo projeto evita colisão com containers
soltos da mesma plataforma. Isso não é hipótese: durante a construção, o
PostgreSQL que a Aula 05 sobe por `docker run` colidiu de fato com o do Compose.
`container_name` fixo transformaria isso em erro travado; sem ele, os dois
convivem.

### 4. O cache do AI Gateway usa similaridade lexical, declarada como aproximação

A pergunta de verificação 3 da aula é sobre **caching semântico**, que se faz com
embeddings e distância vetorial. O gateway do laboratório implementa duas
camadas: acerto exato e similaridade lexical de Jaccard sobre a pergunta
normalizada.

Isso é uma **aproximação, e é dito ao aluno como tal**: Jaccard acerta paráfrase
com vocabulário parecido e erra paráfrase com vocabulário diferente, que é
exatamente onde o embedding ganha. O caching semântico de verdade chega na
Aula 12, com `pgvector`, e o slide aponta para lá. Implementar embedding aqui
exigiria modelo de embedding no laboratório de Compose, deslocando o foco da
aula.

### 5. O Compose orquestra serviços mínimos por padrão, com caminho de troca

Os quatro serviços de negócio no kit da Aula 07 (`pedidos`, `faturamento`,
`frete`, `notificacoes`) são versões **mínimas**: obedecem às rotas e portas da
`ADR-006`, mas não têm os padrões de projeto que as Aulas 05 e 06 ensinam.

O motivo é tempo de aula. Os serviços reais são Spring Boot e .NET, e
conteinerizá-los acrescenta build de Maven e de NuGet ao laboratório. Com os
mínimos, o build dos sete serviços leva 31,7 s e a plataforma fica saudável em
11,9 s, o que cabe nos 60 minutos.

O custo é real e não se esconde: a promessa da espiral é o aluno orquestrar **o
que ele mesmo construiu**. Por isso o kit traz um **caminho de troca testado**:
Dockerfiles multi-stage para os quatro serviços reais e um
`docker-compose.override.yml` que os coloca no lugar dos mínimos. Quem completou
as Aulas 05 e 06 troca e vê a própria implementação subir; quem não completou
segue com os mínimos e não fica travado.

Efeito colateral bem-vindo: escrever esses Dockerfiles é o reencontro direto do
multi-stage da Aula 03, agora sobre Java e C#.

## Motivações

- Defeito observado vale mais que preferência: as decisões 1, 2 e 3 vieram de
  falha reproduzida, e cada uma virou comentário no arquivo que o aluno lê.
- Aproximação declarada é honesta; aproximação silenciosa ensina errado.
- Um laboratório que não termina no tempo não ensina orquestração nenhuma.

## Riscos conhecidos

| Risco | Mitigação |
|---|---|
| O aluno acha que o serviço mínimo é o "certo" e descarta o que fez nas Aulas 05 e 06 | O README e o slide dizem o contrário, e o caminho de troca é parte do kit, não apêndice |
| O caminho de troca apodrecer, porque não é o caminho padrão | O `verificar.py` julga pelo contrato, que é o mesmo nos dois caminhos |
| Jaccard ser lembrado como "caching semântico" | O slide nomeia a limitação e aponta a Aula 12 |
| A rede e o volume `external` faltarem na máquina do aluno | O `post-create.sh` os cria; o erro do Compose sem eles é obscuro e está documentado no README |

## Consequências

**Positivas**
- O laboratório sobe em tempo de aula e ainda assim permite orquestrar o código
  real de quem acompanhou o módulo.
- Três armadilhas de produção (IPv6 no healthcheck, colisão de nome de
  container, conexão única que expira) viraram conteúdo, com o número medido.

**Negativas**
- Dois caminhos para manter no mesmo kit.
- O caminho padrão entrega menos espiral do que o ideal, e isso só é compensado
  se o professor mencionar a troca em sala.

## ADRs relacionadas

- `ADR-002`: origem da dívida da passagem por arquivo entre coletor e painel,
  paga no passo 3 deste laboratório.
- `ADR-005`: fim do GitHub Models, que define o provedor local do gateway.
- `ADR-006`: o contrato da plataforma que as duas versões dos serviços obedecem.
