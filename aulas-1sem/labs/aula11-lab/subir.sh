#!/usr/bin/env bash
# Sobe os quatro processos congelados de que o painel administrativo depende.
#
# Por que um script e nao quatro terminais: sao quatro processos so para o
# painel ter o que consumir, e nenhum deles e tarefa desta aula. Gastar dez
# dos sessenta minutos abrindo terminal seria gastar a aula com o cenario em
# vez do conteudo.
#
#   coletor      UDP 8081, TCP 8080, HTTP 8082   telemetria (Aula 02)
#   simulador    emite posicoes por UDP           a frota fingindo existir
#   painel       HTTP 3000                        SSE que o Angular consome
#   faturamento  HTTP 5080                        C#/.NET (Aula 05)
#
# O Angular NAO sobe aqui: `cd painel-admin && npm start` e trabalho de voces.
#
# Uso:
#   bash subir.sh
#   bash derrubar.sh    para encerrar tudo
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS="$RAIZ/.logs"
mkdir -p "$LOGS" "$RAIZ/dados"

porta_ocupada() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -i ":$1" >/dev/null 2>&1
  else
    curl -sf --connect-timeout 1 "http://localhost:$1/health" >/dev/null 2>&1
  fi
}

for porta in 3000 5080 8082; do
  if porta_ocupada "$porta"; then
    echo "A porta $porta ja esta ocupada. Encerre o processo antes (bash derrubar.sh)."
    exit 1
  fi
done

echo "==> coletor de telemetria (8081/udp, 8080/tcp, 8082/http)"
LOGITECH_DADOS="$RAIZ/dados/telemetria.jsonl" \
  nohup python3 "$RAIZ/servicos/coletor/server_telemetry.py" > "$LOGS/coletor.log" 2>&1 &
echo $! > "$LOGS/coletor.pid"
sleep 2

echo "==> simulador da frota (12 caminhoes, 1 posicao por segundo)"
nohup python3 "$RAIZ/servicos/simulador/frota.py" --caminhoes 12 --intervalo 1 --excesso 0.25 \
  > "$LOGS/simulador.log" 2>&1 &
echo $! > "$LOGS/simulador.pid"

echo "==> painel de rastreamento (3000, SSE com CORS)"
nohup node "$RAIZ/servicos/painel/server.js" > "$LOGS/painel.log" 2>&1 &
echo $! > "$LOGS/painel.pid"

echo "==> servico de faturamento (5080, C#/.NET, atraso deliberado de 800 ms)"
nohup dotnet run --project "$RAIZ/servicos/faturamento" > "$LOGS/faturamento.log" 2>&1 &
echo $! > "$LOGS/faturamento.pid"

echo ""
echo "Aguardando as sondas de saude responderem..."
for _ in $(seq 1 60); do
  ok=0
  curl -sf --connect-timeout 1 http://localhost:8082/health >/dev/null 2>&1 && ok=$((ok+1))
  curl -sf --connect-timeout 1 http://localhost:3000/health >/dev/null 2>&1 && ok=$((ok+1))
  curl -sf --connect-timeout 1 http://localhost:5080/health >/dev/null 2>&1 && ok=$((ok+1))
  [ "$ok" -eq 3 ] && break
  sleep 1
done

echo ""
for alvo in "coletor http://localhost:8082/health" \
            "painel http://localhost:3000/health" \
            "faturamento http://localhost:5080/health"; do
  set -- $alvo
  if curl -sf --connect-timeout 2 "$2" >/dev/null 2>&1; then
    echo "  [OK]    $1"
  else
    echo "  [FALHA] $1  (veja $LOGS/$1.log)"
  fi
done

echo ""
echo "Agora suba o painel administrativo:  cd painel-admin && npm start"
echo "E abra                               http://localhost:4200"
