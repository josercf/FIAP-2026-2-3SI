package br.com.fiap.logitech.pedidos.faturamento;

import br.com.fiap.logitech.pedidos.dominio.Pedido;
import br.com.fiap.logitech.pedidos.dominio.SolicitacaoFatura;

/**
 * Contrato de um conector de faturamento: cada tipo de cliente da LogiTech é
 * cobrado de um jeito, e cada jeito é uma implementação desta interface.
 *
 * <p>Esta é a abstração que o Factory Method (TODO-2) devolve e que o
 * princípio Aberto/Fechado (TODO-3) usa: acrescentar um tipo de cliente novo
 * vira acrescentar uma classe nova, não editar um {@code if} existente.</p>
 *
 * <p>Não é tarefa: a interface já vem pronta.</p>
 */
public interface ConectorFaturamento {

    /**
     * Tipo de cliente que este conector atende: PADRAO, OURO, CONTRATO, ...
     * É por este valor que a fábrica escolhe o conector.
     */
    String tipoClienteAtendido();

    /** Monta a solicitação de fatura com as condições comerciais deste tipo de cliente. */
    SolicitacaoFatura montar(Pedido pedido);
}
