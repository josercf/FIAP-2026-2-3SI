#!/usr/bin/env bash
# Preparacao do ambiente do laboratorio. Roda uma vez, na criacao do container.
set -euo pipefail

echo "==> Configurando o laboratorio mwe-2026-2-lab12-rag-mcp"

MODELO_CONVERSA="${LOGITECH_MODELO:-qwen2.5:1.5b}"
MODELO_EMBEDDING="${LOGITECH_EMBEDDING_MODELO:-paraphrase-multilingual}"

# --- Dependencias da stack -------------------------------------------------
if [ -f requirements.txt ]; then pip install --user -r requirements.txt; fi
pip install --user pytest >/dev/null 2>&1 || true

# A rede vem da Aula 03 e entra no Compose como external: sem ela o
# `docker compose up` falha com uma mensagem obscura.
docker network create logitech-net 2>/dev/null || true

if [ -f .env.exemplo ] && [ ! -f .env ]; then cp .env.exemplo .env; fi

# --- Ollama: SLM rodando dentro do proprio container -----------------------
# Backend unico de IA dos laboratorios, decisao registrada na ADR-005 do
# acervo: o GitHub Models foi retirado do ar em 30/07/2026.
# O instalador do Ollama extrai com zstd, que a imagem base nao traz.
if ! command -v zstd >/dev/null 2>&1; then
  echo "==> Instalando o zstd, exigido pelo instalador do Ollama"
  SUDO=""; command -v sudo >/dev/null 2>&1 && SUDO=sudo
  $SUDO apt-get update -y >/dev/null 2>&1 || true
  $SUDO apt-get install -y zstd \
    || echo "    AVISO: nao consegui instalar o zstd; o Ollama pode falhar."
fi
if ! command -v ollama >/dev/null 2>&1; then
  echo "==> Instalando o Ollama"
  curl -fsSL --connect-timeout 10 --max-time 600 https://ollama.com/install.sh | sh
fi

echo "==> Subindo o servidor Ollama"
(ollama serve >/tmp/ollama.log 2>&1 &)

# Espera o servidor aceitar conexao (ate 30s)
for _ in $(seq 1 30); do
  if curl -sf --connect-timeout 2 --max-time 5 http://localhost:11434/api/tags >/dev/null 2>&1; then break; fi
  sleep 1
done

# --- DOIS modelos, e nao um ------------------------------------------------
# Modelo de geracao nao serve para embedding e vice-versa: sao cabecas
# diferentes, treinadas para tarefas diferentes. Esta e a primeira aula em que
# a distincao aparece na pratica (ADR-008).
echo "==> Baixando o modelo de embedding ${MODELO_EMBEDDING} (cerca de 560 MB)"
ollama pull "${MODELO_EMBEDDING}" \
  || echo "    AVISO: falha ao baixar. Rode 'ollama pull ${MODELO_EMBEDDING}' manualmente."

echo "==> Baixando o modelo de conversa ${MODELO_CONVERSA} (uso unico, fica em cache)"
ollama pull "${MODELO_CONVERSA}" \
  || echo "    AVISO: falha ao baixar. Rode 'ollama pull ${MODELO_CONVERSA}' manualmente."

# --- Verificacao do backend de IA -----------------------------------------
if curl -sf --connect-timeout 5 --max-time 10 http://localhost:11434/api/tags >/dev/null 2>&1 \
   && ollama list 2>/dev/null | grep -q "${MODELO_EMBEDDING}"; then
  echo "==> Backend de IA pronto."
  echo "    Teste o embedding com:"
  echo "      curl -s --connect-timeout 5 --max-time 60 http://localhost:11434/api/embed \\"
  echo "        -d '{\"model\":\"${MODELO_EMBEDDING}\",\"input\":[\"teste\"]}' | head -c 120"
else
  echo "==> AVISO: o Ollama nao confirmou o modelo ${MODELO_EMBEDDING}."
  echo "    Suba o servidor com: ollama serve"
  echo "    Depois baixe o modelo com: ollama pull ${MODELO_EMBEDDING}"
fi

echo ""
echo "Ambiente pronto. Comece pelo README.md, Passo 0."
