# Servico de Notificacoes (Node 22). Sem `npm install` no build: este servico
# nao tem uma unica dependencia externa. `node:http` serve HTTP e `node:crypto`
# verifica RS256 a partir de uma chave em formato JWK.
#
# A imagem final nao carrega nem `package.json`, e roda como usuario sem
# privilegio, que e o padrao da imagem oficial `node`.

FROM node:22-alpine
WORKDIR /app

COPY server.mjs seguranca.mjs ./
# A suite vai junto, para rodar dentro do container com
# `docker compose exec notificacoes node --test seguranca.test.mjs`.
COPY seguranca.test.mjs ./

USER node
EXPOSE 3001

CMD ["node", "server.mjs"]
