import { HttpInterceptorFn } from '@angular/common/http';

import { tokenAtual } from './pkce';

/**
 * Interceptador que carimba `Authorization: Bearer` em toda requisição do
 * painel.
 *
 * É o mesmo padrão do `interceptadorDeCorrelacao`: o Decorator da Aula 06
 * aplicado à cadeia de HTTP. Nenhum service precisa saber que existe token, e
 * é por isso que ligar a autenticação neste painel custou zero linha dentro de
 * `FaturamentoService` e de `FrotaService`.
 *
 * Só carimba requisição que sai para a plataforma. Um token da LogiTech
 * enviado para um endereço de terceiro seria vazamento de credencial, e a
 * conferência de origem é o que impede isso.
 */
export const interceptadorDeAutorizacao: HttpInterceptorFn = (requisicao, proximo) => {
  const token = tokenAtual();
  if (!token || !/^https?:\/\/(localhost|127\.0\.0\.1)[:/]/.test(requisicao.url)) {
    return proximo(requisicao);
  }
  return proximo(requisicao.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};
