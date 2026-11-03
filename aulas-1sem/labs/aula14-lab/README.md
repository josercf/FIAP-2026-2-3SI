# Dojo ArenaLog

Noite de quem apareceu. A ArenaLog ranqueia confrontos de e-sports universitário. Quatro serviços, um banco, uma faixa. Quem fecha missão ganha XP. Quem fecha o boss entra no ranking da sala.

O mini-mundo é este: o atleta abre o confronto pelo aplicativo, na arena ou pelo Discord, e o pedido se perde entre os canais. A faixa vira a opinião de quem atendeu. O placar do campus, que deveria ser público, sai com nome, texto livre e coordenada. A malha abaixo separa essas responsabilidades.

## Mapa de missões

| Missão | O que fecha | XP | Medalha | Onde |
|---|---|---:|---|---|
| 1 | Malha declarada no Compose | 100 | Recruta | `docker-compose.yml`, `db/init.sql` |
| 2 | Elenco recusa atleta inválido | 150 | Analista | `elenco/validar.js` |
| 3 | Strategy de faixa, com Spy | 250 | Estrategista | `motor-ranking/ranking.py` |
| 4 | Ciclo de vida e o 409 | 150 | Juiz | `partidas/ciclo.py` |
| 5 | Série dentro de 48 horas | 200 | Cronista | `partidas/serie.py` |
| 6 | Placar sem dado pessoal | 150 | Narrador | `placar/agregar.js` |
| 7 | Stub e Mock da orquestração | 200 | Maestro | `partidas/test_dubles.py` (já verde: não quebre) |
| 8 | Boss fight com a malha no ar | 150 | Campeão | `scripts/boss.py` |

1350 XP é Lenda da Arena. Dá para chegar longe sem o boss; o boss é a luta ao vivo.

## Pré-requisitos

Docker com Compose, Python 3.11+ e Node 22. As missões 2 a 7 não precisam de container: são teste de unidade, com o Compose derrubado.

## Subir

```bash
cd aulas-1sem/labs/aula14-lab
docker compose up -d --build
python3 verificar.py
```

Portas na sua máquina: elenco `8081`, motor `8000`, partidas `8080`, placar `8082`. Postgres fica só na rede do Compose.

Entre containers a URL é `http://elenco:8081`, `http://motor-ranking:8000`, `http://partidas:8080`. `localhost` nessa URL aponta para o próprio container e a chamada morre.

## Os quatro serviços

| Serviço | Linguagem | Porta | Persistência | Fala com |
|---|---|---:|---|---|
| `elenco` | Node | 8081 | schema `elenco` | ninguém |
| `motor-ranking` | Python | 8000 | nenhuma | ninguém |
| `partidas` | Python | 8080 | schema `partidas` | `elenco` e `motor-ranking` |
| `placar` | Node | 8082 | nenhuma | `partidas` |

Dois schemas, dois usuários, sem grant cruzado. A URL do schema `elenco` só existe no elenco. A URL do schema `partidas` só existe em partidas. O motor e o placar sobem sem variável de banco. O placar não conhece a URL do elenco.

Contratos com exemplo de request e response: `contratos.md`.

## O que você escreve

A orquestração (`partidas/orquestrar.py` e os servidores HTTP) já chama os vizinhos na ordem certa. As cinco funções abaixo nascem abertas.

1. `elenco/validar.js`: nome de 2 a 80, campus obrigatório, canal `APP`, `ARENA` ou `DISCORD`.
2. `motor-ranking/ranking.py`, função `calcular`. A `TabelaDePesos` já existe. Consulte a chave da modalidade nela. Rivalidade (`rivalidade.json`: Campus Norte e Campus Rio) soma 2. Série soma 1. A comparação do campus ignora maiúsculas e espaços repetidos.

| Pontos | Faixa | Janela |
|---|---|---:|
| 5 ou mais | LENDARIO | 8 h |
| 4 | OURO | 24 h |
| 2 ou 3 | PRATA | 72 h |
| 0 ou 1 | BRONZE | 168 h |

| Modalidade | Pontos-base |
|---|---:|
| FPS | 3 |
| MOBA | 3 |
| LUTE | 2 |
| ESPORTE | 2 |
| CARTAS | 1 |

LUTE e ESPORTE valem o mesmo de propósito. O número sozinho não revela a chave. O Spy revela.

3. `partidas/ciclo.py`: `ABERTO` só vai para `CONFIRMADO` ou `CANCELADO`; `CONFIRMADO` para `EM_JOGO` ou `CANCELADO`; `EM_JOGO` para `ENCERRADO` ou `CANCELADO`. `ENCERRADO` e `CANCELADO` não saem. Destino igual ao atual também recusa. Recusa é 409 e não grava.
4. `partidas/serie.py`: mesmo modalidade e campus, status ainda aberto (`ABERTO`, `CONFIRMADO`, `EM_JOGO`), criado há menos de 48 horas. 47h59 conta. 48h00 não conta.
5. `placar/agregar.js`: conte `porStatus` e `porFaixa`. As chaves existem mesmo zeradas. Não deixe passar `nome`, `descricao`, `atletaId`, `latitude`, `longitude` nem `id`.

## Stub, Mock e Spy

Os testes já têm o dublê no nome. Rode com o Compose derrubado.

| Teste | O que o dublê segura |
|---|---|
| `stub_elenco_inexistente_nao_chama_motor` | elenco responde ausente; o motor registra zero chamadas; o repositório não recebe insert |
| `stub_motor_indisponivel_nao_persiste` | o motor falha; o repositório não recebe insert |
| `mock_motor_recebe_serie_true` | o repositório diz que há série; o mock exige um único ranking com `serie: true` |
| `mock_modalidade_invalida_nao_chama_motor` | modalidade fora da lista; zero chamadas ao motor e zero inserts |
| `spy_lute_consulta_a_propria_chave` | Spy sobre a `TabelaDePesos` real; a chave é `LUTE`; a base, sem rivalidade e sem série, é 2 |
| `spy_esporte_consulta_a_propria_chave` | a chave é `ESPORTE`; a base também é 2 |
| `resumo_publico_nao_expoe_dado_pessoal` | a lista traz nome, descrição, atleta e coordenada; o resumo não tem essas chaves |
| `stub_janela_47h59_conta_48h00_nao` | relógio injetado; 47h59 conta, 48h00 não conta |

## Boss

Com a malha no ar e as cinco funções fechadas:

```bash
python3 scripts/boss.py
```

O roteiro cria a atleta Lia Park, abre CARTAS no Centro, FPS no Campus Norte, dois ESPORTE no Campus Rio, recusa pular de `ABERTO` para `ENCERRADO`, recusa atleta inexistente e lê o placar do Campus Rio sem dado pessoal.

## O que mostrar no fim da noite

O grupo mostra a saída de `python3 verificar.py` e os arquivos que mudou: `validar.js`, `ranking.py`, `ciclo.py`, `serie.py`, `agregar.js`. Não suba `node_modules` nem `.env`.

Se a mesa travar depois do intervalo, `resgate/LEIA-ME.md` tem a cópia resolvida. Abrir antes da primeira tentativa queima a medalha da mesa, não a do verificador.

Slides da noite: `../../aulas/aula14.html`.
