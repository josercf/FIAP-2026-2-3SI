import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { interceptadorDeCorrelacao } from './nucleo/correlacao';

/**
 * RESGATE do TODO-1b. Veja `resgate/README.md` antes de copiar.
 *
 * A configuração do injetor raiz da aplicação.
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),

    // TODO-1b resolvido: a cadeia HTTP montada pelo injetor, com o
    // interceptador de correlação empilhado por fora do backend.
    provideHttpClient(withInterceptors([interceptadorDeCorrelacao])),
  ],
};
