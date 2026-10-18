using Faturamento.Api.Aplicacao;
using Faturamento.Api.Dominio;
using Faturamento.Api.Infraestrutura;
using Microsoft.EntityFrameworkCore;

// Serviço de Faturamento da LogiTech Enterprise.
// C# / .NET 8, porta 5080, rotas conforme o contrato da plataforma (ADR-006).
// Não é tarefa: este arquivo só muda em uma linha, no TODO-4, para registrar a
// interface do repositório no contêiner de injeção de dependência.

var builder = WebApplication.CreateBuilder(args);

string porta = Environment.GetEnvironmentVariable("LOGITECH_FATURAMENTO_PORT") ?? "5080";
builder.WebHost.UseUrls($"http://0.0.0.0:{porta}");

string urlBanco = Environment.GetEnvironmentVariable("LOGITECH_DB_URL")
                  ?? "jdbc:postgresql://localhost:5432/logitech";
string usuario = Environment.GetEnvironmentVariable("LOGITECH_DB_USER") ?? "logitech";
string senha = Environment.GetEnvironmentVariable("LOGITECH_DB_PASSWORD") ?? "logitech";

builder.Services.AddDbContext<FaturamentoDbContext>(opcoes =>
    opcoes.UseNpgsql(ConexaoPostgres.Traduzir(urlBanco, usuario, senha)));

// TODO-4: quando IFaturaRepository existir, registre a implementação aqui:
//   builder.Services.AddScoped<IFaturaRepository, EfFaturaRepository>();
builder.Services.AddScoped<EfFaturaRepository>();
builder.Services.AddScoped<FaturaService>();

var app = builder.Build();

PrepararBanco(app);

// Contrato da plataforma: todo serviço responde 200 e {"status":"ok"} em /health.
// É onde o healthcheck do Docker Compose da Aula 07 vai bater.
app.MapGet("/health", () => Results.Ok(new { status = "ok", servico = "faturamento" }));

app.MapPost("/api/v1/faturas", (SolicitacaoFatura solicitacao, FaturaService servico) =>
{
    try
    {
        Fatura fatura = servico.Emitir(solicitacao);
        return Results.Created($"/api/v1/faturas/{fatura.PedidoId}", FaturaResposta.De(fatura));
    }
    catch (ArgumentException erro)
    {
        return Results.BadRequest(new { erro = erro.Message });
    }
});

app.MapGet("/api/v1/faturas/{pedidoId}", (string pedidoId, FaturaService servico) =>
{
    Fatura? fatura = servico.PorPedido(pedidoId);
    return fatura is null
        ? Results.NotFound(new { erro = $"não há fatura emitida para o pedido {pedidoId}" })
        : Results.Ok(FaturaResposta.De(fatura));
});

app.MapGet("/api/v1/faturas", (FaturaService servico) =>
    Results.Ok(servico.Todas().Select(FaturaResposta.De)));

app.Run();

// Cria o schema e a tabela na primeira subida. O banco pode ainda estar
// aceitando conexão quando o serviço sobe, principalmente dentro do Compose:
// por isso a tentativa é repetida antes de desistir, com uma mensagem que diz
// o que fazer. Na Aula 07 este laço vira um healthcheck declarado no YAML.
static void PrepararBanco(WebApplication app)
{
    const int tentativas = 10;
    for (int tentativa = 1; tentativa <= tentativas; tentativa++)
    {
        try
        {
            using var escopo = app.Services.CreateScope();
            var banco = escopo.ServiceProvider.GetRequiredService<FaturamentoDbContext>();
            banco.Database.EnsureCreated();

            // O contador de notas vive em memória e morre com o processo. Se o
            // serviço reiniciasse numerando do zero, a primeira emissão bateria
            // no índice único da tabela. A numeração recomeça de onde parou.
            List<string> emitidas = banco.Faturas.Select(f => f.NumeroNotaFiscal).ToList();
            int ultimo = emitidas.Count == 0 ? 0 : emitidas.Max(NumeroDaNota);
            NumeradorNotaFiscal.Instancia.IniciarEm(ultimo);

            Console.WriteLine($"[faturamento] schema pronto, numeração continua a partir de {ultimo}");
            return;
        }
        catch (Exception erro) when (tentativa < tentativas)
        {
            Console.WriteLine($"[faturamento] banco ainda não respondeu " +
                              $"(tentativa {tentativa} de {tentativas}): {erro.Message}");
            Thread.Sleep(2000);
        }
    }

    throw new InvalidOperationException(
        "não foi possível preparar o banco. Confira se o PostgreSQL está de pé e se " +
        "LOGITECH_DB_URL, LOGITECH_DB_USER e LOGITECH_DB_PASSWORD apontam para ele.");
}

// Extrai a parte numérica de "NF-000042". Devolve 0 para qualquer coisa fora
// do formato, para um registro estranho no banco não derrubar a subida.
static int NumeroDaNota(string numeroNotaFiscal)
{
    string digitos = numeroNotaFiscal.Replace("NF-", string.Empty);
    return int.TryParse(digitos, out int valor) ? valor : 0;
}

/// <summary>Representação da fatura que sai pela API.</summary>
public record FaturaResposta(string PedidoId, string NumeroNotaFiscal, decimal Valor,
                             string MeioPagamento, int PrazoDias, DateTimeOffset EmitidaEm,
                             DateTimeOffset Vencimento)
{
    public static FaturaResposta De(Fatura fatura) => new(
        fatura.PedidoId,
        fatura.NumeroNotaFiscal,
        fatura.Valor,
        fatura.MeioPagamento,
        fatura.PrazoDias,
        fatura.EmitidaEm,
        fatura.Vencimento());
}
