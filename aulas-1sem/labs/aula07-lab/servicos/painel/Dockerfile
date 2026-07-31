# Painel de rastreamento da LogiTech. Multi-stage e usuário não-root, o mesmo
# padrão da Aula 03. Vem pronto: o artefato de hoje é o docker-compose.yml.

FROM node:22-alpine AS base
WORKDIR /app
COPY package.json server.js ./
COPY public ./public

FROM node:22-alpine
WORKDIR /app
RUN adduser -D -H -s /sbin/nologin logitech
COPY --from=base /app ./

# Nenhum LOGITECH_DADOS aqui: desde a Aula 07 este serviço não abre arquivo.
# O endereço da telemetria é injetado pelo Compose em LOGITECH_TELEMETRIA_URL.
ENV NODE_ENV=production

USER logitech
EXPOSE 3000
CMD ["node", "server.js"]
