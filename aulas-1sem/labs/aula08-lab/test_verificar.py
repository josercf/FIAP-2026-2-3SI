"""Testes do próprio `verificar.py`, nos dois sentidos.

Um verificador que só sabe aprovar não verifica nada. Esta suíte prova as duas
direções: ele **reprova o esqueleto** com as lacunas abertas e **aprova o
gabarito** de `resgate/`.

Os dois sentidos rodam em cópias do laboratório dentro de um diretório
temporário, num subprocesso: é o mesmo caminho que o aluno percorre, incluindo
subir o serviço de Pedidos numa porta livre. Nenhum teste daqui toca o
laboratório real nem a trilha de auditoria de ninguém.

Rodar:
    python3 -m pytest test_verificar.py -q
"""
import os
import shutil
import subprocess
import sys

import pytest

import verificar

RAIZ = os.path.dirname(os.path.abspath(__file__))

# Critérios que dependem só do código do aluno, sem worktree nem evidência
# preenchida. São eles que provam o sentido "reprova o esqueleto, aprova o
# gabarito" sem precisar montar um repositório git de mentira.
CRITERIOS_DE_CODIGO = (1, 3, 4, 5)


def _copiar_laboratorio(destino, com_gabarito):
    """Copia o laboratório para `destino`, opcionalmente com as lacunas
    preenchidas pelos arquivos de `resgate/`."""
    ignorar = shutil.ignore_patterns("__pycache__", "*.pyc", ".git",
                                      ".pytest_cache")
    shutil.copytree(RAIZ, destino, ignore=ignorar)
    if com_gabarito:
        for arquivo in ("esquemas.py", "comandos.py"):
            shutil.copyfile(os.path.join(destino, "resgate", arquivo),
                            os.path.join(destino, "agente", arquivo))
    return destino


def _rodar(destino, criterio):
    return subprocess.run(
        [sys.executable, "verificar.py", "--criterio", str(criterio)],
        cwd=destino, capture_output=True, text=True, timeout=180)


@pytest.fixture(scope="module")
def gabarito(tmp_path_factory):
    return _copiar_laboratorio(
        str(tmp_path_factory.mktemp("lab") / "gabarito"), com_gabarito=True)


# ---------------------------------------------------------------------------
# Sentido 1: a lacuna aberta é reprovada
#
# Estes testes reabrem as lacunas em memória, com `monkeypatch`, em vez de
# copiar os arquivos do laboratório. É de propósito: depois que você preencher
# os TODO, uma cópia do seu laboratório já não é mais um esqueleto, e um teste
# que dependesse disso passaria a falhar justamente por você ter acertado.
# ---------------------------------------------------------------------------
CAMPOS_ALTERACAO = ("pedido_id", "logradouro", "numero", "cidade", "uf", "cep")


def _esquema_minimo(obrigatorios, opcionais=()):
    """Monta um JSON Schema mecânico, só com os nomes dos campos.

    Não é o gabarito de TODO-1 nem de TODO-2: não tem descrição, `pattern` nem
    limite de tamanho, que é justamente o que se pede lá. Serve para os testes
    dos critérios 3, 4 e 5 exercitarem a camada de comandos sem depender de os
    esquemas do aluno já estarem prontos.
    """
    campos = list(obrigatorios) + list(opcionais)
    return {
        "type": "object",
        "properties": {c: {"type": "string"} for c in campos},
        "required": list(obrigatorios),
        "additionalProperties": False,
    }


@pytest.fixture
def esquemas_minimos(monkeypatch):
    consultar = _esquema_minimo(["pedido_id"])
    alterar = _esquema_minimo(CAMPOS_ALTERACAO, ["complemento"])
    monkeypatch.setattr(verificar.esquemas, "ESQUEMA_CONSULTAR_STATUS", consultar)
    monkeypatch.setattr(verificar.esquemas, "ESQUEMA_ALTERAR_ENDERECO", alterar)
    monkeypatch.setattr(verificar.mod_comandos.ConsultarStatusPedido,
                        "esquema", consultar)
    monkeypatch.setattr(verificar.mod_comandos.AlterarEnderecoEntrega,
                        "esquema", alterar)
    return consultar, alterar


def test_criterio_1_reprova_esquema_vazio_citando_a_lacuna(monkeypatch):
    monkeypatch.setattr(verificar.esquemas, "ESQUEMA_CONSULTAR_STATUS", {})
    passou, motivo = verificar.criterio_1()
    assert not passou
    assert "TODO-1" in motivo


def test_criterio_1_reprova_required_incompleto(esquemas_minimos, monkeypatch):
    """Schema preenchido pela metade também reprova: sem o cep em required, a
    lacuna TODO-5 deixaria de existir."""
    monkeypatch.setattr(verificar.esquemas, "ESQUEMA_ALTERAR_ENDERECO",
                        _esquema_minimo(CAMPOS_ALTERACAO[:-1], ["cep"]))
    passou, motivo = verificar.criterio_1()
    assert not passou
    assert "cep" in motivo


def test_criterio_3_reprova_com_a_lacuna_tres_aberta(esquemas_minimos, monkeypatch):
    def naoimplementado(self, argumentos):
        raise NotImplementedError("TODO-3: implemente ConsultarStatusPedido")

    monkeypatch.setattr(verificar.mod_comandos.ConsultarStatusPedido,
                        "executar", naoimplementado)
    passou, motivo = verificar.criterio_3()
    assert not passou
    assert "TODO-3" in motivo


def test_criterio_4_reprova_com_a_lacuna_quatro_aberta(esquemas_minimos, monkeypatch):
    def naoimplementado(self, argumentos):
        raise NotImplementedError("TODO-4: implemente AlterarEnderecoEntrega")

    monkeypatch.setattr(verificar.mod_comandos.AlterarEnderecoEntrega,
                        "executar", naoimplementado)
    passou, motivo = verificar.criterio_4()
    assert not passou
    assert "TODO-4" in motivo


def test_criterio_5_reprova_com_a_lacuna_cinco_aberta(monkeypatch):
    class DespachanteSemRecusa:
        def __init__(self, *args, **kwargs):
            pass

        def despachar(self, nome, argumentos):
            raise NotImplementedError("TODO-5: implemente a recusa auditada")

    monkeypatch.setattr(verificar.mod_comandos, "Despachante", DespachanteSemRecusa)
    passou, motivo = verificar.criterio_5()
    assert not passou
    assert "TODO-5" in motivo


def test_criterio_5_reprova_quando_a_recusa_executa_assim_mesmo(monkeypatch):
    """O pior defeito possível: recusar no papel e chamar a API mesmo assim."""

    class DespachanteFrouxo:
        def __init__(self, *args, **kwargs):
            pass

        def despachar(self, nome, argumentos):
            return verificar.mod_comandos.Resultado(
                verificar.auditoria.AUTORIZADO, {"ok": True})

    monkeypatch.setattr(verificar.mod_comandos, "Despachante", DespachanteFrouxo)
    passou, motivo = verificar.criterio_5()
    assert not passou
    assert "RECUSADO" in motivo


# ---------------------------------------------------------------------------
# Sentido 2: o gabarito é aprovado
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("criterio", CRITERIOS_DE_CODIGO)
def test_gabarito_e_aprovado(gabarito, criterio):
    p = _rodar(gabarito, criterio)
    assert p.returncode == 0, p.stdout


def test_gabarito_sobe_o_servico_sozinho(gabarito):
    """O verificador não pode reprovar quem esqueceu o outro terminal aberto:
    ele sobe o serviço de Pedidos numa porta livre quando não acha nenhum."""
    p = _rodar(gabarito, 2)
    assert p.returncode == 0, p.stdout


# ---------------------------------------------------------------------------
# Leitura dos marcadores de evidência
# ---------------------------------------------------------------------------
def test_marcador_ausente_nao_conta_como_preenchido():
    assert verificar._valor_preenchido("CEP_NOVO", "outra coisa\n") is None


def test_preencher_esquecido_nao_conta_como_preenchido():
    assert verificar._valor_preenchido("CEP_NOVO", "CEP_NOVO: PREENCHER") is None


def test_marcador_preenchido_devolve_o_valor():
    assert verificar._valor_preenchido(
        "CEP_NOVO", "CEP_NOVO: 01311-000") == "01311-000"


def _com_evidencias(monkeypatch, tmp_path, conteudo):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "EVIDENCIAS.md").write_text(conteudo, encoding="utf-8")
    monkeypatch.setattr(verificar, "RAIZ", str(tmp_path))


EVIDENCIAS_COMPLETAS = """
PEDIDO_ALTERADO_ID: PED-1044
CEP_NOVO: 01311-000
MOTIVO_DA_RECUSA: falta o campo obrigatório 'cep'
EXECUCOES_AUTORIZADAS: 3
RECUSAS_REGISTRADAS: 1
MODO_USADO: simular
USEI_O_RESGATE: não
"""


def test_criterio_8_aprova_evidencias_completas(monkeypatch, tmp_path):
    _com_evidencias(monkeypatch, tmp_path, EVIDENCIAS_COMPLETAS)
    passou, motivo = verificar.criterio_8()
    assert passou, motivo


def test_criterio_8_reprova_contagem_abaixo_do_minimo(monkeypatch, tmp_path):
    _com_evidencias(monkeypatch, tmp_path,
                    EVIDENCIAS_COMPLETAS.replace("EXECUCOES_AUTORIZADAS: 3",
                                                  "EXECUCOES_AUTORIZADAS: 1"))
    passou, motivo = verificar.criterio_8()
    assert not passou
    assert "EXECUCOES_AUTORIZADAS" in motivo


def test_criterio_8_reprova_cep_fora_do_formato(monkeypatch, tmp_path):
    _com_evidencias(monkeypatch, tmp_path,
                    EVIDENCIAS_COMPLETAS.replace("CEP_NOVO: 01311-000",
                                                  "CEP_NOVO: 01311000"))
    passou, motivo = verificar.criterio_8()
    assert not passou
    assert "CEP_NOVO" in motivo


def test_criterio_8_reprova_motivo_de_uma_palavra(monkeypatch, tmp_path):
    """Copiar 'erro' no lugar do motivo real não conta: o marcador existe para
    o aluno ler a trilha de auditoria, não para preencher qualquer coisa."""
    _com_evidencias(
        monkeypatch, tmp_path,
        EVIDENCIAS_COMPLETAS.replace(
            "MOTIVO_DA_RECUSA: falta o campo obrigatório 'cep'",
            "MOTIVO_DA_RECUSA: erro"))
    passou, motivo = verificar.criterio_8()
    assert not passou
    assert "MOTIVO_DA_RECUSA" in motivo


# ---------------------------------------------------------------------------
# Worktrees
# ---------------------------------------------------------------------------
def _repo_com_worktrees(tmp_path, criar_worktrees):
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        subprocess.run(["git", "-C", str(repo), *args], check=True,
                        capture_output=True, text=True)

    git("init", "-q", "-b", "main", ".")
    git("config", "user.email", "teste@exemplo.local")
    git("config", "user.name", "Teste")
    (repo / "leiame.txt").write_text("laboratório\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "primeiro commit")
    if criar_worktrees:
        for nome, branch in (("wt-agente-pedidos", "agente/pedidos"),
                             ("wt-agente-atendimento", "agente/atendimento")):
            git("branch", branch)
            git("worktree", "add", "-q", str(tmp_path / nome), branch)
    return str(repo)


# O critério 7 exerce `git worktree`. Em ambiente sem git instalado (um
# contêiner cru, por exemplo) o teste pularia com erro de arquivo não
# encontrado; pular explicitamente deixa a suíte verde onde quer que ela rode,
# sem esconder falha de verdade.
sem_git = pytest.mark.skipif(shutil.which("git") is None,
                             reason="git não está instalado neste ambiente")


@sem_git
def test_criterio_7_reprova_sem_worktrees(monkeypatch, tmp_path):
    monkeypatch.setattr(verificar, "RAIZ",
                        _repo_com_worktrees(tmp_path, criar_worktrees=False))
    passou, motivo = verificar.criterio_7()
    assert not passou
    assert "wt-agente-pedidos" in motivo


@sem_git
def test_criterio_7_aprova_com_as_duas_worktrees(monkeypatch, tmp_path):
    monkeypatch.setattr(verificar, "RAIZ",
                        _repo_com_worktrees(tmp_path, criar_worktrees=True))
    passou, motivo = verificar.criterio_7()
    assert passou, motivo


@sem_git
def test_criterio_7_reprova_fora_de_repositorio_git(monkeypatch, tmp_path):
    monkeypatch.setattr(verificar, "RAIZ", str(tmp_path))
    passou, motivo = verificar.criterio_7()
    assert not passou
    assert "git" in motivo.lower()
