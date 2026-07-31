import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { interceptadorDeAutorizacao } from './nucleo/autorizacao';
import { interceptadorDeCorrelacao } from './nucleo/correlacao';

/**
 * A configuração do injetor raiz da aplicação. CONGELADA na Aula 16.
 *
 * A ordem dos interceptadores é a ordem da pilha: o de autorização entra
 * primeiro e o de correlação por fora dele, de modo que o cabeçalho de
 * correlação apareça também nas requisições que já saem carimbadas com token.
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),

    // TODO-1b resolvido: a cadeia HTTP montada pelo injetor, com o
    // interceptador de correlação empilhado por fora do backend.
    provideHttpClient(
      withInterceptors([interceptadorDeAutorizacao, interceptadorDeCorrelacao]),
    ),
  ],
};
