using Faturamento.Api.Dominio;
using Microsoft.EntityFrameworkCore;

namespace Faturamento.Api.Infraestrutura;

/// <summary>
/// Persistência de faturas em PostgreSQL, via EF Core.
/// </summary>
/// <remarks>
/// <para><strong>TODO-4 (Repository e injeção por construtor):</strong> hoje
/// <c>FaturaService</c> depende deste tipo concreto, ou seja, a regra de
/// negócio do faturamento conhece o EF Core. Crie a interface
/// <c>IFaturaRepository</c> em <c>Dominio/</c>, faça esta classe implementá-la
/// e mude <c>FaturaService</c> para receber a interface no construtor. Registre
/// a implementação no contêiner de injeção de dependência, em
/// <c>Program.cs</c>, com
/// <c>builder.Services.AddScoped&lt;IFaturaRepository, EfFaturaRepository&gt;()</c>.</para>
///
/// <para>Os métodos são <c>virtual</c> de propósito: é o que permite, hoje, o
/// dublê de teste herdar desta classe. Depois do TODO-4 esse truque some, e é
/// justamente esse o ponto.</para>
/// </remarks>
public class EfFaturaRepository
{
    private readonly FaturamentoDbContext _banco;

    public EfFaturaRepository(FaturamentoDbContext banco)
    {
        _banco = banco;
    }

    public virtual Fatura Salvar(Fatura fatura)
    {
        _banco.Faturas.Add(fatura);
        _banco.SaveChanges();
        return fatura;
    }

    public virtual Fatura? PorPedido(string pedidoId)
    {
        return _banco.Faturas.AsNoTracking().FirstOrDefault(f => f.PedidoId == pedidoId);
    }

    public virtual IReadOnlyList<Fatura> Todas()
    {
        return _banco.Faturas.AsNoTracking().OrderBy(f => f.EmitidaEm).ToList();
    }
}
