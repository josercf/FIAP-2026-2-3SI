# Evidências, Aula 05, POO, SOLID e Design Patterns

Formulário único, preenchido à medida que você fecha cada lacuna. O
`verificar.py` lê estes marcadores procurando por `MARCADOR: valor`. Não apague
o nome do marcador, não mude a grafia, e troque `PREENCHER` pelo valor real
medido na sua máquina. Um `PREENCHER` esquecido reprova o critério CA-11.

São sete marcadores no total. Seis deles o `verificar.py` confere: as duas
contagens de nota duplicada, as duas contagens de teste e os dois
identificadores do caminho ponta a ponta. O sétimo, `AMBIENTE`, é lido só pelo
professor na correção.

---

## A corrida do Singleton (TODO-5 e TODO-6)

Este é o par de números mais importante da noite, e a ordem em que você os
colhe é o exercício:

1. escreva o teste do TODO-6 **antes** de corrigir o TODO-5;
2. rode `dotnet test` com o Singleton ainda quebrado. O teste falha, e a
   mensagem do xUnit mostra quantos números vieram repetidos
   (`Assert.Equal() Failure` com o valor em `Actual`). Esse é o
   `NOTAS_DUPLICADAS_ANTES`;
3. corrija o Singleton e rode de novo. Agora o teste passa, e
   `NOTAS_DUPLICADAS_DEPOIS` é zero.

`NOTAS_DUPLICADAS_ANTES` precisa ser maior que zero: um valor zero aqui
significa que a corrida não foi observada, e o TODO-5 vira afirmação em vez de
prova. Se o teste passou de primeira, ele não está concorrente de verdade:
confira se são 100 chamadas e se elas partem juntas.

```
NOTAS_DUPLICADAS_ANTES: PREENCHER
NOTAS_DUPLICADAS_DEPOIS: PREENCHER
```

---

## As duas suítes de teste

Total de testes verdes em cada suíte, lido da última linha de cada comando:

- `cd pedidos && mvn test` termina com `Tests run: N, Failures: 0, Errors: 0`;
- `cd faturamento && dotnet test` termina com `Passed: N`.

O mínimo é 15 do lado Java e 10 do lado C#. Esses mínimos correspondem ao que
o esqueleto já trazia mais os testes que as lacunas pedem: os do cliente
CONTRATO (TODO-3) e o de concorrência (TODO-6).

```
TESTES_JAVA: PREENCHER
TESTES_CSHARP: PREENCHER
```

---

## O caminho ponta a ponta

Com os dois serviços de pé e o PostgreSQL rodando, crie um pedido de cliente
CONTRATO e consulte a fatura correspondente:

```bash
curl -s -X POST http://localhost:8080/api/v1/pedidos \
  -H 'Content-Type: application/json' \
  -d '{"cliente":"Distribuidora Sul","tipoCliente":"CONTRATO",
       "origem":"São Paulo/SP","destino":"Curitiba/PR",
       "enderecoEntrega":"Rua das Araucárias, 480",
       "pesoKg":120.0,"valor":1000.00}'

curl -s http://localhost:5080/api/v1/faturas/COLE_O_ID_AQUI
```

Registre o `id` devolvido pelo POST e o `numeroNotaFiscal` que apareceu nas
duas respostas. Se o pedido voltar com status `AGUARDANDO_FATURAMENTO`, o
serviço de Faturamento não foi alcançado: confira `LOGITECH_FATURAMENTO_URL`.

```
PEDIDO_ID: PREENCHER
NUMERO_NOTA_FISCAL: PREENCHER
```

---

## Ambiente onde você mediu

Não entra na verificação automática, e é o que permite comparar números entre
duplas: Codespaces ou máquina local, e quantos núcleos.

```
AMBIENTE: PREENCHER
```
