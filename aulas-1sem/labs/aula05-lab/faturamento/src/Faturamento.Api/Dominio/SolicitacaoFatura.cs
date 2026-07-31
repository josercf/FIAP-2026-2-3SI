namespace Faturamento.Api.Dominio;

/// <summary>
/// O que o serviço de Pedidos (Java) envia no <c>POST /api/v1/faturas</c>.
/// </summary>
/// <remarks>
/// Os nomes dos campos são o contrato entre dois serviços escritos em
/// linguagens diferentes: eles precisam bater com o record
/// <c>SolicitacaoFatura</c> do lado Java. Renomear um campo aqui quebra a
/// integração, mesmo com os dois serviços compilando. Não é tarefa.
/// </remarks>
public record SolicitacaoFatura(string PedidoId, string Cliente, decimal Valor,
                                string MeioPagamento, int PrazoDias);
