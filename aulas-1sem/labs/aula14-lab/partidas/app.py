"""HTTP de partidas. Fala com elenco e com o motor pelo nome DNS do Compose."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

import psycopg

from ciclo import TransicaoRecusada, transicionar
from orquestrar import (
    AtletaInexistente,
    MissaoPendente,
    MotorIndisponivel,
    PedidoInvalido,
    abrir_desafio,
)
from serie import eh_serie

PORTA = 8080


def _agora():
    return datetime.now(timezone.utc)


def _iso(valor):
    if valor is None:
        return None
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc).isoformat()


class ElencoHttp:
    def __init__(self, base):
        self.base = base.rstrip("/")

    def obter(self, atleta_id):
        if not atleta_id:
            return None
        url = f"{self.base}/api/v1/atletas/{atleta_id}"
        try:
            with urlopen(url, timeout=4) as resposta:
                return json.loads(resposta.read().decode("utf-8"))
        except HTTPError as erro:
            if erro.code == 404:
                return None
            raise MotorIndisponivel("elenco") from erro
        except URLError as erro:
            raise MotorIndisponivel("elenco") from erro


class MotorHttp:
    def __init__(self, base):
        self.base = base.rstrip("/")

    def ranquear(self, modalidade, campus, serie):
        corpo = json.dumps(
            {"modalidade": modalidade, "campus": campus, "serie": bool(serie)}
        ).encode("utf-8")
        requisicao = Request(
            f"{self.base}/api/v1/ranking",
            data=corpo,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(requisicao, timeout=4) as resposta:
                return json.loads(resposta.read().decode("utf-8"))
        except HTTPError as erro:
            detalhe = erro.read().decode("utf-8", errors="replace")
            if erro.code == 501:
                raise MissaoPendente(detalhe) from erro
            if erro.code >= 500:
                raise MotorIndisponivel(detalhe) from erro
            raise PedidoInvalido("motor") from erro
        except URLError as erro:
            raise MotorIndisponivel("motor") from erro


class RepositorioPostgres:
    def __init__(self, conexao):
        self.conexao = conexao

    def existe_serie(self, modalidade, campus, agora):
        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT modalidade, campus, status, criado_em
                FROM partidas.desafios
                WHERE modalidade = %s
                """,
                (modalidade,),
            )
            linhas = cursor.fetchall()
        for modalidade_db, campus_db, status, criado in linhas:
            anterior = {
                "modalidade": modalidade_db,
                "campus": campus_db,
                "status": status,
                "criado_em": criado,
            }
            if eh_serie(anterior, modalidade, campus, agora):
                return True
        return False

    def inserir(self, desafio):
        identificador = str(uuid.uuid4())
        criado = _agora()
        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO partidas.desafios (
                    id, atleta_id, modalidade, descricao, campus,
                    latitude, longitude, status, pontos, faixa,
                    janela_horas, serie, criado_em
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
                """,
                (
                    identificador,
                    desafio["atletaId"],
                    desafio["modalidade"],
                    desafio["descricao"],
                    desafio["campus"],
                    desafio["latitude"],
                    desafio["longitude"],
                    desafio["status"],
                    desafio["pontos"],
                    desafio["faixa"],
                    desafio["janelaHoras"],
                    desafio["serie"],
                    criado,
                ),
            )
        return self.obter(identificador)

    def obter(self, identificador):
        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, atleta_id, modalidade, descricao, campus,
                       latitude, longitude, status, pontos, faixa,
                       janela_horas, serie, criado_em
                FROM partidas.desafios
                WHERE id = %s
                """,
                (identificador,),
            )
            linha = cursor.fetchone()
        if linha is None:
            return None
        return _linha(linha)

    def listar(self, campus, status):
        clausulas = []
        valores = []
        if campus:
            clausulas.append("campus = %s")
            valores.append(campus)
        if status:
            clausulas.append("status = %s")
            valores.append(status)
        onde = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        with self.conexao.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT id, atleta_id, modalidade, descricao, campus,
                       latitude, longitude, status, pontos, faixa,
                       janela_horas, serie, criado_em
                FROM partidas.desafios
                {onde}
                ORDER BY criado_em
                """,
                valores,
            )
            return [_linha(linha) for linha in cursor.fetchall()]

    def atualizar_status(self, identificador, destino):
        with self.conexao.cursor() as cursor:
            cursor.execute(
                "UPDATE partidas.desafios SET status = %s WHERE id = %s",
                (destino, identificador),
            )
        return self.obter(identificador)


def _linha(linha):
    (
        identificador,
        atleta_id,
        modalidade,
        descricao,
        campus,
        latitude,
        longitude,
        status,
        pontos,
        faixa,
        janela_horas,
        serie,
        criado,
    ) = linha
    return {
        "id": str(identificador),
        "atletaId": str(atleta_id),
        "modalidade": modalidade,
        "descricao": descricao,
        "campus": campus,
        "latitude": latitude,
        "longitude": longitude,
        "status": status,
        "pontos": pontos,
        "faixa": faixa,
        "janelaHoras": janela_horas,
        "serie": bool(serie),
        "criadoEm": _iso(criado),
    }


def conectar():
    url = os.environ["DATABASE_URL"]
    ultimo = None
    for _ in range(30):
        try:
            return psycopg.connect(url, autocommit=True)
        except psycopg.OperationalError as erro:
            ultimo = erro
            time.sleep(1)
    raise SystemExit(f"postgres indisponivel: {ultimo}")


class Fabrica:
    def __init__(self, repositorio, elenco, motor):
        self.repositorio = repositorio
        self.elenco = elenco
        self.motor = motor

    def handler(self):
        repositorio = self.repositorio
        elenco = self.elenco
        motor = self.motor

        class Manipulador(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self):
                caminho = urlparse(self.path)
                if caminho.path == "/health":
                    self._json(200, {"status": "ok"})
                    return
                if caminho.path == "/api/v1/desafios":
                    consulta = parse_qs(caminho.query)
                    campus = (consulta.get("campus") or [None])[0]
                    status = (consulta.get("status") or [None])[0]
                    self._json(200, repositorio.listar(campus, status))
                    return
                partes = caminho.path.strip("/").split("/")
                if len(partes) == 4 and partes[:3] == ["api", "v1", "desafios"]:
                    achado = repositorio.obter(partes[3])
                    if achado is None:
                        self._json(404, {"erro": "desafio nao encontrado"})
                        return
                    self._json(200, achado)
                    return
                self._json(404, {"erro": "nao encontrado"})

            def do_POST(self):
                caminho = urlparse(self.path).path
                if caminho != "/api/v1/desafios":
                    self._json(404, {"erro": "nao encontrado"})
                    return
                try:
                    pedido = self._corpo()
                except json.JSONDecodeError:
                    self._json(400, {"erro": "json invalido"})
                    return
                try:
                    criado = abrir_desafio(
                        pedido, elenco, motor, repositorio, _agora()
                    )
                except PedidoInvalido as erro:
                    self._json(400, {"erro": erro.motivo})
                    return
                except AtletaInexistente:
                    self._json(404, {"erro": "atleta nao encontrado"})
                    return
                except MissaoPendente as erro:
                    self._json(501, {"erro": str(erro)})
                    return
                except MotorIndisponivel:
                    self._json(503, {"erro": "vizinho indisponivel"})
                    return
                self._json(201, criado)

            def do_PATCH(self):
                caminho = urlparse(self.path).path
                marcador = "/api/v1/desafios/"
                sufixo = "/status"
                if not (caminho.startswith(marcador) and caminho.endswith(sufixo)):
                    self._json(404, {"erro": "nao encontrado"})
                    return
                identificador = caminho[len(marcador) : -len(sufixo)]
                atual = repositorio.obter(identificador)
                if atual is None:
                    self._json(404, {"erro": "desafio nao encontrado"})
                    return
                try:
                    corpo = self._corpo()
                except json.JSONDecodeError:
                    self._json(400, {"erro": "json invalido"})
                    return
                destino = corpo.get("status")
                try:
                    transicionar(atual["status"], destino)
                except NotImplementedError as erro:
                    self._json(501, {"erro": str(erro)})
                    return
                except TransicaoRecusada:
                    self._json(409, {"erro": "transicao recusada"})
                    return
                self._json(200, repositorio.atualizar_status(identificador, destino))

            def do_OPTIONS(self):
                self._json(204, {})

            def _corpo(self):
                tamanho = int(self.headers.get("Content-Length", "0"))
                return json.loads(self.rfile.read(tamanho) or b"{}")

            def _json(self, status, corpo):
                dados = json.dumps(corpo).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(dados)))
                self.end_headers()
                self.wfile.write(dados)

            def log_message(self, formato, *args):
                return

        return Manipulador


def main():
    conexao = conectar()
    fabrica = Fabrica(
        RepositorioPostgres(conexao),
        ElencoHttp(os.environ["ELENCO_URL"]),
        MotorHttp(os.environ["MOTOR_URL"]),
    )
    ThreadingHTTPServer(("0.0.0.0", PORTA), fabrica.handler()).serve_forever()


if __name__ == "__main__":
    main()
