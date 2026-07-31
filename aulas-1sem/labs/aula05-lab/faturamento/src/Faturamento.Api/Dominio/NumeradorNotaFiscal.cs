namespace Faturamento.Api.Dominio;

/// <summary>
/// TODO-5 (Singleton thread-safe): gerador do número sequencial da nota fiscal.
/// </summary>
/// <remarks>
/// <para>Número de nota fiscal é sequencial e único por natureza: dois pedidos
/// com a mesma nota é problema fiscal, não bug de tela. Por isso o contador
/// mora em uma instância única compartilhada por todas as requisições, e é
/// exatamente aí que mora o perigo.</para>
///
/// <para>Este Singleton está <strong>quebrado de propósito</strong>, em dois
/// pontos:</para>
/// <list type="number">
///   <item>a criação da instância (<c>??=</c>) não é sincronizada: duas threads
///         chegando juntas na primeira chamada criam dois numeradores, cada um
///         com o seu contador;</item>
///   <item><c>Proximo()</c> faz ler, somar e gravar em três passos separados.
///         Entre a leitura e a gravação, outra thread pode ler o mesmo valor e
///         produzir o mesmo número de nota.</item>
/// </list>
///
/// <para>A chamada a <c>Thread.Yield()</c> no meio do método não cria o defeito:
/// ela apenas alarga uma janela que já existe, para a corrida aparecer em 100
/// execuções em vez de aparecer uma vez a cada tantos milhares. Tirar o
/// <c>Yield</c> não conserta nada.</para>
///
/// <h3>O que você faz aqui</h3>
/// <list type="number">
///   <item>Escreva primeiro o teste do TODO-6 e veja-o falhar com números
///         repetidos. Registre a quantidade em
///         <c>docs/EVIDENCIAS.md</c>, no campo <c>NOTAS_DUPLICADAS_ANTES</c>.</item>
///   <item>Só então torne este Singleton thread-safe: a criação da instância
///         (<c>Lazy&lt;T&gt;</c> ou campo <c>static readonly</c>) e o incremento
///         do contador (<c>lock</c> ou <c>Interlocked.Increment</c>).</item>
///   <item>Rode o teste de novo e registre <c>NOTAS_DUPLICADAS_DEPOIS</c>.</item>
/// </list>
///
/// <para>Não mude a forma do número devolvido: o formato <c>NF-000001</c>, com
/// seis dígitos, é lido pelo serviço de Pedidos e pelo verificador.</para>
/// </remarks>
public sealed class NumeradorNotaFiscal
{
    // TODO-5: criação da instância sem sincronização nenhuma.
    private static NumeradorNotaFiscal? _instancia;

    private int _ultimo;

    private NumeradorNotaFiscal()
    {
    }

    public static NumeradorNotaFiscal Instancia => _instancia ??= new NumeradorNotaFiscal();

    /// <summary>Devolve o próximo número de nota fiscal, no formato NF-000001.</summary>
    public string Proximo()
    {
        // TODO-5: ler, somar e gravar em três passos separados é o que permite
        // duas threads devolverem o mesmo número.
        int atual = _ultimo;
        Thread.Yield();
        atual = atual + 1;
        _ultimo = atual;

        return $"NF-{atual:D6}";
    }

    /// <summary>
    /// Continua a numeração a partir do último número já gravado no banco.
    /// </summary>
    /// <remarks>
    /// Chamado uma única vez, na subida do serviço. Sem isto, cada reinício
    /// recomeçaria em NF-000001 e esbarraria no índice único da tabela de
    /// faturas: estado em memória não sobrevive ao processo, e o Singleton
    /// precisa ser reconstruído a partir de onde a verdade mora, que é o banco.
    /// </remarks>
    public void IniciarEm(int ultimoEmitido)
    {
        _ultimo = ultimoEmitido;
    }

    /// <summary>
    /// Zera o contador. Existe só para os testes conseguirem partir sempre do
    /// mesmo ponto: nenhum código de produção chama este método.
    /// </summary>
    public void ReiniciarParaTeste()
    {
        IniciarEm(0);
    }
}
