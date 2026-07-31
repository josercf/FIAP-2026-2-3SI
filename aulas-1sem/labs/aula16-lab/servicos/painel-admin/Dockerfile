# Painel administrativo da LogiTech (Angular, TypeScript, RxJS). Porta 4200.
#
# Multi-stage, pelo mesmo motivo do Portal: o estágio de build carrega o Angular
# CLI, o compilador e as centenas de megabytes de `node_modules`; o final leva o
# bundle e um servidor estático de cinquenta linhas, sem dependência nenhuma.
#
# Diferença em relação ao Portal, e ela é conteúdo: no Angular a configuração de
# ambiente é **arquivo** (`src/app/nucleo/ambiente.ts`), não variável de
# processo. Por isso não há ARG de endereço aqui. Os dois estão certos, cada um
# na convenção da sua ferramenta, e o nome canônico continua sendo o do
# contrato (ADR-006 e ADR-008).

FROM node:22-alpine AS build
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY angular.json tsconfig.json tsconfig.app.json tsconfig.spec.json ./
COPY public ./public
COPY src ./src
RUN npm run build

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
COPY --from=build /build/dist ./dist
COPY servir.mjs package.json ./

ENV NODE_ENV=production \
    LOGITECH_PORTA=4200

USER logitech
EXPOSE 4200
CMD ["node", "servir.mjs"]
