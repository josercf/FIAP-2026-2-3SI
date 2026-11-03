#!/usr/bin/env bash
# Pega um token de acesso para os `curl` do laboratório.
#
#     ./scripts/token.sh carla.admin
#     TOKEN=$(./scripts/token.sh ana.cliente)
#     curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/pedidos
#
# Usa o *direct access grant*, que é um caminho de LABORATÓRIO e está declarado
# como tal em keycloak/LEIA-ME.md. O fluxo das pessoas é o Authorization Code
# com PKCE, pelo navegador, e é ele que o Portal e o Painel executam. Se você
# ainda não viu o PKCE acontecer na aba de rede do navegador, veja antes de
# usar este atalho: colar `curl` com token sem entender o fluxo é o modo mais
# rápido de chegar à banca sem saber explicar a própria arquitetura.

set -euo pipefail
USUARIO="${1:-carla.admin}"
SENHA="${2:-logitech}"
KEYCLOAK="${LOGITECH_KEYCLOAK_URL:-http://localhost:8090}"

curl -s -X POST "$KEYCLOAK/realms/logitech/protocol/openid-connect/token" \
  -d grant_type=password \
  -d client_id=logitech-portal \
  -d "username=$USUARIO" \
  -d "password=$SENHA" \
| python3 -c "
import json, sys
d = json.load(sys.stdin)
if 'access_token' not in d:
    sys.exit('o Keycloak recusou: %s' % d.get('error_description', d))
print(d['access_token'])
"
