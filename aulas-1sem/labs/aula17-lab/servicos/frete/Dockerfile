# Cálculo de Frete (Python 3.12, FastAPI). Multi-stage: as dependências são
# instaladas num estágio à parte, para a imagem final não carregar o pip nem
# o cache de instalação.

FROM python:3.12-alpine AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/instalado -r requirements.txt

FROM python:3.12-alpine
WORKDIR /app
RUN adduser -D -H -s /sbin/nologin logitech
COPY --from=build /instalado /usr/local
COPY main.py seguranca.py ./

ENV PYTHONUNBUFFERED=1 \
    LOGITECH_PORTA=8000

USER logitech
EXPOSE 8000
CMD ["python", "main.py"]
