#!/usr/bin/env python3
"""
LogiTech Enterprise - Coletor de Telemetria.

SERVIÇO CONGELADO. NÃO É TAREFA DESTE LABORATÓRIO.
==================================================
Ele nasceu na Aula 02, ganhou a API HTTP na Aula 07 e chega aqui exatamente
como vocês o deixaram. Não editem este arquivo. O artefato da Aula 11 é o
painel administrativo em Angular, dentro de `painel-admin/`.

Por que ele está aqui: é ele que produz o fluxo contínuo que o RxJS de hoje
tem para manipular. Sem posição de caminhão chegando o tempo todo, o
`Observable` do laboratório emitiria um valor e completaria, virando uma
Promise com nome diferente.

Os três sockets, herdados das Aulas 02 e 07:

  UDP 8081/udp   telemetria de GPS dos caminhões (UC01)
                 frescor vale mais que completude, perder um datagrama é
                 aceitável

  TCP 8080/tcp   confirmação de entrega assinada pelo motorista (UC02)
                 integridade vale mais que milissegundos, precisa de ACK
                 (interno à rede do Compose, não é publicado no host)

  HTTP 8082/tcp  a API de leitura da telemetria
                 GET /health      -> {"status": "ok"}
                 GET /telemetria  -> a última posição conhecida de cada placa

O painel consome `GET /telemetria` e reemite cada mudança como evento SSE
em `GET /api/v1/eventos`. O endereço vem de `LOGITECH_TELEMETRIA_URL`.

Este serviço não precisa de CORS: nenhum navegador fala com ele. Quem o
navegador chama é o painel, na porta 3000, e é lá que a ADR-008 manda ligar
o CORS.

Uso:
    python3 servicos/coletor/server_telemetry.py
    LOGITECH_DADOS=/tmp/t.jsonl python3 servicos/coletor/server_telemetry.py
"""

import argparse
import json
import os
import socket
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DIR_SERVICO = os.path.dirname(os.path.abspath(__file__))
RAIZ_LAB = os.path.dirname(os.path.dirname(DIR_SERVICO))
CAMINHO_DADOS = os.environ.get(
    "LOGITECH_DADOS", os.path.join(RAIZ_LAB, "dados", "telemetria.jsonl")
)
DIR_DADOS = os.path.dirname(CAMINHO_DADOS) or "."
ARQ_TELEMETRIA = CAMINHO_DADOS
ARQ_ENTREGAS = os.path.join(DIR_DADOS, "entregas.jsonl")

# Linguagem Ubíqua desta implementação. Os mesmos nomes aparecem no JSON da
# API, nos eventos SSE do painel e na tela do operador.
CAMPOS_OBRIGATORIOS = ("placa", "lat", "lng")

_trava_arquivo = threading.Lock()
_trava_memoria = threading.Lock()
_contadores = {"telemetria": 0, "entregas": 0, "invalidos": 0, "consultas_http": 0}

# Última posição conhecida por placa, mantida em memória para que
# GET /telemetria responda sem reler o arquivo inteiro a cada chamada.
_ultima_por_placa = {}

INICIADO_EM = datetime.now(timezone.utc)


def agora_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def anexar(caminho, registro):
    """Grava um registro por linha (JSON Lines) com flush imediato."""
    linha = json.dumps(registro, ensure_ascii=False)
    with _trava_arquivo:
        with open(caminho, "a", encoding="utf-8") as arquivo:
            arquivo.write(linha + "\n")
            arquivo.flush()


def carregar_do_disco():
    """Recompõe a última posição por placa a partir do arquivo.

    Chamado uma única vez na subida. É o que faz o coletor reiniciado dentro
    do Compose voltar já sabendo onde a frota estava, em vez de responder uma
    lista vazia até o próximo datagrama chegar.
    """
    if not os.path.exists(ARQ_TELEMETRIA):
        return 0
    lidas = 0
    with open(ARQ_TELEMETRIA, encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha:
                continue
            try:
                posicao = json.loads(linha)
            except json.JSONDecodeError:
                continue
            if posicao.get("placa"):
                _ultima_por_placa[posicao["placa"]] = posicao
                lidas += 1
    return lidas


def registrar_posicao(posicao):
    anexar(ARQ_TELEMETRIA, posicao)
    with _trava_memoria:
        _ultima_por_placa[posicao["placa"]] = posicao
        _contadores["telemetria"] += 1


def validar_posicao(dados):
    faltando = [c for c in CAMPOS_OBRIGATORIOS if c not in dados]
    if faltando:
        return "campos ausentes: %s" % ", ".join(faltando)
    return None


def instantaneo_da_frota():
    """A fotografia que a rota GET /telemetria devolve."""
    with _trava_memoria:
        posicoes = sorted(_ultima_por_placa.values(), key=lambda p: p["placa"])
        _contadores["consultas_http"] += 1
    return {
        "atualizado_em": agora_iso(),
        "total": len(posicoes),
        "posicoes": posicoes,
    }


# ---------------------------------------------------------------------------
# Camada 4: os dois sockets herdados da Aula 02
# ---------------------------------------------------------------------------


def escutar_udp(porta):
    """Telemetria de GPS. Fire-and-forget: não existe resposta."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", porta))
    print("[UDP] telemetria de GPS escutando na porta %d" % porta, flush=True)

    while True:
        dados, remetente = servidor.recvfrom(2048)
        try:
            posicao = json.loads(dados.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            _contadores["invalidos"] += 1
            print("[UDP] datagrama ilegível de %s:%d, descartado" % remetente, flush=True)
            continue

        erro = validar_posicao(posicao)
        if erro:
            _contadores["invalidos"] += 1
            print("[UDP] datagrama rejeitado de %s:%d, %s"
                  % (remetente[0], remetente[1], erro), flush=True)
            continue

        posicao["recebido_em"] = agora_iso()
        registrar_posicao(posicao)

        if _contadores["telemetria"] % 10 == 0:
            print("[UDP] %d posições gravadas em %s"
                  % (_contadores["telemetria"], ARQ_TELEMETRIA), flush=True)


def atender_conexao(conexao, remetente):
    """Uma confirmação de entrega. TCP: lê, confirma e encerra."""
    try:
        dados = conexao.recv(2048)
        if not dados:
            return
        try:
            entrega = json.loads(dados.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            conexao.sendall(json.dumps({
                "status": "REJEITADO",
                "motivo": "payload não é JSON válido",
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
              % (entrega.get("pedido"), remetente[0], remetente[1]), flush=True)
    finally:
        conexao.close()


def escutar_tcp(porta):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", porta))
    servidor.listen(8)
    print("[TCP] confirmações de entrega escutando na porta %d" % porta, flush=True)

    while True:
        conexao, remetente = servidor.accept()
        threading.Thread(
            target=atender_conexao, args=(conexao, remetente), daemon=True
        ).start()


# ---------------------------------------------------------------------------
# Camada 7: a API de leitura, novidade da Aula 07
# ---------------------------------------------------------------------------


class ApiTelemetria(BaseHTTPRequestHandler):
    """Servidor HTTP mínimo, só com a biblioteca padrão.

    Duas rotas, as duas do contrato da plataforma (ADR-006): `/health`, que o
    `healthcheck` do Compose consulta, e `/telemetria`, que o painel consome
    no lugar do arquivo compartilhado.
    """

    server_version = "LogiTechColetor/2.0"

    def _responder(self, status, corpo):
        texto = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(texto)))
        self.end_headers()
        self.wfile.write(texto)

    def do_GET(self):  # noqa: N802 (nome imposto pela BaseHTTPRequestHandler)
        rota = self.path.split("?", 1)[0]

        if rota == "/health":
            segundos = int((datetime.now(timezone.utc) - INICIADO_EM).total_seconds())
            return self._responder(200, {
                "status": "ok",
                "servico": "coletor",
                "uptime_s": segundos,
                "placas_conhecidas": len(_ultima_por_placa),
                "posicoes_recebidas": _contadores["telemetria"],
            })

        if rota == "/telemetria":
            return self._responder(200, instantaneo_da_frota())

        return self._responder(404, {
            "erro": "rota não encontrada",
            "rota": rota,
            "disponiveis": ["/health", "/telemetria"],
        })

    def log_message(self, formato, *args):
        """Silencia o log de acesso linha a linha.

        O `healthcheck` do Compose bate em `/health` a cada dez segundos e o
        painel consulta `/telemetria` a cada segundo: sem isso, o
        `docker compose logs` do coletor vira ruído puro e esconde as
        mensagens que importam.
        """
        return


def servir_http(porta):
    servidor = ThreadingHTTPServer(("0.0.0.0", porta), ApiTelemetria)
    print("[HTTP] API de telemetria escutando na porta %d "
          "(GET /health, GET /telemetria)" % porta, flush=True)
    servidor.serve_forever()


def main():
    parser = argparse.ArgumentParser(
        description="Coletor de telemetria da LogiTech Enterprise")
    parser.add_argument("--porta-udp", type=int,
                        default=int(os.environ.get("LOGITECH_PORTA_UDP", 8081)))
    parser.add_argument("--porta-tcp", type=int,
                        default=int(os.environ.get("LOGITECH_PORTA_TCP", 8080)))
    parser.add_argument("--porta-http", type=int,
                        default=int(os.environ.get("LOGITECH_PORTA_HTTP", 8082)))
    args = parser.parse_args()

    os.makedirs(DIR_DADOS, exist_ok=True)
    recuperadas = carregar_do_disco()

    print("=== LogiTech Enterprise - Coletor de Telemetria ===", flush=True)
    print("gravando telemetria em %s" % ARQ_TELEMETRIA, flush=True)
    print("gravando entregas   em %s" % ARQ_ENTREGAS, flush=True)
    print("posições recuperadas do disco na subida: %d" % recuperadas, flush=True)
    print("encerre com Ctrl+C", flush=True)

    threading.Thread(target=escutar_udp, args=(args.porta_udp,), daemon=True).start()
    threading.Thread(target=escutar_tcp, args=(args.porta_tcp,), daemon=True).start()

    try:
        servir_http(args.porta_http)
    except KeyboardInterrupt:
        print("\nencerrando. posições: %d, entregas: %d, descartados: %d, "
              "consultas HTTP: %d"
              % (_contadores["telemetria"], _contadores["entregas"],
                 _contadores["invalidos"], _contadores["consultas_http"]), flush=True)


if __name__ == "__main__":
    main()
