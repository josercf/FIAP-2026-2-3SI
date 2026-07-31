package br.com.fiap.logitech.pedidos.dominio;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

/**
 * Base da pirâmide de testes: o domínio, sem Spring, sem banco, sem rede.
 *
 * <p>Esta classe já vem verde e precisa continuar verde depois dos seus três
 * TODOs. Se um teste daqui quebrar, a refatoração mudou comportamento, e
 * refatoração que muda comportamento não é refatoração.</p>
 */
class PedidoTest {

    private Pedido pedidoValido() {
        return new Pedido("Distribuidora Sul", "PADRAO", "São Paulo/SP", "Curitiba/PR",
                "Rua das Araucárias, 480", new BigDecimal("120.0"), new BigDecimal("890.00"));
    }

    @Test
    @DisplayName("pedido novo nasce com id gerado e status CRIADO")
    void pedidoNovoNasceCriado() {
        Pedido pedido = pedidoValido();

        assertNotNull(pedido.getId());
        assertEquals(36, pedido.getId().length());
        assertEquals(StatusPedido.CRIADO, pedido.getStatus());
        assertEquals("Distribuidora Sul", pedido.getCliente());
    }

    @Test
    @DisplayName("valor e peso precisam ser positivos")
    void recusaValorEPesoInvalidos() {
        assertThrows(IllegalArgumentException.class, () ->
                new Pedido("Distribuidora Sul", "PADRAO", "São Paulo/SP", "Curitiba/PR",
                        "Rua das Araucárias, 480", new BigDecimal("120.0"), BigDecimal.ZERO));

        assertThrows(IllegalArgumentException.class, () ->
                new Pedido("Distribuidora Sul", "PADRAO", "São Paulo/SP", "Curitiba/PR",
                        "Rua das Araucárias, 480", new BigDecimal("-1"), new BigDecimal("890.00")));
    }

    @Test
    @DisplayName("faturar guarda o número da nota e muda o status")
    void faturarMudaStatus() {
        Pedido pedido = pedidoValido();

        pedido.faturar("NF-000042");

        assertEquals(StatusPedido.FATURADO, pedido.getStatus());
        assertEquals("NF-000042", pedido.getNumeroNotaFiscal());
    }

    @Test
    @DisplayName("endereço de entrega muda enquanto o pedido não foi entregue")
    void alteraEndereco() {
        Pedido pedido = pedidoValido();

        pedido.alterarEndereco("Avenida das Torres, 1200");

        assertEquals("Avenida das Torres, 1200", pedido.getEnderecoEntrega());
    }

    @Test
    @DisplayName("endereço vazio é recusado pelo próprio domínio")
    void recusaEnderecoVazio() {
        Pedido pedido = pedidoValido();

        assertThrows(IllegalArgumentException.class, () -> pedido.alterarEndereco("   "));
    }
}
