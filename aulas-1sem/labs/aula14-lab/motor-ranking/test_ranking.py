"""Os nomes começam pelo dublê: spy_ revela qual chave a tabela consultou."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ranking import ModalidadeDesconhecida, TabelaDePesos, calcular

RIVAIS = json.loads(Path(__file__).with_name("rivalidade.json").read_text(encoding="utf-8"))


class SpyTabela(TabelaDePesos):
    def __init__(self):
        super().__init__()
        self.chaves = []

    def pontos_base(self, modalidade):
        self.chaves.append(str(modalidade).strip().upper())
        return super().pontos_base(modalidade)


class RankingTests(unittest.TestCase):
    def spy_lute_consulta_a_propria_chave(self):
        spy = SpyTabela()
        resultado = calcular("LUTE", "Centro", False, spy, RIVAIS)
        self.assertEqual(spy.chaves, ["LUTE"])
        self.assertEqual(resultado["pontos"], 2)
        self.assertEqual(resultado["faixa"], "PRATA")
        self.assertEqual(resultado["janelaHoras"], 72)

    def spy_esporte_consulta_a_propria_chave(self):
        spy = SpyTabela()
        resultado = calcular("ESPORTE", "Centro", False, spy, RIVAIS)
        self.assertEqual(spy.chaves, ["ESPORTE"])
        self.assertEqual(resultado["pontos"], 2)
        self.assertEqual(resultado["faixa"], "PRATA")
        self.assertEqual(resultado["janelaHoras"], 72)

    def caso_cartas_centro(self):
        resultado = calcular("CARTAS", "Centro", False, TabelaDePesos(), RIVAIS)
        self.assertEqual(resultado["pontos"], 1)
        self.assertEqual(resultado["faixa"], "BRONZE")
        self.assertEqual(resultado["janelaHoras"], 168)

    def caso_fps_campus_norte(self):
        resultado = calcular("FPS", "Campus Norte", False, TabelaDePesos(), RIVAIS)
        self.assertEqual(resultado["pontos"], 5)
        self.assertEqual(resultado["faixa"], "LENDARIO")
        self.assertEqual(resultado["janelaHoras"], 8)

    def caso_esporte_campus_rio_serie(self):
        resultado = calcular("ESPORTE", "Campus Rio", True, TabelaDePesos(), RIVAIS)
        self.assertEqual(resultado["pontos"], 5)
        self.assertEqual(resultado["faixa"], "LENDARIO")
        self.assertEqual(resultado["janelaHoras"], 8)

    def caso_lute_centro_serie(self):
        resultado = calcular("LUTE", "Centro", True, TabelaDePesos(), RIVAIS)
        self.assertEqual(resultado["pontos"], 3)
        self.assertEqual(resultado["faixa"], "PRATA")
        self.assertEqual(resultado["janelaHoras"], 72)

    def caso_lute_campus_norte_ignora_espacos(self):
        resultado = calcular("LUTE", "  campus   norte ", False, TabelaDePesos(), RIVAIS)
        self.assertEqual(resultado["pontos"], 4)
        self.assertEqual(resultado["faixa"], "OURO")
        self.assertEqual(resultado["janelaHoras"], 24)

    def caso_modalidade_desconhecida(self):
        with self.assertRaises(ModalidadeDesconhecida):
            calcular("XADREZ", "Centro", False, TabelaDePesos(), RIVAIS)


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for nome, valor in vars(RankingTests).items():
        if nome.startswith(("spy_", "caso_")) and callable(valor):
            suite.addTest(RankingTests(nome))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
