using Faturamento.Api.Infraestrutura;
using Xunit;

namespace Faturamento.Tests;

/// <summary>
/// A mesma variável de ambiente serve dois serviços em linguagens diferentes.
/// Já vem verde e continua verde depois dos seus TODOs.
/// </summary>
public class ConexaoPostgresTests
{
    [Fact]
    public void TraduzUrlJdbcParaCadeiaDoNpgsql()
    {
        string cadeia = ConexaoPostgres.Traduzir(
            "jdbc:postgresql://postgres:5432/logitech", "logitech", "segredo");

        Assert.Contains("Host=postgres", cadeia);
        Assert.Contains("Port=5432", cadeia);
        Assert.Contains("Database=logitech", cadeia);
        Assert.Contains("Username=logitech", cadeia);
    }

    [Fact]
    public void RepassaCadeiaQueJaVeioNoFormatoDoNpgsql()
    {
        const string original = "Host=localhost;Port=5432;Database=logitech;Username=logitech;Password=x";

        Assert.Equal(original, ConexaoPostgres.Traduzir(original, "ignorado", "ignorado"));
    }

    [Fact]
    public void RecusaUrlVazia()
    {
        Assert.Throws<ArgumentException>(() => ConexaoPostgres.Traduzir("", "logitech", "segredo"));
    }
}
