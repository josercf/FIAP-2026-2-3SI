import { HttpInterceptorFn } from '@angular/common/http';

/**
 * Cabeçalho de correlação, o mesmo que o `ai-gateway` da Aula 07 registra no
 * log de cada chamada.
 */
export const CABECALHO_CORRELACAO = 'X-Correlation-Id';

let sequencia = 0;

/** Um identificador por requisição, legível no log dos dois lados. */
export function proximoIdDeCorrelacao(): string {
  sequencia += 1;
  return `painel-admin-${Date.now().toString(36)}-${sequencia}`;
}

/**
 * Interceptador que carimba toda requisição HTTP do painel com um
 * identificador de correlação.
 *
 * Já vem pronto. O que falta é **registrá-lo**, e é isso que o TODO-1b pede.
 *
 * Repare no formato: uma função que recebe a requisição e o próximo elo da
 * corrente, devolve o que o próximo devolver, e no meio faz o que quiser.
 * É o Decorator da Aula 06, agora aplicado à cadeia de HTTP: o `HttpClient`
 * não sabe que existe um interceptador, e o interceptador não sabe quem está
 * chamando. Quem monta a pilha é o injetor, no `app.config.ts`.
 *
 * Numa plataforma com sete serviços em cinco linguagens, isto é o que
 * permite pegar um erro no painel administrativo e achar, no log do serviço
 * de Faturamento em C#, exatamente a requisição que o causou.
 */
export const interceptadorDeCorrelacao: HttpInterceptorFn = (requisicao, proximo) => {
  const carimbada = requisicao.clone({
    setHeaders: { [CABECALHO_CORRELACAO]: proximoIdDeCorrelacao() },
  });
  return proximo(carimbada);
};
