# Imagem base do laboratório, saneada antes dos features do devcontainer.
FROM mcr.microsoft.com/devcontainers/java:1-21-bookworm

# A imagem oficial de Java traz o repositório apt do Yarn pré-configurado em
# /etc/apt/sources.list.d/yarn.list, e a chave GPG desse repositório expirou
# (NO_PUBKEY 62D54FD4003F6525). Todo feature do devcontainer começa com um
# apt-get update; com o repositório quebrado presente, o apt sai com código
# 100, o feature aborta, o build inteiro falha e o Codespaces entrega um
# container de recuperação sem Docker, sem Java e sem .NET.
#
# Removendo o repositório aqui, os features passam a ser aplicados sobre uma
# base sã. O Yarn continua instalado; o que se perde é a atualização dele por
# apt, que nenhum laboratório usa.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
 && apt-get update \
 && rm -rf /var/lib/apt/lists/*

# A imagem base traz apenas o Python mínimo (python3-minimal), sem a biblioteca
# padrão: falta o módulo json, entre outros. O verificar.py, que é como o aluno
# confere os onze critérios de aceitação, importa json e não roda sem isto.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/*

# A imagem base não traz o Maven, e o Passo 1 do laboratório roda
# "mvn spring-boot:run". Instalado aqui a partir do tarball oficial, e não
# pelo feature java do devcontainer: aquele feature reaponta o JAVA_HOME para
# um diretório do SDKMAN que fica vazio quando o JDK já vem na imagem, e o
# Maven passa a recusar a execução com "JAVA_HOME is not defined correctly".
ARG MAVEN_VERSION=3.9.9
RUN curl -fsSL --retry 3 \
      "https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz" \
      -o /tmp/maven.tar.gz \
 && mkdir -p /opt/maven \
 && tar -xzf /tmp/maven.tar.gz -C /opt/maven --strip-components=1 \
 && rm /tmp/maven.tar.gz \
 && ln -s /opt/maven/bin/mvn /usr/local/bin/mvn
