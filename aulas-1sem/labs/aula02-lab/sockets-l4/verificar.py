#!/usr/bin/env python3
"""
Verificacao do Passo 2: o coletor UDP que voce completou.

Rode com o coletor no ar, em outro terminal:

    python3 sockets-l4/server_telemetry.py     # terminal 1
    python3 sockets-l4/verificar.py            # terminal 2

Este script manda datagramas de propria conta, entao voce NAO precisa do
client_telemetry.py rodando junto. Ele confere quatro criterios e sai com
codigo 1 se algum falhar.

Sem dependencias: so a biblioteca padrao.
"""

import json
import os
import socket
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_TELEMETRIA = os.path.join(RAIZ, "data", "telemetria.jsonl")

HOST = "127.0.0.1"
PORTA = int(os.environ.get("PORTA_UDP", "8081"))
CAMPOS = ("placa", "lat", "lng", "recebido_em")

resultados = []


def registrar(codigo, descricao, passou, detalhe=""):
    resultados.append(passou)
    print("[%s] %s  %s" % ("PASSOU" if passou else "FALHOU", codigo, descricao))
    if detalhe:
        print("         %s" % detalhe)


def ler_linhas():
    if not os.path.exists(ARQ_TELEMETRIA):
        return []
    with open(ARQ_TELEMETRIA, "r", encoding="utf-8") as arquivo:
        return [linha for linha in arquivo.read().splitlines() if linha.strip()]


def enviar(payload_bytes, quantidade=1, intervalo=0.05):
    emissor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        for _ in range(quantidade):
            emissor.sendto(payload_bytes, (HOST, PORTA))
            time.sleep(intervalo)
    finally:
        emissor.close()


def posicao_valida(indice):
    return json.dumps({
        "placa": "VRF-%04d" % (1000 + indice),
        "lat": -23.5505 + indice * 0.001,
        "lng": -46.6333 + indice * 0.001,
        "velocidade": 60 + indice,
    }).encode("utf-8")


print("Verificando o coletor UDP em %s:%d\n" % (HOST, PORTA))

antes = len(ler_linhas())

# --- CA-L4-01: o coletor recebe e grava -----------------------------------
for i in range(5):
    enviar(posicao_valida(i))
time.sleep(1.0)

depois = len(ler_linhas())
cresceu = depois > antes
registrar(
    "CA-L4-01",
    "O coletor grava as posicoes recebidas em data/telemetria.jsonl",
    cresceu,
    "" if cresceu else (
        "o arquivo tinha %d linhas e continua com %d. O coletor esta no ar? "
        "Os TODO 1 a 4 de escutar_udp foram implementados?" % (antes, depois)),
)

linhas_novas = ler_linhas()[antes:]

# --- CA-L4-02: cada linha e um JSON valido --------------------------------
registros = []
quebradas = 0
for linha in linhas_novas:
    try:
        registros.append(json.loads(linha))
    except json.JSONDecodeError:
        quebradas += 1

registrar(
    "CA-L4-02",
    "Cada linha do arquivo e um JSON valido, uma posicao por linha",
    bool(registros) and quebradas == 0,
    "" if registros and not quebradas else
    "%d linha(s) ilegivel(is) de %d. Grave com json.dumps e um \\n no fim."
    % (quebradas, len(linhas_novas)),
)

# --- CA-L4-03: os campos da Linguagem Ubiqua estao la ---------------------
if registros:
    ausentes = sorted({c for c in CAMPOS for r in registros if c not in r})
    completo = not ausentes
else:
    ausentes = list(CAMPOS)
    completo = False

registrar(
    "CA-L4-03",
    "As posicoes trazem placa, lat, lng e recebido_em",
    completo,
    "" if completo else
    "faltando em pelo menos um registro: %s. O campo recebido_em e o "
    "carimbo do servidor, via agora_iso()." % ", ".join(ausentes),
)

# --- CA-L4-04 e CA-L4-05: robustez a datagrama ruim -----------------------
# So fazem sentido se o coletor ja estiver gravando. Sem isso, "nada foi
# gravado" passaria por "descartou corretamente", que e um falso positivo.
if not cresceu:
    inconclusivo = "o coletor nao gravou nada: resolva o CA-L4-01 primeiro"
    registrar("CA-L4-04",
              "Datagrama ilegivel ou incompleto e descartado, e o coletor continua no ar",
              False, inconclusivo)
    registrar("CA-L4-05", "O coletor continua gravando depois de receber lixo",
              False, inconclusivo)
else:
    marca = len(ler_linhas())
    enviar(b"\xff\xfe isto nao e json \x00")
    enviar(json.dumps({"placa": "SEM-GPS"}).encode("utf-8"))  # faltam lat e lng
    time.sleep(1.0)
    apos_lixo = len(ler_linhas())

    descartou = apos_lixo == marca
    registrar(
        "CA-L4-04",
        "Datagrama ilegivel ou incompleto e descartado, e o coletor continua no ar",
        descartou,
        "" if descartou else
        "o arquivo cresceu de %d para %d linhas depois de dois datagramas ruins. "
        "Valide antes de gravar e siga com continue." % (marca, apos_lixo),
    )

    enviar(posicao_valida(99))
    time.sleep(1.0)
    vivo = len(ler_linhas()) > apos_lixo
    registrar(
        "CA-L4-05",
        "O coletor continua gravando depois de receber lixo",
        vivo,
        "" if vivo else
        "nada foi gravado depois dos datagramas ruins. Um pacote corrompido nao "
        "pode derrubar o laco: trate a excecao e use continue.",
    )

falhas = resultados.count(False)
print("\n%d de %d criterios atendidos." % (len(resultados) - falhas, len(resultados)))

if falhas:
    print("Corrija os TODO de escutar_udp e rode de novo.")
    sys.exit(1)

print("Coletor L4 aprovado. Siga para o Passo 3.")
