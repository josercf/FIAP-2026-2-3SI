// LogiTech Enterprise - validação de JWT por JWKS em C#, só com a BCL.
//
// O mesmo contrato que o `seguranca.py` dos serviços Python e o
// `Seguranca.java` do serviço de Pedidos cumprem. Nenhum pacote NuGet novo:
// `System.Security.Cryptography` já verifica RSA com SHA-256, e
// `System.Text.Json` já lê o JWKS.
//
// Contrato (ADR-009):
//
//     LOGITECH_AUTH_ATIVA       false por padrão; a Aula 14 liga
//     LOGITECH_OIDC_ISSUER      o `iss` que o token precisa trazer
//     LOGITECH_OIDC_JWKS_URL    de onde as chaves públicas são lidas
//
// O papel viaja em `realm_access.roles`. Ler daqui, e não de
// `resource_access.<client>.roles`, é o que faz o mesmo token valer em Java,
// C#, Python e Node.
//
// Não é tarefa. Este arquivo vem pronto.

using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

/// <summary>Resultado da validação: 200, 401 ou 403, e o motivo.</summary>
public sealed record Veredito(int Status, string Motivo, string[] Papeis)
{
    public bool Autorizado => Status == 200;
}

public static class Seguranca
{
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(5) };
    private static readonly Dictionary<string, RSA> Chaves = new();
    private static DateTimeOffset _chavesLidasEm = DateTimeOffset.MinValue;
    private static readonly TimeSpan ValidadeDoCache = TimeSpan.FromMinutes(5);
    private static readonly SemaphoreSlim Trava = new(1, 1);

    private static string Env(string nome, string padrao)
    {
        var valor = Environment.GetEnvironmentVariable(nome);
        return string.IsNullOrWhiteSpace(valor) ? padrao : valor;
    }

    /// <summary>A autenticação só entra em vigor com LOGITECH_AUTH_ATIVA ligada.</summary>
    public static bool Ativa()
        => Env("LOGITECH_AUTH_ATIVA", "false").Trim().ToLowerInvariant()
            is "1" or "true" or "sim" or "on";

    private static byte[] B64Url(string dado)
    {
        var texto = dado.Replace('-', '+').Replace('_', '/');
        return Convert.FromBase64String(texto.PadRight(texto.Length + (4 - texto.Length % 4) % 4, '='));
    }

    /// <summary>
    /// Baixa e guarda as chaves públicas do provedor de identidade.
    ///
    /// O cache de cinco minutos é o motivo de o backend não consultar o
    /// Keycloak a cada requisição: o token traz o `kid` que diz qual chave
    /// usar, e a verificação acontece dentro deste processo.
    /// </summary>
    private static async Task CarregarChavesAsync(bool forcar)
    {
        await Trava.WaitAsync();
        try
        {
            if (!forcar && Chaves.Count > 0
                && DateTimeOffset.UtcNow - _chavesLidasEm < ValidadeDoCache) return;

            var url = Env("LOGITECH_OIDC_JWKS_URL", "");
            if (string.IsNullOrWhiteSpace(url))
                throw new InvalidOperationException("LOGITECH_OIDC_JWKS_URL não configurada");

            using var documento = JsonDocument.Parse(await Http.GetStringAsync(url));
            foreach (var rsa in Chaves.Values) rsa.Dispose();
            Chaves.Clear();

            foreach (var chave in documento.RootElement.GetProperty("keys").EnumerateArray())
            {
                if (chave.GetProperty("kty").GetString() != "RSA") continue;
                var kid = chave.GetProperty("kid").GetString()!;
                var rsa = RSA.Create();
                rsa.ImportParameters(new RSAParameters
                {
                    Modulus = B64Url(chave.GetProperty("n").GetString()!),
                    Exponent = B64Url(chave.GetProperty("e").GetString()!)
                });
                Chaves[kid] = rsa;
            }
            _chavesLidasEm = DateTimeOffset.UtcNow;
        }
        finally
        {
            Trava.Release();
        }
    }

    /// <summary>
    /// Valida o cabeçalho `Authorization` e confere o papel.
    ///
    /// 401 é "não sei quem você é". 403 é "sei quem você é e não é o
    /// bastante". A diferença entre os dois é conteúdo de aula e critério do
    /// verificador da Aula 16.
    /// </summary>
    public static async Task<Veredito> ExigirAsync(string? cabecalho, params string[] aceitos)
    {
        if (!Ativa()) return new Veredito(200, "autenticação desligada", Array.Empty<string>());

        if (string.IsNullOrWhiteSpace(cabecalho)
            || !cabecalho.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
            return new Veredito(401, "cabeçalho Authorization ausente ou sem o esquema Bearer",
                                Array.Empty<string>());

        var partes = cabecalho[7..].Trim().Split('.');
        if (partes.Length != 3)
            return new Veredito(401, "o token não tem as três partes de um JWT", Array.Empty<string>());

        JsonElement cabecalhoJwt, payload;
        byte[] assinatura;
        try
        {
            cabecalhoJwt = JsonDocument.Parse(B64Url(partes[0])).RootElement;
            payload = JsonDocument.Parse(B64Url(partes[1])).RootElement;
            assinatura = B64Url(partes[2]);
        }
        catch (Exception erro)
        {
            return new Veredito(401, $"token malformado: {erro.Message}", Array.Empty<string>());
        }

        if (cabecalhoJwt.TryGetProperty("alg", out var alg) && alg.GetString() != "RS256")
            return new Veredito(401, "algoritmo recusado: este serviço só aceita RS256",
                                Array.Empty<string>());

        var kid = cabecalhoJwt.TryGetProperty("kid", out var k) ? k.GetString() ?? "" : "";

        try
        {
            await CarregarChavesAsync(false);
            if (!Chaves.ContainsKey(kid)) await CarregarChavesAsync(true);   // o provedor girou a chave
        }
        catch (Exception erro)
        {
            return new Veredito(401, $"não foi possível ler o JWKS: {erro.Message}",
                                Array.Empty<string>());
        }

        if (!Chaves.TryGetValue(kid, out var rsaChave))
            return new Veredito(401, $"kid {kid} não está no JWKS", Array.Empty<string>());

        var assinado = Encoding.ASCII.GetBytes($"{partes[0]}.{partes[1]}");
        if (!rsaChave.VerifyData(assinado, assinatura, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1))
            return new Veredito(401, "assinatura inválida", Array.Empty<string>());

        if (payload.TryGetProperty("exp", out var exp)
            && exp.GetInt64() < DateTimeOffset.UtcNow.ToUnixTimeSeconds())
            return new Veredito(401, "token expirado", Array.Empty<string>());

        var issuerEsperado = Env("LOGITECH_OIDC_ISSUER", "");
        var issuerDoToken = payload.TryGetProperty("iss", out var iss) ? iss.GetString() : null;
        if (!string.IsNullOrWhiteSpace(issuerEsperado) && issuerEsperado != issuerDoToken)
            // O `iss` que o Keycloak grava é o endereço pelo qual o NAVEGADOR
            // chegou (localhost:8090); o JWKS é buscado pelo endereço da rede
            // interna (keycloak:8090). São dois valores e duas variáveis.
            return new Veredito(401,
                $"issuer divergente: o token traz {issuerDoToken} e este serviço espera {issuerEsperado}",
                Array.Empty<string>());

        var papeis = Array.Empty<string>();
        if (payload.TryGetProperty("realm_access", out var realm)
            && realm.TryGetProperty("roles", out var lista))
        {
            papeis = lista.EnumerateArray()
                          .Select(p => (p.GetString() ?? "").ToUpperInvariant())
                          .Where(p => p.Length > 0).ToArray();
        }

        if (aceitos.Length > 0 && !aceitos.Any(a => papeis.Contains(a.ToUpperInvariant())))
            return new Veredito(403,
                $"este token tem [{string.Join(", ", papeis)}] e a rota exige um de [{string.Join(", ", aceitos)}]",
                papeis);

        return new Veredito(200, "ok", papeis);
    }
}
