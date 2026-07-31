package br.com.fiap.logitech.pedidos.dominio;

import java.math.BigDecimal;

/**
 * Dados de entrada para abrir um pedido. Não é tarefa.
 */
public record NovoPedido(String cliente, String tipoCliente, String origem, String destino,
                         String enderecoEntrega, BigDecimal pesoKg, BigDecimal valor) {
}
