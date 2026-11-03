"""A lista em memória faz o papel de Stub. O relógio é o argumento agora."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from serie import eh_serie

AGORA = datetime(2026, 11, 3, 22, 0, tzinfo=timezone.utc)


def _anterior(**extra):
    base = {
        "modalidade": "FPS",
        "campus": "Campus Norte",
        "status": "ABERTO",
        "criado_em": AGORA - timedelta(hours=1),
    }
    base.update(extra)
    return base


class SerieTests(unittest.TestCase):
    def stub_janela_47h59_conta_48h00_nao(self):
        quase = _anterior(criado_em=AGORA - timedelta(hours=47, minutes=59))
        exato = _anterior(criado_em=AGORA - timedelta(hours=48))
        self.assertTrue(eh_serie(quase, "FPS", "Campus Norte", AGORA))
        self.assertFalse(eh_serie(exato, "FPS", "Campus Norte", AGORA))

    def stub_encerrado_nao_conta(self):
        anterior = _anterior(status="ENCERRADO")
        self.assertFalse(eh_serie(anterior, "FPS", "Campus Norte", AGORA))

    def stub_outra_modalidade_nao_conta(self):
        anterior = _anterior(modalidade="MOBA")
        self.assertFalse(eh_serie(anterior, "FPS", "Campus Norte", AGORA))

    def stub_campus_ignora_espacos(self):
        anterior = _anterior(campus="campus   norte")
        self.assertTrue(eh_serie(anterior, "FPS", "Campus Norte", AGORA))


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for nome, valor in vars(SerieTests).items():
        if nome.startswith("stub_") and callable(valor):
            suite.addTest(SerieTests(nome))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
