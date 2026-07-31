# `keycloak/` - o realm importado de arquivo

O `realm-logitech.json` desta pasta é montado em
`/opt/keycloak/data/import` e lido pelo `start-dev --import-realm`.

**Não escreva comentário dentro do JSON.** O importador do Keycloak desserializa
o arquivo em `RealmRepresentation` com campo desconhecido proibido: uma chave a
mais, ainda que chamada `_comentario`, derruba a subida inteira com

```
ERROR: Failed to run import
ERROR: Unrecognized field "_comentario" (class ...RealmRepresentation),
       not marked as ignorable
```

Esse erro aconteceu de verdade na construção deste laboratório, em 31/07/2026, e
é a razão de esta explicação estar aqui, em Markdown, e não lá dentro.

## O que o arquivo declara (ADR-009)

| Item | Valor |
|---|---|
| Realm | `logitech` |
| Papéis de realm | `ADMIN`, `MOTORISTA`, `CLIENTE` |
| Client do Portal React | `logitech-portal`, público, PKCE S256, `http://localhost:5173/*` |
| Client do Painel Angular | `logitech-painel-admin`, público, PKCE S256, `http://localhost:4200/*` |
| Validade do access token | 900 s |

Usuários semeados, todos com a senha `logitech`:

| Usuário | Papel |
|---|---|
| `ana.cliente` | `CLIENTE` |
| `bruno.motorista` | `MOTORISTA` |
| `carla.admin` | `ADMIN` |

Senha fraca e igual para os três é deliberado: é ambiente de laboratório.
Credencial de laboratório que parece de produção ensina a coisa errada.

## Por que realm importado, e não configurado na tela

Configurar realm clicando em vinte telas não é reproduzível, não entra no Git e
não sobrevive a um `docker compose down -v`. Este JSON é versionado, e o
ambiente de todo mundo na sala nasce igual.

## `directAccessGrantsEnabled` no `logitech-portal`

Ligado, e é um caminho de **laboratório**, não o fluxo da aula. Ele existe para
que o `verificar.py` e o servidor MCP consigam um token sem abrir navegador:

```bash
curl -s -X POST http://localhost:8090/realms/logitech/protocol/openid-connect/token \
  -d grant_type=password -d client_id=logitech-portal \
  -d username=carla.admin -d password=logitech
```

O fluxo que a pessoa usa continua sendo o Authorization Code com PKCE, pelo
navegador, e é ele que as telas do Portal e do Painel executam.

## Onde o `iss` é decidido

`KC_HOSTNAME: http://localhost:8090`, no `docker-compose.yml`. É esse valor que
acaba dentro do `iss` de todo token emitido. Os serviços de backend, por outro
lado, buscam o JWKS por `http://keycloak:8090`, o endereço da rede interna.

Os dois endereços **não coincidem**, e é por isso que o contrato tem duas
variáveis: `LOGITECH_OIDC_ISSUER` e `LOGITECH_OIDC_JWKS_URL`.
