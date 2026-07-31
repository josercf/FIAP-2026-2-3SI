#!/usr/bin/env bash
# Preparacao do ambiente do laboratorio. Roda uma vez, na criacao do container.
#
# O bloco pratico da Aula 10 tem 60 minutos e duas stacks. Nenhum deles pode
# ser gasto esperando `npm install`: as dependencias do portal sao instaladas
# aqui, na criacao do container.
set -euo pipefail

echo "==> Configurando o laboratorio mwe-2026-2-lab10-testes-react"

# --- Dependencias de Python ------------------------------------------------
if [ -f servicos/frete/requirements.txt ]; then
  pip install --user -r servicos/frete/requirements.txt
fi
if [ -f servicos/pedidos/requirements.txt ]; then
  pip install --user -r servicos/pedidos/requirements.txt
fi

# --- Dependencias do portal ------------------------------------------------
# `npm ci` quando ha package-lock.json (reproduzivel), `npm install` quando nao ha.
if [ -f portal/package.json ]; then
  if [ -f portal/package-lock.json ]; then
    (cd portal && npm ci --no-audit --no-fund)
  else
    (cd portal && npm install --no-audit --no-fund)
  fi
  # Aquece o cache do esbuild e do vitest, para a primeira execucao em sala
  # nao pagar a compilacao de TypeScript.
  (cd portal && npx vitest run --silent >/dev/null 2>&1 || true)
fi

if [ ! -f portal/.env ] && [ -f portal/.env.exemplo ]; then
  cp portal/.env.exemplo portal/.env
fi

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
  if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then break; fi
  sleep 1
done

echo "==> Baixando o modelo qwen2.5:1.5b (uso unico, fica em cache)"
ollama pull qwen2.5:1.5b || echo "    AVISO: falha ao baixar o modelo. Rode 'ollama pull qwen2.5:1.5b' manualmente."

# --- Verificacao do ambiente ----------------------------------------------
echo ""
if python3 -m pytest --version >/dev/null 2>&1; then
  echo "==> pytest disponivel."
else
  echo "==> AVISO: pytest nao respondeu. Rode 'pip install -r servicos/frete/requirements.txt'."
fi
if [ -d portal/node_modules ]; then
  echo "==> Dependencias do portal instaladas."
else
  echo "==> AVISO: o portal esta sem node_modules. Rode 'cd portal && npm install'."
fi
if curl -sf --connect-timeout 5 http://localhost:11434/api/tags >/dev/null 2>&1 \
   && ollama list 2>/dev/null | grep -q "qwen2.5:1.5b"; then
  echo "==> Backend de IA pronto: Ollama respondendo com o modelo qwen2.5:1.5b."
  echo "    Teste com: python ai/ask.py \"diga ola\""
else
  echo "==> AVISO: o Ollama nao confirmou o modelo qwen2.5:1.5b."
  echo "    Suba o servidor com: ollama serve"
  echo "    Depois baixe o modelo com: ollama pull qwen2.5:1.5b"
fi

echo ""
echo "Ambiente pronto. Comece pelo README.md."
