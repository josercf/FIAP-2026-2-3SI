# Serviço `rag` como container. Caminho OPCIONAL, fora do tempo de aula:
# durante o laboratório o serviço roda direto no devcontainer, porque você vai
# editar `busca.py` várias vezes e um rebuild por tentativa custa caro.
#
# Multi-stage, mesmas regras que a Aula 03 cobrou: base enxuta no estágio
# final, usuário não-root, nunca `COPY . .`.
#
# O contexto de build é a RAIZ do laboratório, e não a pasta `rag/`: o serviço
# precisa da pasta `contratos/`, que é irmã dela. Por isso o compose declara
# `context: .` e `dockerfile: rag/Dockerfile`.

FROM python:3.12-slim AS build
WORKDIR /build
COPY rag/requirements.txt .
RUN pip install --no-cache-dir --prefix=/instalado -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

RUN useradd --uid 10012 --no-create-home --shell /usr/sbin/nologin logitech

COPY --from=build /instalado /usr/local
COPY rag/*.py /app/rag/
COPY contratos /app/contratos

USER logitech
EXPOSE 8010

CMD ["uvicorn", "rag.app:app", "--host", "0.0.0.0", "--port", "8010"]
