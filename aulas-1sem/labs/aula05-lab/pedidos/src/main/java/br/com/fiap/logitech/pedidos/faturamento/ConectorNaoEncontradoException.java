package br.com.fiap.logitech.pedidos.faturamento;

/**
 * Não existe conector de faturamento para o tipo de cliente informado.
 *
 * <p>Erro de entrada, não falha de sistema: o controlador devolve 400 e diz
 * qual tipo de cliente não é atendido. Não é tarefa.</p>
 */
public class ConectorNaoEncontradoException extends RuntimeException {

    public ConectorNaoEncontradoException(String tipoCliente) {
        super("não existe conector de faturamento para o tipo de cliente '" + tipoCliente + "'");
    }
}
