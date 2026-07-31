# Portal do Cliente da LogiTech (React 19, TypeScript, Vite). Porta 5173.
#
# Multi-stage no sentido mais claro que existe: o estágio de build carrega o
# Vite, o TypeScript e as centenas de megabytes de `node_modules`; o estágio
# final leva `dist/` e um servidor estático de cinquenta linhas, sem uma única
# dependência instalada.
#
# As variáveis VITE_* são lidas em tempo de BUILD, não de execução: o Vite as
# substitui no código empacotado. É a diferença entre configurar um serviço de
# servidor e configurar uma aplicação que roda no navegador de outra pessoa, e
# é por isso que elas aparecem como ARG aqui e não como ENV lá embaixo.

FROM node:22-alpine AS build
WORKDIR /build

ARG VITE_PEDIDOS_URL=http://localhost:8080
ARG VITE_FRETE_URL=http://localhost:8000
ARG VITE_OIDC_AUTORIDADE=http://localhost:8090/realms/logitech
ARG VITE_OIDC_CLIENT_ID=logitech-portal
ENV VITE_PEDIDOS_URL=$VITE_PEDIDOS_URL \
    VITE_FRETE_URL=$VITE_FRETE_URL \
    VITE_OIDC_AUTORIDADE=$VITE_OIDC_AUTORIDADE \
    VITE_OIDC_CLIENT_ID=$VITE_OIDC_CLIENT_ID

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY tsconfig.json vite.config.ts index.html ./
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
COPY servir.js ./
COPY package.json ./

ENV NODE_ENV=production \
    LOGITECH_PORTA=5173

USER logitech
EXPOSE 5173
CMD ["node", "servir.js"]
