# ArenaLog: a noite da Lia

Lia Park estuda no Campus Norte e joga FPS. Sexta, 19h, ela chega na arena da FIAP para a final. O sistema faz três besteiras.

1. **A ficha some.** Ela se inscreve no balcão. Uma hora depois o aplicativo diz que ela não existe. No Discord abriram outra ficha, com outro número.
2. **A faixa é chute.** Um organizador fala "isso é ouro". O colega fala "é bronze". Não existe conta. Quem grita mais alto define a prioridade.
3. **A TV entrega a Lia.** No corredor, a televisão mostra o nome dela, o texto do desafio e a coordenada do ginásio.

Vocês consertam as três coisas. Este arquivo é o roteiro. Sigam de cima para baixo. Não esperem o professor explicar o próximo passo.

Os slides da noite contam a mesma história, com a conta desenhada: `../../aulas/aula14.html`.

## O que já está pronto

Quatro programas já sobem e já conversam entre si. Vocês não criam serviço, não trocam de linguagem e não editam `verificar.py`.

| Programa | Na vida real | Arquivo que vocês trocam |
|---|---|---|
| elenco, porta 8081, Node | Guarda a ficha: nome, campus, canal. É o único que guarda o nome. | `elenco/validar.js` |
| motor-ranking, porta 8000, Python | Só faz a conta da faixa. Não tem banco. | `motor-ranking/ranking.py`, função `calcular` |
| partidas, porta 8080, Python | Abre o confronto. Pergunta se a Lia existe, pergunta a faixa, grava. Não guarda o nome. | `partidas/ciclo.py` e `partidas/serie.py` |
| placar, porta 8082, Node | A TV do corredor. Conta os jogos. Sem nome e sem mapa. | `placar/agregar.js` |

Cada programa é um computador. Dentro de partidas, `localhost` é a própria partidas. O elenco se chama `http://elenco:8081`. O motor se chama `http://motor-ranking:8000`. O placar pergunta só para `http://partidas:8080`.

O banco tem duas gavetas, `elenco` e `partidas`. Uma não lê a outra. Vocês não mexem no SQL hoje.

## Passo 0. Pegue a pasta

Na raiz do repositório, ou clonando agora:

```bash
git clone https://github.com/josercf/FIAP-2026-2-3SI.git
cd FIAP-2026-2-3SI/aulas-1sem/labs/aula14-lab
python3 verificar.py
```

Se a pasta já existir, entrem nela e façam `git pull` antes de editar.

A primeira saída tem que parecer com isto. Os nomes podem quebrar a coluna, o que importa são as marcas:

```text
1       Pasta no lugar            100  OK       Recruta
2       Elenco                    150  ABERTA   Analista
3       Conta da faixa            250  ABERTA   Estrategista
7       Testes prontos            200  OK       Maestro
TOTAL 300 / 1350 XP
FAIXA Analista
```

Missão 1 e missão 7 nascem verdes. As outras cinco estão ABERTAS: são as funções vazias. Todos os comandos abaixo rodam de dentro de `aula14-lab`.

Precisa de Python 3.11 ou mais novo e Node 22. Docker só entra no passo 6.

## A conta, antes de abrir o código

Jogo da Lia: FPS, Campus Norte, primeira vez (não é série).

| Pedaço | Por quê | Pontos |
|---|---|---:|
| FPS | todo FPS começa com 3 | 3 |
| Campus Norte | está na lista de rivais | +2 |
| Série | não existe outro FPS aberto ali | +0 |
| Total | 5 ou mais é LENDARIO, janela de 8 horas | 5 |

Ponto de partida: FPS 3, MOBA 3, LUTE 2, ESPORTE 2, CARTAS 1.

| Soma | Faixa | Janela |
|---|---|---:|
| 5 ou mais | LENDARIO | 8 h |
| 4 | OURO | 24 h |
| 2 ou 3 | PRATA | 72 h |
| 0 ou 1 | BRONZE | 168 h |

Rivais, no arquivo `motor-ranking/rivalidade.json`: Campus Norte e Campus Rio. `campus   norte` vale igual, porque a comparação ignora maiúscula e espaço repetido.

Mais dois exemplos, para não decorar só o da Lia:

- ESPORTE no Campus Rio, e já tem outro aberto: 2 + 2 + 1 = 5. LENDARIO, 8 horas.
- CARTAS no Centro, primeira vez: Centro não é rival e não é série. Sobra 1. BRONZE, 168 horas.

Série é o mesmo jogo, no mesmo campus, ainda aberto, criado há menos de 48 horas. 47 horas e 59 minutos conta. 48 horas em ponto não conta. Jogo ENCERRADO ou CANCELADO não conta. Quem decide isso é `serie.py`. O motor só recebe sim ou não.

O status não pula etapa. Nasce ABERTO. ABERTO só vai para CONFIRMADO ou CANCELADO. CONFIRMADO vai para EM_JOGO ou CANCELADO. EM_JOGO vai para ENCERRADO ou CANCELADO. ENCERRADO e CANCELADO não saem. Pular é 409 e não grava.

## Passo 1. A ficha da Lia

Abra `elenco/validar.js`. A função `validarAtleta` hoje só faz `return null`, e por isso aceita qualquer coisa.

Apaguem desde a linha `function validarAtleta` até a chave `}` que fecha essa função. Não apaguem `const CANAIS` nem a linha `module.exports`.

Colem isto no lugar:

```javascript
function validarAtleta(corpo) {
  if (!corpo || typeof corpo !== "object") return "corpo ausente";
  const nome = typeof corpo.nome === "string" ? corpo.nome.trim() : "";
  if (nome.length < 2 || nome.length > 80) return "nome invalido";
  const campus = typeof corpo.campus === "string" ? corpo.campus.trim() : "";
  if (!campus) return "campus obrigatorio";
  if (!CANAIS.has(corpo.canal)) return "canal invalido";
  return null;
}
```

`null` significa ficha aceita. Texto significa recusa. Nome de 2 a 80, campus preenchido, canal só APP, ARENA ou DISCORD.

Salvem o arquivo e rodem:

```bash
node --test elenco/test/validar.test.js
```

Querem ver `# pass 5` e `# fail 0`. São 150 XP.

## Passo 2. A faixa

Abra `motor-ranking/ranking.py`. Troquem só a função `calcular`. Não apaguem `faixa_de`, `normalizar` nem a classe `TabelaDePesos`.

A primeira linha tem que chamar `tabela.pontos_base`. É assim que o teste vê se a chave foi LUTE ou ESPORTE, já que os dois valem 2.

```python
def calcular(modalidade, campus, serie, tabela, campi_rivais):
    pontos = tabela.pontos_base(modalidade)
    if any(normalizar(nome) == normalizar(campus) for nome in campi_rivais):
        pontos += 2
    if serie:
        pontos += 1
    faixa, janela = faixa_de(pontos)
    return {"pontos": pontos, "faixa": faixa, "janelaHoras": janela}
```

Salvem e rodem:

```bash
cd motor-ranking && python3 -m unittest test_ranking.py && cd ..
```

Querem `OK` e nenhum `FAIL`. São 250 XP.

## Passo 3. O status

Abra `partidas/ciclo.py`. A tabela `ACEITOS` já está no arquivo. A função só consulta. Destino igual ao atual também recusa, porque ele não está na lista.

```python
def transicionar(atual, destino):
    if destino not in ACEITOS.get(atual, set()):
        raise TransicaoRecusada(atual, destino)
    return destino
```

```bash
cd partidas && python3 -m unittest test_ciclo.py && cd ..
```

São 150 XP. O 409 de verdade aparece no passo 6, quando o boss tentar encerrar um jogo que ainda está ABERTO.

## Passo 4. A série

Abra `partidas/serie.py`. `ABERTOS`, `normalizar` e `timedelta` já estão no arquivo. Não apaguem o import.

```python
def eh_serie(anterior, modalidade, campus, agora):
    if str(anterior.get("modalidade", "")).upper() != str(modalidade).upper():
        return False
    if normalizar(anterior.get("campus", "")) != normalizar(campus):
        return False
    if anterior.get("status") not in ABERTOS:
        return False
    return (agora - anterior["criado_em"]) < timedelta(hours=48)
```

```bash
cd partidas && python3 -m unittest test_serie.py && cd ..
```

São 200 XP. 47h59 passa. 48h00 não passa.

## Passo 5. A TV

Abra `placar/agregar.js`. Hoje a função devolve a lista inteira, com nome e coordenada. A TV só pode devolver contagem. `STATUS` e `FAIXAS` já existem. Chave zerada continua no JSON.

```javascript
function agregar(desafios, campus) {
  const porStatus = Object.fromEntries(STATUS.map((s) => [s, 0]));
  const porFaixa = Object.fromEntries(FAIXAS.map((f) => [f, 0]));
  for (const item of desafios) {
    if (porStatus[item.status] !== undefined) porStatus[item.status] += 1;
    if (porFaixa[item.faixa] !== undefined) porFaixa[item.faixa] += 1;
  }
  return { campus, porStatus, porFaixa };
}
```

O JSON final tem `campus`, cinco contagens de status e quatro contagens de faixa. Não tem `nome`, `descricao`, `atletaId`, `latitude`, `longitude` nem `id`.

```bash
node --test placar/test/agregar.test.js
```

Querem `# pass 1`. São 150 XP.

## Passo 6. Subam tudo e enfrentem o boss

Antes do Docker, o verificador já deve marcar OK nas missões 1 a 7. A 8 fica PENDENTE, e tudo bem. O total fica em 1200 XP, faixa Campeão.

```bash
python3 verificar.py
docker compose up -d --build
python3 scripts/boss.py
python3 verificar.py
```

O `compose` na primeira vez baixa imagem. Não cancelem. Quando os quatro programas e o banco estiverem `healthy`, o boss repete a noite da Lia:

1. Os quatro programas respondem que estão ok.
2. Cria a ficha: Lia Park, Campus Norte, canal ARENA.
3. CARTAS no Centro: 1, BRONZE, 168 horas, não é série, e a resposta não traz o nome.
4. FPS no Campus Norte: 5, LENDARIO, 8 horas.
5. Dois ESPORTE no Campus Rio. O segundo é série: 5, LENDARIO, 8 horas.
6. Tenta encerrar o jogo de cartas, que ainda está ABERTO. Tem que dar 409, e ele continua ABERTO.
7. Tenta abrir jogo para um id que o elenco não tem. Tem que dar 404.
8. A TV do Campus Rio mostra LENDARIO com contagem 2, sem nome e sem coordenada.

Quando o boss imprimir `BOSS: derrotado`, rodem o verificador de novo. 1350 XP é Lenda da Arena.

## Se a linha ficar vermelha

1. Leiam a primeira linha que diz `not ok` ou `FAIL`. O nome do teste diz qual caso quebrou. Voltem ao passo dessa missão e confiram se copiaram a função inteira.
2. Erro de `import` ou `CANAIS is not defined`: vocês apagaram linha de cima do arquivo. Restaurem com `git checkout -- caminho/do/arquivo` e colem só a função.
3. Boss diz que o programa não responde: o Compose ainda está baixando, ou um serviço caiu. Rode `docker compose ps` e esperem `healthy`.
4. Só depois disso abram `resgate/LEIA-ME.md`. Copiar o resgate antes de ler o erro queima a história de que a mesa resolveu.

No fim da noite, mostrem a saída de `python3 verificar.py`. Não subam `node_modules` nem `.env`.

`contratos.md` é a lista de URL, campo e código HTTP. Abram só se o boss reclamar de um campo que vocês não reconhecem.
