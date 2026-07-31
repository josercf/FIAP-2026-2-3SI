#!/usr/bin/env python3
"""Suíte de testes do verificador da Aula 07.

Cobre as funções puras do `verificar.py`: leitura de marcador, conversão de
número, normalização do `environment`, leitura de limite de memória, de
portas e de volumes. Nada aqui precisa de Docker rodando, e é de propósito:
esta suíte é a rede de segurança do próprio verificador, e precisa rodar em
qualquer máquina, inclusive na correção.

    python3 -m unittest discover -v

O que ela deliberadamente não cobre: os cinco critérios ponta a ponta. Eles
dependem de oito containers de pé e são validados nos dois sentidos à mão
(reprovando o esqueleto, aprovando o resgate), como registrado no README.
"""

import unittest

import verificar


class TestLeituraDeMarcador(unittest.TestCase):

    def test_le_valor_simples(self):
        texto = "ACERTOS_DE_CACHE: 4\n"
        self.assertEqual(verificar._valor_preenchido("ACERTOS_DE_CACHE", texto), "4")

    def test_recusa_marcador_ausente(self):
        self.assertIsNone(verificar._valor_preenchido("NAO_EXISTE", "outra coisa"))

    def test_recusa_texto_de_esqueleto(self):
        texto = "MEMORIA_TOTAL_MB: PREENCHER\n"
        self.assertIsNone(verificar._valor_preenchido("MEMORIA_TOTAL_MB", texto))

    def test_recusa_esqueleto_com_sufixo(self):
        """'PREENCHER com o valor lido' também é esqueleto, não resposta."""
        texto = "MEMORIA_TOTAL_MB: PREENCHER com o valor do docker stats\n"
        self.assertIsNone(verificar._valor_preenchido("MEMORIA_TOTAL_MB", texto))

    def test_nao_confunde_marcadores_de_prefixo_comum(self):
        texto = "MEMORIA_TOTAL_MB: 1600\nMEMORIA_MAIOR_CONSUMIDOR_MB: 320\n"
        self.assertEqual(
            verificar._valor_preenchido("MEMORIA_MAIOR_CONSUMIDOR_MB", texto), "320")


class TestConversaoDeNumero(unittest.TestCase):

    def test_aceita_ponto_decimal(self):
        self.assertAlmostEqual(verificar._para_float("1632.5"), 1632.5)

    def test_aceita_virgula_decimal(self):
        self.assertAlmostEqual(verificar._para_float("1632,5"), 1632.5)

    def test_ignora_unidade_colada(self):
        self.assertAlmostEqual(verificar._para_float("48 s"), 48.0)

    def test_recusa_texto_sem_numero(self):
        with self.assertRaises(ValueError):
            verificar._para_float("muito rápido")


class TestNormalizacaoDoAmbiente(unittest.TestCase):

    def test_aceita_dicionario(self):
        svc = {"environment": {"LOGITECH_TELEMETRIA_URL": "http://coletor:8082/telemetria"}}
        self.assertEqual(verificar.ambiente(svc)["LOGITECH_TELEMETRIA_URL"],
                         "http://coletor:8082/telemetria")

    def test_aceita_lista(self):
        svc = {"environment": ["LOGITECH_DB_USER=logitech", "LOGITECH_PORTA=8080"]}
        self.assertEqual(verificar.ambiente(svc)["LOGITECH_DB_USER"], "logitech")

    def test_variavel_sem_valor_vira_texto_vazio(self):
        svc = {"environment": {"LOGITECH_IA_REMOTA_CHAVE": None}}
        self.assertEqual(verificar.ambiente(svc)["LOGITECH_IA_REMOTA_CHAVE"], "")

    def test_servico_sem_environment(self):
        self.assertEqual(verificar.ambiente({}), {})


class TestLimiteDeMemoria(unittest.TestCase):

    def test_le_mem_limit_em_megabytes(self):
        self.assertEqual(verificar.limite_de_memoria({"mem_limit": "256m"}),
                         256 * 1024 ** 2)

    def test_le_mem_limit_ja_em_bytes(self):
        self.assertEqual(verificar.limite_de_memoria({"mem_limit": 268435456}),
                         268435456)

    def test_le_a_grafia_longa_do_deploy(self):
        svc = {"deploy": {"resources": {"limits": {"memory": "320M"}}}}
        self.assertEqual(verificar.limite_de_memoria(svc), 320 * 1024 ** 2)

    def test_devolve_none_quando_nao_ha_limite(self):
        self.assertIsNone(verificar.limite_de_memoria({"image": "alpine"}))


class TestPortasPublicadas(unittest.TestCase):

    def test_forma_curta(self):
        self.assertIn((8082, "tcp"),
                      verificar.portas_publicadas({"ports": ["8082:8082"]}))

    def test_forma_curta_com_udp(self):
        self.assertIn((8081, "udp"),
                      verificar.portas_publicadas({"ports": ["8081:8081/udp"]}))

    def test_forma_longa_normalizada_pelo_compose(self):
        svc = {"ports": [{"mode": "ingress", "target": 4000,
                          "published": "4000", "protocol": "tcp"}]}
        self.assertIn((4000, "tcp"), verificar.portas_publicadas(svc))

    def test_servico_sem_portas(self):
        self.assertEqual(verificar.portas_publicadas({}), set())


class TestVolumesMontados(unittest.TestCase):

    def test_forma_curta(self):
        svc = {"volumes": ["logitech-telemetria:/dados"]}
        self.assertEqual(verificar.volumes_montados(svc), ["logitech-telemetria"])

    def test_forma_longa_normalizada_pelo_compose(self):
        svc = {"volumes": [{"type": "volume", "source": "logitech-postgres",
                            "target": "/var/lib/postgresql/data"}]}
        self.assertEqual(verificar.volumes_montados(svc), ["logitech-postgres"])

    def test_painel_sem_volume(self):
        """O critério do Passo 3 depende deste caso: lista vazia, não erro."""
        self.assertEqual(verificar.volumes_montados({"image": "node"}), [])


class TestTextoDoHealthcheck(unittest.TestCase):

    def test_lista_vira_texto(self):
        svc = {"healthcheck": {"test": ["CMD-SHELL", "pg_isready -U logitech"]}}
        self.assertIn("pg_isready", verificar.texto_do_healthcheck(svc))

    def test_string_pura(self):
        svc = {"healthcheck": {"test": "pg_isready -U logitech"}}
        self.assertIn("pg_isready", verificar.texto_do_healthcheck(svc))

    def test_sem_healthcheck_devolve_vazio(self):
        self.assertEqual(verificar.texto_do_healthcheck({"image": "alpine"}), "")


class TestContratoDaPlataforma(unittest.TestCase):
    """Guarda-corpo contra divergência silenciosa da ADR-006."""

    def test_os_oito_servicos_do_contrato(self):
        self.assertEqual(
            verificar.SERVICOS_ESPERADOS,
            ["ai-gateway", "coletor", "faturamento", "frete",
             "notificacoes", "painel", "pedidos", "postgres"])

    def test_portas_do_contrato(self):
        esperado = {"pedidos": 8080, "faturamento": 5080, "frete": 8000,
                    "notificacoes": 3001, "coletor": 8082, "painel": 3000,
                    "ai-gateway": 4000}
        self.assertEqual({k: v[0] for k, v in verificar.CONTRATO.items()}, esperado)


if __name__ == "__main__":
    unittest.main()
