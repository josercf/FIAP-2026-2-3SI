# Laboratório Prático - Aula 06

## Disciplina: Microservice and Web Engineering & IT Services
**Prof.º José Romualdo | FIAP Sistemas de Informação**

### Case: LogiTech Enterprise AI Platform (Fase 6, os serviços de apoio)

Na Aula 05 vocês entregaram Pedidos em Java e Faturamento em C#, os dois com
SOLID no lugar e testes de unidade passando. Hoje entram os dois serviços de
apoio que faltam para a plataforma fechar: o **motor de cálculo de frete** em
Python e o **serviço de notificações** em Node.

E entram com três dores de negócio reais:

1. **O frete muda por campanha comercial.** Hoje a rota HTTP conhece cada
   modalidade pelo nome, numa cadeia de `if`. Toda promoção nova obriga a
   abrir a rota e acrescentar um ramo, com risco de quebrar o que já
   funcionava. **Strategy** resolve.
2. **O rastreamento da transportadora parceira responde num formato legado**
   que ninguém na LogiTech controla: campos abreviados em maiúsculas, data em
   `dd/MM/aaaa` e vocabulário de situação próprio. Deixar esse formato entrar
   no sistema é entregar o nosso código para o time deles versionar.
   **Adapter** resolve.
3. **As notificações precisam de log e de reenvio**, e o enviador de e-mail
   já está em produção com fornecedor homologado. Não dá para reescrever a
   classe: log e retentativa têm que entrar por fora. **Decorator** resolve.

**Atividade em dupla**, seis lacunas nomeadas, 60 minutos.

---

## O que já vem pronto, e o que vocês fazem

| Vem pronto, não é tarefa | Vocês escrevem |
|---|---|
| `servicos/frete/`, o serviço FastAPI **rodando** na porta 8000 | As lacunas `TODO-1`, `TODO-2` e `TODO-3` do frete |
| `servicos/notificacoes/`, o serviço Node **rodando** na porta 3001 | As lacunas `TODO-4`, `TODO-5` e `TODO-6` das notificações |
| `servicos/parceira-rastreio/`, o sistema legado da parceira, congelado | Uma **modalidade nova** de frete, sem tocar na rota |
| `servicos/notificacoes/src/enviadores.ts`, congelado e conferido por hash | `docs/EVIDENCIAS.md` com os marcadores preenchidos |
| As duas suítes de teste, já escritas e **falhando de propósito** | Os commits, um por lacuna |
| `verificar.py`, a mesma régua que o professor roda na correção | |

Os dois serviços **sobem e respondem desde o primeiro minuto**. Vocês não
escrevem serviço do zero: preenchem lacunas nomeadas, cada uma correspondendo
a uma decisão de projeto. O que muda ao longo da noite é a estrutura interna,
nunca o contrato que o cliente da API enxerga.

Os testes já vêm escritos e vermelhos. Não é engano: é a pirâmide de testes
trabalhando a favor de vocês. Cada lacuna preenchida acende um bloco de
testes, e a suíte inteira verde é o critério de aceitação.

**Não editem `servicos/notificacoes/src/enviadores.ts`.** O `verificar.py`
guarda a impressão digital do arquivo original e reprova o critério 6 se ele
mudar. Resolver log e retentativa por dentro do enviador funcionaria, e
perderia a aula inteira.

---

## Pré-requisitos

- Fork de `josercf/mwe-2026-2-lab06-apis-patterns` (nunca clone direto).
- GitHub Codespaces, ou máquina local com **Python 3.12+** e **Node 22+**.

O devcontainer já traz Python, Node, as dependências dos dois serviços e o
Ollama com o modelo local do laboratório.

### Se estiver rodando fora do devcontainer

```bash
pip install -r servicos/frete/requirements.txt
cd servicos/notificacoes && npm install && cd ../..
```

---

## Como conferir que está tudo de pé (antes de escrever qualquer linha)

Três terminais:

```bash
# terminal 1: o sistema legado da parceira
python3 servicos/parceira-rastreio/servidor.py

# terminal 2: o serviço de frete
cd servicos/frete && uvicorn app.main:app --port 8000 --reload

# terminal 3: o serviço de notificações
cd servicos/notificacoes && npm run dev
```

Confira as três sondas de saúde exigidas pela ADR-006:

```bash
curl -s http://localhost:8000/health      # {"status":"ok"}
curl -s http://localhost:3001/health      # {"status":"ok"}
curl -s http://localhost:9090/health      # {"status":"ok"}
```

E o `/docs` do FastAPI, a especificação OpenAPI que o Pydantic gera sozinho:
<http://localhost:8000/docs>.

---

## Os seis passos

Cada passo fecha com um commit. Rode `python3 verificar.py --criterio N` a
qualquer momento para saber exatamente o que ainda falta.

### Passo 1, `TODO-1`: o contrato comum das estratégias (8 min)

Arquivo: `servicos/frete/app/estrategias.py`.

Declare `EstrategiaFrete` como um `Protocol` do módulo `typing`, com o
atributo `modalidade: str` e o método
`cotar(self, distancia_km: float, peso_kg: float) -> Cotacao`.

`Protocol` descreve o formato esperado sem obrigar herança: quem tiver os
membros certos já é uma `EstrategiaFrete`. Protocolo vazio aceita qualquer
objeto e não é contrato nenhum, e é isso que o critério 1 cobra.

```bash
python3 verificar.py --criterio 1
git commit -am "feat(todo-1): EstrategiaFrete como protocolo comum"
```

### Passo 2, `TODO-2`: uma classe por algoritmo de frete (10 min)

Mesmo arquivo. Implemente `cotar` em `FreteExpresso`, `FreteEconomico` e
`FretePadrao`, seguindo a tabela de preços congelada na docstring do módulo.
A função `valor_base` já vem pronta: o exercício é a estrutura, não a
aritmética.

Na rota de referência (`SAO -> LDB`, 500 km, 100 kg) os três precisam dar
exatamente **545,00 em 1 dia**, **265,00 em 4 dias** e **380,00 em 2 dias**.

```bash
python3 -m pytest servicos/frete/tests/test_estrategias.py
python3 verificar.py --criterio 2
git commit -am "feat(todo-2): as tres modalidades como estrategias"
```

### Passo 3, `TODO-3`: o registro, e uma rota que não conhece modalidade (12 min)

Arquivos: `servicos/frete/app/registro.py` e `servicos/frete/app/main.py`.

Duas metades:

1. Em `registro.py`, registre as três modalidades com `registrar(...)`.
2. Em `main.py`, troque a cadeia de `if` por duas linhas: `obter(...)` e
   `estrategia.cotar(...)`. `KeyError` do registro vira `HTTPException(422)`.

Ao final, **nenhum nome de modalidade pode sobrar em `main.py`**. O critério
3 procura por eles no texto do arquivo.

```bash
python3 verificar.py --criterio 3
git commit -am "feat(todo-3): registro de estrategias e rota fechada para modificacao"
```

### Passo 4, `TODO-4`: o Adapter do rastreamento da parceira (10 min)

Arquivo: `servicos/notificacoes/src/adaptador.ts`.

Implemente `adaptar`, traduzindo o formato legado para o do case. A
especificação campo a campo está na documentação da classe, e os testes
cobram cada linha dela: código sem espaços, situação pela tabela com
`'desconhecido'` como saída de emergência, data para ISO, UF em maiúsculas.

Nenhum outro arquivo do serviço pode citar `COD_OBJ`, `SIT` ou `DT_ULT_MOV`.

```bash
cd servicos/notificacoes && npx vitest run tests/adaptador.test.ts && cd ../..
python3 verificar.py --criterio 4
git commit -am "feat(todo-4): adapter do rastreamento da parceira"
```

### Passo 5, `TODO-5`: `ComLog` como Decorator do enviador (10 min)

Arquivo: `servicos/notificacoes/src/decoradores.ts`.

Envolva a chamada ao enviador embrulhado com as quatro etapas descritas na
documentação da classe: `tentativa` antes, `sucesso` depois, `falha` no
`catch`, e **relançar** o erro. Decorador que engole exceção não é decorador,
é remendo: quem decide o que fazer com a falha é a camada de cima.

```bash
cd servicos/notificacoes && npx vitest run tests/decoradores.test.ts && cd ../..
python3 verificar.py --criterio 5
git commit -am "feat(todo-5): ComLog como decorator do enviador"
```

### Passo 6, `TODO-6`: `ComRetentativa` empilhado sobre o `ComLog` (10 min)

Mesmo arquivo. Transforme a chamada única em um laço de até `maxTentativas`,
devolvendo o resultado com o número da tentativa que funcionou e relançando o
último erro quando as tentativas se esgotarem.

A prova é o teste de empilhamento: um canal que falha uma vez produz, no log,
a sequência `tentativa`, `falha`, `tentativa`, `sucesso`, **e
`enviadores.ts` continua sem uma linha de log ou de retentativa**. O teste lê
o arquivo do disco para conferir isso.

```bash
cd servicos/notificacoes && npx vitest run tests/empilhamento.test.ts && cd ../..
python3 verificar.py --criterio 6
git commit -am "feat(todo-6): ComRetentativa empilhavel sobre o ComLog"
```

### Fechamento: a modalidade nova e as evidências (10 min)

Aqui o Strategy prova que valeu a pena. Acrescente uma quarta modalidade de
frete (`refrigerado`, `carga_perigosa`, a campanha comercial que quiserem):
uma classe nova em `estrategias.py`, uma linha em `registro.py`, e mais nada.

```bash
git diff --name-only          # app/main.py NÃO pode aparecer aqui
python3 -m pytest
cd servicos/notificacoes && npx vitest run && cd ../..
python3 verificar.py
git commit -am "feat(evidencias): modalidade nova e evidencias do laboratorio"
git push
```

Preencha `docs/EVIDENCIAS.md` com os valores que a **sua** execução devolveu.
O verificador executa a sua estratégia e compara: número inventado não passa.

---

## Entregáveis

- As **6 lacunas** preenchidas, uma por commit.
- `python3 -m pytest` verde, com no mínimo **30 testes**.
- `npx vitest run` verde, com no mínimo **27 testes**.
- **1 modalidade nova** de frete registrada, com `git diff --name-only` sem
  `app/main.py`.
- `docs/EVIDENCIAS.md` com **10 marcadores** preenchidos, entre eles
  `VALOR_EXPRESSO_500KM`, `VALOR_ECONOMICO_500KM` e `STATUS_ADAPTADO`, e o
  bloco do log da retentativa com as **4 linhas** na ordem certa.
- `python3 verificar.py` imprimindo **8 de 8**.

---

## Critérios de aceitação

A tabela espelha, um a um, o que `verificar.py` confere.

| # | Critério | Verificado por |
|---|---|---|
| CA-01 | `EstrategiaFrete` declara `modalidade: str` e `cotar` | `verificar.py --criterio 1` |
| CA-02 | As três estratégias devolvem 545,00/1d, 265,00/4d e 380,00/2d na rota de referência | `verificar.py --criterio 2` |
| CA-03 | As três modalidades registradas e `app/main.py` sem nome de modalidade e sem `modalidade ==` | `verificar.py --criterio 3` |
| CA-04 | `AdaptadorRastreioLegado` traduz os cinco campos, com os testes do Adapter verdes | `verificar.py --criterio 4` |
| CA-05 | `ComLog` registra tentativa, sucesso e falha, e relança o erro | `verificar.py --criterio 5` |
| CA-06 | `ComRetentativa` empilha sobre o `ComLog` e `enviadores.ts` continua com a impressão digital original | `verificar.py --criterio 6` |
| CA-07 | `pytest` com no mínimo 30 testes e `vitest` com no mínimo 27, os dois verdes | `verificar.py --criterio 7` |
| CA-08 | Modalidade nova registrada, cotando o valor declarado, sem `main.py` no diff, e o log da retentativa na ordem | `verificar.py --criterio 8` |

```bash
python3 verificar.py             # roda os oito critérios
python3 verificar.py --criterio 6
python3 verificar.py --lista     # o que cada critério cobra
```

A tabela "o que a máquina prova e o que fica por sua conta" está no fim de
`docs/EVIDENCIAS.md`.

---

## Se o tempo apertar: ordem de corte

Sessenta minutos são apertados para seis lacunas em duas linguagens. A ordem
de prioridade, declarada antes de começar:

1. **`TODO-1`, `TODO-2` e `TODO-3`** (Strategy). É o que a Aula 07 orquestra e
   o que o CP2 cobra. Não caem em hipótese nenhuma.
2. **`TODO-5` e `TODO-6`** (Decorator). O empilhamento é a prova da aula.
3. **`TODO-4`** (Adapter) e a **modalidade nova**. São os primeiros a ficar
   para casa se o relógio vencer. Terminem depois da aula e refaçam o push:
   o `verificar.py` continua sendo a mesma régua.

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
`ADR-006` e **não são negociáveis**: a Aula 07 vai orquestrar exatamente o que
vocês entregarem hoje.

| Serviço | Porta | Rotas do contrato |
|---|---|---|
| `frete` | 8000 | `GET /health`, `POST /api/v1/frete/cotacao` |
| `notificacoes` | 3001 | `GET /health`, `POST /api/v1/notificacoes` |

Endereço de serviço nunca aparece cravado no código: o rastreamento da
parceira vem de `LOGITECH_RASTREIO_PARCEIRA_URL`, com padrão
`http://localhost:9090`. Na Aula 07 essa variável passa a apontar para o nome
do serviço dentro da rede `logitech-net`, e nenhuma linha de código muda
junto. É esse o teste de que a variável estava no lugar certo.

Os serviços de Pedidos e Faturamento da Aula 05 não são necessários aqui: o
frete e as notificações não dependem deles. Os quatro se encontram no lab kit
da Aula 07, todos congelados.

---

## Na próxima aula

A Aula 07 sobe a plataforma inteira com **Docker Compose**: os quatro
serviços poliglotas, o coletor e o painel da Aula 03, o PostgreSQL e um AI
Gateway, com `healthcheck`, rede, variáveis e limites de memória. O que vocês
entregarem hoje vira três linhas de YAML lá. Guardem o fork.
