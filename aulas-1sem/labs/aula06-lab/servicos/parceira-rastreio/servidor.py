#!/usr/bin/env python3
"""Rastreamento da transportadora parceira: CONGELADO, NÃO É TAREFA.

Este serviço faz o papel do sistema de uma empresa **de fora**. Ele está
aqui para ter um formato legado de verdade contra o qual o Adapter da lacuna
TODO-4 trabalha, e não para ser modificado: mexer nele é exatamente o que
não se pode fazer com a API de um terceiro.

Note o formato da resposta, que é o ponto: campos abreviados em maiúsculas,
data em `dd/MM/aaaa HH:mm` e vocabulário de situação próprio. Nada disso
combina com o vocabulário da LogiTech, e nada disso pode entrar no nosso
sistema sem passar pelo Adapter.

Sem dependências: só a biblioteca padrão do Python.

Uso:
    python3 servicos/parceira-rastreio/servidor.py          # porta 9090
    PORT=9999 python3 servicos/parceira-rastreio/servidor.py

Consulta:
    curl "http://localhost:9090/consulta?objeto=BR9912345"
"""

import json
import os
import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORTA = int(os.environ.get("PORT", "9090"))

SITUACOES = [
    ("POSTADO", "Objeto postado na unidade de origem"),
    ("EM_TRANSITO", "Objeto em transito para a unidade de destino"),
    ("SAIU_ENTREGA", "Objeto saiu para entrega ao destinatario"),
    ("ENTREGUE", "Objeto entregue ao destinatario"),
    ("DEVOLVIDO_REMETENTE", "Objeto devolvido ao remetente"),
]

UFS = ["SP", "RJ", "MG", "PR", "BA", "RS"]


def rastreio_de(codigo):
    """Monta a resposta legada de um objeto.

    A situação é derivada do próprio código, e não sorteada a cada chamada:
    consulta repetida do mesmo objeto precisa devolver o mesmo estado, senão
    o aluno não consegue conferir o que viu na chamada anterior.
    """
    semente = random.Random(codigo)
    situacao, descricao = semente.choice(SITUACOES)
    dia = semente.randint(1, 8)
    hora = semente.randint(8, 19)
    minuto = semente.choice([0, 12, 27, 32, 45, 58])
    return {
        "COD_OBJ": codigo,
        "DT_ULT_MOV": "%02d/09/2026 %02d:%02d" % (dia, hora, minuto),
        "SIT": situacao,
        "UF_ULT": semente.choice(UFS),
        "DESC_SIT": descricao,
    }


class Manipulador(BaseHTTPRequestHandler):
    """Duas rotas apenas: a consulta e a sonda de saúde."""

    def _responder(self, status, corpo):
        texto = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(texto)))
        self.end_headers()
        self.wfile.write(texto)

    def do_GET(self):  # noqa: N802  (nome exigido pela BaseHTTPRequestHandler)
        endereco = urlparse(self.path)
        if endereco.path == "/health":
            self._responder(200, {"status": "ok"})
            return
        if endereco.path == "/consulta":
            objeto = parse_qs(endereco.query).get("objeto", [""])[0].strip()
            if not objeto:
                self._responder(400, {"ERRO": "parametro objeto ausente"})
                return
            self._responder(200, rastreio_de(objeto))
            return
        self._responder(404, {"ERRO": "recurso nao encontrado"})

    def log_message(self, formato, *args):
        """Log enxuto, para não poluir o terminal do laboratório."""
        print("parceira: %s" % (formato % args))


def main():
    servidor = ThreadingHTTPServer(("0.0.0.0", PORTA), Manipulador)
    print("Rastreamento da parceira ouvindo em http://localhost:%d" % PORTA)
    print("Experimente: curl \"http://localhost:%d/consulta?objeto=BR9912345\"" % PORTA)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nRastreamento da parceira encerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
