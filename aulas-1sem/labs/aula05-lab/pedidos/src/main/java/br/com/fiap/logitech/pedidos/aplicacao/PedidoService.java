package br.com.fiap.logitech.pedidos.aplicacao;

import br.com.fiap.logitech.pedidos.dominio.NovoPedido;
import br.com.fiap.logitech.pedidos.dominio.Pedido;
import br.com.fiap.logitech.pedidos.dominio.SolicitacaoFatura;
import br.com.fiap.logitech.pedidos.faturamento.ClienteFaturamento;
import br.com.fiap.logitech.pedidos.faturamento.ConectorBoleto;
import br.com.fiap.logitech.pedidos.faturamento.ConectorCartaoCorporativo;
import br.com.fiap.logitech.pedidos.faturamento.ConectorFaturamento;
import br.com.fiap.logitech.pedidos.faturamento.ConectorNaoEncontradoException;
import br.com.fiap.logitech.pedidos.faturamento.FaturamentoIndisponivelException;
import br.com.fiap.logitech.pedidos.infra.JpaPedidoRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * Regra de negócio do contexto de Pedidos.
 *
 * <p>Esta classe funciona. Ela também é o exemplo do que esta aula inteira
 * trata de consertar: uma regra de negócio que conhece o ORM que a persiste e
 * a lista de todas as formas de cobrança da empresa. Duas lacunas de projeto,
 * três TODOs.</p>
 *
 * <ul>
 *   <li><strong>TODO-1 (DIP):</strong> o campo {@code repositorio} é do tipo
 *       concreto {@code JpaPedidoRepository}. Regra de negócio dependendo de
 *       infraestrutura: trocar de banco, de ORM ou testar sem banco custa
 *       mexer aqui. Crie a interface {@code PedidoRepository} no pacote
 *       {@code dominio}, faça {@code JpaPedidoRepository} implementá-la e
 *       passe a depender da interface. O import de {@code infra} tem que
 *       sumir deste arquivo.</li>
 *   <li><strong>TODO-2 (Factory Method):</strong> {@link #escolherConector}
 *       é uma cadeia de {@code if} que cresce a cada contrato novo. Mova a
 *       decisão para {@code ConectorFaturamentoFactory} e apague este método
 *       privado.</li>
 *   <li><strong>TODO-3 (OCP):</strong> depois do TODO-2, acrescente o tipo de
 *       cliente CONTRATO <strong>sem tocar em nenhuma linha desta classe</strong>.
 *       Se você precisou editar este arquivo para o tipo novo funcionar, o
 *       Aberto/Fechado não foi alcançado.</li>
 * </ul>
 */
@Service
public class PedidoService {

    private static final Logger log = LoggerFactory.getLogger(PedidoService.class);

    // TODO-1: tipo concreto. Deveria ser a abstração PedidoRepository.
    private final JpaPedidoRepository repositorio;
    private final ClienteFaturamento clienteFaturamento;

    // TODO-1 e TODO-2: o construtor recebe a implementação concreta do
    // repositório e não recebe a fábrica de conectores. Os dois mudam.
    public PedidoService(JpaPedidoRepository repositorio, ClienteFaturamento clienteFaturamento) {
        this.repositorio = repositorio;
        this.clienteFaturamento = clienteFaturamento;
    }

    /**
     * Abre um pedido e tenta emitir a fatura correspondente.
     *
     * <p>Se o serviço de Faturamento estiver fora do ar, o pedido é gravado
     * assim mesmo, com status {@code AGUARDANDO_FATURAMENTO}: a
     * indisponibilidade de um Bounded Context não pode derrubar o outro.</p>
     */
    @Transactional
    public Pedido criar(NovoPedido novo) {
        Pedido pedido = new Pedido(novo.cliente(), novo.tipoCliente(), novo.origem(),
                novo.destino(), novo.enderecoEntrega(), novo.pesoKg(), novo.valor());

        ConectorFaturamento conector = escolherConector(pedido.getTipoCliente());
        SolicitacaoFatura solicitacao = conector.montar(pedido);

        try {
            String numeroNotaFiscal = clienteFaturamento.emitir(solicitacao);
            pedido.faturar(numeroNotaFiscal);
        } catch (FaturamentoIndisponivelException erro) {
            log.warn("faturamento indisponível para o pedido {}: {}", pedido.getId(), erro.getMessage());
            pedido.aguardarFaturamento();
        }

        return repositorio.salvar(pedido);
    }

    // TODO-2 e TODO-3: este método privado é o problema. Cada contrato novo do
    // comercial vira mais um "else if" aqui dentro, num arquivo que não deveria
    // ter motivo nenhum para mudar por causa disso.
    private ConectorFaturamento escolherConector(String tipoCliente) {
        if (ConectorBoleto.TIPO_CLIENTE.equals(tipoCliente)) {
            return new ConectorBoleto();
        }
        if (ConectorCartaoCorporativo.TIPO_CLIENTE.equals(tipoCliente)) {
            return new ConectorCartaoCorporativo();
        }
        throw new ConectorNaoEncontradoException(tipoCliente);
    }

    @Transactional(readOnly = true)
    public List<Pedido> listar() {
        return repositorio.todos();
    }

    @Transactional(readOnly = true)
    public Pedido porId(String id) {
        return repositorio.porId(id).orElseThrow(() -> new PedidoNaoEncontradoException(id));
    }

    /** Rota consumida pelo agente de IA da Aula 08. */
    @Transactional
    public Pedido alterarEndereco(String id, String novoEndereco) {
        Pedido pedido = porId(id);
        pedido.alterarEndereco(novoEndereco);
        return repositorio.salvar(pedido);
    }
}
