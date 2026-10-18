package br.com.fiap.logitech.pedidos.faturamento;

import br.com.fiap.logitech.pedidos.dominio.Pedido;
import br.com.fiap.logitech.pedidos.dominio.SolicitacaoFatura;
import org.springframework.stereotype.Component;

/**
 * Cliente PADRAO da LogiTech: cobrança por boleto, sem desconto, 3 dias de prazo.
 *
 * <p>Não é tarefa: já vem pronto, e serve de modelo para o conector que você
 * vai escrever no TODO-3.</p>
 */
@Component
public class ConectorBoleto implements ConectorFaturamento {

    public static final String TIPO_CLIENTE = "PADRAO";

    @Override
    public String tipoClienteAtendido() {
        return TIPO_CLIENTE;
    }

    @Override
    public SolicitacaoFatura montar(Pedido pedido) {
        return new SolicitacaoFatura(
                pedido.getId(),
                pedido.getCliente(),
                pedido.getValor(),
                "BOLETO",
                3);
    }
}
