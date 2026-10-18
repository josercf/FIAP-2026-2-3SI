# Servico de Pedidos (Java 21). Multi-stage, a mesma tecnica da Aula 03: o
# JDK inteiro so existe no estagio de compilacao e a imagem final leva o JRE
# e as classes.
#
# Nenhum artefato e baixado da rede durante o build. Nao ha Maven, nao ha
# Gradle e nao ha driver JDBC, porque o estado deste servico vive em memoria.
# Consequencia pratica: o `docker compose build` funciona sem repositorio de
# artefatos respondendo, o que ja salvou mais de uma aula.

FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /build
COPY *.java ./
# A suite de testes e compilada junto, de proposito: ela e a regua do
# laboratorio e precisa estar dentro da imagem para rodar com
# `docker compose exec pedidos java -cp /app/classes TestesSeguranca`.
RUN javac -d /build/classes *.java

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN adduser -D -H -s /sbin/nologin logitech
COPY --from=build /build/classes /app/classes

USER logitech
EXPOSE 8080

# -XX:MaxRAMPercentage faz a JVM respeitar o limite de memoria do container em
# vez do total do host. Sem isso, `mem_limit` no Compose e heap da JVM
# discordam e o servico morre por OOMKilled sem explicacao aparente.
CMD ["java", "-XX:MaxRAMPercentage=70", "-cp", "/app/classes", "Pedidos"]
