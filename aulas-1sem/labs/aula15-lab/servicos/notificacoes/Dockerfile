# Serviço de Notificações (Node 22, TypeScript). Herdado da Aula 07, sem uma
# linha alterada: multi-stage por simetria com os demais serviços, e aqui não
# há passo de compilação porque o Node 22 apaga a anotação de tipo em tempo de
# carga.
#
# TODO-5a. **Este Dockerfile é a lacuna do Passo 5.**
#
# Não mexa nele antes de rodar `./varrer.sh`. A ordem do exercício é ver o
# relatório primeiro e só então mudar o arquivo: quem corrige antes de medir
# não sabe o que corrigiu, e não consegue preencher `CVES_CRITICAL_ANTES`.
#
# Quando chegar a hora, uma pista sobre onde procurar: o Trivy diz o **caminho**
# do pacote vulnerável dentro da imagem, no campo `PkgPath` do relatório em
# JSON. Leia esse caminho antes de decidir o que fazer. Ele responde sozinho
# duas perguntas:
#
#     de onde veio este pacote?
#     este container precisa dele para rodar `node server.ts`?
#
# Trocar a imagem base por uma mais nova é a primeira ideia de todo mundo, e às
# vezes é a resposta certa. Neste caso específico, não é a melhor: a próxima
# versão da base traz o mesmo pacote e o relógio volta a correr. Existe uma
# correção que resolve a classe inteira do problema, e ela cabe em duas linhas.

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
