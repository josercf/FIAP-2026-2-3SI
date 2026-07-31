using System.Collections.Concurrent;
using System.Text.RegularExpressions;
using Faturamento.Api.Aplicacao;
using Faturamento.Api.Dominio;
using Faturamento.Api.Infraestrutura;
using Xunit;

namespace Faturamento.Tests;

/// <summary>
/// Testes de unidade da regra de faturamento: sem PostgreSQL, sem servidor web.
/// Já vêm verdes e precisam continuar verdes depois dos TODOs 4, 5 e 6.
/// </summary>
public class FaturaServiceTests
{
    /// <summary>
    /// Dublê de teste do repositório.
    /// </summary>
    /// <remarks>
    /// <para><strong>TODO-4:</strong> repare no preço do acoplamento. Como
    /// <c>FaturaService</c> depende da classe concreta, este dublê é obrigado a
    /// <em>herdar</em> do repositório do EF Core e a chamar <c>base(null!)</c>
    /// passando um <c>DbContext</c> nulo que ninguém usa.</para>
    ///
    /// <para>Depois de criar <c>IFaturaRepository</c>, troque
    /// <c>: EfFaturaRepository</c> por <c>: IFaturaRepository</c>, apague o
    /// construtor com <c>base(null!)</c>, tire os <c>override</c> e apague o
    /// <c>using</c> de <c>Infraestrutura</c>. Os testes continuam passando, e
    /// agora eles não sabem mais que existe um ORM no projeto.</para>
    ///
    /// <para>O dicionário é concorrente de propósito: o defeito que o TODO-6 vai
    /// expor está no numerador de notas, e não no armazenamento do dublê.</para>
    /// </remarks>
    private class FaturaRepositorioEmMemoria : EfFaturaRepository
    {
        private readonly ConcurrentDictionary<string, Fatura> _dados = new();

        public FaturaRepositorioEmMemoria() : base(null!)
        {
        }

        public override Fatura Salvar(Fatura fatura)
        {
            _dados[fatura.PedidoId] = fatura;
            return fatura;
        }

        public override Fatura? PorPedido(string pedidoId)
        {
            return _dados.TryGetValue(pedidoId, out Fatura? fatura) ? fatura : null;
        }

        public override IReadOnlyList<Fatura> Todas()
        {
            return _dados.Values.OrderBy(f => f.EmitidaEm).ToList();
        }
    }

    private static SolicitacaoFatura Solicitacao(string pedidoId = "pedido-1",
                                                 string meio = "BOLETO",
                                                 int prazo = 3)
    {
        return new SolicitacaoFatura(pedidoId, "Distribuidora Sul", 1000.00m, meio, prazo);
    }

    private static FaturaService ServicoNovo()
    {
        NumeradorNotaFiscal.Instancia.ReiniciarParaTeste();
        // TODO-4: quando a interface existir, a linha abaixo continua igual;
        // o que muda é o tipo que FaturaService declara receber.
        return new FaturaService(new FaturaRepositorioEmMemoria());
    }

    [Fact]
    public void EmitirGeraNotaFiscalNoFormatoDoContrato()
    {
        FaturaService servico = ServicoNovo();

        Fatura fatura = servico.Emitir(Solicitacao());

        Assert.Matches(new Regex(@"^NF-\d{6}$"), fatura.NumeroNotaFiscal);
        Assert.Equal("pedido-1", fatura.PedidoId);
        Assert.Equal(1000.00m, fatura.Valor);
    }

    [Fact]
    public void EmitirDuasVezesParaOMesmoPedidoNaoGeraDuasNotas()
    {
        FaturaService servico = ServicoNovo();

        Fatura primeira = servico.Emitir(Solicitacao());
        Fatura segunda = servico.Emitir(Solicitacao());

        Assert.Equal(primeira.NumeroNotaFiscal, segunda.NumeroNotaFiscal);
        Assert.Single(servico.Todas());
    }

    [Fact]
    public void PrazoDoClienteViraVencimentoDaFatura()
    {
        FaturaService servico = ServicoNovo();

        Fatura fatura = servico.Emitir(Solicitacao(prazo: 30, meio: "FATURA_MENSAL"));

        Assert.Equal("FATURA_MENSAL", fatura.MeioPagamento);
        Assert.Equal(fatura.EmitidaEm.AddDays(30), fatura.Vencimento());
    }

    [Fact]
    public void ValorNaoPositivoEhRecusadoPeloDominio()
    {
        FaturaService servico = ServicoNovo();

        Assert.Throws<ArgumentException>(() =>
            servico.Emitir(new SolicitacaoFatura("pedido-2", "Distribuidora Sul", 0m, "BOLETO", 3)));
    }
}
