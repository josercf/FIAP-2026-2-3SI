package br.com.fiap.logitech.pedidos.dominio;

import java.math.BigDecimal;

/**
 * O que o contexto de Pedidos pede ao contexto de Faturamento.
 *
 * <p>Repare no que este record NÃO tem: nada de tabela, nada de conexão, nada
 * de HTTP. É só o dado que atravessa a fronteira entre dois Bounded Contexts.
 * Quem sabe transformar isso em uma chamada de rede é a infraestrutura.</p>
 *
 * @param pedidoId       identificador do pedido que originou a cobrança
 * @param cliente        nome do cliente, para aparecer na nota
 * @param valor          valor a cobrar
 * @param meioPagamento  BOLETO, CARTAO_CORPORATIVO, FATURA_MENSAL, ...
 * @param prazoDias      prazo de pagamento concedido, em dias
 */
public record SolicitacaoFatura(String pedidoId, String cliente, BigDecimal valor,
                                String meioPagamento, int prazoDias) {
}
