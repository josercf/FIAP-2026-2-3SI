package br.com.fiap.logitech.pedidos.faturamento;

import br.com.fiap.logitech.pedidos.dominio.Pedido;
import br.com.fiap.logitech.pedidos.dominio.SolicitacaoFatura;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Cliente OURO da LogiTech: cartão corporativo, 5% de desconto negociado em
 * contrato e pagamento à vista.
 *
 * <p>Não é tarefa: já vem pronto.</p>
 */
@Component
public class ConectorCartaoCorporativo implements ConectorFaturamento {

    public static final String TIPO_CLIENTE = "OURO";

    private static final BigDecimal DESCONTO = new BigDecimal("0.95");

    @Override
    public String tipoClienteAtendido() {
        return TIPO_CLIENTE;
    }

    @Override
    public SolicitacaoFatura montar(Pedido pedido) {
        BigDecimal comDesconto = pedido.getValor()
                .multiply(DESCONTO)
                .setScale(2, RoundingMode.HALF_UP);
        return new SolicitacaoFatura(
                pedido.getId(),
                pedido.getCliente(),
                comDesconto,
                "CARTAO_CORPORATIVO",
                0);
    }
}
