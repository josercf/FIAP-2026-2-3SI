// LogiTech Enterprise - Serviço de Faturamento (Bounded Context: Faturamento).
//
// ATENÇÃO, LEIA ANTES DE COMPARAR COM A AULA 05
// ---------------------------------------------
// Versão **mínima**, escrita para o laboratório da Aula 07 ter o que
// orquestrar. Cumpre o contrato da plataforma (ADR-006): porta 5080, as três
// rotas e `/health` devolvendo {"status":"ok"}.
//
// O que ela **não** é: a implementação da Aula 05. Lá o serviço nasce com
// IFaturaRepository sobre EF Core, injeção por construtor e um
// NumeradorNotaFiscal Singleton thread-safe, que é o conteúdo daquela aula.
// Aqui as faturas vivem em memória, porque o assunto de hoje é orquestração.
// As variáveis LOGITECH_DB_* já chegam pelo Compose e ficam declaradas em
// /health: quando a versão da Aula 05 substituir esta pasta, o
// docker-compose.yml não muda uma linha.
//
// Não é tarefa. Não editem este arquivo.
//
// Rotas (ADR-006):
//   GET  /health
//   POST /api/v1/faturas
//   GET  /api/v1/faturas/{pedidoId}

using System.Collections.Concurrent;
using System.Text.Json;
using System.Text.Json.Serialization;

var porta = Environment.GetEnvironmentVariable("LOGITECH_PORTA") ?? "5080";
var bancoUrl = Environment.GetEnvironmentVariable("LOGITECH_DB_URL") ?? "(não configurado)";
var iniciadoEm = DateTimeOffset.UtcNow;

var construtor = WebApplication.CreateBuilder(args);
construtor.WebHost.UseUrls($"http://0.0.0.0:{porta}");
construtor.Services.ConfigureHttpJsonOptions(opcoes =>
{
    opcoes.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
    opcoes.SerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull;
});

var aplicacao = construtor.Build();

// Armazenamento em memória. Concorrente porque o Kestrel atende várias
// requisições ao mesmo tempo, e um Dictionary comum corromperia sob carga.
var faturas = new ConcurrentDictionary<long, Fatura>();
var numerador = new NumeradorNotaFiscal();

aplicacao.MapGet("/health", () => Results.Ok(new
{
    status = "ok",
    servico = "faturamento",
    uptimeS = (long)(DateTimeOffset.UtcNow - iniciadoEm).TotalSeconds,
    faturasEmitidas = faturas.Count,
    banco = bancoUrl,
    persistencia = "memória (a versão da Aula 05 usa EF Core sobre o schema faturamento)"
}));

aplicacao.MapPost("/api/v1/faturas", (EntradaFatura entrada) =>
{
    if (entrada.PedidoId <= 0)
    {
        return Results.BadRequest(new { erro = "campo obrigatório ausente", detalhe = "pedidoId" });
    }

    var fatura = faturas.GetOrAdd(entrada.PedidoId, id => new Fatura(
        PedidoId: id,
        Numero: numerador.Proximo(),
        Cliente: string.IsNullOrWhiteSpace(entrada.Cliente) ? "não informado" : entrada.Cliente,
        Valor: entrada.Valor,
        EmitidaEm: DateTimeOffset.UtcNow));

    return Results.Created($"/api/v1/faturas/{fatura.PedidoId}", fatura);
});

aplicacao.MapGet("/api/v1/faturas/{pedidoId:long}", (long pedidoId) =>
    faturas.TryGetValue(pedidoId, out var fatura)
        ? Results.Ok(fatura)
        : Results.NotFound(new { erro = "fatura não encontrada", detalhe = pedidoId.ToString() }));

Console.WriteLine("=== LogiTech Enterprise - Serviço de Faturamento ===");
Console.WriteLine($"[HTTP] faturamento escutando na porta {porta}");
Console.WriteLine($"[DB]   variável LOGITECH_DB_URL recebida: {bancoUrl}");

aplicacao.Run();

/// <summary>Uma fatura emitida para um pedido.</summary>
record Fatura(long PedidoId, string Numero, string Cliente, decimal Valor, DateTimeOffset EmitidaEm);

/// <summary>O que o serviço de Pedidos envia ao pedir a emissão.</summary>
record EntradaFatura(long PedidoId, string? Cliente, decimal Valor);

/// <summary>
/// Gera o número sequencial da nota fiscal.
///
/// Aqui já vem sincronizado com Interlocked. Na Aula 05 esta classe é a
/// lacuna TODO-5, entregue **sem** sincronização de propósito, para que o
/// teste de 100 emissões concorrentes falhe de verdade com número repetido
/// antes de o aluno consertar.
/// </summary>
sealed class NumeradorNotaFiscal
{
    private long _ultimo;

    public string Proximo() => $"NF-{Interlocked.Increment(ref _ultimo):D8}";
}
