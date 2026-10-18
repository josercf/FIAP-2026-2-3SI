package br.com.fiap.logitech.pedidos.faturamento;

import org.springframework.stereotype.Component;

/**
 * TODO-2 (Factory Method): quem decide qual conector de faturamento usar.
 *
 * <p>Hoje essa decisão está dentro de {@code PedidoService}, numa cadeia de
 * {@code if} que cresce a cada tipo de cliente novo. Enquanto ela ficar lá, a
 * regra de negócio de pedidos sabe o nome de todas as formas de cobrança da
 * empresa, e muda toda vez que o comercial fecha um contrato diferente.</p>
 *
 * <h3>O que você faz aqui</h3>
 * <ol>
 *   <li>Receba, no construtor, a {@code List&lt;ConectorFaturamento&gt;} com todos
 *       os conectores. O Spring injeta a lista sozinho: todo conector anotado
 *       com {@code @Component} entra nela sem que ninguém precise registrá-lo
 *       à mão.</li>
 *   <li>Monte um índice de {@code tipoClienteAtendido()} para o conector
 *       correspondente.</li>
 *   <li>Implemente {@link #para(String)} devolvendo o conector do tipo pedido, e
 *       lançando {@link ConectorNaoEncontradoException} quando não existir
 *       conector para aquele tipo.</li>
 *   <li>Em {@code PedidoService}, troque a cadeia de {@code if} por uma chamada
 *       a esta fábrica.</li>
 * </ol>
 *
 * <p>Dica: {@code conectores.stream().collect(Collectors.toMap(
 * ConectorFaturamento::tipoClienteAtendido, c -&gt; c))}.</p>
 */
@Component
public class ConectorFaturamentoFactory {

    public ConectorFaturamento para(String tipoCliente) {
        // TODO-2: devolva o conector registrado para este tipo de cliente.
        throw new UnsupportedOperationException(
                "TODO-2: a fábrica de conectores ainda não foi implementada");
    }
}
