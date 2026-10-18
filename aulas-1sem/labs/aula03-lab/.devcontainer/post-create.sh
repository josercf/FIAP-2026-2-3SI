#!/usr/bin/env bash
# Preparacao do ambiente do laboratorio. Roda uma vez, na criacao do container.
set -euo pipefail

echo "==> Configurando o laboratorio mwe-2026-2-lab03-docker"

# --- Dependencias da stack -------------------------------------------------
if [ -f requirements.txt ]; then pip install --user -r requirements.txt; fi

# --- Ollama: SLM rodando dentro do proprio container -----------------------
# Backend único de IA dos laboratórios, decisão registrada na ADR-005 do
# acervo: o GitHub Models foi retirado do ar em 30/07/2026.
# O instalador do Ollama extrai com zstd, que a imagem base não traz.
if ! command -v zstd >/dev/null 2>&1; then
  echo "==> Instalando o zstd, exigido pelo instalador do Ollama"
  SUDO=""; command -v sudo >/dev/null 2>&1 && SUDO=sudo
  $SUDO apt-get update -y >/dev/null 2>&1 || true
  $SUDO apt-get install -y zstd \
    || echo "    AVISO: não consegui instalar o zstd; o Ollama pode falhar."
fi
if ! command -v ollama >/dev/null 2>&1; then
  echo "==> Instalando o Ollama"
  curl -fsSL --connect-timeout 10 --max-time 600 https://ollama.com/install.sh | sh
fi

echo "==> Subindo o servidor Ollama"
(ollama serve >/tmp/ollama.log 2>&1 &)

# Espera o servidor aceitar conexao (ate 30s)
for _ in $(seq 1 30); do
  if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then break; fi
  sleep 1
done

echo "==> Baixando o modelo qwen3.5:2b (uso unico, fica em cache)"
ollama pull qwen3.5:2b || echo "    AVISO: falha ao baixar o modelo. Rode 'ollama pull qwen3.5:2b' manualmente."

# --- docker-agent: runtime de agentes que lê as skills do repositório ------
# Usado como executável standalone (docker-agent run agente.yaml) na etapa 8.
echo "==> Instalando o docker-agent"
mkdir -p ~/.local/bin
ARCH=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')
if curl -fsSL --connect-timeout 10 --max-time 300 -o /tmp/docker-agent \
     "https://github.com/docker/docker-agent/releases/latest/download/docker-agent-linux-${ARCH}"; then
  chmod +x /tmp/docker-agent
  mv /tmp/docker-agent ~/.local/bin/docker-agent
  echo "    docker-agent instalado. Teste com: docker-agent --version"
else
  echo "    AVISO: falha ao baixar o docker-agent. A etapa 8 é bônus, siga sem ele."
fi

# --- Verificacao do backend de IA -----------------------------------------
if curl -sf --connect-timeout 5 http://localhost:11434/api/tags >/dev/null 2>&1 \
   && ollama list 2>/dev/null | grep -q "qwen3.5:2b"; then
  echo "==> Backend de IA pronto: Ollama respondendo com o modelo qwen3.5:2b."
  echo "    Teste com: python ai/ask.py \"diga olá\""
else
  echo "==> AVISO: o Ollama não confirmou o modelo qwen3.5:2b."
  echo "    Suba o servidor com: ollama serve"
  echo "    Depois baixe o modelo com: ollama pull qwen3.5:2b"
fi

echo ""
echo "Ambiente pronto. Comece pelo README.md."
