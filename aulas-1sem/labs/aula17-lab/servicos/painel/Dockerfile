# Painel de rastreamento da LogiTech. Multi-stage e usuário não-root, o mesmo
# padrão da Aula 03. Vem pronto: o artefato de hoje é o docker-compose.yml.

FROM node:22-alpine AS base
WORKDIR /app
COPY package.json server.js ./
COPY public ./public

FROM node:22-alpine
WORKDIR /app
RUN adduser -D -H -s /sbin/nologin logitech

# --- Frente 5, cadeia de suprimentos ---------------------------------------
# O `npm` que a imagem base carrega traz `tar` 7.5.11, e o Trivy aponta nele
# uma CVE CRITICAL (CVE-2026-59873, corrigida em 7.5.19). A dependência não é
# do nosso código: é do gerenciador de pacotes, e a imagem final não instala
# nada em tempo de execução. Removê-lo tira a vulnerabilidade e ainda encolhe
# a imagem. Medido em 31/07/2026: 1 CRITICAL antes, 0 depois.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx
COPY --from=base /app ./

# Nenhum LOGITECH_DADOS aqui: desde a Aula 07 este serviço não abre arquivo.
# O endereço da telemetria é injetado pelo Compose em LOGITECH_TELEMETRIA_URL.
ENV NODE_ENV=production

USER logitech
EXPOSE 3000
CMD ["node", "server.js"]
