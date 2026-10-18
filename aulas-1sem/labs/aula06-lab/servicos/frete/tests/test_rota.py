"""Testes da API HTTP do serviço de frete.

Estes testes **passam desde o esqueleto** e precisam continuar passando
depois do TODO-3. É a rede de segurança da refatoração: o Strategy muda a
estrutura interna, nunca a resposta que o cliente da API recebe.

Se algum destes quebrar durante o laboratório, o refactor mudou
comportamento, e isso não é refactor.
"""

from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)

CARGA_REFERENCIA = {"origem": "SAO", "destino": "LDB", "pesoKg": 100.0}


def test_health_responde_ok():
    """Contrato da ADR-006: todo serviço da plataforma tem esta rota."""
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_cotacao_expressa_na_rota_de_referencia():
    resposta = cliente.post("/api/v1/frete/cotacao",
                            json={**CARGA_REFERENCIA, "modalidade": "expresso"})
    assert resposta.status_code == 200
    assert resposta.json() == {"valor": 545.0, "prazoDias": 1,
                               "modalidade": "expresso"}


def test_cotacao_economica_na_rota_de_referencia():
    resposta = cliente.post("/api/v1/frete/cotacao",
                            json={**CARGA_REFERENCIA, "modalidade": "economico"})
    assert resposta.status_code == 200
    assert resposta.json() == {"valor": 265.0, "prazoDias": 4,
                               "modalidade": "economico"}


def test_cotacao_padrao_na_rota_de_referencia():
    resposta = cliente.post("/api/v1/frete/cotacao",
                            json={**CARGA_REFERENCIA, "modalidade": "padrao"})
    assert resposta.status_code == 200
    assert resposta.json() == {"valor": 380.0, "prazoDias": 2,
                               "modalidade": "padrao"}


def test_modalidade_desconhecida_devolve_422():
    """O cliente precisa saber que pediu algo que não existe."""
    resposta = cliente.post("/api/v1/frete/cotacao",
                            json={**CARGA_REFERENCIA, "modalidade": "foguete"})
    assert resposta.status_code == 422


def test_peso_negativo_e_recusado_pelo_contrato_pydantic():
    """Validação de entrada é do Pydantic, não da regra de negócio."""
    resposta = cliente.post("/api/v1/frete/cotacao",
                            json={"origem": "SAO", "destino": "LDB",
                                  "pesoKg": -3, "modalidade": "expresso"})
    assert resposta.status_code == 422


def test_openapi_publica_o_contrato_da_cotacao():
    """O `/docs` do FastAPI sai daqui: o esquema é gerado, não escrito."""
    esquema = cliente.get("/openapi.json").json()
    assert "/api/v1/frete/cotacao" in esquema["paths"]
    propriedades = esquema["components"]["schemas"]["PedidoCotacao"]["properties"]
    assert set(propriedades) == {"origem", "destino", "pesoKg", "modalidade"}


def test_rota_de_modalidades_lista_o_registro():
    """Passa a valer de verdade depois do TODO-3, quando o registro enche."""
    resposta = cliente.get("/api/v1/frete/modalidades")
    assert resposta.status_code == 200
    assert isinstance(resposta.json()["modalidades"], list)
