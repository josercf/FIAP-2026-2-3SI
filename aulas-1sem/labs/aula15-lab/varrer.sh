#!/usr/bin/env bash
# Varredura das imagens do laboratório com o Trivy (ADR-009, seção 7).
#
#     ./varrer.sh            varre as quatro imagens e grava em relatorios/
#     ./varrer.sh --resumo   só reimprime o resumo do que já está em relatorios/
#
# Se o `trivy` estiver instalado, ele é usado. Se não, cai para a imagem
# oficial `aquasec/trivy`, que fala com o mesmo Docker daemon pelo socket. O
# resultado é idêntico e ninguém precisa instalar nada.
#
# A primeira execução baixa o banco de vulnerabilidades, uns 60 MB. As
# seguintes reaproveitam o cache em `.cache-trivy/`.

set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAIDA="$RAIZ/relatorios"
CACHE="$RAIZ/.cache-trivy"
mkdir -p "$SAIDA" "$CACHE"

# As três primeiras são construídas por você. A quarta não: é o banco que a
# Aula 12 trouxe, e ela está aqui justamente por isso. O critério de "zero
# CRITICAL" vale para as imagens do projeto; a de terceiro tem outro
# tratamento, e é o assunto do TODO-6.
IMAGENS=(
  "logitech-ai-gateway:aula15"
  "logitech-rag:aula15"
  "logitech-notificacoes:aula15"
  "pgvector/pgvector:pg16"
)

varrer() {
  local imagem="$1" destino="$2"
  if command -v trivy >/dev/null 2>&1; then
    trivy image --quiet --severity HIGH,CRITICAL --scanners vuln \
          --cache-dir "$CACHE" -f json "$imagem" > "$destino"
  else
    docker run --rm \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v "$CACHE:/root/.cache" \
      aquasec/trivy:latest image --quiet --severity HIGH,CRITICAL \
      --scanners vuln -f json "$imagem" > "$destino"
  fi
}

if [ "${1:-}" != "--resumo" ]; then
  for imagem in "${IMAGENS[@]}"; do
    destino="$SAIDA/$(echo "$imagem" | tr ':/' '__').json"
    echo ">>> varrendo $imagem"
    varrer "$imagem" "$destino"
    echo "    relatório em relatorios/$(basename "$destino")"
  done
fi

echo
python3 "$RAIZ/resumo_trivy.py"
