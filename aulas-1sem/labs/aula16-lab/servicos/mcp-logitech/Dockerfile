# Servidor MCP da LogiTech (Node 22, TypeScript, transporte stdio).
#
# O único serviço da plataforma que NÃO expõe porta: o transporte padrão do MCP
# é stdio, e quem conversa com ele é um processo, não um cliente HTTP. Por isso
# não há `EXPOSE` aqui e não há `GET /health` no servidor.
#
# O contexto de build é a RAIZ do laboratório: o servidor serve os contratos em
# `contratos/`, que ficam fora desta pasta.
#
# Multi-stage por simetria com os demais serviços. Não há passo de compilação:
# o Node 22 apaga a anotação de tipo em tempo de carga.

FROM node:22-alpine AS base
WORKDIR /build
COPY servicos/mcp-logitech/package.json ./
COPY servicos/mcp-logitech/src ./src

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
COPY contratos /contratos

# O servidor resolve os contratos em ../../contratos a partir de src/, ou seja
# /contratos quando a aplicacao mora em /app/src. O caminho fica explicito para
# quem for ler o Dockerfile em vez do codigo.
ENV NODE_ENV=production

USER logitech

# Fica de pé lendo stdin, esperando JSON-RPC. `stdin_open: true` no Compose é o
# que mantém a entrada padrão aberta; sem ele o processo receberia EOF e sairia
# na hora, e o container entraria em laço de reinício.
CMD ["node", "--experimental-strip-types", "src/servidor.ts"]
