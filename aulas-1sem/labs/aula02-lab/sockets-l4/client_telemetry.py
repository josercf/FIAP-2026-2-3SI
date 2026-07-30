#!/usr/bin/env python3
"""
LogiTech Enterprise - Simulador de frota.

Faz o papel dos rastreadores instalados nos caminhoes: emite posicoes por
UDP continuamente e, de tempos em tempos, uma confirmacao de entrega por TCP.

Uso:
    python3 sockets-l4/client_telemetry.py
    python3 sockets-l4/client_telemetry.py --caminhoes 5 --intervalo 1
    python3 sockets-l4/client_telemetry.py --duracao 60
"""

import argparse
import json
import random
import socket
import time

# Ponto de partida: regiao metropolitana de Sao Paulo.
LAT_BASE = -23.5505
LNG_BASE = -46.6333


def montar_frota(quantidade):
    """Placas deterministicas, para o painel ficar estavel entre execucoes."""
    frota = []
    for i in range(1, quantidade + 1):
        frota.append({
            "placa": "LGT%dA%02d" % (i, i),
            "lat": LAT_BASE + random.uniform(-0.08, 0.08),
            "lng": LNG_BASE + random.uniform(-0.08, 0.08),
        })
    return frota


def andar(caminhao):
    """Passo curto de rota, para o painel mostrar movimento plausivel."""
    caminhao["lat"] += random.uniform(-0.0035, 0.0035)
    caminhao["lng"] += random.uniform(-0.0035, 0.0035)
    return {
        "placa": caminhao["placa"],
        "lat": round(caminhao["lat"], 6),
        "lng": round(caminhao["lng"], 6),
        "velocidade_kmh": random.randint(0, 95),
        "temperatura_c": round(random.uniform(2.0, 8.0), 1),
    }


def enviar_confirmacao_entrega(host, porta, placa, sequencia):
    """TCP: precisa de resposta, entao a conexao e aberta e aguardada."""
    pedido = "PED-%05d" % sequencia
    try:
        with socket.create_connection((host, porta), timeout=3) as conexao:
            payload = json.dumps({
                "pedido": pedido,
                "placa": placa,
                "status": "ENTREGUE",
                "assinatura": "OK",
            })
            conexao.sendall(payload.encode("utf-8"))
            resposta = conexao.recv(1024).decode("utf-8")
            print("[TCP] %s -> %s" % (pedido, resposta))
    except OSError as erro:
        print("[TCP] falha ao confirmar %s: %s" % (pedido, erro))


def main():
    parser = argparse.ArgumentParser(description="Simulador de frota da LogiTech")
    parser.add_argument("--caminhoes", type=int, default=5,
                        help="quantos caminhoes emitem telemetria (padrao 5)")
    parser.add_argument("--intervalo", type=float, default=1.0,
                        help="segundos entre rodadas de envio (padrao 1.0)")
    parser.add_argument("--duracao", type=int, default=0,
                        help="segundos de simulacao, 0 para rodar ate Ctrl+C")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--porta-udp", type=int, default=8081)
    parser.add_argument("--porta-tcp", type=int, default=8080)
    args = parser.parse_args()

    frota = montar_frota(args.caminhoes)
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("simulando %d caminhoes, 1 posicao a cada %.1fs"
          % (args.caminhoes, args.intervalo))
    print("encerre com Ctrl+C")

    inicio = time.time()
    rodada = 0
    enviados = 0

    try:
        while True:
            rodada += 1
            for caminhao in frota:
                posicao = andar(caminhao)
                socket_udp.sendto(
                    json.dumps(posicao).encode("utf-8"),
                    (args.host, args.porta_udp),
                )
                enviados += 1

            if rodada % 10 == 0:
                print("[UDP] %d posicoes enviadas" % enviados)
                enviar_confirmacao_entrega(
                    args.host, args.porta_tcp,
                    random.choice(frota)["placa"], rodada // 10,
                )

            if args.duracao and (time.time() - inicio) >= args.duracao:
                break
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        pass
    finally:
        socket_udp.close()
        print("\nsimulacao encerrada. %d posicoes enviadas." % enviados)


if __name__ == "__main__":
    main()
