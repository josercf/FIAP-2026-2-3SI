package br.com.fiap.logitech.pedidos.faturamento;

import br.com.fiap.logitech.pedidos.dominio.Pedido;
import br.com.fiap.logitech.pedidos.dominio.SolicitacaoFatura;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Cada conector traduz as condições comerciais de um tipo de cliente.
 *
 * <p>Já vem verde. No TODO-3 você acrescenta aqui o teste do conector do tipo
 * CONTRATO, no mesmo formato dos dois que já existem.</p>
 */
class ConectorFaturamentoTest {

    private Pedido pedidoDe(String tipoCliente) {
        return new Pedido("Distribuidora Sul", tipoCliente, "São Paulo/SP", "Curitiba/PR",
                "Rua das Araucárias, 480", new BigDecimal("120.0"), new BigDecimal("1000.00"));
    }

    @Test
    @DisplayName("cliente PADRAO é cobrado por boleto, sem desconto, em 3 dias")
    void clientePadraoPagaBoleto() {
        SolicitacaoFatura solicitacao = new ConectorBoleto().montar(pedidoDe("PADRAO"));

        assertEquals("BOLETO", solicitacao.meioPagamento());
        assertEquals(0, new BigDecimal("1000.00").compareTo(solicitacao.valor()));
        assertEquals(3, solicitacao.prazoDias());
    }

    @Test
    @DisplayName("cliente OURO paga no cartão corporativo com 5% de desconto, à vista")
    void clienteOuroPagaCartaoComDesconto() {
        SolicitacaoFatura solicitacao = new ConectorCartaoCorporativo().montar(pedidoDe("OURO"));

        assertEquals("CARTAO_CORPORATIVO", solicitacao.meioPagamento());
        assertEquals(0, new BigDecimal("950.00").compareTo(solicitacao.valor()));
        assertEquals(0, solicitacao.prazoDias());
    }

    // TODO-3: acrescente aqui o teste do conector do cliente CONTRATO.
    // Meio de pagamento FATURA_MENSAL, valor cheio, prazo de 30 dias.
}
