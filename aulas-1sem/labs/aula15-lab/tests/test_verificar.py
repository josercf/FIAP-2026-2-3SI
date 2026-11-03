"""Testes do próprio verificador, nos dois sentidos.

Um verificador que aprova tudo é pior do que nenhum, porque dá confiança
falsa. Estes testes provam que cada critério **reprova** o esqueleto e
**aprova** o resgate, sem depender de container nenhum no ar: o que fala com
a rede é substituído por dublê.

    python3 -m pytest tests/ -q
"""

import importlib.util
import json
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carregar():
    """Importa `verificar.py` como módulo, sem depender de pacote."""
    caminho = os.path.join(RAIZ, "verificar.py")
    spec = importlib.util.spec_from_file_location("verificar_a14", caminho)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["verificar_a14"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture()
def v(monkeypatch):
    # O `docker compose config` interpola a senha do admin a partir do `.env`,
    # que está no .gitignore e pode não existir na máquina que roda os testes.
    # Aqui ela vem do ambiente, que é o mesmo caminho que o Compose usa.
    monkeypatch.setenv("LOGITECH_KEYCLOAK_ADMIN_PASSWORD", "senha-de-teste")
    modulo = carregar()
    modulo.TOKENS.clear()
    return modulo


# ---------------------------------------------------------------------------
# Critério 1: o Compose
# ---------------------------------------------------------------------------


def test_criterio_1_avisa_quando_falta_o_env(v, monkeypatch):
    """Falha de interpolação por falta de `.env` precisa dizer isso, e não
    mandar o aluno procurar erro de YAML."""
    monkeypatch.delenv("LOGITECH_KEYCLOAK_ADMIN_PASSWORD", raising=False)
    v.ARQUIVO_COMPOSE = "resgate/docker-compose.yml"
    problemas = v.criterio_1()
    assert problemas and ".env" in problemas[0]


def test_criterio_1_reprova_o_esqueleto(v):
    """O `docker-compose.yml` entregue não tem o serviço keycloak."""
    v.ARQUIVO_COMPOSE = "docker-compose.yml"
    problemas = v.criterio_1()
    assert problemas, "o esqueleto nao pode passar no criterio 1"
    assert any("keycloak" in p for p in problemas)


@pytest.mark.skipif(not os.path.exists(os.path.join(RAIZ, "resgate/docker-compose.yml")),
                    reason="resgate ausente")
def test_criterio_1_aprova_o_resgate(v):
    v.ARQUIVO_COMPOSE = "resgate/docker-compose.yml"
    assert v.criterio_1() == []


def test_criterio_1_cobra_o_import_realm(v, tmp_path, monkeypatch):
    """Um Compose com keycloak mas sem --import-realm precisa reprovar."""
    def config_falso(_arquivo):
        return {"services": {
            "keycloak": {
                "image": "quay.io/keycloak/keycloak:26.0",
                "command": ["start-dev", "--http-port=8090"],
                "volumes": [{"source": os.path.join(RAIZ, "keycloak")}],
                "ports": [{"published": "8090"}],
                "environment": {"KC_HEALTH_ENABLED": "true"},
                "healthcheck": {"test": ["CMD-SHELL", "true"]},
            },
            "pedidos": {"depends_on": {"keycloak": {"condition": "service_healthy"}}},
            "notificacoes": {"depends_on": {"keycloak": {"condition": "service_healthy"}}},
        }}, ""
    monkeypatch.setattr(v, "compose_config", config_falso)
    problemas = v.criterio_1()
    assert any("import-realm" in p for p in problemas)


def test_criterio_1_cobra_o_depends_on_com_condicao(v, monkeypatch):
    def config_falso(_arquivo):
        return {"services": {
            "keycloak": {
                "image": "quay.io/keycloak/keycloak:26.0",
                "command": ["start-dev", "--import-realm"],
                "volumes": [{"source": os.path.join(RAIZ, "keycloak")}],
                "ports": [{"published": "8090"}],
                "environment": {"KC_HEALTH_ENABLED": "true"},
                "healthcheck": {"test": ["CMD-SHELL", "true"]},
            },
            "pedidos": {"depends_on": {"keycloak": {"condition": "service_started"}}},
            "notificacoes": {},
        }}, ""
    monkeypatch.setattr(v, "compose_config", config_falso)
    problemas = v.criterio_1()
    assert sum("service_healthy" in p for p in problemas) == 2


# ---------------------------------------------------------------------------
# Critérios 2 a 5: o comportamento HTTP
# ---------------------------------------------------------------------------


def dublar_http(monkeypatch, modulo, respostas):
    """Substitui `chamar` por uma tabela (metodo, url) -> (codigo, corpo)."""
    def chamar(metodo, url, token=None, corpo=None):
        chave = (metodo, url, token_de(modulo, token))
        return respostas.get(chave, respostas.get((metodo, url), (0, "nao mapeado")))
    monkeypatch.setattr(modulo, "chamar", chamar)


def token_de(modulo, token):
    for usuario, dado in modulo.TOKENS.items():
        if dado.get("access_token") == token:
            return usuario
    return None


def test_criterio_2_reprova_health_fechada(v, monkeypatch):
    dublar_http(monkeypatch, v, {
        ("GET", v.PEDIDOS + "/health"): (401, "{}"),
        ("GET", v.NOTIFICACOES + "/health"): (200, json.dumps({"autenticacaoAtiva": True})),
    })
    problemas = v.criterio_2()
    assert any("401" in p and "SEM token" in p for p in problemas)


def test_criterio_2_reprova_interruptor_desligado(v, monkeypatch):
    corpo = json.dumps({"status": "ok", "autenticacaoAtiva": False})
    dublar_http(monkeypatch, v, {
        ("GET", v.PEDIDOS + "/health"): (200, corpo),
        ("GET", v.NOTIFICACOES + "/health"): (200, corpo),
    })
    problemas = v.criterio_2()
    assert len(problemas) == 2
    assert all("LOGITECH_AUTH_ATIVA" in p for p in problemas)


def test_criterio_2_aprova_o_esperado(v, monkeypatch):
    corpo = json.dumps({"status": "ok", "autenticacaoAtiva": True})
    dublar_http(monkeypatch, v, {
        ("GET", v.PEDIDOS + "/health"): (200, corpo),
        ("GET", v.NOTIFICACOES + "/health"): (200, corpo),
    })
    assert v.criterio_2() == []


def test_criterio_3_reprova_403_no_lugar_de_401(v, monkeypatch):
    """O erro clássico: mandar 403 para quem nem se identificou."""
    dublar_http(monkeypatch, v, {
        ("GET", v.PEDIDOS + "/api/v1/pedidos"): (403, "{}"),
        ("POST", v.NOTIFICACOES + "/api/v1/notificacoes"): (401, "{}"),
    })
    problemas = v.criterio_3()
    assert len(problemas) == 1
    assert "403" in problemas[0] and "401" in problemas[0]


def test_criterio_3_reprova_rota_desprotegida(v, monkeypatch):
    dublar_http(monkeypatch, v, {
        ("GET", v.PEDIDOS + "/api/v1/pedidos"): (200, "[]"),
        ("POST", v.NOTIFICACOES + "/api/v1/notificacoes"): (401, "{}"),
    })
    assert len(v.criterio_3()) == 1


def test_criterio_3_aprova_401_nos_dois(v, monkeypatch):
    dublar_http(monkeypatch, v, {
        ("GET", v.PEDIDOS + "/api/v1/pedidos"): (401, "{}"),
        ("POST", v.NOTIFICACOES + "/api/v1/notificacoes"): (401, "{}"),
    })
    assert v.criterio_3() == []


def preparar_tokens(modulo):
    modulo.TOKENS.clear()
    for usuario in modulo.USUARIOS:
        modulo.TOKENS[usuario] = {"access_token": "token-de-" + usuario}


def test_criterio_4_reprova_motorista_criando_pedido(v, monkeypatch):
    preparar_tokens(v)
    respostas = {
        ("GET", v.PEDIDOS + "/api/v1/pedidos", "ana.cliente"): (200, "{}"),
        ("GET", v.PEDIDOS + "/api/v1/pedidos", "bruno.motorista"): (200, "{}"),
        # o defeito: o motorista consegue criar
        ("POST", v.PEDIDOS + "/api/v1/pedidos", "bruno.motorista"): (201, "{}"),
        ("PATCH", v.PEDIDOS + "/api/v1/pedidos/PED-1042/endereco", "ana.cliente"): (200, "{}"),
        ("PATCH", v.PEDIDOS + "/api/v1/pedidos/PED-1042/endereco", "bruno.motorista"): (403, "{}"),
        ("GET", v.PEDIDOS + "/api/v1/pedidos/PED-1042/status", "bruno.motorista"): (200, "{}"),
    }
    dublar_http(monkeypatch, v, respostas)
    problemas = v.criterio_4()
    assert len(problemas) == 1
    assert "201" in problemas[0]


def test_criterio_4_aprova_a_matriz_correta(v, monkeypatch):
    preparar_tokens(v)
    respostas = {
        ("GET", v.PEDIDOS + "/api/v1/pedidos", "ana.cliente"): (200, "{}"),
        ("GET", v.PEDIDOS + "/api/v1/pedidos", "bruno.motorista"): (200, "{}"),
        ("POST", v.PEDIDOS + "/api/v1/pedidos", "bruno.motorista"): (403, "{}"),
        ("PATCH", v.PEDIDOS + "/api/v1/pedidos/PED-1042/endereco", "ana.cliente"): (200, "{}"),
        ("PATCH", v.PEDIDOS + "/api/v1/pedidos/PED-1042/endereco", "bruno.motorista"): (403, "{}"),
        ("GET", v.PEDIDOS + "/api/v1/pedidos/PED-1042/status", "bruno.motorista"): (200, "{}"),
    }
    dublar_http(monkeypatch, v, respostas)
    assert v.criterio_4() == []


def test_criterio_5_reprova_papel_lido_do_lugar_errado(v, monkeypatch):
    """Node lendo de `resource_access` deixa passar quem devia levar 403."""
    preparar_tokens(v)
    dublar_http(monkeypatch, v, {
        ("POST", v.NOTIFICACOES + "/api/v1/notificacoes", "carla.admin"): (201, "{}"),
        ("POST", v.NOTIFICACOES + "/api/v1/notificacoes", "bruno.motorista"): (201, "{}"),
        ("GET", v.PEDIDOS + "/api/v1/pedidos", "bruno.motorista"): (200, "{}"),
    })
    problemas = v.criterio_5()
    assert len(problemas) == 1
    assert "realm_access.roles" in problemas[0]


def test_criterio_5_aprova_o_esperado(v, monkeypatch):
    preparar_tokens(v)
    dublar_http(monkeypatch, v, {
        ("POST", v.NOTIFICACOES + "/api/v1/notificacoes", "carla.admin"): (201, "{}"),
        ("POST", v.NOTIFICACOES + "/api/v1/notificacoes", "bruno.motorista"): (403, "{}"),
        ("GET", v.PEDIDOS + "/api/v1/pedidos", "bruno.motorista"): (200, "{}"),
    })
    assert v.criterio_5() == []


# ---------------------------------------------------------------------------
# Critério 6: as evidências
# ---------------------------------------------------------------------------


EVIDENCIAS_COMPLETAS = """
TOKEN_EXPIRA_EM_S: 300
PAPEIS_NO_TOKEN: ["CLIENTE"]
ISSUER_NO_TOKEN: http://localhost:8090/realms/logitech
CURL_SEM_TOKEN: HTTP/1.1 401 Unauthorized
CURL_PAPEL_ERRADO: HTTP/1.1 403 Forbidden
WORKTREE_AUTH: ../agent-auth
WORKTREE_UI: ../agent-ui
SAIDA_DO_GIT_WORKTREE_LIST: /w/lab14 abc1234 [main]
/w/agent-auth def5678 [seguranca/backend]
/w/agent-ui   9876abc [seguranca/portal]
"""


def token_falso(exp_menos_iat=300):
    import base64
    def parte(o):
        return base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")
    return "%s.%s.assinatura" % (
        parte({"alg": "RS256"}),
        parte({"iat": 1000, "exp": 1000 + exp_menos_iat,
               "realm_access": {"roles": ["CLIENTE"]}}))


def test_criterio_6_reprova_o_esqueleto(v):
    """O arquivo entregue está cheio de PREENCHER."""
    problemas = v.criterio_6()
    assert len(problemas) >= 5
    assert any("TOKEN_EXPIRA_EM_S" in p for p in problemas)


def test_criterio_6_reprova_numero_inventado(v, monkeypatch, tmp_path):
    v.TOKENS["ana.cliente"] = {"access_token": token_falso(300)}
    texto = EVIDENCIAS_COMPLETAS.replace("TOKEN_EXPIRA_EM_S: 300",
                                         "TOKEN_EXPIRA_EM_S: 3600")
    monkeypatch.setattr(v, "ler", lambda _c: texto)
    problemas = v.criterio_6()
    assert any("3600" in p and "300" in p for p in problemas)


def test_criterio_6_reprova_worktree_list_sem_as_duas(v, monkeypatch):
    v.TOKENS["ana.cliente"] = {"access_token": token_falso(300)}
    texto = EVIDENCIAS_COMPLETAS.replace("[seguranca/portal]", "[outra-coisa]") \
                                .replace("/w/agent-ui   9876abc", "/w/outro 9876abc")
    monkeypatch.setattr(v, "ler", lambda _c: texto)
    assert any("agent-ui" in p for p in v.criterio_6())


def test_criterio_6_reprova_401_registrado_como_403(v, monkeypatch):
    v.TOKENS["ana.cliente"] = {"access_token": token_falso(300)}
    texto = EVIDENCIAS_COMPLETAS.replace("CURL_SEM_TOKEN: HTTP/1.1 401 Unauthorized",
                                         "CURL_SEM_TOKEN: HTTP/1.1 403 Forbidden")
    monkeypatch.setattr(v, "ler", lambda _c: texto)
    assert any("CURL_SEM_TOKEN" in p for p in v.criterio_6())


def test_criterio_6_aprova_evidencias_completas(v, monkeypatch):
    v.TOKENS["ana.cliente"] = {"access_token": token_falso(300)}
    monkeypatch.setattr(v, "ler", lambda _c: EVIDENCIAS_COMPLETAS)
    assert v.criterio_6() == []


# ---------------------------------------------------------------------------
# Ferramentas do próprio verificador
# ---------------------------------------------------------------------------


def test_valor_recusa_o_esqueleto_preencher(v):
    assert v._valor("X", "X: PREENCHER") is None
    assert v._valor("X", "X: ") is None
    assert v._valor("X", "Y: 3") is None
    assert v._valor("X", "X: 300") == "300"


def test_decodificar_le_o_conteudo_do_token(v):
    conteudo = v.decodificar(token_falso(300))
    assert conteudo["exp"] - conteudo["iat"] == 300
    assert conteudo["realm_access"]["roles"] == ["CLIENTE"]


def test_b64url_nao_tem_preenchimento(v):
    assert "=" not in v.b64url(b"\x01\x02\x03\x04\x05")
