# Contratos HTTP da ArenaLog

Prefixo `/api/v1`. `GET /health` em cada serviço devolve `200` e `{"status":"ok"}`.

Entre containers o host é o nome do serviço no Compose. `localhost` só existe na sua máquina, na porta publicada.

## elenco (8081)

`POST /api/v1/atletas` → 201

```json
{ "nome": "Lia Park", "campus": "Campus Norte", "canal": "ARENA" }
```

`GET /api/v1/atletas/{id}` → 200 ou 404.

Canal aceito: `APP`, `ARENA`, `DISCORD`.

## motor-ranking (8000)

`POST /api/v1/ranking` → 200, ou 400 se a modalidade for desconhecida.

```json
{ "modalidade": "FPS", "campus": "Campus Norte", "serie": false }
```

```json
{ "pontos": 5, "faixa": "LENDARIO", "janelaHoras": 8 }
```

## partidas (8080)

`POST /api/v1/desafios` → 201. A descrição tem de 15 a 400 caracteres.

```json
{
  "atletaId": "uuid-do-elenco",
  "modalidade": "FPS",
  "descricao": "Final de FPS no palco principal, serie ouro contra o norte.",
  "campus": "Campus Norte"
}
```

Ordem: consulta o elenco, calcula a série no próprio banco, consulta o motor, grava. Atleta ausente vira 404 sem chamar o motor. Motor fora do ar vira 503 e não grava.

`GET /api/v1/desafios?campus=&status=` → 200 e uma lista. Lista vazia é `[]`.

`GET /api/v1/desafios/{id}` → 200 ou 404. O JSON não traz `nome`.

`PATCH /api/v1/desafios/{id}/status` com `{"status":"ENCERRADO"}` → 200, 409 ou 404. 409 não grava.

## placar (8082)

`GET /api/v1/resumo?campus=Campus%20Rio` → 200.

```json
{
  "campus": "Campus Rio",
  "porStatus": {
    "ABERTO": 0,
    "CONFIRMADO": 0,
    "EM_JOGO": 0,
    "ENCERRADO": 0,
    "CANCELADO": 0
  },
  "porFaixa": { "BRONZE": 0, "PRATA": 0, "OURO": 0, "LENDARIO": 2 }
}
```

Sem `nome`, `descricao`, `atletaId`, `latitude`, `longitude` ou `id`.
