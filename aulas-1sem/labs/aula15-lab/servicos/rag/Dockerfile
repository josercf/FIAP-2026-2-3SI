# Serviço de RAG da LogiTech (Python 3.12, FastAPI). Multi-stage, como todos os
# serviços da plataforma desde a Aula 03.
#
# O contexto de build é a **raiz do laboratório**, e não este diretório: a
# imagem precisa levar `contratos/` junto, e no Docker o `COPY` não sobe acima
# do contexto. Veja o `docker-compose.yml`.

FROM python:3.12-alpine AS build
WORKDIR /build
COPY servicos/rag/requirements.txt .
RUN pip install --no-cache-dir --prefix=/instalado -r requirements.txt

FROM python:3.12-alpine
WORKDIR /app
RUN adduser -D -H -s /sbin/nologin logitech
COPY --from=build /instalado /usr/local
COPY servicos/rag/app.py servicos/rag/recuperacao.py servicos/rag/composicao.py ./
COPY contratos ./contratos

ENV PYTHONUNBUFFERED=1 \
    LOGITECH_PORTA=8010 \
    LOGITECH_CONTRATOS=/app/contratos \
    LOGITECH_GUARDRAILS_ATIVOS=true

USER logitech
EXPOSE 8010
CMD ["python", "app.py"]
