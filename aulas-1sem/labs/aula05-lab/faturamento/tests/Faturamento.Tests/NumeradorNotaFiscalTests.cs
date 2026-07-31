using System.Collections.Concurrent;
using Faturamento.Api.Dominio;
using Xunit;

namespace Faturamento.Tests;

/// <summary>
/// O Singleton que numera as notas fiscais da LogiTech.
/// </summary>
/// <remarks>
/// <para>O teste que já está aqui é sequencial: uma chamada depois da outra,
/// uma thread só. Ele passa mesmo com o Singleton quebrado, e é essa a
/// armadilha que esta lacuna quer mostrar. Defeito de concorrência não aparece
/// em teste sequencial: ele espera a produção.</para>
///
/// <para><strong>TODO-6:</strong> escreva o teste que dispara 100 emissões
/// concorrentes e prova que não existe número repetido. Faça isso
/// <strong>antes</strong> de corrigir o TODO-5: o teste precisa falhar de
/// verdade primeiro, com número de nota duplicado, e o número de duplicatas
/// vai para <c>docs/EVIDENCIAS.md</c>, no campo
/// <c>NOTAS_DUPLICADAS_ANTES</c>.</para>
///
/// <para>Forma esperada do teste:</para>
/// <list type="number">
///   <item>pegue <c>NumeradorNotaFiscal.Instancia</c> e chame
///         <c>ReiniciarParaTeste()</c>, para partir do zero;</item>
///   <item>guarde os números em uma coleção concorrente
///         (<c>ConcurrentBag&lt;string&gt;</c>);</item>
///   <item>dispare 100 chamadas concorrentes a <c>Proximo()</c>. Com
///         <c>Task.Run</c> mais <c>Task.WhenAll</c> a concorrência é maior e o
///         defeito aparece com mais facilidade do que com <c>Parallel.For</c>,
///         principalmente em máquina de poucos núcleos;</item>
///   <item>conte as duplicatas com
///         <c>numeros.Count - numeros.Distinct().Count()</c>;</item>
///   <item>termine com <c>Assert.Equal(0, duplicadas)</c>. A mensagem de falha do
///         xUnit mostra quantas foram: é dela que sai o valor de
///         <c>NOTAS_DUPLICADAS_ANTES</c>.</item>
/// </list>
///
/// <para>Depois de corrigir o TODO-5, rode de novo, confirme que passa e
/// registre <c>NOTAS_DUPLICADAS_DEPOIS: 0</c>.</para>
/// </remarks>
public class NumeradorNotaFiscalTests
{
    [Fact]
    public void ChamadasSequenciaisDevolvemNumerosCrescentes()
    {
        NumeradorNotaFiscal numerador = NumeradorNotaFiscal.Instancia;
        numerador.ReiniciarParaTeste();

        string primeiro = numerador.Proximo();
        string segundo = numerador.Proximo();

        Assert.Equal("NF-000001", primeiro);
        Assert.Equal("NF-000002", segundo);
    }

    [Fact]
    public void FormatoDoNumeroSegueOContratoDaPlataforma()
    {
        NumeradorNotaFiscal numerador = NumeradorNotaFiscal.Instancia;
        numerador.ReiniciarParaTeste();

        string numero = numerador.Proximo();

        Assert.StartsWith("NF-", numero);
        Assert.Equal(9, numero.Length);
    }

    // TODO-6: escreva aqui o teste de concorrência descrito no comentário desta
    // classe. Ele precisa disparar 100 emissões concorrentes, contar quantos
    // números vieram repetidos e exigir zero duplicatas.
    //
    // Deixe o `using System.Collections.Concurrent;` do topo do arquivo: ele já
    // está aqui para você usar a ConcurrentBag.
}
