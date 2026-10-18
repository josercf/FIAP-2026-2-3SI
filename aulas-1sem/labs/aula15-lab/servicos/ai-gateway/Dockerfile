# AI Gateway da LogiTech (Python 3.12, FastAPI). Multi-stage desde a Aula 03:
# as dependências são instaladas num estágio à parte, e a imagem final não
# carrega o pip nem o cache de instalação.
#
# O multi-stage já reduz a superfície de ataque, e isso é conteúdo da Aula 15:
# cada pacote que não está na imagem final é uma CVE que nunca vai aparecer no
# relatório do Trivy.

FROM python:3.12-alpine AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/instalado -r requirements.txt

FROM python:3.12-alpine
WORKDIR /app
RUN adduser -D -H -s /sbin/nologin logitech
COPY --from=build /instalado /usr/local
COPY app.py fachada.py provedores.py roteamento.py politicas.py metricas.py \
     guardrails.py persona.py ./

ENV PYTHONUNBUFFERED=1 \
    LOGITECH_PORTA=4000 \
    LOGITECH_GUARDRAILS_ATIVOS=true

USER logitech
EXPOSE 4000
CMD ["python", "app.py"]
