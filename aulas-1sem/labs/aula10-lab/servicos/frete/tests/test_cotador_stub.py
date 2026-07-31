"""TODO-1: o Stub. Resposta pré-programada, asserção sobre o resultado.

ESTE ARQUIVO É SEU. Escreva aqui.

O que é um Stub, em uma frase: um dublê que **responde o que você mandou
responder**, para o teste poder chegar até a regra que interessa.

`CotadorDePedido` recebe o cliente no construtor. Nenhum teste desta pasta
pode usar `ClientePedidosHttp`: o `conftest.py` bloqueia a rede e o teste
falharia na hora. No lugar dele, entre com um objeto seu.

Um Stub em Python puro cabe em cinco linhas, e não precisa herdar de nada,
porque `ClientePedidos` é um `Protocol`:

    class ClientePedidosStub:
        def __init__(self, pedido):
            self._pedido = pedido

        def buscar(self, pedido_id):
            return self._pedido

Escreva **no mínimo quatro** testes, cobrindo as regras de valor e de prazo
do `CotadorDePedido` (leia a docstring de `app/cotador.py`):

1. a cotação da rota de referência (`PEDIDO_LEVE`, SAO -> LDB, 500 km,
   100 kg) na modalidade `expresso` sai por **545,00 em 1 dia**, sem
   desconto, porque 100 kg está longe de carga fechada;
2. um pedido a partir de 1000 kg recebe os 8 por cento de desconto de carga
   fechada, e `carga_fechada` volta `True`;
3. uma rota acima de 1000 km ganha **um dia** a mais de prazo por causa do
   pernoite obrigatório;
4. carga acima do limite da frota levanta `CargaAcimaDoLimite`.

Os pedidos de apoio já estão no `conftest.py`: `PEDIDO_LEVE`,
`PEDIDO_CARGA_FECHADA`, `PEDIDO_PESADO` e `PEDIDO_ACIMA_DO_LIMITE`. Importe
de `conftest` ou construa `PedidoResumo` você mesmo, como preferir.

UMA ARMADILHA, e ela reprova critério: escreva o valor esperado **à mão**.
Calcular o esperado com `bruto * (1 - DESCONTO_CARGA_FECHADA)`, importando a
constante do próprio código sob teste, produz um teste que passa mesmo com o
desconto zerado, porque os dois lados da igualdade mudam juntos. Teste que
repete a fórmula da implementação não testa a fórmula: testa a si mesmo.

Como o verificador avalia este arquivo (`--criterio 1`): ele estraga uma
cópia do código de produção, trocando um número da tabela de preços e
depois zerando o desconto de carga fechada, e exige que **os seus testes
reprovem** nas duas. Teste que não reprova código errado não é teste, é
decoração verde.
"""

# Sugestão de importações. Apague o que não usar.
# import pytest
#
# from app.cotador import CargaAcimaDoLimite, CotadorDePedido
# from conftest import (
#     PEDIDO_ACIMA_DO_LIMITE,
#     PEDIDO_LEVE,
#     PEDIDO_PESADO,
# )


# TODO-1: escreva aqui o seu Stub e os quatro testes descritos acima.
