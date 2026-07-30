#!/usr/bin/env python3
"""
LogiTech Enterprise - Coletor de Telemetria na camada L4 (OSI).

Este e o servico da Aula 01, entregue pronto na Aula 02. Ele nao e tarefa:
e o ponto de partida sobre o qual voces constroem a camada HTTP/SSE.

Dois sockets, conforme o SDD:

  UDP 8081  telemetria de GPS dos caminhoes (UC01)
            frescor vale mais que completude, perder um datagrama e aceitavel

  TCP 8080  confirmacao de entrega assinada pelo motorista (UC02)
            integridade vale mais que milissegundos, precisa de ACK

Cada datagrama recebido e anexado a data/telemetria.jsonl, uma linha por
posicao. E dessa linha que o servidor HTTP da Aula 02 le.

Uso:
    python3 sockets-l4/server_telemetry.py
    python3 sockets-l4/server_telemetry.py --porta-udp 8081 --porta-tcp 8080
"""

import argparse
import json
import os
import socket
import threading
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DADOS = os.path.join(RAIZ, "data")
ARQ_TELEMETRIA = os.path.join(DIR_DADOS, "telemetria.jsonl")
ARQ_ENTREGAS = os.path.join(DIR_DADOS, "entregas.jsonl")

# Linguagem Ubiqua desta implementacao. Os mesmos nomes aparecem no JSON da
# API, nos eventos SSE e no painel. Se o SDD da sua dupla usa outros termos,
# reconcilie os dois: e exatamente esse o ponto do Code Review de hoje.
CAMPOS_OBRIGATORIOS = ("placa", "lat", "lng")

_trava_arquivo = threading.Lock()
_contadores = {"telemetria": 0, "entregas": 0, "invalidos": 0}


def agora_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def anexar(caminho, registro):
    """Grava um registro por linha (JSON Lines) com flush imediato.

    O flush importa: sem ele o servidor HTTP so enxergaria as posicoes
    quando o buffer do sistema operacional fosse descarregado.
    """
    linha = json.dumps(registro, ensure_ascii=False)
    with _trava_arquivo:
        with open(caminho, "a", encoding="utf-8") as arquivo:
            arquivo.write(linha + "\n")
            arquivo.flush()


def validar_posicao(dados):
    faltando = [c for c in CAMPOS_OBRIGATORIOS if c not in dados]
    if faltando:
        return "campos ausentes: %s" % ", ".join(faltando)
    return None


def escutar_udp(porta):
    """Telemetria de GPS. Fire-and-forget: nao existe resposta."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", porta))
    print("[UDP] telemetria de GPS escutando na porta %d" % porta)

    while True:
        dados, remetente = servidor.recvfrom(2048)
        try:
            posicao = json.loads(dados.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            _contadores["invalidos"] += 1
            print("[UDP] datagrama ilegivel de %s:%d, descartado" % remetente)
            continue

        erro = validar_posicao(posicao)
        if erro:
            _contadores["invalidos"] += 1
            print("[UDP] datagrama rejeitado de %s:%d, %s" % (remetente[0], remetente[1], erro))
            continue

        posicao["recebido_em"] = agora_iso()
        anexar(ARQ_TELEMETRIA, posicao)
        _contadores["telemetria"] += 1

        if _contadores["telemetria"] % 10 == 0:
            print("[UDP] %d posicoes gravadas em data/telemetria.jsonl"
                  % _contadores["telemetria"])


def atender_conexao(conexao, remetente):
    """Uma confirmacao de entrega. TCP: le, confirma e encerra."""
    try:
        dados = conexao.recv(2048)
        if not dados:
            return
        try:
            entrega = json.loads(dados.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            conexao.sendall(json.dumps({
                "status": "REJEITADO",
                "motivo": "payload nao e JSON valido",
            }).encode("utf-8"))
            return

        entrega["recebido_em"] = agora_iso()
        anexar(ARQ_ENTREGAS, entrega)
        _contadores["entregas"] += 1

        resposta = json.dumps({
            "status": "CONFIRMADO",
            "pedido": entrega.get("pedido"),
            "recebido_em": entrega["recebido_em"],
        })
        conexao.sendall(resposta.encode("utf-8"))
        print("[TCP] entrega confirmada: %s (de %s:%d)"
              % (entrega.get("pedido"), remetente[0], remetente[1]))
    finally:
        conexao.close()


def escutar_tcp(porta):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", porta))
    servidor.listen(8)
    print("[TCP] confirmacoes de entrega escutando na porta %d" % porta)

    while True:
        conexao, remetente = servidor.accept()
        threading.Thread(
            target=atender_conexao, args=(conexao, remetente), daemon=True
        ).start()


def main():
    parser = argparse.ArgumentParser(
        description="Coletor L4 de telemetria da LogiTech Enterprise")
    parser.add_argument("--porta-udp", type=int, default=8081)
    parser.add_argument("--porta-tcp", type=int, default=8080)
    args = parser.parse_args()

    os.makedirs(DIR_DADOS, exist_ok=True)

    print("=== LogiTech Enterprise - Telemetry Service (camada L4) ===")
    print("gravando telemetria em %s" % ARQ_TELEMETRIA)
    print("gravando entregas   em %s" % ARQ_ENTREGAS)
    print("encerre com Ctrl+C")

    threading.Thread(target=escutar_udp, args=(args.porta_udp,), daemon=True).start()
    threading.Thread(target=escutar_tcp, args=(args.porta_tcp,), daemon=True).start()

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nencerrando. posicoes: %d, entregas: %d, descartados: %d"
              % (_contadores["telemetria"], _contadores["entregas"],
                 _contadores["invalidos"]))


if __name__ == "__main__":
    main()
