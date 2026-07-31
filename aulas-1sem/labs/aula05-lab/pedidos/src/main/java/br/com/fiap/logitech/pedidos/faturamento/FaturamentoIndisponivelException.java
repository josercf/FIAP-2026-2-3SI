package br.com.fiap.logitech.pedidos.faturamento;

/**
 * O serviço de Faturamento não respondeu.
 *
 * <p>Não é motivo para perder o pedido: quem trata esta exceção grava o pedido
 * como {@code AGUARDANDO_FATURAMENTO}. Não é tarefa.</p>
 */
public class FaturamentoIndisponivelException extends RuntimeException {

    public FaturamentoIndisponivelException(String mensagem, Throwable causa) {
        super(mensagem, causa);
    }

    public FaturamentoIndisponivelException(String mensagem) {
        super(mensagem);
    }
}
