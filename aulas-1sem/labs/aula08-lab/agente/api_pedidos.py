#!/usr/bin/env python3
"""Cliente HTTP do serviço de Pedidos da LogiTech.

PRONTO: não é tarefa. Os seus Commands chamam as funções daqui.

O endereço do serviço **nunca** aparece cravado no código: vem da variável
`LOGITECH_PEDIDOS_URL`, com padrão de desenvolvimento local. É essa regra do
contrato da plataforma (ADR-006) que permite o mesmo agente falar com o
serviço solto na sua máquina hoje e com o serviço dentro do Docker Compose
depois, sem alterar uma linha.
"""
import json
import os
import urllib.error
import urllib.request

BASE_URL = os.environ.get("LOGITECH_PEDIDOS_URL", "http://localhost:8080").rstrip("/")
TIMEOUT = int(os.environ.get("LOGITECH_PEDIDOS_TIMEOUT", "15"))


class ErroDeApi(Exception):
    """Falha ao falar com o serviço de Pedidos.

    Carrega o código HTTP quando existe (`status`) e o corpo devolvido pelo
    serviço (`corpo`), porque a diferença entre "o serviço está fora do ar" e
    "o serviço recusou o meu payload" muda completamente o que o agente deve
    responder ao atendente.
    """

    def __init__(self, mensagem, status=None, corpo=None):
        super().__init__(mensagem)
        self.status = status
        self.corpo = corpo


def _requisitar(metodo, caminho, corpo=None):
    url = BASE_URL + caminho
    dados = None
    cabecalhos = {"Accept": "application/json"}
    if corpo is not None:
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        cabecalhos["Content-Type"] = "application/json; charset=utf-8"

    req = urllib.request.Request(url, data=dados, headers=cabecalhos, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resposta:
            bruto = resposta.read().decode("utf-8")
            return json.loads(bruto) if bruto else {}
    except urllib.error.HTTPError as erro:
        bruto = erro.read().decode("utf-8", "replace")
        try:
            detalhe = json.loads(bruto)
        except ValueError:
            detalhe = {"erro": bruto[:300]}
        raise ErroDeApi(
            "o serviço de Pedidos respondeu HTTP %d para %s %s: %s"
            % (erro.code, metodo, caminho, detalhe.get("erro", bruto[:200])),
            status=erro.code, corpo=detalhe)
    except (urllib.error.URLError, OSError) as erro:
        raise ErroDeApi(
            "não foi possível alcançar o serviço de Pedidos em %s (%s). "
            "Suba o serviço com: python3 servicos/pedidos/app.py"
            % (BASE_URL, erro))


def saude():
    """GET /health. Devolve o corpo, ou levanta ErroDeApi."""
    return _requisitar("GET", "/health")


def no_ar():
    """True quando o serviço responde /health com status ok."""
    try:
        return saude().get("status") == "ok"
    except ErroDeApi:
        return False


def obter_status(pedido_id):
    """GET /api/v1/pedidos/{id}/status."""
    return _requisitar("GET", "/api/v1/pedidos/%s/status" % pedido_id)


def obter_pedido(pedido_id):
    """GET /api/v1/pedidos/{id}."""
    return _requisitar("GET", "/api/v1/pedidos/%s" % pedido_id)


def alterar_endereco(pedido_id, endereco):
    """PATCH /api/v1/pedidos/{id}/endereco.

    `endereco` é um dicionário com `logradouro`, `numero`, `cidade`, `uf`,
    `cep` e, opcionalmente, `complemento`.
    """
    return _requisitar("PATCH", "/api/v1/pedidos/%s/endereco" % pedido_id, endereco)
