from __future__ import annotations

import unittest

from ciclo import TransicaoRecusada, transicionar


class CicloTests(unittest.TestCase):
    def transicao_aberto_para_confirmado(self):
        self.assertEqual(transicionar("ABERTO", "CONFIRMADO"), "CONFIRMADO")

    def transicao_confirmado_para_em_jogo(self):
        self.assertEqual(transicionar("CONFIRMADO", "EM_JOGO"), "EM_JOGO")

    def transicao_em_jogo_para_encerrado(self):
        self.assertEqual(transicionar("EM_JOGO", "ENCERRADO"), "ENCERRADO")

    def transicao_aberto_para_encerrado_recusada(self):
        with self.assertRaises(TransicaoRecusada):
            transicionar("ABERTO", "ENCERRADO")

    def transicao_igual_recusada(self):
        with self.assertRaises(TransicaoRecusada):
            transicionar("ABERTO", "ABERTO")

    def transicao_encerrado_nao_volta(self):
        with self.assertRaises(TransicaoRecusada):
            transicionar("ENCERRADO", "ABERTO")


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for nome, valor in vars(CicloTests).items():
        if nome.startswith("transicao_") and callable(valor):
            suite.addTest(CicloTests(nome))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
