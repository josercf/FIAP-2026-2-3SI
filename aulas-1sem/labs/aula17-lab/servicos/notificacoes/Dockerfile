# Serviço de Notificações (Node 22, TypeScript). Multi-stage por simetria com
# os demais serviços: aqui não há passo de compilação, porque o Node 22 apaga
# a anotação de tipo em tempo de carga. TypeScript de verdade, sem tsc.

FROM node:22-alpine AS base
WORKDIR /build
COPY package.json server.ts seguranca.ts ./

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
COPY --from=base /build ./

ENV NODE_ENV=production \
    LOGITECH_PORTA=3001

USER logitech
EXPOSE 3001
CMD ["node", "server.ts"]
