using Faturamento.Api.Dominio;
using Faturamento.Api.Infraestrutura;

namespace Faturamento.Api.Aplicacao;

/// <summary>
/// Regra de negócio do Bounded Context de Faturamento.
/// </summary>
/// <remarks>
/// <para><strong>TODO-4:</strong> o campo abaixo é do tipo concreto
/// <c>EfFaturaRepository</c>. Regra de negócio dependendo de infraestrutura,
/// o mesmo defeito que o serviço de Pedidos tem em Java, agora em C#: a
/// violação do DIP não é característica de linguagem, é de projeto. Troque
/// pela interface <c>IFaturaRepository</c>.</para>
///
/// <para>Emitir fatura é idempotente por pedido: o serviço de Pedidos pode
/// repetir a chamada depois de um timeout, e repetir não pode gerar duas
/// notas fiscais para o mesmo pedido.</para>
/// </remarks>
public class FaturaService
{
    // TODO-4: tipo concreto. Deveria ser a abstração IFaturaRepository.
    private readonly EfFaturaRepository _repositorio;

    public FaturaService(EfFaturaRepository repositorio)
    {
        _repositorio = repositorio;
    }

    public Fatura Emitir(SolicitacaoFatura solicitacao)
    {
        Fatura? jaEmitida = _repositorio.PorPedido(solicitacao.PedidoId);
        if (jaEmitida is not null)
        {
            return jaEmitida;
        }

        // O número da nota vem do Singleton compartilhado por todas as
        // requisições. É o ponto onde a concorrência aparece (TODO-5).
        string numero = NumeradorNotaFiscal.Instancia.Proximo();

        var fatura = new Fatura(
            solicitacao.PedidoId,
            solicitacao.Cliente,
            solicitacao.Valor,
            solicitacao.MeioPagamento,
            solicitacao.PrazoDias,
            numero);

        return _repositorio.Salvar(fatura);
    }

    public Fatura? PorPedido(string pedidoId) => _repositorio.PorPedido(pedidoId);

    public IReadOnlyList<Fatura> Todas() => _repositorio.Todas();
}
