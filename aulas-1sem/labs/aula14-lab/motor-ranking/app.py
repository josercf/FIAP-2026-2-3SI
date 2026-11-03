"""HTTP do motor de ranking. Não abre banco e não chama outro serviço."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ranking import ModalidadeDesconhecida, TabelaDePesos, calcular

PORTA = 8000
TABELA = TabelaDePesos()
RIVAIS = json.loads(Path(__file__).with_name("rivalidade.json").read_text(encoding="utf-8"))


class Manipulador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/health":
            self._json(200, {"status": "ok"})
            return
        self._json(404, {"erro": "nao encontrado"})

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/v1/ranking":
            self._json(404, {"erro": "nao encontrado"})
            return
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            corpo = json.loads(self.rfile.read(tamanho) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"erro": "json invalido"})
            return
        try:
            resultado = calcular(
                corpo.get("modalidade"),
                corpo.get("campus", ""),
                bool(corpo.get("serie")),
                TABELA,
                RIVAIS,
            )
        except ModalidadeDesconhecida:
            self._json(400, {"erro": "modalidade desconhecida"})
            return
        except NotImplementedError as erro:
            self._json(501, {"erro": str(erro)})
            return
        self._json(200, resultado)

    def do_OPTIONS(self):
        self._json(204, {})

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


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORTA), Manipulador).serve_forever()
