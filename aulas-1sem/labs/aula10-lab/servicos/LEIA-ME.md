# Os serviços congelados

**Nada nesta pasta é tarefa, com uma exceção nomeada logo abaixo.**

Aqui estão os serviços das aulas anteriores, prontos e funcionando, para que
quem faltou à Aula 05 ou à Aula 06 consiga fazer a Aula 10 do mesmo jeito.
Regra herdada da `ADR-006` e mantida pela `ADR-008`.

| Pasta | O que é | Porta | Editar? |
|---|---|---|---|
| `pedidos/` | Serviço de Pedidos, versão mínima | 8080 | Não |
| `frete/app/` | Serviço de frete, o da Aula 06 já resolvido | 8000 | Não |
| `frete/tests/` | **A sua área de trabalho de hoje** | | Sim, os três `test_cotador_*.py` |

## A exceção: `frete/tests/`

O laboratório de hoje inverte o de sempre. Nas Aulas 05 e 06 vocês escreveram
código de produção e receberam os testes prontos. Hoje o código de produção
está pronto e congelado, e o entregável é o **teste**.

Dentro de `frete/tests/`:

- `conftest.py` e `test_estrategias.py` são congelados. O primeiro bloqueia a
  rede durante os testes, o segundo é o modelo de escrita para você ler antes
  de começar.
- `test_cotador_stub.py`, `test_cotador_mock.py` e `test_cotador_spy.py` são
  seus. Estão vazios, com o enunciado na docstring.

## As duas diferenças em relação ao que vocês entregaram

Declaradas aqui para ninguém achar que é engano.

**1. CORS ligado.** `pedidos` e `frete` sobem lendo `LOGITECH_CORS_ORIGINS`,
com padrão `http://localhost:5173,http://localhost:4200`. Até a Aula 08 todo
consumidor destas APIs era outro processo de servidor, e servidor ignora a
política de mesma origem. A partir de hoje quem chama é o navegador. A
decisão está na `ADR-008`.

**2. O frete ganhou um vizinho.** `frete/app/cotador.py` e
`frete/app/cliente_pedidos.py` não existiam na Aula 06. Eles implementam o
caso de uso "cotar o frete de um pedido que já existe", que precisa perguntar
o peso ao serviço de Pedidos. É essa colaboração que dá o que testar hoje: um
teste de unidade não pode depender de outro processo no ar.

Um detalhe a mais, e ele é o coração do `TODO-3`: `distancias.py` deixou de
ser uma função de módulo e virou a classe `TabelaDistancias`, recebida no
construtor do cotador. Dependência injetada é dependência testável.

## O serviço de Pedidos não é o da Aula 05

`pedidos/app.py` está escrito em Python com FastAPI, e o serviço da Aula 05 é
Java com Spring Boot. Ele cumpre o mesmo contrato da `ADR-006` (porta 8080,
as mesmas rotas, o mesmo JSON) e serve ao mesmo propósito aqui, que é ter o
que consumir.

A troca é deliberada e tem custo declarado: exigir uma JDK dentro de um
devcontainer de Python e Node consumiria minutos do bloco prático sem ensinar
nada sobre teste de unidade nem sobre React. É o mesmo raciocínio que a
Aula 07 usou quando escreveu uma versão mínima do Pedidos para ter o que
orquestrar.

## Como subir os dois

```bash
# terminal 1
cd servicos/pedidos && uvicorn app:app --port 8080 --reload

# terminal 2
cd servicos/frete && uvicorn app.main:app --port 8000 --reload
```

```bash
curl -s http://localhost:8080/health    # {"status":"ok"}
curl -s http://localhost:8000/health    # {"status":"ok"}
```

E o `/docs` do FastAPI, a especificação OpenAPI que o Pydantic gera sozinho:
<http://localhost:8000/docs>.
