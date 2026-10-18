# Serviço de Notificações (Node 22, TypeScript). Multi-stage por simetria com
# os demais serviços: aqui não há passo de compilação, porque o Node 22 apaga
# a anotação de tipo em tempo de carga. TypeScript de verdade, sem tsc.

FROM node:22-alpine AS base
WORKDIR /build
COPY package.json server.ts ./

FROM node:22-alpine
WORKDIR /app
RUN adduser -D -H -s /sbin/nologin logitech
COPY --from=base /build ./

ENV NODE_ENV=production \
    LOGITECH_PORTA=3001

USER logitech
EXPOSE 3001
CMD ["node", "server.ts"]
