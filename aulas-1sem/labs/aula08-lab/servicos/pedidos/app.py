#!/usr/bin/env python3
"""Serviço de Pedidos da LogiTech Enterprise, versão mínima para a Aula 08.

CONGELADO: este arquivo não é tarefa do laboratório. Ele existe para que o
agente de IA que você escreve hoje tenha uma API real para chamar, com
exatamente as rotas, as portas e os payloads fixados no contrato da
plataforma (ADR-006 do acervo da disciplina).

Rotas expostas, todas na porta 8080:

    GET    /health                            {"status": "ok"}
    GET    /api/v1/pedidos                    lista resumida
    GET    /api/v1/pedidos/{id}               pedido completo
    POST   /api/v1/pedidos                    cria pedido
    GET    /api/v1/pedidos/{id}/status        usado pelo agente
    PATCH  /api/v1/pedidos/{id}/endereco      usado pelo agente

O estado vive em memória: reiniciar o processo devolve os pedidos semente.
Isso é deliberado, porque o laboratório de hoje é sobre o agente, não sobre
persistência, e permite repetir o exercício quantas vezes for preciso.

Uso:
    python3 servicos/pedidos/app.py
    LOGITECH_PEDIDOS_PORT=8090 python3 servicos/pedidos/app.py
"""
import json
import os
import re
import threading
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTA = int(os.environ.get("LOGITECH_PEDIDOS_PORT", "8080"))

# Campos que o contrato exige em qualquer alteração de endereço de entrega.
# O agente precisa reproduzir exatamente esta lista no JSON Schema da
# ferramenta: é aqui que a recusa da lacuna TODO-5 ganha sentido, porque o
# serviço rejeita de verdade o que chega incompleto.
CAMPOS_ENDERECO_OBRIGATORIOS = ("logradouro", "numero", "cidade", "uf", "cep")
CAMPOS_ENDERECO_OPCIONAIS = ("complemento",)

_TRAVA = threading.Lock()


def _agora():
    return datetime.now().replace(microsecond=0).isoformat()


def _semente():
    """Pedidos de partida, com nomes e rotas do case LogiTech."""
    hoje = date.today()
    return {
        "PED-1042": {
            "pedidoId": "PED-1042",
            "cliente": "Distribuidora Sertão Norte",
            "status": "EM_TRANSITO",
            "transportadora": "LogiTech Frota 07",
            "previsaoEntrega": (hoje + timedelta(days=2)).isoformat(),
            "ultimaPosicao": "Ribeirão Preto, SP",
            "atualizadoEm": _agora(),
            "enderecoEntrega": {
                "logradouro": "Rua das Palmeiras",
                "numero": "455",
                "complemento": "Galpão B",
                "cidade": "Ribeirão Preto",
                "uf": "SP",
                "cep": "14020-260",
            },
        },
        "PED-1043": {
            "pedidoId": "PED-1043",
            "cliente": "Supermercados Vale Verde",
            "status": "AGUARDANDO_COLETA",
            "transportadora": "LogiTech Frota 12",
            "previsaoEntrega": (hoje + timedelta(days=4)).isoformat(),
            "ultimaPosicao": "Centro de distribuição Guarulhos",
            "atualizadoEm": _agora(),
            "enderecoEntrega": {
                "logradouro": "Avenida Brasil",
                "numero": "2100",
                "complemento": "",
                "cidade": "Campinas",
                "uf": "SP",
                "cep": "13070-180",
            },
        },
        "PED-1044": {
            "pedidoId": "PED-1044",
            "cliente": "Farmácias Bem Viver",
            "status": "SAIU_PARA_ENTREGA",
            "transportadora": "LogiTech Frota 03",
            "previsaoEntrega": hoje.isoformat(),
            "ultimaPosicao": "São Bernardo do Campo, SP",
            "atualizadoEm": _agora(),
            "enderecoEntrega": {
                "logradouro": "Rua Marechal Deodoro",
                "numero": "88",
                "complemento": "",
                "cidade": "São Bernardo do Campo",
                "uf": "SP",
                "cep": "09710-000",
            },
        },
        "PED-2001": {
            "pedidoId": "PED-2001",
            "cliente": "Indústria Metalúrgica Andrade",
            "status": "ENTREGUE",
            "transportadora": "LogiTech Frota 21",
            "previsaoEntrega": (hoje - timedelta(days=1)).isoformat(),
            "ultimaPosicao": "Entregue em Belo Horizonte, MG",
            "atualizadoEm": _agora(),
            "enderecoEntrega": {
                "logradouro": "Rodovia Fernão Dias, km 12",
                "numero": "s/n",
                "complemento": "Portaria 2",
                "cidade": "Belo Horizonte",
                "uf": "MG",
                "cep": "31270-901",
            },
        },
    }


PEDIDOS = _semente()

ROTA_STATUS = re.compile(r"^/api/v1/pedidos/([^/]+)/status$")
ROTA_ENDERECO = re.compile(r"^/api/v1/pedidos/([^/]+)/endereco$")
ROTA_PEDIDO = re.compile(r"^/api/v1/pedidos/([^/]+)$")


class ManipuladorPedidos(BaseHTTPRequestHandler):
    """Rotas do serviço de Pedidos, escritas só com a biblioteca padrão."""

    server_version = "LogiTechPedidos/1.0"

    def _responder(self, codigo, corpo):
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def _corpo_json(self):
        """Lê o corpo da requisição como JSON. Devolve (dicionário, erro)."""
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None, "Content-Length inválido"
        if tamanho <= 0:
            return None, "corpo da requisição vazio"
        bruto = self.rfile.read(tamanho)
        try:
            corpo = json.loads(bruto.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as erro:
            return None, "corpo não é JSON válido: %s" % erro
        if not isinstance(corpo, dict):
            return None, "o corpo precisa ser um objeto JSON"
        return corpo, None

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------
    def do_GET(self):
        caminho = self.path.split("?")[0]

        if caminho == "/health":
            return self._responder(200, {"status": "ok"})

        if caminho == "/api/v1/pedidos":
            with _TRAVA:
                resumo = [
                    {
                        "pedidoId": p["pedidoId"],
                        "cliente": p["cliente"],
                        "status": p["status"],
                    }
                    for p in PEDIDOS.values()
                ]
            return self._responder(200, {"pedidos": resumo, "total": len(resumo)})

        casamento = ROTA_STATUS.match(caminho)
        if casamento:
            pedido_id = casamento.group(1)
            with _TRAVA:
                pedido = PEDIDOS.get(pedido_id)
                if pedido is None:
                    return self._responder(
                        404, {"erro": "pedido não encontrado", "pedidoId": pedido_id})
                return self._responder(200, {
                    "pedidoId": pedido["pedidoId"],
                    "status": pedido["status"],
                    "transportadora": pedido["transportadora"],
                    "previsaoEntrega": pedido["previsaoEntrega"],
                    "ultimaPosicao": pedido["ultimaPosicao"],
                    "atualizadoEm": pedido["atualizadoEm"],
                })

        casamento = ROTA_PEDIDO.match(caminho)
        if casamento:
            pedido_id = casamento.group(1)
            with _TRAVA:
                pedido = PEDIDOS.get(pedido_id)
                if pedido is None:
                    return self._responder(
                        404, {"erro": "pedido não encontrado", "pedidoId": pedido_id})
                return self._responder(200, dict(pedido))

        return self._responder(404, {"erro": "rota não encontrada", "caminho": caminho})

    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------
    def do_POST(self):
        caminho = self.path.split("?")[0]
        if caminho != "/api/v1/pedidos":
            return self._responder(
                404, {"erro": "rota não encontrada", "caminho": caminho})

        corpo, erro = self._corpo_json()
        if erro:
            return self._responder(400, {"erro": erro})

        cliente = str(corpo.get("cliente") or "").strip()
        if not cliente:
            return self._responder(
                400, {"erro": "campos obrigatórios ausentes", "campos": ["cliente"]})

        with _TRAVA:
            novo_id = "PED-%d" % (9000 + len(PEDIDOS) + 1)
            pedido = {
                "pedidoId": novo_id,
                "cliente": cliente,
                "status": "AGUARDANDO_COLETA",
                "transportadora": corpo.get("transportadora", "a definir"),
                "previsaoEntrega": (date.today() + timedelta(days=5)).isoformat(),
                "ultimaPosicao": "Centro de distribuição Guarulhos",
                "atualizadoEm": _agora(),
                "enderecoEntrega": corpo.get("enderecoEntrega", {}),
            }
            PEDIDOS[novo_id] = pedido
        return self._responder(201, dict(pedido))

    # ------------------------------------------------------------------
    # PATCH
    # ------------------------------------------------------------------
    def do_PATCH(self):
        caminho = self.path.split("?")[0]
        casamento = ROTA_ENDERECO.match(caminho)
        if not casamento:
            return self._responder(
                404, {"erro": "rota não encontrada", "caminho": caminho})

        pedido_id = casamento.group(1)
        corpo, erro = self._corpo_json()
        if erro:
            return self._responder(400, {"erro": erro})

        ausentes = [c for c in CAMPOS_ENDERECO_OBRIGATORIOS
                    if not str(corpo.get(c) or "").strip()]
        if ausentes:
            # O serviço recusa o que chega incompleto. O ponto pedagógico da
            # aula é que a recusa não deveria precisar chegar até aqui: o
            # agente valida o JSON Schema antes de fazer a chamada.
            return self._responder(400, {
                "erro": "campos obrigatórios ausentes",
                "campos": ausentes,
            })

        with _TRAVA:
            pedido = PEDIDOS.get(pedido_id)
            if pedido is None:
                return self._responder(
                    404, {"erro": "pedido não encontrado", "pedidoId": pedido_id})
            if pedido["status"] in ("ENTREGUE", "CANCELADO"):
                return self._responder(409, {
                    "erro": "pedido já finalizado, endereço não pode mudar",
                    "pedidoId": pedido_id,
                    "status": pedido["status"],
                })

            endereco = {c: str(corpo[c]).strip() for c in CAMPOS_ENDERECO_OBRIGATORIOS}
            for c in CAMPOS_ENDERECO_OPCIONAIS:
                endereco[c] = str(corpo.get(c) or "").strip()
            pedido["enderecoEntrega"] = endereco
            pedido["atualizadoEm"] = _agora()
            resposta = {
                "pedidoId": pedido["pedidoId"],
                "enderecoEntrega": dict(endereco),
                "atualizadoEm": pedido["atualizadoEm"],
            }
        return self._responder(200, resposta)

    def log_message(self, formato, *args):
        """Log de uma linha por requisição, para o aluno ver o agente batendo
        na API enquanto conversa com ele.

        `flush=True` não é detalhe: sem ele, com a saída redirecionada para
        arquivo, o Python segura as linhas em buffer e o log só aparece quando
        o processo morre. O laboratório pede exatamente para olhar este log no
        instante da recusa, e um log atrasado responderia a pergunta errada.
        """
        print("[pedidos] %s - %s" % (self.address_string(), formato % args),
              flush=True)


def main():
    servidor = ThreadingHTTPServer(("0.0.0.0", PORTA), ManipuladorPedidos)
    print("[pedidos] serviço de Pedidos da LogiTech ouvindo em "
          "http://localhost:%d" % PORTA, flush=True)
    print("[pedidos] pedidos semente: %s" % ", ".join(sorted(PEDIDOS)), flush=True)
    print("[pedidos] encerre com Ctrl+C", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[pedidos] encerrando.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
