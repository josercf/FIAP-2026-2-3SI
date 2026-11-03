#!/usr/bin/env bash
# Mede o que a Frente 1 cobra: quanto tempo a plataforma leva para ficar
# saudável e quanta memória os treze serviços consomem em repouso.
#
#     ./scripts/medir.sh
#
# Derruba a plataforma antes de medir: medir uma subida que já estava de pé
# devolve um número que não significa nada.

set -uo pipefail
cd "$(dirname "$0")/.."

echo "== derrubando o que estiver de pé (o volume do banco é preservado)"
docker compose down --remove-orphans >/dev/null 2>&1

echo "== subindo e cronometrando"
INICIO=$(python3 -c 'import time;print(time.time())')
docker compose up -d --wait --wait-timeout 420
CODIGO=$?
FIM=$(python3 -c 'import time;print(time.time())')

python3 -c "print('TEMPO_ATE_TODOS_SAUDAVEIS_S: %.1f' % ($FIM - $INICIO))"

if [ "$CODIGO" -ne 0 ]; then
  echo
  echo "O --wait desistiu. Quem não ficou saudável:"
  docker compose ps -a --format '{{.Service}}\t{{.Status}}' | grep -v healthy
  echo
  echo "Registre em docs/EVIDENCIAS.md quantos dos 13 subiram, e siga o runbook."
fi

echo
echo "== esperando 10 s para a memória estabilizar"
sleep 10

docker stats --no-stream --format '{{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}' $(docker compose ps -q) | sort

docker stats --no-stream --format '{{.MemUsage}}' $(docker compose ps -q) \
  | awk -F'/' '{print $1}' | sed 's/MiB//; s/GiB/*1024/' \
  | python3 -c "
import sys
total = sum(eval(l.strip()) for l in sys.stdin if l.strip())
print()
print('MEMORIA_TOTAL_MB: %.0f' % total)
"

echo
echo "SERVICOS_SAUDAVEIS: $(docker compose ps --format '{{.Status}}' | grep -c healthy) de 13"
echo
echo "Copie os três valores para docs/EVIDENCIAS.md, junto com o MAQUINA."
