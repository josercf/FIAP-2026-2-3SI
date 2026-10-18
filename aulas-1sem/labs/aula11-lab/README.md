# Laboratório Prático - Aula 11

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 11, o painel de quem opera)

Na Aula 10 vocês entregaram o **Portal do Cliente em React**: a visão de quem
comprou, que rastreia um pedido e cota um frete. Hoje entra a outra metade da
plataforma, a visão de **quem opera**: o painel administrativo da sala de
controle da LogiTech.

E ele tem uma exigência que o portal não tinha. O cliente abre a página,
consulta o pedido dele e fecha. O operador da LogiTech deixa o painel aberto
**a noite inteira**, com a posição dos caminhões chegando o tempo todo, e ao
mesmo tempo consulta faturas de pedidos enquanto os caminhões continuam se
movendo. São **dois fluxos assíncronos concorrentes e contínuos**, e é isso
que separa este laboratório de "mais uma tela que chama uma API".

Três dores de negócio reais:

1. **A frota não para de emitir.** Posição de caminhão não é uma resposta que
   chega uma vez: é um fluxo que começa quando o operador abre o painel e não
   termina nunca. `Promise` resolve uma vez e acabou. `Observable` não.
2. **O operador filtra enquanto o fluxo corre.** Ele clica em `PR` e a tabela
   precisa refiltrar **na hora**, sem esperar o próximo caminhão chegar, e o
   próximo caminhão precisa respeitar o filtro que ele acabou de escolher.
   São duas fontes de verdade que precisam ser cruzadas.
3. **A consulta de fatura demora, e ele continua digitando.** Cada tecla
   dispara uma consulta que leva 800 ms. Digitar `1003` são quatro consultas
   correndo juntas, e a resposta do `100` pode chegar depois da resposta do
   `1003` e sobrescrever a tela com o dado errado. Isso tem nome: *race
   condition*. E tem operador: `switchMap`.

**Atividade em dupla**, seis lacunas nomeadas, 60 minutos.

---

## O que já vem pronto, e o que vocês fazem

| Vem pronto, não é tarefa | Vocês escrevem |
|---|---|
| `painel-admin/`, o workspace Angular 22 com dependências já instaladas | As lacunas `TODO-1` a `TODO-6` em três arquivos |
| Os componentes `FrotaComponent`, `FaturasComponent` e a casca `App` | `docs/EVIDENCIAS.md` com os marcadores preenchidos |
| `servicos/faturamento/`, C#/.NET da Aula 05, **com CORS ligado** | Os commits, um por lacuna |
| `servicos/painel/`, Node da Aula 02, com SSE e **CORS ligado** | |
| `servicos/coletor/` e `servicos/simulador/`, a telemetria da Aula 02 | |
| `subir.sh` e `derrubar.sh`, os quatro processos em um comando | |
| A suíte de 31 testes, já escrita e **vermelha de propósito** | |
| `verificar.py`, a mesma régua que o professor roda na correção | |
| `resgate/`, a rede de segurança para não travar em uma lacuna | |

Vocês **não criam projeto Angular do zero**. O painel abre e roda desde o
primeiro minuto, só que vazio: as seis lacunas são exatamente o que falta
para o dado chegar na tela.

### As duas diferenças em relação ao que vocês escreveram nas Aulas 02 e 05

Os serviços em `servicos/` são os das aulas anteriores, congelados, com uma
mudança declarada: **CORS**. Está na `ADR-008` e vale a pena entender por quê.

Até a Aula 07 todo consumidor de API na plataforma era outro processo de
servidor, e servidor ignora a política de mesma origem. A partir da Aula 10 o
consumidor é o **navegador**, e `http://localhost:4200` é outra origem que
`http://localhost:5080`: porta diferente já basta. Sem
`Access-Control-Allow-Origin` na resposta, o navegador **recebe os bytes e os
joga fora** antes de o seu código vê-los. O sintoma é uma tela vazia sem erro
de rede aparente, e é dos piores defeitos para depurar ao vivo.

A segunda mudança é no `faturamento`: ele demora **800 ms de propósito** e
conta quantas consultas o cliente abandonou no meio. É o instrumento de
medição da aula.

---

## Pré-requisitos

- Fork de `josercf/mwe-2026-2-lab11-angular-rxjs` (nunca clone direto).
- GitHub Codespaces, ou máquina local com **Node 22+**, **.NET 8** e
  **Python 3.12+**.

O devcontainer já traz tudo instalado, incluindo o `npm ci` do Angular e o
`dotnet build` do Faturamento. `npm install` de um workspace Angular dentro do
bloco prático não caberia nos 60 minutos, e por isso ele roda na criação do
container.

### Se estiver rodando fora do devcontainer

```bash
cd painel-admin && npm ci && cd ..
dotnet build servicos/faturamento
```

---

## Como conferir que está tudo de pé (antes de escrever qualquer linha)

```bash
bash subir.sh
```

Ele sobe os quatro processos congelados e espera as sondas de saúde
responderem:

```
coletor      UDP 8081, TCP 8080, HTTP 8082   telemetria da Aula 02
simulador    emite posições por UDP           a frota fingindo existir
painel       HTTP 3000                        SSE que o Angular consome
faturamento  HTTP 5080                        C#/.NET da Aula 05
```

Confira as três sondas exigidas pelo contrato da plataforma:

```bash
curl -s http://localhost:8082/health   # {"status": "ok", "servico": "coletor", ...}
curl -s http://localhost:3000/health   # {"status":"ok","servico":"painel", ...}
curl -s http://localhost:5080/health   # {"status":"ok","servico":"faturamento", ...}
```

E confira o CORS, que é o que muda nesta fase:

```bash
curl -s -D- -o /dev/null -H "Origin: http://localhost:4200" \
  http://localhost:3000/api/v1/posicoes | grep -i access-control
```

Se `Access-Control-Allow-Origin: http://localhost:4200` não aparecer, pare: o
painel nunca vai funcionar, e o problema não está no seu código.

Agora suba o painel administrativo:

```bash
cd painel-admin && npm start
```

E abra <http://localhost:4200>. A tela monta, e está **vazia**. É assim que
tem que estar.

Ao terminar a noite: `bash derrubar.sh`.

---

## As seis lacunas

Cada passo fecha com um commit. Rode `python3 verificar.py --criterio N` a
qualquer momento para saber exatamente o que ainda falta.

| Lacuna | Arquivo | Assunto |
|---|---|---|
| `TODO-1a` | `faturas/faturamento.service.ts` | `providedIn: 'root'` |
| `TODO-1b` | `app.config.ts` | `provideHttpClient(withInterceptors([...]))` |
| `TODO-2` | `frota/frota.service.ts` | `new Observable` sobre SSE, com teardown |
| `TODO-3` | `frota/frota.service.ts` | `scan` e `map` |
| `TODO-4` | `frota/frota.service.ts` | `filter` e `map` |
| `TODO-5` | `frota/frota.service.ts` | `BehaviorSubject` e `combineLatest` |
| `TODO-6` | `faturas/faturamento.service.ts` | `debounceTime`, `distinctUntilChanged`, `switchMap` |

### Passo 1, `TODO-1`: quem entrega o quê (8 min)

Duas metades, as duas sobre Injeção de Dependência.

1. Em `faturamento.service.ts`, complete o decorador com
   `@Injectable({ providedIn: 'root' })`. Sem isso, o `inject(FaturamentoService)`
   do componente estoura `NullInjectorError` e a tela inteira não monta.
2. Em `app.config.ts`, acrescente
   `provideHttpClient(withInterceptors([interceptadorDeCorrelacao]))`.
   O interceptador já está escrito em `nucleo/correlacao.ts`: ele carimba toda
   requisição com `X-Correlation-Id`, que é o que permite achar, no log do
   serviço em C#, exatamente a requisição que o painel disparou.

Repare no formato do interceptador: recebe a requisição e o próximo elo,
devolve o que o próximo devolver, e faz o que quiser no meio. É o **Decorator
da Aula 06**, aplicado à cadeia HTTP.

```bash
python3 verificar.py --criterio 1
git commit -am "feat(todo-1): servico no injetor raiz e cadeia http com correlacao"
```

### Passo 2, `TODO-2`: o Observable escrito à mão (12 min)

Arquivo: `frota/frota.service.ts`, método `criarFluxoDeEventos`.

Devolva um `new Observable<Posicao>(...)` que abre a fonte de eventos,
inscreve um ouvinte em `'posicao'`, chama `inscrito.next(JSON.parse(evento.data))`
a cada mensagem, e **devolve uma função de teardown que fecha a fonte**.

O teardown é a metade que todo mundo esquece e é a metade que importa: sem
ele, cada componente destruído deixa uma conexão SSE viva no servidor. O
`GET /health` do painel mostra isso ao vivo, no campo `sse_assinantes`.

```bash
python3 verificar.py --criterio 2
git commit -am "feat(todo-2): observable sobre o sse, com teardown"
```

### Passo 3, `TODO-3`: de evento avulso para fotografia (8 min)

Mesmo arquivo, método `montarFrota`. Encadeie
`scan(acumularPorPlaca, new Map())` e `map(ordenarPorPlaca)` sobre
`this.eventos$`.

`scan` é o `reduce` que não espera o fim. Num fluxo que nunca termina, um
`reduce` jamais emitiria coisa alguma, e é por isso que ele não serve aqui.

A tabela de frota acende na tela. É o primeiro dado do laboratório.

```bash
python3 verificar.py --criterio 3
git commit -am "feat(todo-3): fotografia da frota com scan e map"
```

### Passo 4, `TODO-4`: o fluxo de alertas (8 min)

Mesmo arquivo, método `montarAlertas`. `filter` decide **se** o valor segue,
`map` decide **como** ele segue: `Posicao` acima de 90 km/h vira `Alerta`, e
`velocidade_kmh` (o vocabulário do rastreador) vira `velocidadeKmh` (o
vocabulário da tela).

```bash
python3 verificar.py --criterio 4
git commit -am "feat(todo-4): alertas de velocidade com filter e map"
```

### Passo 5, `TODO-5`: cruzar dois fluxos (12 min)

Mesmo arquivo, duas metades.

1. Troque o `Subject` do filtro de UF por um `BehaviorSubject<string>`
   iniciado em `UF_TODAS`. `Subject` puro não guarda valor: quem se inscreve
   depois da última emissão fica esperando a próxima, e como o filtro só muda
   quando o operador clica, o painel abriria vazio e continuaria vazio.
2. Em `montarFrotaFiltrada`, cruze `this.frota$` com `this.filtroUf$` usando
   `combineLatest`.

`combineLatest` reemite quando **qualquer** um dos dois emite, sempre com o
último valor de cada. É isso que faz o clique em `PR` refiltrar na hora, e o
caminhão novo respeitar a UF já escolhida.

```bash
python3 verificar.py --criterio 5
git commit -am "feat(todo-5): filtro de uf com behaviorsubject e combinelatest"
```

### Passo 6, `TODO-6`: a busca sem corrida (12 min)

**Antes de tocar no código, meça o "antes".** O que está no esqueleto funciona
e está errado de propósito, e essa medição é entregável:

```bash
curl -X POST http://localhost:5080/api/v1/metricas/zerar
# no painel, digite 1003 tecla a tecla, com meio segundo entre elas
curl -s http://localhost:5080/api/v1/metricas
```

Anote `consultasRecebidas`, `consultasConcluidas` e `consultasCanceladas` em
`ANTES_*` no formulário de evidências.

Agora reescreva o encadeamento de `consultar`, nesta ordem:

```
map(termo => termo.trim())
debounceTime(ESPERA_DE_DIGITACAO_MS)
distinctUntilChanged()
filter(termo => termo.length > 0)
switchMap(termo => this.buscarUma(termo))
```

Repita a medição e anote em `DEPOIS_*`. Abra também a aba **Rede** do
navegador: as requisições canceladas aparecem com status `(canceled)`.

Na execução de referência deste kit, o mesmo roteiro deu **4 recebidas, 4
concluídas e 0 canceladas** antes, e **4 recebidas, 1 concluída e 3
canceladas** depois. Os seus números podem ser outros; o que não pode mudar é
o sinal: `switchMap` cancela, `mergeMap` não.

```bash
python3 verificar.py --criterio 6
git commit -am "feat(todo-6): busca em tempo real com switchmap"
```

### Fechamento: as evidências (10 min)

```bash
cd painel-admin && npx ng test --watch=false && npx ng build && cd ..
python3 -m pytest tests/
python3 verificar.py
git commit -am "feat(evidencias): medicoes do laboratorio"
git push
```

Preencha `docs/EVIDENCIAS.md` com os valores que a **sua** execução devolveu.
O verificador confere a coerência entre eles e aborta uma consulta de verdade
contra o serviço de Faturamento para provar que o instrumento funciona:
número inventado não passa.

---

## Entregáveis

- As **6 lacunas** preenchidas, uma por commit.
- `npx ng test --watch=false` verde, com no mínimo **31 testes**.
- `npx ng build` concluindo, com o **Initial total** anotado.
- `python3 -m pytest tests/` verde, com no mínimo **14 testes**.
- `docs/EVIDENCIAS.md` com os **13 marcadores** preenchidos, entre eles
  `SSE_ASSINANTES_PAINEL_FECHADO` e o par `ANTES_CANCELADAS` /
  `DEPOIS_CANCELADAS`.
- `python3 verificar.py` imprimindo **8 de 8**.

---

## Critérios de aceitação

A tabela espelha, um a um, o que `verificar.py` confere.

| # | Critério | Verificado por |
|---|---|---|
| CA-01 | `FaturamentoService` no injetor raiz e `HttpClient` com o interceptador de correlação | `verificar.py --criterio 1` |
| CA-02 | `criarFluxoDeEventos` devolve um `new Observable` que abre a fonte e a fecha no teardown | `verificar.py --criterio 2` |
| CA-03 | `montarFrota` acumula por placa com `scan` e vira lista com `map` | `verificar.py --criterio 3` |
| CA-04 | `montarAlertas` usa `filter` no limite e `map` na tradução | `verificar.py --criterio 4` |
| CA-05 | O filtro de UF é `BehaviorSubject` e cruza com a frota por `combineLatest` | `verificar.py --criterio 5` |
| CA-06 | `consultar` usa `debounceTime`, `distinctUntilChanged` e `switchMap`, e nenhum `mergeMap` | `verificar.py --criterio 6` |
| CA-07 | Suíte inteira verde com no mínimo 31 testes, e `ng build` concluindo | `verificar.py --criterio 7` |
| CA-08 | Evidências coerentes entre si, e cancelamento provado ao vivo contra o serviço | `verificar.py --criterio 8` |

```bash
python3 verificar.py             # roda os oito critérios
python3 verificar.py --criterio 6
python3 verificar.py --lista     # o que cada critério cobra
```

O critério 8 precisa do serviço de Faturamento no ar: ele aborta uma consulta
de verdade e confere que o contador subiu.

A tabela "o que a máquina prova e o que fica por sua conta" está no fim de
`docs/EVIDENCIAS.md`.

---

## Se o tempo apertar: ordem de corte

Sessenta minutos são apertados para seis lacunas. A ordem de prioridade,
declarada antes de começar:

1. **`TODO-1`, `TODO-2` e `TODO-3`.** São a espinha: sem eles nenhum dado
   chega à tela e a aula não aconteceu. Não caem em hipótese nenhuma.
2. **`TODO-6`.** É a Pergunta de Verificação 3 e o que o CP3 cobra. Se
   precisar escolher entre o `TODO-6` e os dois de baixo, faça o `TODO-6`.
3. **`TODO-5`.** O filtro é bonito e é o segundo em importância conceitual,
   porque `combineLatest` é o primeiro cruzamento de fluxos do curso.
4. **`TODO-4`.** O fluxo de alertas é o primeiro a ficar para casa: `filter` e
   `map` são os dois operadores mais simples do dia, e são os que vocês
   conseguem terminar sozinhos depois.

Terminem em casa e refaçam o push: o `verificar.py` continua sendo a mesma
régua.

E se travarem numa lacuna, usem o `resgate/` em vez de perder a noite. Leiam
`resgate/README.md` primeiro.

---

## Como entregar

**Um commit por lacuna**, no padrão Conventional Commits, como nos exemplos de
cada passo. A progressão precisa ficar visível no histórico do fork: seis
commits e o de evidências, não um único commit final com tudo dentro.

Ao terminar, submeta a **URL do seu fork** no formulário da aula. O endereço
será publicado antes da aula no portal da disciplina.

Um envio por dupla, com os dois nomes no formulário.

---

## Sobre o contrato da plataforma

Nomes de serviço, portas, rotas e variáveis deste laboratório estão fixados na
`ADR-006` e na `ADR-008`, e **não são negociáveis**.

| Serviço | Container | Porta | Rotas do contrato |
|---|---|---|---|
| Painel administrativo | `painel-admin` | 4200 | consome, não expõe |
| `painel` | `painel` | 3000 | `GET /health`, `GET /api/v1/posicoes`, `GET /api/v1/eventos` |
| `faturamento` | `faturamento` | 5080 | `GET /health`, `POST /api/v1/faturas`, `GET /api/v1/faturas/{pedidoId}` |
| `coletor` | `coletor` | 8081/udp, 8080/tcp, 8082 | `GET /health`, `GET /telemetria` |

O `faturamento` ganhou duas rotas nesta aula, `GET /api/v1/metricas` e
`POST /api/v1/metricas/zerar`, que existem para o laboratório ter como medir o
cancelamento. Elas não fazem parte do contrato da plataforma.

Endereço de serviço nunca aparece cravado no meio do código. No Angular a
configuração de ambiente é **arquivo**, não variável de processo: o navegador
não tem `process.env`, e o que existisse ali estaria no bundle de qualquer
forma. Os nomes canônicos do contrato viram campos de
`painel-admin/src/app/nucleo/ambiente.ts`, e é esse arquivo que muda quando o
painel sai do `localhost` e entra no Compose.

---

## Na próxima aula

A Aula 12 leva a plataforma do relacional ao vetorial: `psql` dentro do
container, DDL à mão para um schema novo, `JOIN`, e então busca semântica com
`pgvector` entrando como **mais um `ORDER BY`**. Depois, um servidor **MCP**
expondo a API de Pedidos para agentes parceiros.

Guardem o fork. O painel de hoje é o que o CP3 cobra junto com o portal da
Aula 10.
