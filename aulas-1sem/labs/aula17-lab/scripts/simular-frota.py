#!/usr/bin/env python3
"""
LogiTech Enterprise - Simulador da frota.

SERVIÇO CONGELADO. NÃO É TAREFA DESTE LABORATÓRIO.
==================================================
Faz o papel dos rastreadores instalados nos 400 caminhões: emite posições por
UDP, sem parar, para o coletor da Aula 02. É a origem do fluxo contínuo que o
RxJS de vocês vai manipular hoje.

O payload é o mesmo da Aula 02, com dois campos que a Aula 11 usa:

    {
      "placa": "LGT1A01",
      "lat": -23.5505, "lng": -46.6333,
      "uf": "SP",
      "velocidade_kmh": 78,
      "temperatura_c": 4.2
    }

`uf` alimenta o filtro do painel (BehaviorSubject e combineLatest) e
`velocidade_kmh` alimenta o fluxo de alertas (filter e map). O coletor valida
apenas `placa`, `lat` e `lng`; os demais campos atravessam intactos até o
navegador.

Uso:
    python3 servicos/simulador/frota.py
    python3 servicos/simulador/frota.py --caminhoes 12 --intervalo 0.5
    python3 servicos/simulador/frota.py --excesso 0.35   # 35% acima de 90 km/h
"""

import argparse
import json
import random
import socket
import time

# Bases operacionais da LogiTech, uma por UF atendida. Os nomes e as
# coordenadas são fictícios e existem para o painel mostrar agrupamento
# plausível, não precisão cartográfica.
BASES = [
    ("SP", -23.5505, -46.6333),
    ("PR", -25.4284, -49.2733),
    ("MG", -19.9167, -43.9345),
    ("RS", -30.0346, -51.2177),
]

LIMITE_ALERTA_KMH = 90


def montar_frota(quantidade):
    """Placas determinísticas, para o painel ficar estável entre execuções."""
    frota = []
    for i in range(1, quantidade + 1):
        uf, lat, lng = BASES[(i - 1) % len(BASES)]
        frota.append({
            "placa": "LGT%dA%02d" % (i, i),
            "uf": uf,
            "lat": lat + random.uniform(-0.08, 0.08),
            "lng": lng + random.uniform(-0.08, 0.08),
        })
    return frota


def andar(caminhao, probabilidade_excesso):
    """Passo curto de rota, para o painel mostrar movimento plausível.

    A velocidade é sorteada em duas faixas: a normal, sempre abaixo do limite
    de alerta, e a de excesso. A proporção entre elas é parâmetro do
    simulador para que o laboratório consiga provocar alertas na hora que
    quiser, em vez de esperar a sorte.
    """
    caminhao["lat"] += random.uniform(-0.0035, 0.0035)
    caminhao["lng"] += random.uniform(-0.0035, 0.0035)

    if random.random() < probabilidade_excesso:
        velocidade = random.randint(LIMITE_ALERTA_KMH + 1, 128)
    else:
        velocidade = random.randint(0, LIMITE_ALERTA_KMH)

    return {
        "placa": caminhao["placa"],
        "uf": caminhao["uf"],
        "lat": round(caminhao["lat"], 6),
        "lng": round(caminhao["lng"], 6),
        "velocidade_kmh": velocidade,
        "temperatura_c": round(random.uniform(2.0, 8.0), 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Simulador da frota da LogiTech")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--porta-udp", type=int, default=8081)
    parser.add_argument("--caminhoes", type=int, default=12)
    parser.add_argument("--intervalo", type=float, default=1.0,
                        help="segundos entre rodadas de emissão")
    parser.add_argument("--excesso", type=float, default=0.2,
                        help="fração das emissões acima de %d km/h" % LIMITE_ALERTA_KMH)
    parser.add_argument("--duracao", type=float, default=0.0,
                        help="segundos de execução; 0 roda até o Ctrl+C")
    args = parser.parse_args()

    frota = montar_frota(args.caminhoes)
    emissor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inicio = time.time()
    enviadas = 0

    print("=== LogiTech Enterprise - Simulador da frota ===", flush=True)
    print("emitindo %d caminhões para %s:%d a cada %.2fs"
          % (args.caminhoes, args.host, args.porta_udp, args.intervalo), flush=True)
    print("UFs em operação: %s" % ", ".join(sorted({c["uf"] for c in frota})), flush=True)
    print("encerre com Ctrl+C", flush=True)

    try:
        while True:
            for caminhao in frota:
                posicao = andar(caminhao, args.excesso)
                emissor.sendto(
                    json.dumps(posicao).encode("utf-8"),
                    (args.host, args.porta_udp),
                )
                enviadas += 1
            if enviadas % (args.caminhoes * 10) == 0:
                print("%d posições emitidas" % enviadas, flush=True)
            if args.duracao and (time.time() - inicio) >= args.duracao:
                break
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        pass
    finally:
        emissor.close()
        print("\nencerrando. posições emitidas: %d" % enviadas, flush=True)


if __name__ == "__main__":
    main()
