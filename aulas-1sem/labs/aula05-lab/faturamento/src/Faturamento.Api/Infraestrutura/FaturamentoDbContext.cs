using Faturamento.Api.Dominio;
using Microsoft.EntityFrameworkCore;

namespace Faturamento.Api.Infraestrutura;

/// <summary>
/// Contexto do EF Core do Bounded Context de Faturamento.
/// </summary>
/// <remarks>
/// Um schema por Bounded Context, conforme o contrato da plataforma: este
/// serviço só enxerga o schema <c>faturamento</c> e nunca lê a tabela de
/// pedidos. Quem precisa de dado alheio chama a API do outro serviço.
///
/// Não é tarefa.
/// </remarks>
public class FaturamentoDbContext : DbContext
{
    public FaturamentoDbContext(DbContextOptions<FaturamentoDbContext> opcoes) : base(opcoes)
    {
    }

    public DbSet<Fatura> Faturas => Set<Fatura>();

    protected override void OnModelCreating(ModelBuilder modelo)
    {
        modelo.HasDefaultSchema("faturamento");

        modelo.Entity<Fatura>(fatura =>
        {
            fatura.ToTable("faturas");
            fatura.HasKey(f => f.Id);
            fatura.Property(f => f.Id).HasMaxLength(36);
            fatura.Property(f => f.PedidoId).HasMaxLength(36).IsRequired();
            fatura.Property(f => f.Cliente).HasMaxLength(120).IsRequired();
            fatura.Property(f => f.MeioPagamento).HasMaxLength(40).IsRequired();
            fatura.Property(f => f.NumeroNotaFiscal).HasMaxLength(30).IsRequired();
            fatura.Property(f => f.Valor).HasPrecision(12, 2);
            fatura.HasIndex(f => f.PedidoId).IsUnique();
            fatura.HasIndex(f => f.NumeroNotaFiscal).IsUnique();
        });
    }
}
