# Serviço de Pedidos (Java 21). Multi-stage: o JDK inteiro só existe no
# estágio de compilação; a imagem final leva o JRE, as classes e o driver.
#
# O único artefato baixado da rede é o driver JDBC do PostgreSQL, com
# timeout e retentativa explícitos: build que trava esperando um repositório
# de artefatos é o tipo de falha que come uma aula inteira.

FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /build

ARG PGJDBC_VERSAO=42.7.4
ARG PGJDBC_URL=https://repo1.maven.org/maven2/org/postgresql/postgresql/${PGJDBC_VERSAO}/postgresql-${PGJDBC_VERSAO}.jar

RUN wget --timeout=30 --tries=3 -O /build/postgresql.jar "${PGJDBC_URL}"

COPY Pedidos.java Seguranca.java ./
RUN javac -cp /build/postgresql.jar -d /build/classes Pedidos.java Seguranca.java

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN adduser -D -H -s /sbin/nologin logitech
COPY --from=build /build/classes /app/classes
COPY --from=build /build/postgresql.jar /app/postgresql.jar

USER logitech
EXPOSE 8080

# -XX:MaxRAMPercentage faz a JVM respeitar o limite de memória do container
# em vez do total do host. Sem isso, `mem_limit` no Compose e heap da JVM
# discordam, e o serviço morre por OOMKilled sem explicação aparente.
CMD ["java", "-XX:MaxRAMPercentage=70", "-cp", "/app/classes:/app/postgresql.jar", "Pedidos"]
