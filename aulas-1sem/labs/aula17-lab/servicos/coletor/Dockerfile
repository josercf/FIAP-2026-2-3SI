# Coletor de telemetria da LogiTech. Multi-stage e usuário não-root, o mesmo
# padrão que vocês escreveram na Aula 03. Aqui ele vem pronto: hoje o
# artefato de vocês é o docker-compose.yml, não o Dockerfile.

FROM python:3.12-alpine AS base
WORKDIR /app
COPY server_telemetry.py .

FROM python:3.12-alpine
WORKDIR /app
# O usuário não-root nasce sem shell de login: um container comprometido não
# ganha um shell de brinde.
RUN adduser -D -H -s /sbin/nologin logitech \
    && mkdir -p /dados \
    && chown logitech:logitech /dados
COPY --from=base /app/server_telemetry.py .

# Quem decide onde os dados moram dentro do container é o container, não o
# código: o padrão do próprio serviço é relativo ao repositório.
ENV LOGITECH_DADOS=/dados/telemetria.jsonl \
    PYTHONUNBUFFERED=1

USER logitech
EXPOSE 8081/udp 8080/tcp 8082/tcp
CMD ["python", "server_telemetry.py"]
