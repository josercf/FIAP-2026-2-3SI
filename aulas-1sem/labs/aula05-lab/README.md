# Laboratório Prático - Aula 05

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 5, o núcleo de negócio)

A LogiTech já sabe onde a carga está: o coletor da Aula 02 recebe telemetria, o
painel mostra, e a Aula 03 empacotou os dois em imagem Docker. Agora a empresa
precisa **cobrar** pelos fretes que já sabe fazer.

Dois contextos novos entram na plataforma:

- **Pedidos**, em Java 21 com Spring Boot 3, na porta 8080;
- **Faturamento**, em C# com .NET 8, na porta 5080.

Os dois já estão escritos, compilando, rodando e com teste de unidade verde. E
os dois estão **mal projetados de propósito**: a regra de negócio conhece o
ORM, a lista de formas de cobrança da empresa mora dentro de um `if`, e o
numerador de nota fiscal é um Singleton sem sincronização nenhuma.

Sua noite é consertar isso em seis lacunas nomeadas, sem reescrever serviço
nenhum do zero.

**Atividade em dupla**, uma entrega por dupla.

---

## O que já vem pronto, e o que vocês fazem

| Vem pronto, é modelo | Vocês escrevem |
|---|---|
| `pedidos/`, o serviço Java inteiro, compilando e com 13 testes verdes | As três lacunas `TODO-1`, `TODO-2` e `TODO-3` |
| `faturamento/`, o serviço C# inteiro, compilando e com 9 testes verdes | As três lacunas `TODO-4`, `TODO-5` e `TODO-6` |
| `servicos/`, coletor e painel das Aulas 02 e 03, congelados | Os testes do cliente CONTRATO e o de concorrência |
| `verificar.py`, com os onze critérios de aceitação | `docs/EVIDENCIAS.md`, com seis valores medidos e o ambiente da medição |
| Entidades, controladores, rotas e o contrato de porta e URL | Um commit por lacuna fechada |

Nada em `servicos/` é tarefa desta aula: está lá para a plataforma continuar
completa no seu fork e para a Aula 07 ter o que orquestrar. Detalhes em
`servicos/LEIA-ME.md`.

---

## Pré-requisitos

- Fork de `josercf/mwe-2026-2-lab05-solid-patterns` (nunca clone direto).
- GitHub Codespaces, ou máquina local com **Java 21**, **Maven**, **.NET 8 SDK**
  e Docker. O devcontainer do laboratório já traz tudo.
- A rede `logitech-net`, a **mesma que vocês criaram à mão na Aula 03**. Se ela
  não existir mais, o passo 1 recria.

Conferência rápida, antes de começar:

```bash
java -version     # 21
mvn -v            # 3.9 ou superior
dotnet --version  # 8.x
docker version
```

---

## Os oito passos

### Passo 1, subir o banco e ver os dois serviços de pé

O PostgreSQL sobe por `docker run`, na rede da Aula 03. Guardem o comando: na
Aula 07 ele vira três linhas de YAML dentro do `docker-compose.yml`.

```bash
docker network create logitech-net 2>/dev/null || true

docker run -d --name logitech-postgres --network logitech-net \
  -e POSTGRES_DB=logitech -e POSTGRES_USER=logitech -e POSTGRES_PASSWORD=logitech \
  -p 5432:5432 postgres:16-alpine

# um schema por Bounded Context: nenhum serviço lê a tabela do outro
docker exec logitech-postgres psql -U logitech -d logitech \
  -c "CREATE SCHEMA IF NOT EXISTS pedidos; CREATE SCHEMA IF NOT EXISTS faturamento;"
```

Depois, em dois terminais:

```bash
cd faturamento && dotnet run --project src/Faturamento.Api   # porta 5080
cd pedidos     && mvn spring-boot:run                         # porta 8080
```

E, em um terceiro:

```bash
curl -s localhost:8080/health && echo
curl -s localhost:5080/health && echo
python3 verificar.py --criterio 7
```

Os dois `/health` precisam devolver `{"status":"ok"}`. É neste endereço que o
`healthcheck` do Compose da Aula 07 vai bater.

### Passo 2, `TODO-1`: inverter a dependência do repositório (Java)

`PedidoService` depende de `JpaPedidoRepository`, uma classe concreta cheia de
JPA. Crie a interface `PedidoRepository` em
`pedidos/src/main/java/br/com/fiap/logitech/pedidos/dominio/`, faça
`JpaPedidoRepository` implementá-la e mude o serviço para depender da
abstração.

Olhe também o dublê de teste em `PedidoServiceTest`: hoje ele é obrigado a
**herdar** do repositório JPA e chamar `super(null)`. Depois do DIP, ele passa
a implementar a interface, e o teste deixa de saber que existe um ORM no
projeto. Essa mudança faz parte da lacuna.

```bash
cd pedidos && mvn test
python3 ../verificar.py --criterio 1
```

### Passo 3, `TODO-2`: Factory Method para os conectores (Java)

A cadeia de `if` dentro de `PedidoService.escolherConector` decide a forma de
cobrança por tipo de cliente. Mova a decisão para `ConectorFaturamentoFactory`:
o construtor recebe `List<ConectorFaturamento>` (o Spring entrega todos os
conectores anotados com `@Component` sozinho), monta o índice por
`tipoClienteAtendido()` e devolve o conector certo em `para(tipoCliente)`.
Apague o método privado antigo.

### Passo 4, `TODO-3`: um tipo de cliente novo sem tocar no serviço (Java)

O comercial fechou contrato mensal com uma rede de distribuidoras. Tipo de
cliente `CONTRATO`, meio de pagamento `FATURA_MENSAL`, valor cheio, prazo de
**30 dias**.

Escreva o conector novo, anote com `@Component`, e acrescente dois testes: um
em `ConectorFaturamentoTest` e outro em `PedidoServiceTest`, provando que um
pedido `CONTRATO` é faturado como `FATURA_MENSAL`.

O critério do Aberto/Fechado não é o teste passar: é `git diff` mostrar que
**nenhuma linha de `PedidoService` mudou** neste passo.

```bash
git diff --stat pedidos/src/main/java/br/com/fiap/logitech/pedidos/aplicacao/PedidoService.java
```

### Passo 5, `TODO-4`: Repository e injeção por construtor (C#)

O mesmo defeito do TODO-1, agora em outra linguagem: `FaturaService` depende de
`EfFaturaRepository`. Crie `IFaturaRepository` em
`faturamento/src/Faturamento.Api/Dominio/`, faça `EfFaturaRepository`
implementá-la, mude o construtor do serviço e registre a implementação no
contêiner de injeção de dependência, em `Program.cs`:

```csharp
builder.Services.AddScoped<IFaturaRepository, EfFaturaRepository>();
```

Ajuste também o dublê de teste em `FaturaServiceTests`, que hoje herda do
repositório do EF Core e chama `base(null!)`.

### Passo 6, `TODO-6`: escrever o teste que faz a corrida aparecer (C#)

Este passo vem **antes** da correção, e é o coração da aula. Em
`NumeradorNotaFiscalTests`, escreva o teste que dispara **100 emissões
concorrentes** de número de nota fiscal, conta quantos números vieram
repetidos e exige zero duplicatas.

Rode com o Singleton ainda quebrado:

```bash
cd faturamento && dotnet test
```

O teste falha, e a mensagem do xUnit mostra o número de duplicatas em
`Actual`. Registre esse número em `docs/EVIDENCIAS.md`, em
`NOTAS_DUPLICADAS_ANTES`. **Vocês acabaram de ver uma race condition
acontecer**, e não de ouvir dizer que ela existe.

> **Medição de referência.** Na preparação desta aula, com o esqueleto exatamente
> como está aqui, três execuções seguidas do teste deram **35, 41 e 44** notas
> duplicadas num macOS arm64 de 10 núcleos com .NET SDK 8.0.404, e **19**
> duplicadas num contêiner `mcr.microsoft.com/dotnet/sdk:8.0` limitado a 2
> núcleos (`docker run --cpus=2`). O número de vocês vai ser outro, e é isso que
> caracteriza uma corrida: ela depende de quando cada thread foi escalonada.

### Passo 7, `TODO-5`: tornar o Singleton thread-safe (C#)

Agora conserte os dois defeitos de `NumeradorNotaFiscal`: a criação da
instância (`Lazy<T>` ou campo `static readonly`) e o incremento do contador
(`lock` ou `Interlocked.Increment`). Rode o teste de novo, confirme que passa e
registre `NOTAS_DUPLICADAS_DEPOIS: 0`.

### Passo 8, ponta a ponta, evidências e entrega

Com os dois serviços no ar, crie um pedido de cliente `CONTRATO` e consulte a
fatura emitida. Os comandos completos estão em `docs/EVIDENCIAS.md`. Registre
`PEDIDO_ID`, `NUMERO_NOTA_FISCAL`, `TESTES_JAVA`, `TESTES_CSHARP` e `AMBIENTE`,
e rode a verificação inteira:

```bash
python3 verificar.py
```

---

## Critérios de aceitação

| # | Critério | Verificado por |
|---|---|---|
| CA-01 | Interface `PedidoRepository` existe, `JpaPedidoRepository` a implementa e `PedidoService` não cita mais o tipo concreto nem o pacote `infra` | `verificar.py --criterio 1` |
| CA-02 | `ConectorFaturamentoFactory` recebe `List<ConectorFaturamento>`, expõe `para(...)`, e `PedidoService` não instancia mais conector com `new` | `verificar.py --criterio 2` |
| CA-03 | Conector do tipo `CONTRATO` com `FATURA_MENSAL` e 30 dias, anotado com `@Component`; `PedidoService` sem nenhum literal de tipo de cliente; teste do CONTRATO em `PedidoServiceTest` | `verificar.py --criterio 3` |
| CA-04 | `IFaturaRepository` existe, `EfFaturaRepository` a implementa, `FaturaService` a recebe no construtor e ela está registrada em `Program.cs` | `verificar.py --criterio 4` |
| CA-05 | `NumeradorNotaFiscal` com criação de instância segura e incremento protegido por `lock` ou `Interlocked` | `verificar.py --criterio 5` |
| CA-06 | Teste de concorrência com 100 emissões, contagem de duplicatas com `Distinct` e `Assert` | `verificar.py --criterio 6` |
| CA-07 | `GET /health` devolvendo `200` e `{"status":"ok"}` nos dois serviços | `verificar.py --criterio 7` |
| CA-08 | `POST /api/v1/pedidos` de cliente `CONTRATO` devolvendo `201` e `FATURADO`, e `GET /api/v1/faturas/{id}` trazendo a mesma nota com `FATURA_MENSAL` | `verificar.py --criterio 8` |
| CA-09 | `mvn test` verde, com no mínimo **15** testes | `verificar.py --criterio 9` |
| CA-10 | `dotnet test` verde, com no mínimo **10** testes | `verificar.py --criterio 10` |
| CA-11 | `docs/EVIDENCIAS.md` com os seis marcadores preenchidos, `NOTAS_DUPLICADAS_ANTES` maior que zero e `DEPOIS` igual a zero | `verificar.py --criterio 11` |

```bash
python3 verificar.py                 # roda os onze critérios
python3 verificar.py --criterio 5    # roda só um
python3 verificar.py --sem-testes    # pula mvn test e dotnet test
```

> `mvn test` e `dotnet test` reconstroem os binários dos serviços por baixo dos
> processos que estão executando. Por isso os critérios que chamam os serviços
> no ar (CA-07 e CA-08) rodam **antes** dos que rodam as suítes (CA-09 e
> CA-10). Se ainda assim o CA-08 acusar `AGUARDANDO_FATURAMENTO` logo depois de
> uma bateria de testes, reinicie os dois serviços e rode
> `python3 verificar.py --criterio 8` de novo.

### O que a máquina prova, e o que fica por sua conta

| Critério | Verificado por máquina | Declarado por vocês |
|---|---|---|
| CA-01 a CA-06 | Leitura estrutural do código: a abstração existe, a implementação a declara, a regra de negócio não cita mais o tipo concreto, o teste tem a forma pedida | Se os nomes ficaram bons e se a modelagem é a melhor possível. Isso é a correção do professor |
| CA-07 e CA-08 | Chamadas HTTP reais aos dois serviços, incluindo o pedido percorrendo Java e C# | Nada |
| CA-09 e CA-10 | As duas suítes rodam de verdade, e o verificador lê o total e as falhas na saída dos comandos | Nada |
| CA-11 | Formato e faixa dos seis valores: inteiro positivo, zero, UUID, `NF-000001` | Que os números foram medidos por vocês e não inventados. O `NOTAS_DUPLICADAS_ANTES` só existe se vocês rodaram o teste antes de corrigir: o verificador não consegue voltar no tempo para conferir |

---

## Se o tempo apertar

A ordem de corte é declarada, para ninguém perder a aula inteira travado:

1. **Nunca corte os passos 6 e 7** (`TODO-6` e `TODO-5`). São o núcleo da aula
   e a resposta da terceira pergunta de verificação.
2. O primeiro a cair, se precisar, é o passo 4 (`TODO-3`): sem ele, os
   critérios CA-03, CA-08 (o pedido `CONTRATO` ponta a ponta) e CA-09 (que
   cobra os 15 testes) ficam vermelhos, e o resto continua de pé.
3. Depois dele, o passo 5 (`TODO-4`).
4. Os passos 2 e 3 (`TODO-1` e `TODO-2`) andam juntos: o Factory Method vive
   melhor num serviço que já inverteu a dependência do repositório.

Entregar seis lacunas fechadas é o alvo. Entregar quatro lacunas fechadas com
os números do Singleton medidos vale mais do que seis pela metade.

---

## Como entregar

**Um commit por lacuna fechada**, no padrão Conventional Commits:

```bash
git add pedidos/src && git commit -m "feat(todo-1): inverte a dependência do repositório de pedidos"
git add pedidos/src && git commit -m "feat(todo-2): factory method dos conectores de faturamento"
git add pedidos/src && git commit -m "feat(todo-3): cliente CONTRATO sem alterar PedidoService"
git add faturamento/src faturamento/tests && git commit -m "feat(todo-4): repository e injeção por construtor no faturamento"
git add faturamento/tests docs && git commit -m "test(todo-6): 100 emissões concorrentes expõem a corrida"
git add faturamento/src docs && git commit -m "fix(todo-5): singleton thread-safe do numerador de nota fiscal"
git push
```

A ordem importa: o commit do `TODO-6` vem **antes** do `TODO-5`, e é o
histórico do fork que mostra que vocês viram o teste falhar antes de corrigir.

Ao terminar, submetam a **URL do fork** no formulário da aula. O endereço será
publicado no portal da disciplina antes do encontro.

---

## Na próxima aula

A Aula 06 acrescenta o motor de cálculo de frete em Python e o serviço de
notificações em Node, com Strategy, Adapter e Decorator. A Aula 07 sobe os seis
serviços mais o banco e o AI Gateway com um único `docker compose up`, e é lá
que o `docker run` do PostgreSQL do passo 1 vira três linhas de YAML. Guardem o
fork.
