"""Configuração comum da suíte de testes do laboratório.

Coloca a raiz do laboratório no `sys.path` para que `import agente` funcione
sem instalar pacote nenhum, e oferece dois utilitários que quase todo teste
usa: uma API de Pedidos falsa e uma trilha de auditoria em arquivo temporário.
"""
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from agente import api_pedidos  # noqa: E402


class ApiFalsa:
    """Dublê do serviço de Pedidos.

    Guarda as chamadas recebidas, o que permite provar o que interessa na
    lacuna TODO-5: que, diante de uma recusa, **nenhuma** chamada chegou aqui.
    """

    def __init__(self):
        self.chamadas = []
        self.pedidos = {
            "PED-1042": {
                "pedidoId": "PED-1042",
                "status": "EM_TRANSITO",
                "transportadora": "LogiTech Frota 07",
                "previsaoEntrega": "2026-09-24",
                "ultimaPosicao": "Ribeirão Preto, SP",
                "atualizadoEm": "2026-09-22T19:20:00",
            },
        }

    def obter_status(self, pedido_id):
        self.chamadas.append(("obter_status", pedido_id, None))
        if pedido_id not in self.pedidos:
            raise api_pedidos.ErroDeApi("pedido não encontrado", status=404)
        return dict(self.pedidos[pedido_id])

    def alterar_endereco(self, pedido_id, endereco):
        self.chamadas.append(("alterar_endereco", pedido_id, dict(endereco)))
        faltando = [c for c in ("logradouro", "numero", "cidade", "uf", "cep")
                    if not endereco.get(c)]
        if faltando:
            raise api_pedidos.ErroDeApi(
                "campos obrigatórios ausentes: %s" % ", ".join(faltando),
                status=400, corpo={"campos": faltando})
        return {
            "pedidoId": pedido_id,
            "enderecoEntrega": dict(endereco),
            "atualizadoEm": "2026-09-22T21:40:00",
        }


@pytest.fixture
def api(monkeypatch):
    """Substitui as funções de rede do cliente de Pedidos pelo dublê."""
    falsa = ApiFalsa()
    monkeypatch.setattr(api_pedidos, "obter_status", falsa.obter_status)
    monkeypatch.setattr(api_pedidos, "alterar_endereco", falsa.alterar_endereco)
    return falsa


@pytest.fixture
def trilha(tmp_path):
    """Caminho de uma trilha de auditoria isolada, por teste."""
    return str(tmp_path / "AUDITORIA.md")
