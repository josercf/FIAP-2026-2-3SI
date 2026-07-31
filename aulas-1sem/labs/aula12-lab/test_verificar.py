"""Testes das funções puras de `verificar.py` e de `rag/chunking.py`.

Nenhum deles precisa de banco, de Ollama ou de Docker no ar: cobrem leitura de
marcador, separação das consultas nomeadas, normalização de acento e as regras
de divisão do contrato em trechos.

    python3 -m unittest discover -v
"""

import unittest

import verificar
from rag import chunking


class TestValorDoMarcador(unittest.TestCase):
    def test_le_o_valor(self):
        texto = "TRECHOS_INGERIDOS: 44\n"
        self.assertEqual(verificar.valor_do_marcador("TRECHOS_INGERIDOS", texto), "44")

    def test_recusa_o_texto_de_esqueleto(self):
        texto = "TRECHOS_INGERIDOS: PREENCHER (quantos trechos)\n"
        self.assertIsNone(verificar.valor_do_marcador("TRECHOS_INGERIDOS", texto))

    def test_recusa_ausencia(self):
        self.assertIsNone(verificar.valor_do_marcador("NAO_EXISTE", "outra coisa"))

    def test_recusa_valor_vazio(self):
        self.assertIsNone(verificar.valor_do_marcador("X", "X:   \n"))

    def test_nao_confunde_marcador_parecido(self):
        texto = "TRECHOS_INGERIDOS_TOTAL: 99\nTRECHOS_INGERIDOS: 44\n"
        self.assertEqual(verificar.valor_do_marcador("TRECHOS_INGERIDOS", texto), "44")


class TestSemAcento(unittest.TestCase):
    def test_tira_acento_e_baixa_a_caixa(self):
        self.assertEqual(verificar.sem_acento("Petroquímica"), "petroquimica")

    def test_casa_nome_de_arquivo_com_texto_acentuado(self):
        texto = "Contrato da Petroquímica Litoral S.A."
        self.assertIn("petroquimica", verificar.sem_acento(texto))

    def test_preserva_texto_sem_acento(self):
        self.assertEqual(verificar.sem_acento("aurora"), "aurora")


class TestConsultasNomeadas(unittest.TestCase):
    ARQUIVO = """
-- cabecalho de apoio, com um ____ que nao pode virar falso positivo

-- consulta: primeira
SELECT 1 AS um;

-- consulta: segunda
SELECT 2 AS dois
FROM generate_series(1, 1);

SELECT 'sobra, fora de bloco nomeado';
"""

    def setUp(self):
        self.blocos = verificar.consultas_nomeadas(self.ARQUIVO)

    def test_acha_os_dois_blocos(self):
        self.assertEqual(sorted(self.blocos), ["primeira", "segunda"])

    def test_para_no_ponto_e_virgula(self):
        self.assertEqual(self.blocos["primeira"].strip(), "SELECT 1 AS um;")

    def test_bloco_de_varias_linhas(self):
        self.assertIn("generate_series", self.blocos["segunda"])
        self.assertNotIn("sobra", self.blocos["segunda"])

    def test_nao_arrasta_o_texto_de_apoio(self):
        self.assertNotIn("____", self.blocos["primeira"])

    def test_arquivo_sem_marcador(self):
        self.assertEqual(verificar.consultas_nomeadas("SELECT 1;"), {})


class TestLerCabecalho(unittest.TestCase):
    def test_separa_yaml_do_corpo(self):
        bruto = "---\ncliente: Aurora\ntitulo: Contrato X\n---\n\n# Titulo\n\ncorpo"
        metadados, corpo = chunking.ler_cabecalho(bruto)
        self.assertEqual(metadados["cliente"], "Aurora")
        self.assertEqual(metadados["titulo"], "Contrato X")
        self.assertTrue(corpo.startswith("# Titulo"))

    def test_arquivo_sem_cabecalho(self):
        metadados, corpo = chunking.ler_cabecalho("# So o corpo")
        self.assertEqual(metadados, {})
        self.assertEqual(corpo, "# So o corpo")

    def test_valor_com_dois_pontos_no_meio(self):
        bruto = "---\nvigencia: 2026-01-01 a 2027-12-31\n---\ncorpo"
        metadados, _ = chunking.ler_cabecalho(bruto)
        self.assertEqual(metadados["vigencia"], "2026-01-01 a 2027-12-31")


class TestDividir(unittest.TestCase):
    def test_uma_clausula_por_trecho(self):
        corpo = (
            "## Clausula 1\n\n" + "a" * 300 + "\n\n"
            "## Clausula 2\n\n" + "b" * 300 + "\n\n"
            "## Clausula 3\n\n" + "c" * 300
        )
        trechos = chunking.dividir(corpo)
        self.assertEqual(len(trechos), 3)
        self.assertTrue(trechos[0].startswith("## Clausula 1"))

    def test_clausula_longa_e_quebrada_repetindo_o_titulo(self):
        paragrafo = "x" * 800
        corpo = "## Clausula 1\n\n%s\n\n%s\n\n%s" % (paragrafo, paragrafo, paragrafo)
        trechos = chunking.dividir(corpo)
        self.assertGreater(len(trechos), 1)
        for trecho in trechos:
            self.assertTrue(trecho.startswith("## Clausula 1"))

    def test_respeita_o_teto_com_folga_de_um_paragrafo(self):
        paragrafo = "y" * 500
        corpo = "## C\n\n" + "\n\n".join([paragrafo] * 6)
        for trecho in chunking.dividir(corpo):
            self.assertLessEqual(len(trecho), chunking.TAMANHO_MAXIMO + 520)

    def test_trecho_curto_e_colado_no_seguinte(self):
        corpo = "## Titulo solto\n\n## Clausula 1\n\n" + "z" * 400
        trechos = chunking.dividir(corpo)
        self.assertEqual(len(trechos), 1)
        self.assertIn("Titulo solto", trechos[0])
        self.assertIn("Clausula 1", trechos[0])

    def test_corpo_vazio(self):
        self.assertEqual(chunking.dividir("   \n\n  "), [])

    def test_ordem_preservada(self):
        corpo = "\n\n".join("## C%d\n\n%s" % (i, "w" * 300) for i in range(1, 6))
        trechos = chunking.dividir(corpo)
        for i, trecho in enumerate(trechos, start=1):
            self.assertTrue(trecho.startswith("## C%d" % i))


class TestContratosDoAcervo(unittest.TestCase):
    """Os quatro contratos precisam gerar trechos suficientes para o RAG.

    Se alguém encurtar um contrato a ponto de ele virar dois trechos, a busca
    passa a ter pouco onde escolher e o Critério 5 fica frágil sem que ninguém
    perceba a causa.
    """

    def test_cada_contrato_gera_pelo_menos_seis_trechos(self):
        import os

        pasta = os.path.join(verificar.RAIZ, "contratos")
        arquivos = [n for n in os.listdir(pasta) if n.endswith(".md")]
        self.assertEqual(len(arquivos), 4)
        for nome in arquivos:
            with open(os.path.join(pasta, nome), encoding="utf-8") as f:
                _, corpo = chunking.ler_cabecalho(f.read())
            self.assertGreaterEqual(len(chunking.dividir(corpo)), 6, nome)


if __name__ == "__main__":
    unittest.main()
