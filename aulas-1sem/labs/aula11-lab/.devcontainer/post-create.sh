#!/usr/bin/env bash
# Preparacao do ambiente do laboratorio. Roda uma vez, na criacao do container.
#
# A regra que manda neste arquivo: nada que demore pode sobrar para o bloco
# pratico de 60 minutos. `npm ci` de um workspace Angular e `dotnet build` de
# um projeto ASP.NET rodam AQUI, na criacao do container, e nao em sala.
set -euo pipefail

echo "==> Configurando o laboratorio mwe-2026-2-lab11-angular-rxjs"

# --- Angular: dependencias instaladas antes da aula ------------------------
if [ -f painel-admin/package-lock.json ]; then
  echo "==> Instalando as dependencias do painel-admin (npm ci)"
  (cd painel-admin && npm ci)
elif [ -f painel-admin/package.json ]; then
  (cd painel-admin && npm install)
fi

# Primeira compilacao, para o cache do Angular ja existir quando o aluno
# rodar `ng serve` pela primeira vez.
if [ -d painel-admin/node_modules ]; then
  echo "==> Aquecendo o build do Angular"
  (cd painel-admin && npx ng build >/dev/null 2>&1) \
    || echo "    AVISO: o build de aquecimento falhou; nao e impeditivo."
fi

# --- .NET: restore e build do servico congelado de Faturamento -------------
if command -v dotnet >/dev/null 2>&1 && [ -f servicos/faturamento/Faturamento.csproj ]; then
  echo "==> Restaurando e compilando o servico de Faturamento (.NET 8)"
  dotnet build servicos/faturamento -c Debug >/dev/null 2>&1 \
    || echo "    AVISO: o build do Faturamento falhou; rode 'dotnet build servicos/faturamento'."
fi

# --- Python: pytest para os testes do verificador --------------------------
if command -v pip >/dev/null 2>&1; then
  pip install --user --quiet pytest || echo "    AVISO: falha ao instalar o pytest."
fi

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

echo "==> Baixando o modelo qwen2.5:1.5b (uso unico, fica em cache)"
ollama pull qwen2.5:1.5b || echo "    AVISO: falha ao baixar o modelo. Rode 'ollama pull qwen2.5:1.5b' manualmente."

# --- Verificacao do backend de IA -----------------------------------------
if curl -sf --connect-timeout 5 http://localhost:11434/api/tags >/dev/null 2>&1 \
   && ollama list 2>/dev/null | grep -q "qwen2.5:1.5b"; then
  echo "==> Backend de IA pronto: Ollama respondendo com o modelo qwen2.5:1.5b."
  echo "    Teste com: python ai/ask.py \"diga olá\""
else
  echo "==> AVISO: o Ollama não confirmou o modelo qwen2.5:1.5b."
  echo "    Suba o servidor com: ollama serve"
  echo "    Depois baixe o modelo com: ollama pull qwen2.5:1.5b"
fi

echo ""
echo "Ambiente pronto. Comece pelo README.md."
echo "Os quatro processos do laboratorio sobem com: bash subir.sh"
