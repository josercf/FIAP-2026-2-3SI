namespace Faturamento.Api.Infraestrutura;

/// <summary>
/// Traduz a variável de ambiente <c>LOGITECH_DB_URL</c> para uma cadeia de
/// conexão do Npgsql.
/// </summary>
/// <remarks>
/// O contrato da plataforma (ADR-006) manda os dois serviços lerem a mesma
/// variável. Só que o formato que o mundo Java usa
/// (<c>jdbc:postgresql://host:5432/logitech</c>) não é o que o Npgsql espera
/// (<c>Host=...;Port=...;Database=...</c>). Em vez de inventar uma segunda
/// variável, o serviço traduz. É um detalhe pequeno e é o tipo de coisa que
/// aparece em toda plataforma poliglota de verdade.
///
/// Não é tarefa.
/// </remarks>
public static class ConexaoPostgres
{
    public static string Traduzir(string url, string usuario, string senha)
    {
        if (string.IsNullOrWhiteSpace(url))
        {
            throw new ArgumentException("LOGITECH_DB_URL não pode ser vazia", nameof(url));
        }

        // Já veio no formato do Npgsql: repassa sem mexer.
        if (url.Contains("Host=", StringComparison.OrdinalIgnoreCase))
        {
            return url;
        }

        string semJdbc = url.StartsWith("jdbc:", StringComparison.OrdinalIgnoreCase)
            ? url.Substring("jdbc:".Length)
            : url;

        var uri = new Uri(semJdbc);
        int porta = uri.Port > 0 ? uri.Port : 5432;
        string banco = uri.AbsolutePath.Trim('/');

        return $"Host={uri.Host};Port={porta};Database={banco};" +
               $"Username={usuario};Password={senha}";
    }
}
