#!/usr/bin/env python3
"""Testes automatizados de `verificar.py`.

Só `unittest` da biblioteca padrão (`unittest.mock` incluso). Nenhum teste
aqui depende de Docker instalado nem de rede: toda chamada real ao binário
`docker` é isolada atrás da função `docker()` do módulo e substituída por
uma versão falsa via `unittest.mock.patch`, porque essa função existe
exatamente para tornar isso possível. Duas rodadas de revisão encontraram,
à mão, seis defeitos que invertiam veredito neste arquivo; esta suíte
existe para que a próxima vez que algo quebrar apareça aqui primeiro.

Rodar de dentro deste diretório:
    python3 -m unittest verificar_test -v
ou:
    python3 -m unittest
"""
import os
import shutil
import tempfile
import unittest
from unittest import mock

import verificar


class TesteBase(unittest.TestCase):
    """Aponta verificar.RAIZ para um diretório temporário isolado antes de
    cada teste, e restaura ao final. Nenhum teste desta suíte deve tocar o
    laboratório real nem deixar arquivo para trás."""

    def setUp(self):
        self._raiz_original = verificar.RAIZ
        self.tmp = tempfile.mkdtemp(prefix="verificar-test-")
        verificar.RAIZ = self.tmp

    def tearDown(self):
        verificar.RAIZ = self._raiz_original
        shutil.rmtree(self.tmp, ignore_errors=True)

    def escreve(self, caminho_relativo, conteudo):
        """Escreve um arquivo dentro do diretório temporário da raiz de
        teste, criando os diretórios intermediários que faltarem."""
        caminho = os.path.join(self.tmp, caminho_relativo)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)


class TesteEstagiosEUsuario(TesteBase):
    """Critical 1 da rodada 1 de revisão: o Docker não exige nome no
    estágio final de um build multi-stage, e não nomeá-lo é prática comum
    e correta. A contagem de estágios não pode depender de nome."""

    def test_estagio_final_sem_nome_conta_como_estagio(self):
        self.escreve("Dockerfile.coletor", (
            "FROM python:3.12-alpine AS builder\n"
            "WORKDIR /build\n"
            "\n"
            "FROM python:3.12-alpine\n"
            "USER logitech\n"
        ))
        estagios, usuario = verificar._estagios_e_usuario("Dockerfile.coletor")
        self.assertEqual(estagios, 2)
        self.assertTrue(usuario)

    def test_um_from_so_reprova_por_falta_de_estagio(self):
        self.escreve("Dockerfile.coletor", (
            "FROM python:3.12-alpine\n"
            "USER logitech\n"
        ))
        estagios, _ = verificar._estagios_e_usuario("Dockerfile.coletor")
        self.assertEqual(estagios, 1)
        self.assertLess(estagios, 2, "um FROM só não pode contar como multi-stage")

    def test_user_root_explicito_nao_conta_como_nao_root(self):
        self.escreve("Dockerfile.coletor", (
            "FROM python:3.12-alpine AS builder\n"
            "FROM python:3.12-alpine\n"
            "USER root\n"
        ))
        _, usuario = verificar._estagios_e_usuario("Dockerfile.coletor")
        self.assertFalse(usuario, "USER root não é usuário não-root")

    def test_ausencia_de_user_tambem_nao_conta_como_nao_root(self):
        self.escreve("Dockerfile.coletor", (
            "FROM python:3.12-alpine AS builder\n"
            "FROM python:3.12-alpine\n"
        ))
        _, usuario = verificar._estagios_e_usuario("Dockerfile.coletor")
        self.assertFalse(usuario)


class TestePreencherReprova(TesteBase):
    """A palavra de esqueleto 'PREENCHER' precisa reprovar em toda etapa
    que lê texto, e não passar despercebida por um regex de presença
    simples (achado da Tarefa 4 original, item 5 do contexto do
    coordenador)."""

    def test_etapa_1_reprova_com_preencher_nos_quatro_marcadores(self):
        self.escreve("etapas/01-isolamento/RESPOSTAS.md", (
            "PID_DENTRO: PREENCHER\n"
            "PID_FORA: PREENCHER\n"
            "HOSTNAME_DENTRO: PREENCHER\n"
            "MOUNTS_DENTRO: PREENCHER\n"
        ))
        passou, motivo = verificar.etapa_1()
        self.assertFalse(passou)
        self.assertIn("PID_DENTRO", motivo)
        self.assertIn("PID_FORA", motivo)
        self.assertIn("HOSTNAME_DENTRO", motivo)
        self.assertIn("MOUNTS_DENTRO", motivo)

    def test_etapa_2_reprova_com_container_id_preencher(self):
        self.escreve("etapas/02-imagem/RESPOSTAS.md", (
            "CONTAINER_ID: PREENCHER\n"
            "ARQUIVO_APOS_RM: sumiu\n"
        ))
        # CONTAINER_ID: PREENCHER falha no regex hexadecimal antes de
        # qualquer chamada ao Docker; docker() nem deveria ser chamado
        # aqui, mas mocko mesmo assim para a suíte nunca depender de rede.
        with mock.patch("verificar.docker", return_value=(0, "", "")):
            passou, motivo = verificar.etapa_2()
        self.assertFalse(passou)
        self.assertIn("CONTAINER_ID", motivo)


class TestePidDentroFora(TesteBase):
    """PID_DENTRO igual a PID_FORA não comprova isolamento nenhum; um par
    plausível (baixo dentro, alto fora, como um container real produz)
    precisa passar."""

    def test_pids_iguais_reprova(self):
        self.escreve("etapas/01-isolamento/RESPOSTAS.md", (
            "PID_DENTRO: 500\n"
            "PID_FORA: 500\n"
            "HOSTNAME_DENTRO: 0f19603ad7f1\n"
            "MOUNTS_DENTRO: 22\n"
        ))
        passou, motivo = verificar.etapa_1()
        self.assertFalse(passou)
        self.assertIn("iguais", motivo)

    def test_par_realista_passa(self):
        self.escreve("etapas/01-isolamento/RESPOSTAS.md", (
            "PID_DENTRO: 7\n"
            "PID_FORA: 731\n"
            "HOSTNAME_DENTRO: 0f19603ad7f1\n"
            "MOUNTS_DENTRO: 22\n"
        ))
        passou, motivo = verificar.etapa_1()
        self.assertTrue(passou, motivo)

    def test_caso_fabricado_do_revisor_pid_fora_baixo_demais_reprova(self):
        # PID_DENTRO=1 / PID_FORA=2: os dois numéricos e diferentes, mas
        # nenhum container precisou existir para escrever isso.
        self.escreve("etapas/01-isolamento/RESPOSTAS.md", (
            "PID_DENTRO: 1\n"
            "PID_FORA: 2\n"
            "HOSTNAME_DENTRO: meucontainer\n"
            "MOUNTS_DENTRO: 22\n"
        ))
        passou, motivo = verificar.etapa_1()
        self.assertFalse(passou)


class TesteParaFloat(unittest.TestCase):
    """Vírgula decimal (convenção em português) e ponto decimal precisam
    produzir o mesmo número, sem truncamento silencioso."""

    def test_virgula_e_ponto_produzem_mesmo_numero(self):
        self.assertEqual(verificar._para_float("95,2"), verificar._para_float("95.2"))
        self.assertEqual(verificar._para_float("86,2"), 86.2)

    def test_valor_inteiro_sem_separador_funciona(self):
        self.assertEqual(verificar._para_float("80"), 80.0)


class TesteLimiteReducao(TesteBase):
    """Redução abaixo do limite reprova, e o valor no limite exato passa.
    O build em si é substituído por uma versão falsa que sempre 'builda
    com sucesso', para isolar só a lógica de leitura de EVIDENCIAS.md e
    comparação com LIMITE_REDUCAO."""

    def setUp(self):
        super().setUp()
        self.escreve("Dockerfile.coletor", (
            "FROM python:3.12-alpine AS builder\n"
            "FROM python:3.12-alpine\n"
            "USER logitech\n"
        ))
        self.escreve("Dockerfile.gateway", (
            "FROM node:22-alpine AS builder\n"
            "FROM node:22-alpine\n"
            "USER logitech\n"
        ))

    def test_reducao_abaixo_do_limite_reprova(self):
        self.escreve("docs/EVIDENCIAS.md", (
            "REDUCAO_COLETOR: 95.2 %\n"
            "REDUCAO_GATEWAY: 79.9 %\n"
        ))
        with mock.patch("verificar.docker", return_value=(0, "", "")):
            passou, motivo = verificar.etapa_4()
        self.assertFalse(passou)
        self.assertIn("abaixo do mínimo", motivo)

    def test_reducao_no_limite_exato_passa(self):
        linha_gateway = "REDUCAO_GATEWAY: %.1f %%\n" % verificar.LIMITE_REDUCAO
        self.escreve("docs/EVIDENCIAS.md",
                      "REDUCAO_COLETOR: 95.2 %\n" + linha_gateway)
        with mock.patch("verificar.docker", return_value=(0, "", "")):
            passou, motivo = verificar.etapa_4()
        self.assertTrue(passou, motivo)

    def test_reducao_com_virgula_no_limite_exato_tambem_passa(self):
        self.escreve("docs/EVIDENCIAS.md", (
            "REDUCAO_COLETOR: 95,2 %\n"
            "REDUCAO_GATEWAY: 80,0 %\n"
        ))
        with mock.patch("verificar.docker", return_value=(0, "", "")):
            passou, motivo = verificar.etapa_4()
        self.assertTrue(passou, motivo)


class TesteArquivoAusente(TesteBase):
    """Arquivo ausente reprova com mensagem legível, e nunca estoura
    exceção: é a diferença entre um verificador utilizável e um que quebra
    a correção de trinta repositórios no primeiro que ainda não fez nada."""

    def test_etapa_1_sem_respostas_md(self):
        passou, motivo = verificar.etapa_1()
        self.assertFalse(passou)
        self.assertIn("não existe", motivo)

    def test_etapa_2_sem_respostas_md(self):
        passou, motivo = verificar.etapa_2()
        self.assertFalse(passou)
        self.assertIn("não existe", motivo)

    def test_etapa_3_sem_dockerfile(self):
        passou, motivo = verificar.etapa_3()
        self.assertFalse(passou)
        self.assertIn("não existe", motivo)

    def test_etapa_4_sem_dockerfile(self):
        passou, motivo = verificar.etapa_4()
        self.assertFalse(passou)
        self.assertIn("não existe", motivo)

    def test_etapa_5_sem_evidencias_com_volume_existindo(self):
        with mock.patch("verificar.docker",
                         return_value=(0, "logitech-telemetria", "")):
            passou, motivo = verificar.etapa_5()
        self.assertFalse(passou)
        self.assertIn("LINHAS_APOS_RM", motivo)

    def test_etapa_6_sem_evidencias_com_rede_existindo(self):
        with mock.patch("verificar.docker",
                         return_value=(0, "logitech-net", "")):
            passou, motivo = verificar.etapa_6()
        self.assertFalse(passou)
        self.assertIn("MEMORIA_COLETOR_MB", motivo)

    def test_etapa_7_sem_evidencias(self):
        passou, motivo = verificar.etapa_7()
        self.assertFalse(passou)
        self.assertIn("IMAGEM_PUBLICA", motivo)


class TesteEtapa7ClassificaFalha(TesteBase):
    """Important da rodada 1: distinguir 'imagem não existe/privada' de
    'não foi possível alcançar o registry', com stderr real do Docker."""

    def setUp(self):
        super().setUp()
        self.escreve("docs/EVIDENCIAS.md",
                      "IMAGEM_PUBLICA: usuario/imagem:1.0\n")

    def test_imagem_negada_cai_no_bucket_de_imagem(self):
        erro = ("errors:\ndenied: requested access to the resource is "
                "denied\nunauthorized: authentication required")
        with mock.patch("verificar.docker", return_value=(1, "", erro)):
            passou, motivo = verificar.etapa_7()
        self.assertFalse(passou)
        self.assertIn("não existe", motivo)

    def test_falha_de_rede_cai_no_bucket_de_rede(self):
        erro = ('failed to configure transport: error pinging v2 registry: '
                'Get "https://exemplo.invalid/v2/": dial tcp: lookup '
                'exemplo.invalid: no such host')
        with mock.patch("verificar.docker", return_value=(1, "", erro)):
            passou, motivo = verificar.etapa_7()
        self.assertFalse(passou)
        self.assertIn("alcançar", motivo)

    def test_timeout_produz_mensagem_de_tempo_esgotado(self):
        with mock.patch("verificar.docker", return_value=(124, "", "tempo esgotado")):
            passou, motivo = verificar.etapa_7()
        self.assertFalse(passou)
        self.assertEqual(motivo, "tempo esgotado")


if __name__ == "__main__":
    unittest.main()
