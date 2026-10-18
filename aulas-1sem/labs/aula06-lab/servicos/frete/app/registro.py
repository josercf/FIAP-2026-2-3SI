"""Registro de modalidades de frete: onde o Open/Closed acontece.

Aqui mora a lacuna TODO-3 do laboratório.

A ideia é simples e é o ponto inteiro da aula: a rota HTTP não pode saber
quais modalidades existem. Ela pergunta ao registro qual estratégia atende
aquele nome, e executa. Acrescentar uma modalidade nova passa a ser
acrescentar uma linha **aqui**, sem tocar em `app/main.py`.

Assim como `estrategias.py`, este módulo não importa FastAPI: o registro é
regra de negócio, não detalhe de transporte.
"""

from .estrategias import (
    EstrategiaFrete,
    FreteEconomico,
    FreteExpresso,
    FretePadrao,
)

REGISTRO: dict[str, EstrategiaFrete] = {}
"""Mapa `nome da modalidade -> instância da estratégia`.

TODO-3: registre aqui as três modalidades originais da LogiTech, usando
`registrar(...)` logo abaixo da definição da função, e depois faça a rota de
`app/main.py` consultar `obter(...)` em vez da cadeia de `if`.
"""


def registrar(estrategia: EstrategiaFrete) -> None:
    """Põe uma estratégia no registro, indexada pelo próprio `modalidade`.

    Recusa nome repetido de propósito: duas estratégias disputando a mesma
    modalidade é erro de programação que se descobre na importação do
    módulo, e não em produção, com o cliente esperando a cotação.
    """
    nome = estrategia.modalidade
    if nome in REGISTRO:
        raise ValueError("modalidade já registrada: %s" % nome)
    REGISTRO[nome] = estrategia


def obter(modalidade: str) -> EstrategiaFrete:
    """Devolve a estratégia de uma modalidade. Levanta `KeyError` se não houver.

    Quem chama decide o que fazer com a ausência: a rota HTTP transforma em
    `422`, um consumidor interno pode querer cair na modalidade padrão.
    """
    try:
        return REGISTRO[modalidade]
    except KeyError:
        raise KeyError(
            "modalidade não suportada: %r. Disponíveis: %s"
            % (modalidade, ", ".join(modalidades()))) from None


def modalidades() -> list[str]:
    """Os nomes registrados, em ordem alfabética.

    Serve à rota `GET /api/v1/frete/modalidades` e é o que prova, no
    verificador, que o registro cresceu sem que a rota mudasse.
    """
    return sorted(REGISTRO)


# TODO-3: descomente e complete o registro das três modalidades originais.
# registrar(FreteExpresso())
# registrar(FreteEconomico())
# registrar(FretePadrao())
