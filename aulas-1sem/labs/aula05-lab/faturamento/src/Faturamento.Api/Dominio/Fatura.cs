namespace Faturamento.Api.Dominio;

/// <summary>
/// Fatura emitida para um pedido da LogiTech.
/// </summary>
/// <remarks>
/// Encapsulamento: todas as propriedades têm <c>private set</c>. Quem quiser
/// mudar o estado da fatura passa por um método de negócio, não por atribuição
/// direta. O construtor privado sem parâmetros existe apenas porque o EF Core
/// precisa dele para materializar a entidade vinda do banco.
///
/// Não é tarefa: esta classe já vem pronta.
/// </remarks>
public class Fatura
{
    public string Id { get; private set; } = string.Empty;

    public string PedidoId { get; private set; } = string.Empty;

    public string Cliente { get; private set; } = string.Empty;

    public decimal Valor { get; private set; }

    public string MeioPagamento { get; private set; } = string.Empty;

    public int PrazoDias { get; private set; }

    public string NumeroNotaFiscal { get; private set; } = string.Empty;

    public DateTimeOffset EmitidaEm { get; private set; }

    private Fatura()
    {
    }

    public Fatura(string pedidoId, string cliente, decimal valor, string meioPagamento,
                  int prazoDias, string numeroNotaFiscal)
    {
        ExigirTexto(pedidoId, nameof(pedidoId));
        ExigirTexto(cliente, nameof(cliente));
        ExigirTexto(meioPagamento, nameof(meioPagamento));
        ExigirTexto(numeroNotaFiscal, nameof(numeroNotaFiscal));
        if (valor <= 0)
        {
            throw new ArgumentException("valor precisa ser maior que zero", nameof(valor));
        }
        if (prazoDias < 0)
        {
            throw new ArgumentException("prazoDias não pode ser negativo", nameof(prazoDias));
        }

        Id = Guid.NewGuid().ToString();
        PedidoId = pedidoId;
        Cliente = cliente;
        Valor = valor;
        MeioPagamento = meioPagamento;
        PrazoDias = prazoDias;
        NumeroNotaFiscal = numeroNotaFiscal;
        EmitidaEm = DateTimeOffset.UtcNow;
    }

    /// <summary>Data de vencimento, derivada do prazo concedido ao tipo de cliente.</summary>
    public DateTimeOffset Vencimento() => EmitidaEm.AddDays(PrazoDias);

    private static void ExigirTexto(string valor, string campo)
    {
        if (string.IsNullOrWhiteSpace(valor))
        {
            throw new ArgumentException($"{campo} é obrigatório", campo);
        }
    }
}
