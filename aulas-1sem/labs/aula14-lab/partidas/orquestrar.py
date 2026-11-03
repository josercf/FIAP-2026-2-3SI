"""Ordem obrigatória ao abrir um desafio. Esta função já vem pronta.

Os testes de Stub e de Mock seguram os vizinhos. Não chame HTTP daqui.
"""

from __future__ import annotations

MODALIDADES = {"FPS", "MOBA", "LUTE", "ESPORTE", "CARTAS"}


class AtletaInexistente(Exception):
    pass


class PedidoInvalido(Exception):
    def __init__(self, motivo):
        super().__init__(motivo)
        self.motivo = motivo


class MotorIndisponivel(Exception):
    pass


class MissaoPendente(Exception):
    pass


def _coordenada_invalida(latitude, longitude):
    if latitude is None and longitude is None:
        return False
    if latitude is None or longitude is None:
        return True
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return True
    return not (-90 <= lat <= 90 and -180 <= lon <= 180)


def abrir_desafio(pedido, elenco, motor, repositorio, agora):
    modalidade = pedido.get("modalidade")
    descricao = pedido.get("descricao") or ""
    campus = pedido.get("campus") or ""
    latitude = pedido.get("latitude", None)
    longitude = pedido.get("longitude", None)

    if modalidade not in MODALIDADES:
        raise PedidoInvalido("modalidade")
    if not isinstance(descricao, str) or not (15 <= len(descricao) <= 400):
        raise PedidoInvalido("descricao")
    if not str(campus).strip():
        raise PedidoInvalido("campus")
    if _coordenada_invalida(latitude, longitude):
        raise PedidoInvalido("coordenada")

    atleta = elenco.obter(pedido.get("atletaId"))
    if atleta is None:
        raise AtletaInexistente()

    serie = bool(repositorio.existe_serie(modalidade, campus, agora))
    try:
        rank = motor.ranquear(modalidade, campus, serie)
    except MissaoPendente:
        raise
    except MotorIndisponivel:
        raise

    desafio = {
        "atletaId": pedido.get("atletaId"),
        "modalidade": modalidade,
        "descricao": descricao,
        "campus": campus,
        "latitude": None if latitude is None else float(latitude),
        "longitude": None if longitude is None else float(longitude),
        "status": "ABERTO",
        "pontos": rank["pontos"],
        "faixa": rank["faixa"],
        "janelaHoras": rank["janelaHoras"],
        "serie": serie,
    }
    return repositorio.inserir(desafio)
