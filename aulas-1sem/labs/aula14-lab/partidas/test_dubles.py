"""Stub segura uma resposta. Mock exige a chamada. Nada disso sobe container."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from orquestrar import (
    AtletaInexistente,
    MotorIndisponivel,
    PedidoInvalido,
    abrir_desafio,
)

AGORA = datetime(2026, 11, 3, 22, 0, tzinfo=timezone.utc)


class ElencoFixo:
    def __init__(self, atleta):
        self.atleta = atleta

    def obter(self, atleta_id):
        return self.atleta


class MotorGravador:
    def __init__(self, resposta=None, falha=None):
        self.resposta = resposta or {
            "pontos": 1,
            "faixa": "BRONZE",
            "janelaHoras": 168,
        }
        self.falha = falha
        self.chamadas = []

    def ranquear(self, modalidade, campus, serie):
        self.chamadas.append(
            {"modalidade": modalidade, "campus": campus, "serie": serie}
        )
        if self.falha:
            raise self.falha
        return self.resposta


class RepositorioGravador:
    def __init__(self, serie=False):
        self.serie = serie
        self.inserts = []

    def existe_serie(self, modalidade, campus, agora):
        return self.serie

    def inserir(self, desafio):
        self.inserts.append(desafio)
        return dict(desafio, id="desafio-1")


def pedido(**extra):
    base = {
        "atletaId": "atleta-1",
        "modalidade": "CARTAS",
        "descricao": "Chave de cartas no intervalo, mesa 2 da arena.",
        "campus": "Centro",
    }
    base.update(extra)
    return base


class DublesTests(unittest.TestCase):
    def stub_elenco_inexistente_nao_chama_motor(self):
        motor = MotorGravador()
        repositorio = RepositorioGravador()
        with self.assertRaises(AtletaInexistente):
            abrir_desafio(pedido(), ElencoFixo(None), motor, repositorio, AGORA)
        self.assertEqual(motor.chamadas, [])
        self.assertEqual(repositorio.inserts, [])

    def stub_motor_indisponivel_nao_persiste(self):
        motor = MotorGravador(falha=MotorIndisponivel("fora"))
        repositorio = RepositorioGravador()
        with self.assertRaises(MotorIndisponivel):
            abrir_desafio(
                pedido(),
                ElencoFixo({"id": "atleta-1"}),
                motor,
                repositorio,
                AGORA,
            )
        self.assertEqual(repositorio.inserts, [])

    def mock_motor_recebe_serie_true(self):
        motor = MotorGravador(
            resposta={"pontos": 5, "faixa": "LENDARIO", "janelaHoras": 8}
        )
        repositorio = RepositorioGravador(serie=True)
        abrir_desafio(
            pedido(modalidade="ESPORTE", campus="Campus Rio"),
            ElencoFixo({"id": "atleta-1"}),
            motor,
            repositorio,
            AGORA,
        )
        self.assertEqual(len(motor.chamadas), 1)
        self.assertEqual(motor.chamadas[0]["serie"], True)
        self.assertEqual(repositorio.inserts[0]["serie"], True)

    def mock_modalidade_invalida_nao_chama_motor(self):
        motor = MotorGravador()
        repositorio = RepositorioGravador()
        with self.assertRaises(PedidoInvalido):
            abrir_desafio(
                pedido(modalidade="XADREZ"),
                ElencoFixo({"id": "atleta-1"}),
                motor,
                repositorio,
                AGORA,
            )
        self.assertEqual(motor.chamadas, [])
        self.assertEqual(repositorio.inserts, [])


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for nome, valor in vars(DublesTests).items():
        if nome.startswith(("stub_", "mock_")) and callable(valor):
            suite.addTest(DublesTests(nome))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
