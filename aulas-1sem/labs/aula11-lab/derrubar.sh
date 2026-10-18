#!/usr/bin/env bash
# Encerra os quatro processos subidos pelo subir.sh.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS="$RAIZ/.logs"

for servico in faturamento painel simulador coletor; do
  arquivo="$LOGS/$servico.pid"
  if [ -f "$arquivo" ]; then
    pid="$(cat "$arquivo")"
    if kill "$pid" 2>/dev/null; then
      echo "  encerrado: $servico (pid $pid)"
    else
      echo "  ja estava fora: $servico"
    fi
    rm -f "$arquivo"
  fi
done

# O `dotnet run` sobe um processo filho que nao morre com o pai.
pkill -f "servicos/faturamento" 2>/dev/null && echo "  encerrado: processo filho do dotnet run"

echo "Tudo encerrado."
