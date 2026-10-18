package br.com.fiap.logitech.pedidos.faturamento;

import br.com.fiap.logitech.pedidos.dominio.SolicitacaoFatura;

/**
 * Porta de saída para o serviço de Faturamento (C#, porta 5080).
 *
 * <p>Repare que esta abstração <strong>já existe</strong> no esqueleto: é o
 * contraste proposital com o repositório do TODO-1, que ainda está acoplado à
 * classe concreta. Como {@code PedidoService} depende desta interface, o teste
 * de unidade troca a chamada HTTP por um dublê em uma linha, sem subir serviço
 * nenhum. Compare com o trabalho que dá testar a parte que ainda não foi
 * invertida.</p>
 *
 * <p>Não é tarefa.</p>
 */
public interface ClienteFaturamento {

    /**
     * Envia a solicitação ao serviço de Faturamento e devolve o número da nota
     * fiscal emitida.
     *
     * @throws FaturamentoIndisponivelException quando o serviço não responde
     */
    String emitir(SolicitacaoFatura solicitacao);
}
