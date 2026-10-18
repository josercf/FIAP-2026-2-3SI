# O que está congelado aqui, e por que só isto

**Nada nesta pasta é tarefa.** Não edite estes arquivos.

Todo laboratório do curso traz, em `servicos/`, o que as aulas anteriores
entregaram, para que quem faltou a uma aula consiga fazer a seguinte. Nesta
aula o que veio de trás **não é código de serviço: é o schema do banco**.

## `orm-gerado.sql`

A saída literal de um `pg_dump --schema-only` tirada de um PostgreSQL onde os
serviços reais das Aulas 05 e 06 tinham acabado de subir:

- `pedidos.pedidos`, criada pelo Hibernate a partir de
  `spring.jpa.hibernate.ddl-auto=update`, no serviço em Java;
- `faturamento.faturas`, criada pelo EF Core a partir de
  `banco.Database.EnsureCreated()` sobre o `FaturamentoDbContext`, no serviço
  em C#.

Nenhuma linha ali foi escrita à mão. É exatamente essa a graça: o Passo 1 do
laboratório manda **ler a SQL que escreveram por você**.

O `docker-compose.yml` monta este arquivo em `/docker-entrypoint-initdb.d/`, e
o PostgreSQL o executa sozinho na primeira subida de um volume vazio.

## Por que os serviços em si não estão aqui

O único serviço de aula anterior que este laboratório consumiria é o de
**Pedidos**, e apenas pela ferramenta opcional `consultar_pedido`
(`TODO-6b` do servidor MCP), que é a primeira coisa da ordem de corte.

Aquele serviço tem as lacunas da Aula 05 em aberto no repositório dele.
Congelá-lo aqui só faria sentido com as lacunas resolvidas, e isso publicaria a
resposta de outro laboratório em um repositório que todo mundo pode abrir.

Então a regra vale, com o custo declarado: se você quiser exercitar o
`TODO-6b`, suba o **seu** fork da Aula 05 em `localhost:8080` e aponte
`LOGITECH_PEDIDOS_URL` para ele. Sem isso, a ferramenta responde com
`isError` e o motivo, que é o comportamento correto de uma ferramenta MCP cuja
dependência está fora do ar, e não uma falha do laboratório de hoje.

Os critérios de aceitação **não** incluem o `TODO-6b`.
