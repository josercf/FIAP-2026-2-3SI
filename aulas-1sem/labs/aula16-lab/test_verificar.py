"""Testes do verificador da Aula 16.

Rode com `python3 -m pytest test_verificar.py -q` ou, sem pytest instalado,
com `python3 test_verificar.py`.

O que estes testes cobrem: as funções puras do verificador, aquelas que não
dependem de Docker nem de rede. As que dependem são exercitadas pelo próprio
`verificar.py` contra a plataforma de pé, que é o único jeito honesto de
testá-las.
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verificar


class TestMarcador(unittest.TestCase):
    """`marcador` precisa recusar tanto ausência quanto o texto de esqueleto."""

    def test_le_o_valor(self):
        self.assertEqual(verificar.marcador("MEMORIA_TOTAL_MB", "MEMORIA_TOTAL_MB: 806"), "806")

    def test_recusa_ausente(self):
        self.assertIsNone(verificar.marcador("NAO_EXISTE", "outra coisa: 1"))

    def test_recusa_esqueleto(self):
        # O caso que um regex de presença simples deixaria passar.
        self.assertIsNone(verificar.marcador("MAQUINA", "MAQUINA: PREENCHER (modelo)"))

    def test_recusa_vazio(self):
        self.assertIsNone(verificar.marcador("MAQUINA", "MAQUINA:   "))


class TestComoJson(unittest.TestCase):
    def test_json_valido(self):
        self.assertEqual(verificar.como_json('{"a": 1}'), {"a": 1})

    def test_texto_qualquer_nao_estoura(self):
        # O verificador nunca pode morrer por causa de uma resposta estranha:
        # ele precisa reportar o critério como falho, não levantar exceção.
        self.assertEqual(verificar.como_json("<html>502 Bad Gateway</html>"), {})


class TestPapeisDoToken(unittest.TestCase):
    def test_le_realm_access(self):
        import base64

        def b64(objeto):
            bruto = json.dumps(objeto).encode()
            return base64.urlsafe_b64encode(bruto).decode().rstrip("=")

        token = ".".join([
            b64({"alg": "RS256"}),
            b64({"iss": "http://localhost:8090/realms/logitech",
                 "realm_access": {"roles": ["ADMIN"]}}),
            "assinatura",
        ])
        carga = verificar.papeis_do_token(token)
        self.assertEqual(carga["realm_access"]["roles"], ["ADMIN"])
        self.assertTrue(carga["iss"].startswith("http://localhost:8090"))


class TestContrato(unittest.TestCase):
    def test_treze_servicos(self):
        self.assertEqual(verificar.TOTAL_DE_SERVICOS, 13)

    def test_mcp_nao_tem_porta_nem_rota_de_saude(self):
        # É o único assim, e a razão é o transporte stdio do MCP.
        porta, rota = verificar.CONTRATO["mcp-logitech"]
        self.assertIsNone(porta)
        self.assertIsNone(rota)

    def test_postgres_nao_fala_http(self):
        self.assertIsNone(verificar.CONTRATO["postgres"][1])


class TestRelato(unittest.TestCase):
    def test_um_passo_falho_reprova_a_frente(self):
        r = verificar.Relato(1, "teste")
        r.passo(True, "primeiro")
        r.passo(False, "segundo")
        self.assertFalse(r.ok)

    def test_nota_nao_reprova(self):
        r = verificar.Relato(1, "teste")
        r.passo(True, "primeiro")
        r.nota("apenas informativo")
        self.assertTrue(r.ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)
