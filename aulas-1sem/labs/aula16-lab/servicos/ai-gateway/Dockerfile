# AI Gateway da LogiTech (Python 3.12, FastAPI). Multi-stage: as dependências
# são instaladas num estágio à parte, e a imagem final não carrega o pip nem
# o cache de instalação.

FROM python:3.12-alpine AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/instalado -r requirements.txt

FROM python:3.12-alpine
WORKDIR /app
RUN adduser -D -H -s /sbin/nologin logitech
COPY --from=build /instalado /usr/local
COPY app.py fachada.py provedores.py roteamento.py politicas.py metricas.py \
     guardrails.py seguranca.py ./

ENV PYTHONUNBUFFERED=1 \
    LOGITECH_PORTA=4000

USER logitech
EXPOSE 4000
CMD ["python", "app.py"]
