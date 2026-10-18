"""TODO-2: o Mock. Asserção sobre a chamada, não sobre o resultado.

ESTE ARQUIVO É SEU. Escreva aqui.

A diferença que a aula inteira gira em torno:

- o **Stub** do `TODO-1` responde e você confere o **número que saiu**;
- o **Mock** responde e você confere **que a chamada aconteceu**, quantas
  vezes e com quais argumentos.

Existem regras no `CotadorDePedido` que nenhuma asserção sobre o número
consegue provar. Duas delas, e são exatamente estas que você vai cobrar:

- **a memória de pedido**: o cotador busca o pedido uma única vez por
  instância. Cotar o mesmo pedido em três modalidades tem que produzir
  **uma** chamada ao serviço de Pedidos, não três. Se alguém remover essa
  memória amanhã, os valores continuam idênticos e a conta de rede triplica
  em produção;
- **o fail fast**: identificador fora do formato `PED-0000` levanta
  `PedidoInvalido` **sem chamar o serviço vizinho**. Se alguém inverter a
  ordem das duas primeiras linhas do método, o erro continua o mesmo e a
  LogiTech passa a bater no serviço de Pedidos para toda digitação errada de
  cliente.

O `unittest.mock` é biblioteca padrão, não precisa instalar nada:

    from unittest.mock import Mock
    from app.cliente_pedidos import ClientePedidos

    cliente = Mock(spec=ClientePedidos)
    cliente.buscar.return_value = PEDIDO_LEVE
    ...
    cliente.buscar.assert_called_once_with("PED-1001")

Use `spec=ClientePedidos`. Sem ele, o `Mock` aceita qualquer método que você
digitar, inclusive um que não existe, e o teste passa contra uma interface
que ninguém implementa. Com ele, `cliente.busca_r(...)` estoura na hora.

Escreva **no mínimo três** testes:

1. três cotações do mesmo pedido, uma por modalidade, produzem exatamente
   **uma** chamada a `buscar`, com o identificador correto;
2. identificador inválido levanta `PedidoInvalido` e `buscar` **não** é
   chamado (`assert_not_called`);
3. o identificador chega ao cliente **normalizado em maiúsculas**: cotar
   `"ped-1001"` chama `buscar("PED-1001")`.

Como o verificador avalia este arquivo (`--criterio 2`): ele estraga uma
cópia do código de produção de dois jeitos que **não mudam nenhum número
devolvido**, só a colaboração, e exige que os seus testes reprovem nos dois.
Um teste escrito só com asserções de valor passa nas duas cópias estragadas
e reprova o critério. É essa a prova de que Mock e Stub não são sinônimos.
"""

# Sugestão de importações. Apague o que não usar.
# import pytest
#
# from unittest.mock import Mock
#
# from app.cliente_pedidos import ClientePedidos
# from app.cotador import CotadorDePedido, PedidoInvalido
# from conftest import PEDIDO_LEVE


# TODO-2: escreva aqui os três testes de interação descritos acima.
