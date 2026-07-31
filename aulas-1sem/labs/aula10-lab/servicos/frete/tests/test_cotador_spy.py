"""TODO-3: o Spy. O colaborador real continua respondendo, e você observa.

ESTE ARQUIVO É SEU. Escreva aqui.

Stub e Mock substituem o colaborador. O **Spy** faz outra coisa: ele
**envolve o objeto real**, deixa a chamada acontecer de verdade e guarda o
registro de quem chamou o quê.

Serve quando o comportamento real importa e a colaboração também. É o caso
da `TabelaDistancias`: você quer a distância verdadeira no cálculo, e quer
provar que o cotador consultou a tabela com origem e destino **na ordem
certa**.

E aqui está a armadilha que faz este teste valer a noite: a tabela é
**simétrica**. `km("SAO", "LDB")` e `km("LDB", "SAO")` devolvem 500,0. Um
cotador que trocasse os dois argumentos devolveria o valor certo, o prazo
certo e o desconto certo. Nenhum teste de resultado pegaria. Só o Spy pega.

No `unittest.mock`, Spy é `Mock(wraps=objeto_real)`:

    from unittest.mock import Mock
    from app.distancias import TabelaDistancias

    tabela_real = TabelaDistancias()
    espia = Mock(wraps=tabela_real)
    cotador = CotadorDePedido(cliente_stub, tabela=espia)

`espia.km(...)` delega para `tabela_real.km(...)`, devolve o número
verdadeiro e ainda assim registra a chamada em `espia.km.call_args`.

Escreva **no mínimo três** testes:

1. a tabela é consultada exatamente uma vez por cotação, com
   `("SAO", "LDB")` **nessa ordem** para o `PEDIDO_LEVE`;
2. o valor devolvido pelo cotador é o mesmo que sairia com a tabela real,
   ou seja, o espião não alterou o comportamento (é isso que separa Spy de
   Stub);
3. rota fora da tabela cai na distância padrão de 750 km, e a tabela é
   consultada assim mesmo. Monte um `PedidoResumo` com um par que não está
   em `DISTANCIAS_KM`, por exemplo `("VIX", "CWB")`.

Como o verificador avalia este arquivo (`--criterio 3`): ele estraga uma
cópia do código de produção trocando a ordem dos argumentos na consulta à
tabela. Como a tabela é simétrica, **todos os números continuam iguais**.
Se os seus testes não reprovarem, é porque nenhum deles olhou para a
chamada.
"""

# Sugestão de importações. Apague o que não usar.
# from unittest.mock import Mock, call
#
# from app.cliente_pedidos import PedidoResumo
# from app.cotador import CotadorDePedido
# from app.distancias import DISTANCIA_PADRAO_KM, TabelaDistancias
# from conftest import PEDIDO_LEVE


# TODO-3: escreva aqui os três testes com Spy descritos acima.
