# Imagem base do laboratório, saneada antes dos features do devcontainer.
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# A imagem base traz o repositório apt do Yarn pré-configurado em
# /etc/apt/sources.list.d/yarn.list, e a chave GPG desse repositório expirou
# (NO_PUBKEY 62D54FD4003F6525). Todo feature do devcontainer começa com um
# apt-get update; com o repositório quebrado presente, o apt sai com código
# 100, o feature aborta, o build inteiro falha e o Codespaces entrega um
# container de recuperação, sem as ferramentas do laboratório.
#
# Removendo o repositório aqui, os features passam a ser aplicados sobre uma
# base sã. O Yarn continua instalado; o que se perde é a atualização dele por
# apt, que nenhum laboratório usa.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
 && apt-get update \
 && rm -rf /var/lib/apt/lists/*

# O cliente psql, que o laboratório usa para inspecionar o banco do Compose.
# Instalado por apt, e não pelo feature ghcr.io/devcontainers/features/
# postgresql-client:1 que estava declarado aqui: esse feature não existe no
# registro, devolve 403 e derrubava o build do devcontainer por si só.
RUN apt-get update \
 && apt-get install -y --no-install-recommends postgresql-client \
 && rm -rf /var/lib/apt/lists/*
