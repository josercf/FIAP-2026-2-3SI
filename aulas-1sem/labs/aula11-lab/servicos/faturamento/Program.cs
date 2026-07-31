// LogiTech Enterprise - Serviço de Faturamento (Bounded Context: Faturamento).
//
// SERVIÇO CONGELADO. NÃO É TAREFA DESTE LABORATÓRIO.
// ==================================================
// Ele nasceu na Aula 05, em C#/.NET, e chega aqui pronto para que quem
// faltou àquela aula consiga fazer a de hoje. O artefato da Aula 11 é o
// painel administrativo em Angular, dentro de `painel-admin/`.
//
// Duas coisas mudaram em relação à versão que vocês receberam na Aula 07, e
// as duas existem por causa do navegador:
//
// 1. CORS ligado (ADR-008). Até a Aula 07 todo consumidor deste serviço era
//    outro processo de servidor, e servidor ignora a política de mesma
//    origem. A partir de hoje quem chama é o Angular servido em
//    http://localhost:4200, e sem `Access-Control-Allow-Origin` o navegador
//    descarta a resposta depois de tê-la recebido. As origens permitidas vêm
//    de LOGITECH_CORS_ORIGINS.
//
// 2. Atraso deliberado e contador de cancelamento. A consulta de fatura
//    demora LOGITECH_FATURAMENTO_ATRASO_MS (padrão 800) de propósito, e o
//    serviço conta quantas requisições o cliente abandonou no meio.
//    É essa contagem que transforma "o switchMap cancela a inscrição
//    anterior" de afirmação em evidência: com switchMap o contador de
//    canceladas sobe; com mergeMap ele fica em zero.
//
// Rotas (contrato da plataforma, ADR-006 e ADR-008):
//   GET  /health
//   POST /api/v1/faturas
//   GET  /api/v1/faturas/{pedidoId}
//   GET  /api/v1/metricas          <- acrescentada na Aula 11, é a evidência
//   POST /api/v1/metricas/zerar    <- acrescentada na Aula 11
//
// Uso:
//   dotnet run --project servicos/faturamento
//   LOGITECH_FATURAMENTO_ATRASO_MS=1500 dotnet run --project servicos/faturamento

using System.Collections.Concurrent;
using System.Text.Json;
using System.Text.Json.Serialization;

var porta = Environment.GetEnvironmentVariable("LOGITECH_PORTA") ?? "5080";
var bancoUrl = Environment.GetEnvironmentVariable("LOGITECH_DB_URL") ?? "(não configurado)";
var atrasoMs = int.TryParse(
    Environment.GetEnvironmentVariable("LOGITECH_FATURAMENTO_ATRASO_MS"), out var lido)
    ? lido
    : 800;
var origens = (Environment.GetEnvironmentVariable("LOGITECH_CORS_ORIGINS")
               ?? "http://localhost:5173,http://localhost:4200")
    .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
var iniciadoEm = DateTimeOffset.UtcNow;

const string PoliticaCors = "logitech-frontends";

var construtor = WebApplication.CreateBuilder(args);
construtor.WebHost.UseUrls($"http://0.0.0.0:{porta}");
construtor.Services.ConfigureHttpJsonOptions(opcoes =>
{
    opcoes.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
    opcoes.SerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull;
});

// CORS por lista explícita de origens, e não AllowAnyOrigin. Origem é
// identidade: liberar qualquer uma seria abrir o serviço interno da LogiTech
// para qualquer página que o operador tiver aberta no navegador.
construtor.Services.AddCors(opcoes =>
{
    opcoes.AddPolicy(PoliticaCors, politica => politica
        .WithOrigins(origens)
        .AllowAnyHeader()
        .AllowAnyMethod());
});

var aplicacao = construtor.Build();
aplicacao.UseCors(PoliticaCors);

// Armazenamento em memória. Concorrente porque o Kestrel atende várias
// requisições ao mesmo tempo, e um Dictionary comum corromperia sob carga.
var faturas = new ConcurrentDictionary<long, Fatura>();
var numerador = new NumeradorNotaFiscal();
var metricas = new ContadorDeConsultas();

// Massa inicial: sem isso o painel abriria vazio e o aluno não teria o que
// consultar antes de emitir a primeira fatura à mão.
var massaInicial = new (long PedidoId, string Cliente, decimal Valor)[]
{
    (1001, "Supermercados Aurora", 4820.50m),
    (1002, "Farmácia Vida Plena", 1290.00m),
    (1003, "Metalúrgica Guarani", 15340.75m),
    (1004, "Distribuidora Sul Alimentos", 7655.20m),
    (1005, "Eletro Center Campinas", 2310.00m),
    (1006, "Cerâmica Ipiranga", 9875.40m),
    (1007, "Atacadão Nordeste", 22400.00m),
    (1008, "Papelaria Central", 640.90m),
};

foreach (var item in massaInicial)
{
    faturas[item.PedidoId] = new Fatura(
        item.PedidoId,
        numerador.Proximo(),
        item.Cliente,
        item.Valor,
        DateTimeOffset.UtcNow.AddDays(-(item.PedidoId % 30)));
}

aplicacao.MapGet("/health", () => Results.Ok(new
{
    status = "ok",
    servico = "faturamento",
    uptimeS = (long)(DateTimeOffset.UtcNow - iniciadoEm).TotalSeconds,
    faturasEmitidas = faturas.Count,
    banco = bancoUrl,
    atrasoMs,
    corsOrigens = origens,
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

// A consulta que o painel administrativo chama enquanto o operador digita.
//
// O CancellationToken vem do HttpContext.RequestAborted: o Kestrel o dispara
// quando o cliente fecha a conexão antes de a resposta sair. Quem fecha, do
// outro lado, é o switchMap do RxJS ao trocar de inscrição.
aplicacao.MapGet("/api/v1/faturas/{pedidoId:long}", async (long pedidoId, CancellationToken cancelamento) =>
{
    var sequencia = metricas.Receber(pedidoId);
    try
    {
        await Task.Delay(atrasoMs, cancelamento);
    }
    catch (OperationCanceledException)
    {
        metricas.Cancelar(sequencia, pedidoId);
        // 499 não é padrão HTTP, é a convenção do nginx para "cliente
        // desistiu". Ninguém vai ler este corpo: a conexão já morreu. Ele
        // existe para o log fazer sentido.
        return Results.StatusCode(499);
    }

    metricas.Concluir(sequencia, pedidoId);
    return faturas.TryGetValue(pedidoId, out var fatura)
        ? Results.Ok(fatura)
        : Results.NotFound(new { erro = "fatura não encontrada", detalhe = pedidoId.ToString() });
});

// A evidência do laboratório. O aluno digita um número de pedido no painel e
// lê estes contadores para descobrir quantas requisições morreram no meio.
aplicacao.MapGet("/api/v1/metricas", () => Results.Ok(metricas.Instantaneo()));

aplicacao.MapPost("/api/v1/metricas/zerar", () =>
{
    metricas.Zerar();
    return Results.Ok(metricas.Instantaneo());
});

Console.WriteLine("=== LogiTech Enterprise - Serviço de Faturamento ===");
Console.WriteLine($"[HTTP] faturamento escutando na porta {porta}");
Console.WriteLine($"[CORS] origens permitidas: {string.Join(", ", origens)}");
Console.WriteLine($"[LENTO] atraso deliberado de {atrasoMs} ms por consulta de fatura");
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
/// lacuna TODO-5, entregue sem sincronização de propósito, para que o teste
/// de 100 emissões concorrentes falhe de verdade com número repetido antes de
/// o aluno consertar.
/// </summary>
sealed class NumeradorNotaFiscal
{
    private long _ultimo;

    public string Proximo() => $"NF-{Interlocked.Increment(ref _ultimo):D8}";
}

/// <summary>
/// Contabilidade das consultas de fatura: recebidas, concluídas e abandonadas
/// pelo cliente.
///
/// É o instrumento de medição da Aula 11. Sem ele, "o switchMap cancela a
/// requisição anterior" seria uma afirmação que o aluno teria que aceitar de
/// boa fé. Com ele, a afirmação vira um número que sobe na tela.
/// </summary>
sealed class ContadorDeConsultas
{
    private long _recebidas;
    private long _concluidas;
    private long _canceladas;
    private readonly ConcurrentQueue<string> _linhaDoTempo = new();

    public long Receber(long pedidoId)
    {
        var sequencia = Interlocked.Increment(ref _recebidas);
        Registrar($"#{sequencia} recebida   pedido={pedidoId}");
        return sequencia;
    }

    public void Concluir(long sequencia, long pedidoId)
    {
        Interlocked.Increment(ref _concluidas);
        Registrar($"#{sequencia} concluida  pedido={pedidoId}");
        Console.WriteLine($"[FATURA] consulta #{sequencia} do pedido {pedidoId} concluída");
    }

    public void Cancelar(long sequencia, long pedidoId)
    {
        Interlocked.Increment(ref _canceladas);
        Registrar($"#{sequencia} CANCELADA  pedido={pedidoId}");
        Console.WriteLine($"[FATURA] consulta #{sequencia} do pedido {pedidoId} CANCELADA pelo cliente");
    }

    public object Instantaneo() => new
    {
        consultasRecebidas = Interlocked.Read(ref _recebidas),
        consultasConcluidas = Interlocked.Read(ref _concluidas),
        consultasCanceladas = Interlocked.Read(ref _canceladas),
        linhaDoTempo = _linhaDoTempo.ToArray()
    };

    public void Zerar()
    {
        Interlocked.Exchange(ref _recebidas, 0);
        Interlocked.Exchange(ref _concluidas, 0);
        Interlocked.Exchange(ref _canceladas, 0);
        _linhaDoTempo.Clear();
    }

    private void Registrar(string linha)
    {
        _linhaDoTempo.Enqueue($"{DateTimeOffset.UtcNow:HH:mm:ss.fff} {linha}");
        while (_linhaDoTempo.Count > 40 && _linhaDoTempo.TryDequeue(out _))
        {
            // Janela deslizante: a evidência é o comportamento recente, e um
            // log infinito em memória seria um vazamento com nome bonito.
        }
    }
}
