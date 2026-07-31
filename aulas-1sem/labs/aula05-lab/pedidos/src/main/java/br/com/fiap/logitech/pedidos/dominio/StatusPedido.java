package br.com.fiap.logitech.pedidos.dominio;

/**
 * Estados possíveis de um pedido da LogiTech, na ordem em que acontecem.
 *
 * <p>{@code AGUARDANDO_FATURAMENTO} existe porque o serviço de Faturamento é
 * outro processo, em outra linguagem, que pode estar fora do ar: o pedido é
 * gravado mesmo assim e a fatura fica pendente. Perder o pedido porque o
 * faturamento caiu seria acoplar a disponibilidade de um contexto à do
 * outro.</p>
 */
public enum StatusPedido {
    CRIADO,
    AGUARDANDO_FATURAMENTO,
    FATURADO,
    EM_TRANSITO,
    ENTREGUE
}
