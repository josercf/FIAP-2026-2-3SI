#!/usr/bin/env bash
# Roda a cada inicializacao do container: garante o Ollama no ar.
set -euo pipefail

if command -v ollama >/dev/null 2>&1; then
  if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    (ollama serve >/tmp/ollama.log 2>&1 &)
  fi
fi
