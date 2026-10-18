package br.com.fiap.logitech.pedidos.aplicacao;

/**
 * Pedido inexistente. Vira 404 no controlador. Não é tarefa.
 */
public class PedidoNaoEncontradoException extends RuntimeException {

    public PedidoNaoEncontradoException(String id) {
        super("pedido não encontrado: " + id);
    }
}
