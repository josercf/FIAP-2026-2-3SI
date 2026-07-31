# Laboratório Prático - Aula 10

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 10, a rede de proteção e a primeira tela)

A plataforma da LogiTech tem seis serviços em quatro linguagens, sobe com um
comando desde a Aula 07 e tem um agente que age sobre ela desde a Aula 08.
Duas coisas ainda faltam, e as duas doem no mesmo lugar:

1. **Ninguém sabe se uma mudança no cálculo de frete quebrou alguma coisa.**
   A tabela comercial muda por campanha, o desconto de carga fechada foi
   negociado com o time de vendas na semana passada, e a única forma de
   conferir hoje é subir o serviço e cotar à mão. Isso não escala, e é
   exatamente o que a **pirâmide de testes** existe para resolver.
2. **O cliente da LogiTech ainda liga para o atendimento** para saber onde
   está a carga. A plataforma inteira responde JSON e não tem uma tela.

Hoje vocês resolvem as duas. E há um detalhe que amarra uma na outra: o
cálculo de frete de um pedido **consulta o serviço de Pedidos** para saber o
peso da carga. Testar isso sem subir outro processo é o assunto da noite, e é
onde Stub, Mock e Spy deixam de ser vocabulário e viram decisão de projeto.

**Atividade em dupla**, seis lacunas nomeadas, 60 minutos.

---

## O que já vem pronto, e o que vocês fazem

| Vem pronto, não é tarefa | Vocês escrevem |
|---|---|
| `servicos/pedidos/`, o serviço de Pedidos **rodando** na porta 8080 | `TODO-1`, `TODO-2` e `TODO-3`: a suíte de unidade do cotador de frete |
| `servicos/frete/app/`, o serviço da Aula 06 **resolvido**, mais o cotador que fala com Pedidos | `TODO-4` e `TODO-5`: os dois componentes React do Portal |
| `servicos/frete/tests/conftest.py`, que **bloqueia a rede** durante os testes | `TODO-6`: o teste que olha para a chamada, e não para a tela |
| `servicos/frete/tests/test_estrategias.py`, 10 testes verdes, o modelo de escrita | `docs/EVIDENCIAS.md` com os 9 marcadores preenchidos |
| `portal/`, projeto Vite com React 19 e TypeScript, dependências já instaladas | Os commits, um por lacuna |
| 7 testes de componente **já escritos e vermelhos** | |
| `verificar.py`, a mesma régua que o professor roda na correção | |

O laboratório de hoje **inverte** o das Aulas 05 e 06. Lá vocês escreviam
código de produção e recebiam os testes prontos. Aqui, no bloco de PyTest, o
código de produção está congelado e o entregável é o teste. No bloco de
React, a ordem volta ao normal: os testes vêm prontos e vermelhos, e o código
que os faz passar é seu. Isso é o ciclo do TDD visto dos dois lados.

**Nada em `servicos/` é para editar**, com uma exceção nomeada: os três
arquivos `test_cotador_*.py` dentro de `servicos/frete/tests/`. Leia
`servicos/LEIA-ME.md`.

---

## Pré-requisitos

- Fork de `josercf/mwe-2026-2-lab10-testes-react` (nunca clone direto).
- GitHub Codespaces, ou máquina local com **Python 3.12+** e **Node 22+**.

O devcontainer já traz Python, Node 22, as dependências dos dois serviços, as
dependências do portal **já instaladas** e o Ollama com o modelo local.

### Se estiver rodando fora do devcontainer

```bash
pip install -r servicos/frete/requirements.txt -r servicos/pedidos/requirements.txt
cd portal && npm install && cd ..
cp portal/.env.exemplo portal/.env
```

---

## Como conferir que está tudo de pé (antes de escrever qualquer linha)

Três terminais:

```bash
# terminal 1: o serviço de Pedidos congelado
cd servicos/pedidos && uvicorn app:app --port 8080 --reload

# terminal 2: o serviço de frete congelado
cd servicos/frete && uvicorn app.main:app --port 8000 --reload

# terminal 3: o Portal do Cliente
cd portal && npm run dev
```

```bash
curl -s http://localhost:8080/health    # {"status":"ok"}
curl -s http://localhost:8000/health    # {"status":"ok"}
```

E o portal em <http://localhost:5173>. Ele sobe mostrando os dois blocos com
o texto `TODO-4` e `TODO-5`: é assim mesmo, são as suas lacunas.

Rode a suíte de unidade uma vez, só para ver o ponto de partida:

```bash
python3 -m pytest
# 10 passed  -> os testes das estratégias, que já vêm prontos
```

---

## Os seis passos

Cada passo fecha com um commit. Rode `python3 verificar.py --criterio N` a
qualquer momento para saber exatamente o que ainda falta.

### Passo 1, `TODO-1`: o Stub (10 min)

Arquivo: `servicos/frete/tests/test_cotador_stub.py`.

Escreva no mínimo **4 testes** cobrindo as regras de valor e de prazo do
`CotadorDePedido`, com um Stub no lugar do cliente de Pedidos.

Os números da rota de referência, que a plataforma devolve de verdade:
`PED-1001` no expresso sai por **545,00 em 1 dia**; `PED-1003` no padrão sai
por **9956,24 em 5 dias**, já com o desconto de carga fechada e o dia de
pernoite.

```bash
python3 -m pytest servicos/frete/tests/test_cotador_stub.py
python3 verificar.py --criterio 1
git commit -am "test(todo-1): stub do cliente de pedidos e as regras de valor"
```

### Passo 2, `TODO-2`: o Mock (10 min)

Arquivo: `servicos/frete/tests/test_cotador_mock.py`.

Escreva no mínimo **3 testes** de interação, com `unittest.mock.Mock`. É o
passo mais importante da noite: existem regras no cotador que **nenhuma**
asserção sobre o número devolvido consegue provar.

```bash
python3 verificar.py --criterio 2
git commit -am "test(todo-2): mock verificando a colaboracao com pedidos"
```

### Passo 3, `TODO-3`: o Spy (8 min)

Arquivo: `servicos/frete/tests/test_cotador_spy.py`.

Escreva no mínimo **3 testes** com `Mock(wraps=...)` sobre a tabela de
distâncias real. A tabela é simétrica: um cotador que trocasse origem por
destino devolveria o valor certo, e só o Spy pegaria.

```bash
python3 verificar.py --criterio 3
python3 verificar.py --criterio 4
git commit -am "test(todo-3): spy sobre a tabela de distancias real"
```

### Passo 4, `TODO-4`: a tela de rastreamento (12 min)

Arquivo: `portal/src/componentes/RastreioPedido.tsx`.

Três `useState`, um `useEffect` com `[pedidoId]`, e a marcação dos três
estados. O contrato de tela está na docstring do arquivo, e os 4 testes que
o cobram já estão escritos e vermelhos em `RastreioPedido.test.tsx`.

```bash
cd portal && npx vitest run src/componentes/RastreioPedido.test.tsx && cd ..
python3 verificar.py --criterio 5
git commit -am "feat(todo-4): tela de rastreamento com useState e useEffect"
```

### Passo 5, `TODO-5`: o formulário de cotação (12 min)

Arquivo: `portal/src/componentes/CotacaoFrete.tsx`.

Formulário controlado com quatro campos, `onSubmit` chamando `cotarFrete` e a
marcação do resultado. Os 3 testes de tela já estão escritos e vermelhos.

```bash
cd portal && npx vitest run src/componentes/CotacaoFrete.tela.test.tsx && cd ..
python3 verificar.py --criterio 6
git commit -am "feat(todo-5): formulario de cotacao de frete"
```

### Passo 6, `TODO-6`: o teste que você escreve (8 min)

Arquivo: `portal/src/componentes/CotacaoFrete.chamada.test.tsx`.

Os testes do passo anterior provam que a **tela** está certa. Nenhum deles
prova que o componente **pediu** a coisa certa: o dublê responde igual de
qualquer jeito. Escreva no mínimo **2 testes** de chamada.

```bash
cd portal && npx vitest run && cd ..
python3 verificar.py --criterio 7
git commit -am "test(todo-6): o que o formulario envia pela rede"
```

### Fechamento: as evidências (10 min)

```bash
python3 -m pytest
cd portal && npx vitest run && cd ..
python3 verificar.py
git commit -am "docs(evidencias): medidas do laboratorio"
git push
```

Preencha `docs/EVIDENCIAS.md` com os valores que a **sua** execução devolveu.
O verificador roda as duas suítes e compara: número inventado não passa.

O passo 5 das evidências pede que você derrube o CORS de propósito e leia o
console do navegador. Vale os dois minutos: é o erro de frontend corporativo
que mais custa tempo de quem nunca o viu.

---

## Como o verificador avalia um teste

Nas aulas anteriores a régua era o código de vocês, e bastava executá-lo. Hoje
o entregável é o teste, e teste se avalia de um jeito só: vendo se ele reprova
código errado.

`verificar.py` copia o serviço de frete e o portal para um diretório
temporário, **estraga a cópia** com um defeito conhecido, roda a sua suíte
contra ela e exige que ela fique vermelha. A técnica tem nome, teste de
mutação, e o defeito plantado se chama mutante.

São sete mutantes, e a divisão entre eles é o conteúdo da aula:

| Mutante | O que ele estraga | Muda algum número? | Pego por |
|---|---|---|---|
| M1 | a tabela de preços do expresso | sim | Stub |
| M2 | zera o desconto de carga fechada | sim | Stub |
| M3 | remove a memória de pedido do cotador | **não** | Mock |
| M4 | inverte o fail fast da validação | **não** | Mock |
| M5 | consulta a tabela com origem e destino trocados | **não** | Spy |
| M6 | crava a modalidade enviada em `padrao` | **não** | Mock no React |
| M7 | envia o peso como texto, e não como número | **não** | Mock no React |

Cinco dos sete não mudam **nenhum** valor devolvido. É a definição
operacional da diferença entre Stub e Mock, e é ela que o CP3 cobra.

```bash
python3 verificar.py --lista    # os oito critérios e os sete mutantes
```

---

## Entregáveis

- As **6 lacunas** preenchidas, uma por commit.
- `python3 -m pytest` verde, com no mínimo **20 testes** (10 já vêm prontos).
- `npx vitest run` verde, com no mínimo **9 testes** (7 já vêm prontos).
- No mínimo **4 testes** no `test_cotador_stub.py`, **3** no
  `test_cotador_mock.py`, **3** no `test_cotador_spy.py` e **2** no
  `CotacaoFrete.chamada.test.tsx`.
- Os **7 mutantes** pegos pela sua suíte.
- `docs/EVIDENCIAS.md` com os **9 marcadores** preenchidos, entre eles
  `VALOR_EXPRESSO_PED_1001`, `VALOR_PADRAO_PED_1003`, `TESTES_PYTEST`,
  `TESTES_VITEST` e a `MENSAGEM_DE_CORS` copiada do console do navegador.
- `python3 verificar.py` imprimindo **8 de 8**.

Sobre cobertura: **este laboratório não pede número de cobertura, e é
deliberado.** Perseguir 100 por cento leva a teste de getter, que é linha
coberta sem comportamento verificado. A régua aqui é mutante pego, não linha
tocada.

---

## Critérios de aceitação

A tabela espelha, um a um, o que `verificar.py` confere.

| # | Critério | Verificado por |
|---|---|---|
| CA-01 | O Stub do `TODO-1` tem 4 testes e pega os mutantes M1 e M2 | `verificar.py --criterio 1` |
| CA-02 | O Mock do `TODO-2` tem 3 testes e pega os mutantes M3 e M4 | `verificar.py --criterio 2` |
| CA-03 | O Spy do `TODO-3` tem 3 testes e pega o mutante M5 | `verificar.py --criterio 3` |
| CA-04 | A suíte do frete verde, com no mínimo 20 testes, e o `conftest.py` que bloqueia a rede intacto | `verificar.py --criterio 4` |
| CA-05 | Os 4 testes de `RastreioPedido.test.tsx` verdes | `verificar.py --criterio 5` |
| CA-06 | Os 3 testes de `CotacaoFrete.tela.test.tsx` verdes | `verificar.py --criterio 6` |
| CA-07 | O `TODO-6` tem 2 testes e pega os mutantes M6 e M7 | `verificar.py --criterio 7` |
| CA-08 | Os 9 marcadores de `docs/EVIDENCIAS.md` preenchidos, com os números batendo com a execução | `verificar.py --criterio 8` |

```bash
python3 verificar.py             # roda os oito critérios
python3 verificar.py --criterio 2
python3 verificar.py --lista     # o que cada critério cobra
```

A tabela "o que a máquina prova e o que fica por sua conta" está no fim de
`docs/EVIDENCIAS.md`.

---

## Se o tempo apertar: ordem de corte

Sessenta minutos são apertados para seis lacunas em duas linguagens. A ordem
de prioridade, declarada antes de começar:

1. **`TODO-1` e `TODO-2`** (Stub e Mock). São a tese da aula e o que o CP3
   cobra escrevendo teste. **Não caem em hipótese nenhuma.**
2. **`TODO-4`** (a tela de rastreamento). É onde `useState`, `useEffect` e o
   array de dependências acontecem. A Aula 11 compara o Angular com isto.
3. **`TODO-5`** (o formulário). Mesma mecânica do `TODO-4`, com formulário
   controlado no lugar do efeito.
4. **`TODO-3`** (o Spy) e **`TODO-6`** (o teste de chamada em React) são os
   primeiros a ficar para casa. Os dois são curtos e o resgate deles é o mais
   fácil de estudar sozinho depois.

Terminem em casa e refaçam o push: o `verificar.py` continua sendo a mesma
régua.

---

## Como entregar

**Um commit por lacuna**, no padrão Conventional Commits, como nos exemplos
de cada passo. A progressão precisa ficar visível no histórico do fork: seis
commits e o de evidências, não um único commit final com tudo dentro.

Ao terminar, submeta a **URL do seu fork** no formulário da aula. O endereço
será publicado antes da aula no portal da disciplina.

Um envio por dupla, com os dois nomes no formulário.

---

## Sobre o contrato da plataforma

Nomes de serviço, portas, rotas e variáveis deste laboratório estão fixados na
`ADR-006` e na `ADR-008`, e **não são negociáveis**.

| Serviço | Porta | Rotas do contrato |
|---|---|---|
| `pedidos` | 8080 | `GET /health`, `GET /api/v1/pedidos`, `GET /api/v1/pedidos/{id}` |
| `frete` | 8000 | `GET /health`, `POST /api/v1/frete/cotacao` |
| `portal` | 5173 | a tela |

Endereço de serviço nunca aparece cravado no código. No Python vem de
`LOGITECH_PEDIDOS_URL`; no portal, o Vite exige o prefixo `VITE_`, então o
mesmo endereço chega como `VITE_PEDIDOS_URL` em `portal/.env`. O nome
canônico continua sendo o do contrato: quem muda é a ferramenta, não a
decisão.

`LOGITECH_CORS_ORIGINS` entrou no contrato hoje, com padrão
`http://localhost:5173,http://localhost:4200`. Vale para todo serviço que um
navegador chama.

Uma rota é acréscimo desta aula e ainda não estava na `ADR-006`:
`POST /api/v1/frete/cotacao/pedido`, que recebe `{pedidoId, modalidade}` e
delega para o `CotadorDePedido`. É a rota HTTP do caso de uso que vocês
testam hoje.

---

## Na próxima aula

A Aula 11 constrói o **painel administrativo em Angular**, com RxJS e o
padrão Observer, consumindo o serviço de Faturamento e a telemetria da frota.
A comparação é direta e é o ponto da aula: o React de hoje é uma biblioteca
que deixa você montar a arquitetura; o Angular é um framework que já vem com
ela montada. Guardem o fork, e guardem a impressão que ficou do `useEffect`:
ela vai ser cobrada lá.
