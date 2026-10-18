# Serviço `rag` da plataforma LogiTech (Python 3.12, FastAPI, porta 8010).
#
# Multi-stage, mesmas regras que a Aula 03 cobrou: base enxuta no estágio
# final, usuário não-root, nunca `COPY . .`.
#
# O contexto de build é a RAIZ do laboratório, e não `servicos/rag/`: o serviço
# precisa da pasta `contratos/`, que fica na raiz. Por isso o compose declara
# `context: .` e `dockerfile: servicos/rag/Dockerfile`.
#
# Base `slim` e não `alpine`: o `psycopg[binary]` distribui roda pronta para
# glibc, e no Alpine o pip cairia na compilação do driver. O preço é que a
# imagem não traz o `wget` do BusyBox, então o healthcheck deste serviço usa
# `python -c` em vez do `wget` dos demais. Está escrito no docker-compose.yml.

FROM python:3.12-slim AS build
WORKDIR /build
COPY servicos/rag/requirements.txt .
RUN pip install --no-cache-dir --prefix=/instalado -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

# --- Frente 5, cadeia de suprimentos ---------------------------------------
# A base Debian traz `perl-base`, e o Trivy aponta nele quatro CVEs CRITICAL
# **sem correcao publicada** (CVE-2026-8376, -13221, -42496, -57433). Sem
# correcao, nao ha o que atualizar: ou se troca a base, ou se remove o pacote,
# ou se aceita o risco por escrito.
#
# Aqui removemos: nada neste servico executa Perl, e `--force-depends` e o que
# permite tirar um pacote que o `dpkg` considera essencial. Isso quebra o
# `apt-get` desta imagem, e nao ha problema: imagem de execucao nao instala
# pacote. Medido em 31/07/2026: 4 CRITICAL antes, 0 depois.
RUN dpkg --purge --force-depends perl-base 2>/dev/null; rm -rf /var/lib/apt/lists/*

RUN useradd --uid 10012 --no-create-home --shell /usr/sbin/nologin logitech

COPY --from=build /instalado /usr/local
COPY servicos/rag/*.py /app/rag/
COPY contratos /app/contratos

ENV PYTHONUNBUFFERED=1

USER logitech
EXPOSE 8010

CMD ["uvicorn", "rag.app:app", "--host", "0.0.0.0", "--port", "8010"]
